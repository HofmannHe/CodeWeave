"""
测试工作流执行API

验证工作流执行相关的API端点功能。
"""

import sys
import pytest
import asyncio
from datetime import datetime
from uuid import uuid4, UUID
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fastapi.testclient import TestClient
from fastapi import status

from workflow_platform.api.main import app
from workflow_platform.database.schemas import (
    UserProfile, WorkflowDefinition, WorkflowExecution,
    ExecutionStatus, WorkflowStatus
)


class TestWorkflowExecutionAPI:
    """测试工作流执行API"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        return UserProfile(
            id=uuid4(),
            username="testuser",
            display_name="测试用户",
            timezone="UTC",
            preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_workflow(self, mock_user):
        """模拟工作流"""
        return WorkflowDefinition(
            id=uuid4(),
            name="test-workflow",
            description="测试工作流",
            yaml_content="name: test\nsteps: []",
            parsed_config={"name": "test", "steps": []},
            version=1,
            status=WorkflowStatus.ACTIVE,
            tags=["test"],
            created_by=mock_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def mock_execution(self, mock_user, mock_workflow):
        """模拟工作流执行"""
        return WorkflowExecution(
            id=uuid4(),
            workflow_id=mock_workflow.id,
            temporal_workflow_id="workflow-123",
            temporal_run_id="run-456",
            status=ExecutionStatus.PENDING,
            input_data={"param1": "value1"},
            output_data={},
            created_by=mock_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def auth_headers(self):
        """认证头"""
        return {"Authorization": "Bearer test-token"}
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    @patch('workflow_platform.api.dependencies.get_workflow_adapter')
    def test_start_workflow_execution_success(
        self, 
        mock_get_workflow_adapter,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_workflow,
        mock_execution,
        auth_headers
    ):
        """测试成功启动工作流执行"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        mock_workflow_adapter = AsyncMock()
        mock_workflow_adapter.get_by_id.return_value = mock_workflow
        mock_get_workflow_adapter.return_value = mock_workflow_adapter
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.create.return_value = mock_execution
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.post(
            "/api/v1/executions/",
            json={
                "workflow_id": str(mock_workflow.id),
                "input_data": {"param1": "value1"}
            },
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["workflow_id"] == str(mock_workflow.id)
        assert data["status"] == ExecutionStatus.PENDING
        assert data["input_data"] == {"param1": "value1"}
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    @patch('workflow_platform.api.dependencies.get_workflow_adapter')
    def test_start_workflow_execution_workflow_not_found(
        self,
        mock_get_workflow_adapter,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        auth_headers
    ):
        """测试启动不存在的工作流执行"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        mock_workflow_adapter = AsyncMock()
        mock_workflow_adapter.get_by_id.return_value = None
        mock_get_workflow_adapter.return_value = mock_workflow_adapter
        
        # 发送请求
        response = client.post(
            "/api/v1/executions/",
            json={
                "workflow_id": str(uuid4()),
                "input_data": {}
            },
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "工作流不存在" in data["message"]
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    @patch('workflow_platform.api.dependencies.get_workflow_adapter')
    def test_start_workflow_execution_permission_denied(
        self,
        mock_get_workflow_adapter,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_workflow,
        auth_headers
    ):
        """测试启动无权限的工作流执行"""
        # 设置模拟 - 工作流属于其他用户
        other_user_workflow = mock_workflow.copy()
        other_user_workflow.created_by = uuid4()
        
        mock_get_current_user.return_value = mock_user
        
        mock_workflow_adapter = AsyncMock()
        mock_workflow_adapter.get_by_id.return_value = other_user_workflow
        mock_get_workflow_adapter.return_value = mock_workflow_adapter
        
        # 发送请求
        response = client.post(
            "/api/v1/executions/",
            json={
                "workflow_id": str(other_user_workflow.id),
                "input_data": {}
            },
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "无权限执行此工作流" in data["message"]
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_list_executions_success(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试成功获取执行列表"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.list_records.return_value = [mock_execution]
        mock_execution_adapter.count.return_value = 1
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.get(
            "/api/v1/executions/",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(mock_execution.id)
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_list_executions_with_filters(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试带过滤条件的执行列表"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.list_records.return_value = [mock_execution]
        mock_execution_adapter.count.return_value = 1
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.get(
            "/api/v1/executions/",
            params={
                "workflow_id": str(mock_execution.workflow_id),
                "status": ExecutionStatus.PENDING,
                "page": 1,
                "size": 10
            },
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10
        
        # 验证适配器调用参数
        mock_execution_adapter.list_records.assert_called_once()
        call_args = mock_execution_adapter.list_records.call_args
        filters = call_args[1]["filters"]
        assert filters["created_by"] == mock_user.id
        assert filters["workflow_id"] == mock_execution.workflow_id
        assert filters["status"] == ExecutionStatus.PENDING
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_get_execution_success(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试成功获取执行详情"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.get_by_id.return_value = mock_execution
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.get(
            f"/api/v1/executions/{mock_execution.id}",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(mock_execution.id)
        assert data["status"] == mock_execution.status
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_get_execution_not_found(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        auth_headers
    ):
        """测试获取不存在的执行详情"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.get_by_id.return_value = None
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.get(
            f"/api/v1/executions/{uuid4()}",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "执行记录不存在" in data["message"]
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_get_execution_permission_denied(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试获取无权限的执行详情"""
        # 设置模拟 - 执行记录属于其他用户
        other_user_execution = mock_execution.copy()
        other_user_execution.created_by = uuid4()
        
        mock_get_current_user.return_value = mock_user
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.get_by_id.return_value = other_user_execution
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.get(
            f"/api/v1/executions/{other_user_execution.id}",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "无权限访问此执行记录" in data["message"]
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_update_execution_success(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试成功更新执行状态"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        updated_execution = mock_execution.copy()
        updated_execution.status = ExecutionStatus.COMPLETED
        updated_execution.output_data = {"result": "success"}
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.get_by_id.return_value = mock_execution
        mock_execution_adapter.update.return_value = updated_execution
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.put(
            f"/api/v1/executions/{mock_execution.id}",
            json={
                "status": ExecutionStatus.COMPLETED,
                "output_data": {"result": "success"}
            },
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == ExecutionStatus.COMPLETED
        assert data["output_data"] == {"result": "success"}
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_cancel_execution_success(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试成功取消执行"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        cancelled_execution = mock_execution.copy()
        cancelled_execution.status = ExecutionStatus.CANCELLED
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.get_by_id.return_value = mock_execution
        mock_execution_adapter.update.return_value = cancelled_execution
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.post(
            f"/api/v1/executions/{mock_execution.id}/cancel",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == ExecutionStatus.CANCELLED
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_cancel_execution_invalid_status(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试取消已完成的执行"""
        # 设置模拟 - 执行已完成
        completed_execution = mock_execution.copy()
        completed_execution.status = ExecutionStatus.COMPLETED
        
        mock_get_current_user.return_value = mock_user
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.get_by_id.return_value = completed_execution
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.post(
            f"/api/v1/executions/{completed_execution.id}/cancel",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "只能取消待执行、运行中或暂停的工作流" in data["message"]
    
    @patch('workflow_platform.api.dependencies.get_current_user')
    @patch('workflow_platform.api.dependencies.get_execution_adapter')
    def test_get_execution_history_success(
        self,
        mock_get_execution_adapter,
        mock_get_current_user,
        client,
        mock_user,
        mock_execution,
        auth_headers
    ):
        """测试成功获取执行历史"""
        # 设置模拟
        mock_get_current_user.return_value = mock_user
        
        mock_execution_adapter = AsyncMock()
        mock_execution_adapter.get_by_id.return_value = mock_execution
        mock_get_execution_adapter.return_value = mock_execution_adapter
        
        # 发送请求
        response = client.get(
            f"/api/v1/executions/{mock_execution.id}/history",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["event"] == "execution_created"


class TestWebSocketConnections:
    """测试WebSocket连接"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)
    
    def test_websocket_execution_updates_connection(self, client):
        """测试执行更新WebSocket连接"""
        execution_id = uuid4()
        
        # 模拟WebSocket连接
        with client.websocket_connect(f"/api/v1/executions/ws/{execution_id}?token=test-token") as websocket:
            # 这里应该接收到连接确认消息
            # 由于测试环境限制，这里只是验证连接可以建立
            pass
    
    def test_websocket_global_updates_connection(self, client):
        """测试全局更新WebSocket连接"""
        # 模拟WebSocket连接
        with client.websocket_connect("/api/v1/executions/ws?token=test-token") as websocket:
            # 这里应该接收到连接确认消息
            # 由于测试环境限制，这里只是验证连接可以建立
            pass


class TestConnectionManager:
    """测试连接管理器"""
    
    def test_connection_manager_initialization(self):
        """测试连接管理器初始化"""
        from workflow_platform.api.routes.executions import ConnectionManager
        
        manager = ConnectionManager()
        assert manager.active_connections == []
        assert manager.execution_connections == {}
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect_disconnect(self):
        """测试连接管理器连接和断开"""
        from workflow_platform.api.routes.executions import ConnectionManager
        
        manager = ConnectionManager()
        
        # 模拟WebSocket连接
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        
        execution_id = str(uuid4())
        
        # 测试连接
        await manager.connect(mock_websocket, execution_id)
        assert mock_websocket in manager.active_connections
        assert execution_id in manager.execution_connections
        assert mock_websocket in manager.execution_connections[execution_id]
        
        # 测试断开连接
        manager.disconnect(mock_websocket, execution_id)
        assert mock_websocket not in manager.active_connections
        assert execution_id not in manager.execution_connections
    
    @pytest.mark.asyncio
    async def test_connection_manager_send_execution_update(self):
        """测试发送执行更新"""
        from workflow_platform.api.routes.executions import ConnectionManager
        
        manager = ConnectionManager()
        
        # 模拟WebSocket连接
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        execution_id = str(uuid4())
        
        # 建立连接
        await manager.connect(mock_websocket, execution_id)
        
        # 发送更新
        message = {
            "type": "execution_updated",
            "execution_id": execution_id,
            "status": "running"
        }
        
        await manager.send_execution_update(execution_id, message)
        
        # 验证消息发送
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """测试广播消息"""
        from workflow_platform.api.routes.executions import ConnectionManager
        
        manager = ConnectionManager()
        
        # 模拟多个WebSocket连接
        mock_websocket1 = Mock()
        mock_websocket1.accept = AsyncMock()
        mock_websocket1.send_text = AsyncMock()
        
        mock_websocket2 = Mock()
        mock_websocket2.accept = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        
        # 建立连接
        await manager.connect(mock_websocket1)
        await manager.connect(mock_websocket2)
        
        # 广播消息
        message = "test broadcast message"
        await manager.broadcast(message)
        
        # 验证消息发送到所有连接
        mock_websocket1.send_text.assert_called_once_with(message)
        mock_websocket2.send_text.assert_called_once_with(message)