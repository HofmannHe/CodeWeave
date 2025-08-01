"""
工作流执行API路由

提供工作流执行相关的RESTful API端点。
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer
from starlette.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from ..dependencies import get_current_user, get_execution_adapter, get_workflow_adapter
from ..schemas import (
    WorkflowExecutionResponse, WorkflowExecutionCreateRequest, WorkflowExecutionUpdateRequest,
    PaginatedResponse, ErrorResponse
)
from ...database.schemas import (
    UserProfile, WorkflowExecution, WorkflowExecutionCreate as DBWorkflowExecutionCreate,
    WorkflowExecutionUpdate as DBWorkflowExecutionUpdate, ExecutionStatus
)
from ...database.adapters import ExecutionAdapter, WorkflowAdapter
from ...core.exceptions import DatabaseError, ValidationError, WorkflowError
from ...core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/executions", tags=["executions"])
security = HTTPBearer()


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.execution_connections: dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, execution_id: Optional[str] = None):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if execution_id:
            if execution_id not in self.execution_connections:
                self.execution_connections[execution_id] = []
            self.execution_connections[execution_id].append(websocket)
        
        logger.info(f"WebSocket连接已建立，执行ID: {execution_id}")
    
    def disconnect(self, websocket: WebSocket, execution_id: Optional[str] = None):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if execution_id and execution_id in self.execution_connections:
            if websocket in self.execution_connections[execution_id]:
                self.execution_connections[execution_id].remove(websocket)
            
            # 如果没有连接了，删除执行ID
            if not self.execution_connections[execution_id]:
                del self.execution_connections[execution_id]
        
        logger.info(f"WebSocket连接已断开，执行ID: {execution_id}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
    
    async def send_execution_update(self, execution_id: str, message: dict):
        """发送执行更新消息"""
        if execution_id in self.execution_connections:
            disconnected = []
            for connection in self.execution_connections[execution_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"发送执行更新失败: {e}")
                    disconnected.append(connection)
            
            # 清理断开的连接
            for connection in disconnected:
                self.disconnect(connection, execution_id)
    
    async def broadcast(self, message: str):
        """广播消息"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)


# 全局连接管理器
manager = ConnectionManager()


@router.post("/", response_model=WorkflowExecutionResponse)
async def start_workflow_execution(
    execution_data: WorkflowExecutionCreateRequest,
    current_user: UserProfile = Depends(get_current_user),
    execution_adapter: ExecutionAdapter = Depends(get_execution_adapter),
    workflow_adapter: WorkflowAdapter = Depends(get_workflow_adapter)
):
    """
    启动工作流执行
    
    - **workflow_id**: 工作流ID
    - **input_data**: 输入数据
    - **description**: 执行描述（可选）
    """
    try:
        # 验证工作流是否存在
        workflow = await workflow_adapter.get_by_id(None, execution_data.workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="工作流不存在"
            )
        
        # 检查用户权限
        if workflow.created_by != current_user.id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="无权限执行此工作流"
            )
        
        # 生成Temporal工作流ID
        import uuid
        temporal_workflow_id = f"workflow-{workflow.id}-{uuid.uuid4().hex[:8]}"
        temporal_run_id = f"run-{uuid.uuid4().hex[:8]}"
        
        # 创建执行记录
        db_execution_data = DBWorkflowExecutionCreate(
            workflow_id=execution_data.workflow_id,
            temporal_workflow_id=temporal_workflow_id,
            temporal_run_id=temporal_run_id,
            status=ExecutionStatus.PENDING,
            input_data=execution_data.input_data,
            created_by=current_user.id
        )
        
        execution = await execution_adapter.create(db_execution_data)
        
        # TODO: 启动Temporal工作流
        # 这里应该调用Temporal客户端启动工作流
        logger.info(f"工作流执行已创建: {execution.id}")
        
        # 发送WebSocket更新
        await manager.send_execution_update(
            str(execution.id),
            {
                "type": "execution_started",
                "execution_id": str(execution.id),
                "status": execution.status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return WorkflowExecutionResponse.from_orm(execution)
        
    except ValidationError as e:
        logger.error(f"启动工作流执行验证失败: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"启动工作流执行数据库错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"启动工作流执行未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="启动工作流执行失败"
        )


@router.get("/", response_model=PaginatedResponse[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[UUID] = Query(None, description="工作流ID过滤"),
    status: Optional[ExecutionStatus] = Query(None, description="状态过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    current_user: UserProfile = Depends(get_current_user),
    execution_adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """
    获取工作流执行列表
    
    支持按工作流ID和状态过滤，支持分页。
    """
    try:
        # 构建过滤条件
        filters = {"created_by": current_user.id}
        if workflow_id:
            filters["workflow_id"] = workflow_id
        if status:
            filters["status"] = status
        
        # 计算偏移量
        offset = (page - 1) * size
        
        # 获取执行列表
        executions = await execution_adapter.list_records(
            None,
            filters=filters,
            limit=size,
            offset=offset,
            order_by="-created_at"
        )
        
        # 获取总数
        total = await execution_adapter.count(None, filters=filters)
        
        # 转换为响应模型
        execution_responses = [
            WorkflowExecutionResponse.from_orm(execution)
            for execution in executions
        ]
        
        return PaginatedResponse(
            items=execution_responses,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size if total > 0 else 0
        )
        
    except DatabaseError as e:
        logger.error(f"获取执行列表数据库错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"获取执行列表未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取执行列表失败"
        )


@router.get("/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    execution_adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """
    获取工作流执行详情
    
    - **execution_id**: 执行ID
    """
    try:
        execution = await execution_adapter.get_by_id(None, execution_id)
        if not execution:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        # 检查用户权限
        if execution.created_by != current_user.id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="无权限访问此执行记录"
            )
        
        return WorkflowExecutionResponse.from_orm(execution)
        
    except DatabaseError as e:
        logger.error(f"获取执行详情数据库错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"获取执行详情未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取执行详情失败"
        )


@router.put("/{execution_id}", response_model=WorkflowExecutionResponse)
async def update_execution(
    execution_id: UUID,
    execution_update: WorkflowExecutionUpdateRequest,
    current_user: UserProfile = Depends(get_current_user),
    execution_adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """
    更新工作流执行状态
    
    - **execution_id**: 执行ID
    - **status**: 新状态
    - **output_data**: 输出数据（可选）
    - **error_message**: 错误消息（可选）
    """
    try:
        # 获取现有执行记录
        execution = await execution_adapter.get_by_id(None, execution_id)
        if not execution:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        # 检查用户权限
        if execution.created_by != current_user.id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="无权限修改此执行记录"
            )
        
        # 更新执行记录
        update_data = DBWorkflowExecutionUpdate(**execution_update.dict(exclude_unset=True))
        
        # 设置时间戳
        if execution_update.status == ExecutionStatus.RUNNING and not execution.started_at:
            update_data.started_at = datetime.utcnow()
        elif execution_update.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]:
            update_data.completed_at = datetime.utcnow()
        
        # 创建更新后的执行对象
        updated_execution_data = execution.dict()
        updated_execution_data.update(update_data.dict(exclude_unset=True))
        updated_execution = WorkflowExecution(**updated_execution_data)
        
        # 保存更新
        result = await execution_adapter.update(updated_execution)
        
        # 发送WebSocket更新
        await manager.send_execution_update(
            str(execution_id),
            {
                "type": "execution_updated",
                "execution_id": str(execution_id),
                "status": result.status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"工作流执行已更新: {execution_id}")
        return WorkflowExecutionResponse.from_orm(result)
        
    except ValidationError as e:
        logger.error(f"更新执行记录验证失败: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"更新执行记录数据库错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"更新执行记录未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="更新执行记录失败"
        )


@router.post("/{execution_id}/cancel", response_model=WorkflowExecutionResponse)
async def cancel_execution(
    execution_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    execution_adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """
    取消工作流执行
    
    - **execution_id**: 执行ID
    """
    try:
        # 获取现有执行记录
        execution = await execution_adapter.get_by_id(None, execution_id)
        if not execution:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        # 检查用户权限
        if execution.created_by != current_user.id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="无权限取消此执行"
            )
        
        # 检查执行状态
        if execution.status not in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING, ExecutionStatus.PAUSED]:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="只能取消待执行、运行中或暂停的工作流"
            )
        
        # 更新状态为已取消
        update_data = DBWorkflowExecutionUpdate(
            status=ExecutionStatus.CANCELLED,
            completed_at=datetime.utcnow()
        )
        
        updated_execution_data = execution.dict()
        updated_execution_data.update(update_data.dict(exclude_unset=True))
        updated_execution = WorkflowExecution(**updated_execution_data)
        
        result = await execution_adapter.update(updated_execution)
        
        # TODO: 取消Temporal工作流
        # 这里应该调用Temporal客户端取消工作流
        
        # 发送WebSocket更新
        await manager.send_execution_update(
            str(execution_id),
            {
                "type": "execution_cancelled",
                "execution_id": str(execution_id),
                "status": result.status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"工作流执行已取消: {execution_id}")
        return WorkflowExecutionResponse.from_orm(result)
        
    except DatabaseError as e:
        logger.error(f"取消执行数据库错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"取消执行未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="取消执行失败"
        )


@router.get("/{execution_id}/history", response_model=List[dict])
async def get_execution_history(
    execution_id: UUID,
    current_user: UserProfile = Depends(get_current_user),
    execution_adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """
    获取工作流执行历史
    
    - **execution_id**: 执行ID
    """
    try:
        # 验证执行记录存在和权限
        execution = await execution_adapter.get_by_id(None, execution_id)
        if not execution:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        if execution.created_by != current_user.id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="无权限访问此执行历史"
            )
        
        # TODO: 实现执行历史获取
        # 这里应该从步骤执行表和日志表获取详细历史
        history = [
            {
                "timestamp": execution.created_at.isoformat(),
                "event": "execution_created",
                "status": "pending",
                "message": "工作流执行已创建"
            }
        ]
        
        if execution.started_at:
            history.append({
                "timestamp": execution.started_at.isoformat(),
                "event": "execution_started",
                "status": "running",
                "message": "工作流执行已开始"
            })
        
        if execution.completed_at:
            history.append({
                "timestamp": execution.completed_at.isoformat(),
                "event": "execution_completed",
                "status": execution.status,
                "message": f"工作流执行已{execution.status}"
            })
        
        return history
        
    except DatabaseError as e:
        logger.error(f"获取执行历史数据库错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="数据库操作失败"
        )
    except Exception as e:
        logger.error(f"获取执行历史未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail="获取执行历史失败"
        )


@router.websocket("/ws/{execution_id}")
async def websocket_execution_updates(
    websocket: WebSocket,
    execution_id: UUID,
    token: str = Query(..., description="JWT token"),
    execution_adapter: ExecutionAdapter = Depends(get_execution_adapter)
):
    """
    工作流执行实时更新WebSocket端点
    
    - **execution_id**: 执行ID
    - **token**: JWT认证token
    """
    try:
        # TODO: 验证JWT token
        # 这里应该验证token并获取用户信息
        
        # 验证执行记录存在
        execution = await execution_adapter.get_by_id(None, execution_id)
        if not execution:
            await websocket.close(code=4004, reason="执行记录不存在")
            return
        
        # 建立WebSocket连接
        await manager.connect(websocket, str(execution_id))
        
        try:
            # 发送初始状态
            await websocket.send_json({
                "type": "connection_established",
                "execution_id": str(execution_id),
                "current_status": execution.status,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 保持连接活跃
            while True:
                # 接收客户端消息（心跳等）
                data = await websocket.receive_text()
                
                # 处理心跳消息
                if data == "ping":
                    await websocket.send_text("pong")
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket连接断开: {execution_id}")
        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
        finally:
            manager.disconnect(websocket, str(execution_id))
            
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
        await websocket.close(code=4000, reason="连接错误")


@router.websocket("/ws")
async def websocket_global_updates(
    websocket: WebSocket,
    token: str = Query(..., description="JWT token")
):
    """
    全局工作流执行更新WebSocket端点
    
    - **token**: JWT认证token
    """
    try:
        # TODO: 验证JWT token
        # 这里应该验证token并获取用户信息
        
        # 建立WebSocket连接
        await manager.connect(websocket)
        
        try:
            # 发送连接确认
            await websocket.send_json({
                "type": "global_connection_established",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # 保持连接活跃
            while True:
                # 接收客户端消息
                data = await websocket.receive_text()
                
                # 处理心跳消息
                if data == "ping":
                    await websocket.send_text("pong")
                
        except WebSocketDisconnect:
            logger.info("全局WebSocket连接断开")
        except Exception as e:
            logger.error(f"全局WebSocket处理错误: {e}")
        finally:
            manager.disconnect(websocket)
            
    except Exception as e:
        logger.error(f"全局WebSocket连接错误: {e}")
        await websocket.close(code=4000, reason="连接错误")