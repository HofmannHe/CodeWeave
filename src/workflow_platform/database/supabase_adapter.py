"""
Supabase数据库适配器实现

用于Supabase方案的数据库适配器。
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID
from datetime import datetime

from supabase import create_client, Client
from postgrest.exceptions import APIError

from ..core.exceptions import DatabaseError, ValidationError, AuthenticationError
from ..core.logging import get_logger
from .adapters import (
    DatabaseAdapter, UserAdapter, WorkflowAdapter, 
    ExecutionAdapter, StepExecutionAdapter, ApprovalAdapter, LogAdapter
)
from .schemas import (
    UserProfile as UserProfileSchema,
    WorkflowDefinition as WorkflowDefinitionSchema,
    WorkflowExecution as WorkflowExecutionSchema,
    StepExecution as StepExecutionSchema,
    ApprovalRequest as ApprovalRequestSchema,
    ExecutionLog as ExecutionLogSchema,
)

logger = get_logger(__name__)
T = TypeVar('T')


class SupabaseAdapter(DatabaseAdapter[T]):
    """Supabase数据库适配器基类"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.client: Optional[Client] = None
        self._table_name = None
        self._schema_class = None
    
    async def connect(self) -> None:
        """建立Supabase连接"""
        try:
            supabase_url = self.connection_config.get('supabase_url')
            supabase_key = self.connection_config.get('supabase_key')
            
            if not supabase_url or not supabase_key:
                raise DatabaseError("Supabase URL或密钥未配置")
            
            self.client = create_client(supabase_url, supabase_key)
            
            # 测试连接
            response = self.client.table('user_profiles').select('id').limit(1).execute()
            
            logger.info("Supabase数据库连接成功")
            
        except Exception as e:
            logger.error(f"Supabase数据库连接失败: {e}")
            raise DatabaseError(f"数据库连接失败: {e}")
    
    async def disconnect(self) -> None:
        """关闭Supabase连接"""
        # Supabase客户端不需要显式关闭连接
        self.client = None
        logger.info("Supabase数据库连接已关闭")
    
    def _handle_supabase_error(self, error: Exception) -> None:
        """处理Supabase错误"""
        if isinstance(error, APIError):
            if error.code == '23505':  # 唯一约束违反
                raise ValidationError(f"记录已存在或违反唯一约束: {error.message}")
            elif error.code == '42501':  # 权限不足
                raise AuthenticationError(f"权限不足: {error.message}")
            else:
                raise DatabaseError(f"数据库操作失败: {error.message}")
        else:
            raise DatabaseError(f"数据库操作失败: {str(error)}")
    
    def _dict_to_schema(self, data: Dict[str, Any]) -> T:
        """将字典转换为Schema"""
        if not self._schema_class:
            raise DatabaseError("Schema类未设置")
        return self._schema_class(**data)
    
    async def create(self, model: T) -> T:
        """创建记录"""
        if not self.client or not self._table_name:
            raise DatabaseError("数据库未连接或表名未设置")
        
        try:
            model_dict = model.dict(exclude_unset=True)
            
            response = self.client.table(self._table_name).insert(model_dict).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            else:
                raise DatabaseError("创建记录失败，无返回数据")
                
        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            self._handle_supabase_error(e)
    
    async def get_by_id(self, model_class: Type[T], record_id: UUID) -> Optional[T]:
        """根据ID获取记录"""
        if not self.client or not self._table_name:
            raise DatabaseError("数据库未连接或表名未设置")
        
        try:
            response = self.client.table(self._table_name).select('*').eq('id', str(record_id)).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"根据ID获取记录失败: {e}")
            self._handle_supabase_error(e)
    
    async def get_by_field(
        self, 
        model_class: Type[T], 
        field_name: str, 
        field_value: Any
    ) -> Optional[T]:
        """根据字段值获取记录"""
        if not self.client or not self._table_name:
            raise DatabaseError("数据库未连接或表名未设置")
        
        try:
            response = self.client.table(self._table_name).select('*').eq(field_name, field_value).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"根据字段获取记录失败: {e}")
            self._handle_supabase_error(e)
    
    async def list_records(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """列出记录"""
        if not self.client or not self._table_name:
            raise DatabaseError("数据库未连接或表名未设置")
        
        try:
            query = self.client.table(self._table_name).select('*')
            
            # 应用过滤器
            if filters:
                for field_name, field_value in filters.items():
                    query = query.eq(field_name, field_value)
            
            # 应用排序
            if order_by:
                if order_by.startswith('-'):
                    field_name = order_by[1:]
                    query = query.order(field_name, desc=True)
                else:
                    query = query.order(order_by, desc=False)
            
            # 应用分页
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            response = query.execute()
            
            return [self._dict_to_schema(item) for item in response.data]
            
        except Exception as e:
            logger.error(f"列出记录失败: {e}")
            self._handle_supabase_error(e)
    
    async def update(self, model: T) -> T:
        """更新记录"""
        if not self.client or not self._table_name:
            raise DatabaseError("数据库未连接或表名未设置")
        
        try:
            model_dict = model.dict(exclude_unset=True)
            record_id = model_dict.get('id')
            
            if not record_id:
                raise ValidationError("更新记录必须提供ID")
            
            # 移除ID字段，避免更新主键
            update_dict = {k: v for k, v in model_dict.items() if k != 'id'}
            
            response = self.client.table(self._table_name).update(update_dict).eq('id', str(record_id)).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            else:
                raise ValidationError(f"记录不存在: {record_id}")
                
        except Exception as e:
            logger.error(f"更新记录失败: {e}")
            self._handle_supabase_error(e)
    
    async def delete(self, model_class: Type[T], record_id: UUID) -> bool:
        """删除记录"""
        if not self.client or not self._table_name:
            raise DatabaseError("数据库未连接或表名未设置")
        
        try:
            response = self.client.table(self._table_name).delete().eq('id', str(record_id)).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            self._handle_supabase_error(e)
    
    async def count(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计记录数量"""
        if not self.client or not self._table_name:
            raise DatabaseError("数据库未连接或表名未设置")
        
        try:
            query = self.client.table(self._table_name).select('id', count='exact')
            
            # 应用过滤器
            if filters:
                for field_name, field_value in filters.items():
                    query = query.eq(field_name, field_value)
            
            response = query.execute()
            
            return response.count or 0
            
        except Exception as e:
            logger.error(f"统计记录数量失败: {e}")
            self._handle_supabase_error(e)
    
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行原始SQL查询"""
        if not self.client:
            raise DatabaseError("数据库未连接")
        
        try:
            # Supabase不直接支持原始SQL查询，需要使用RPC
            response = self.client.rpc('execute_sql', {'query': query, 'params': params or {}}).execute()
            return response.data
            
        except Exception as e:
            logger.error(f"执行原始查询失败: {e}")
            self._handle_supabase_error(e)
    
    async def begin_transaction(self) -> Any:
        """开始事务"""
        # Supabase不支持显式事务，返回None
        logger.warning("Supabase不支持显式事务管理")
        return None
    
    async def commit_transaction(self, transaction: Any) -> None:
        """提交事务"""
        # Supabase不支持显式事务
        pass
    
    async def rollback_transaction(self, transaction: Any) -> None:
        """回滚事务"""
        # Supabase不支持显式事务
        pass


# 具体适配器实现
class SupabaseUserAdapter(SupabaseAdapter, UserAdapter):
    """Supabase用户适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._table_name = 'user_profiles'
        self._schema_class = UserProfileSchema
    
    async def get_by_username(self, username: str) -> Optional[UserProfileSchema]:
        """根据用户名获取用户"""
        return await self.get_by_field(UserProfileSchema, 'username', username)
    
    async def get_by_email(self, email: str) -> Optional[UserProfileSchema]:
        """根据邮箱获取用户"""
        try:
            # 在Supabase中，可以通过auth.users表查询邮箱
            response = self.client.table('user_profiles').select('*').eq('preferences->>email', email).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"根据邮箱获取用户失败: {e}")
            self._handle_supabase_error(e)
    
    async def verify_password(self, user_id: UUID, password: str) -> bool:
        """验证用户密码"""
        # 在Supabase中，密码验证通常通过auth API进行
        try:
            # 这里需要使用Supabase的auth API
            # 实际实现中应该调用auth.signInWithPassword
            logger.warning("Supabase密码验证需要通过auth API实现")
            return True  # 临时返回True
            
        except Exception as e:
            logger.error(f"验证密码失败: {e}")
            return False
    
    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """更新用户密码"""
        # 在Supabase中，密码更新通常通过auth API进行
        try:
            # 这里需要使用Supabase的auth API
            # 实际实现中应该调用auth.updateUser
            logger.warning("Supabase密码更新需要通过auth API实现")
            return True  # 临时返回True
            
        except Exception as e:
            logger.error(f"更新密码失败: {e}")
            return False


class SupabaseWorkflowAdapter(SupabaseAdapter, WorkflowAdapter):
    """Supabase工作流适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._table_name = 'workflow_definitions'
        self._schema_class = WorkflowDefinitionSchema
    
    async def get_by_name_and_version(self, name: str, version: int) -> Optional[WorkflowDefinitionSchema]:
        """根据名称和版本获取工作流"""
        try:
            response = self.client.table(self._table_name).select('*').eq('name', name).eq('version', version).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"根据名称和版本获取工作流失败: {e}")
            self._handle_supabase_error(e)
    
    async def get_latest_version(self, name: str) -> Optional[WorkflowDefinitionSchema]:
        """获取最新版本的工作流"""
        try:
            response = self.client.table(self._table_name).select('*').eq('name', name).order('version', desc=True).limit(1).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"获取最新版本工作流失败: {e}")
            self._handle_supabase_error(e)
    
    async def list_by_user(self, user_id: UUID) -> List[WorkflowDefinitionSchema]:
        """获取用户的工作流列表"""
        return await self.list_records(
            WorkflowDefinitionSchema,
            filters={'created_by': str(user_id)},
            order_by='-created_at'
        )
    
    async def list_by_tags(self, tags: List[str]) -> List[WorkflowDefinitionSchema]:
        """根据标签获取工作流列表"""
        try:
            # 在Supabase中使用数组重叠操作符
            response = self.client.table(self._table_name).select('*').overlaps('tags', tags).execute()
            
            return [self._dict_to_schema(item) for item in response.data]
            
        except Exception as e:
            logger.error(f"根据标签获取工作流失败: {e}")
            self._handle_supabase_error(e)


class SupabaseExecutionAdapter(SupabaseAdapter, ExecutionAdapter):
    """Supabase执行记录适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._table_name = 'workflow_executions'
        self._schema_class = WorkflowExecutionSchema
    
    async def get_by_temporal_workflow_id(self, temporal_workflow_id: str) -> Optional[WorkflowExecutionSchema]:
        """根据Temporal工作流ID获取执行记录"""
        return await self.get_by_field(
            WorkflowExecutionSchema, 
            'temporal_workflow_id', 
            temporal_workflow_id
        )
    
    async def list_by_workflow(self, workflow_id: UUID) -> List[WorkflowExecutionSchema]:
        """获取工作流的执行记录列表"""
        return await self.list_records(
            WorkflowExecutionSchema,
            filters={'workflow_id': str(workflow_id)},
            order_by='-created_at'
        )
    
    async def list_by_user(self, user_id: UUID) -> List[WorkflowExecutionSchema]:
        """获取用户的执行记录列表"""
        return await self.list_records(
            WorkflowExecutionSchema,
            filters={'created_by': str(user_id)},
            order_by='-created_at'
        )
    
    async def list_by_status(self, status: str) -> List[WorkflowExecutionSchema]:
        """根据状态获取执行记录列表"""
        return await self.list_records(
            WorkflowExecutionSchema,
            filters={'status': status},
            order_by='-created_at'
        )


class SupabaseStepExecutionAdapter(SupabaseAdapter, StepExecutionAdapter):
    """Supabase步骤执行适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._table_name = 'step_executions'
        self._schema_class = StepExecutionSchema
    
    async def list_by_execution(self, execution_id: UUID) -> List[StepExecutionSchema]:
        """获取执行记录的步骤列表"""
        return await self.list_records(
            StepExecutionSchema,
            filters={'execution_id': str(execution_id)},
            order_by='created_at'
        )
    
    async def get_by_execution_and_step(
        self, 
        execution_id: UUID, 
        step_id: str
    ) -> Optional[StepExecutionSchema]:
        """根据执行ID和步骤ID获取步骤执行记录"""
        try:
            response = self.client.table(self._table_name).select('*').eq('execution_id', str(execution_id)).eq('step_id', step_id).execute()
            
            if response.data:
                return self._dict_to_schema(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"根据执行ID和步骤ID获取记录失败: {e}")
            self._handle_supabase_error(e)


class SupabaseApprovalAdapter(SupabaseAdapter, ApprovalAdapter):
    """Supabase审批请求适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._table_name = 'approval_requests'
        self._schema_class = ApprovalRequestSchema
    
    async def get_by_token(self, token: str) -> Optional[ApprovalRequestSchema]:
        """根据审批令牌获取审批请求"""
        return await self.get_by_field(ApprovalRequestSchema, 'approval_token', token)
    
    async def list_pending_by_user(self, user_id: UUID) -> List[ApprovalRequestSchema]:
        """获取用户的待审批请求列表"""
        return await self.list_records(
            ApprovalRequestSchema,
            filters={'requested_by': str(user_id), 'status': 'pending'},
            order_by='-created_at'
        )
    
    async def list_by_execution(self, execution_id: UUID) -> List[ApprovalRequestSchema]:
        """获取执行记录的审批请求列表"""
        return await self.list_records(
            ApprovalRequestSchema,
            filters={'execution_id': str(execution_id)},
            order_by='created_at'
        )


class SupabaseLogAdapter(SupabaseAdapter, LogAdapter):
    """Supabase日志适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._table_name = 'execution_logs'
        self._schema_class = ExecutionLogSchema
    
    async def list_by_execution(
        self,
        execution_id: UUID,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[ExecutionLogSchema]:
        """获取执行记录的日志列表"""
        try:
            query = self.client.table(self._table_name).select('*').eq('execution_id', str(execution_id))
            
            if level:
                query = query.eq('level', level)
            
            if start_time:
                query = query.gte('timestamp', start_time.isoformat())
            
            if end_time:
                query = query.lte('timestamp', end_time.isoformat())
            
            query = query.order('timestamp', desc=False)
            
            response = query.execute()
            
            return [self._dict_to_schema(item) for item in response.data]
            
        except Exception as e:
            logger.error(f"获取执行日志失败: {e}")
            self._handle_supabase_error(e)
    
    async def list_by_step(
        self,
        execution_id: UUID,
        step_id: str,
        level: Optional[str] = None
    ) -> List[ExecutionLogSchema]:
        """获取步骤的日志列表"""
        try:
            query = self.client.table(self._table_name).select('*').eq('execution_id', str(execution_id)).eq('step_id', step_id)
            
            if level:
                query = query.eq('level', level)
            
            query = query.order('timestamp', desc=False)
            
            response = query.execute()
            
            return [self._dict_to_schema(item) for item in response.data]
            
        except Exception as e:
            logger.error(f"获取步骤日志失败: {e}")
            self._handle_supabase_error(e)