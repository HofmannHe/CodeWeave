"""
数据库适配器抽象基类

支持双方案部署：Supabase和自建数据库。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

# 泛型类型变量
T = TypeVar('T', bound=BaseModel)


class DatabaseAdapter(ABC, Generic[T]):
    """数据库适配器抽象基类"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.connection_config = connection_config
        self._connection = None
    
    @abstractmethod
    async def connect(self) -> None:
        """建立数据库连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """关闭数据库连接"""
        pass
    
    @abstractmethod
    async def create(self, model: T) -> T:
        """创建记录"""
        pass
    
    @abstractmethod
    async def get_by_id(self, model_class: Type[T], record_id: UUID) -> Optional[T]:
        """根据ID获取记录"""
        pass
    
    @abstractmethod
    async def get_by_field(
        self, 
        model_class: Type[T], 
        field_name: str, 
        field_value: Any
    ) -> Optional[T]:
        """根据字段值获取记录"""
        pass
    
    @abstractmethod
    async def list_records(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """列出记录"""
        pass
    
    @abstractmethod
    async def update(self, model: T) -> T:
        """更新记录"""
        pass
    
    @abstractmethod
    async def delete(self, model_class: Type[T], record_id: UUID) -> bool:
        """删除记录"""
        pass
    
    @abstractmethod
    async def count(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计记录数量"""
        pass
    
    @abstractmethod
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行原始SQL查询"""
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> Any:
        """开始事务"""
        pass
    
    @abstractmethod
    async def commit_transaction(self, transaction: Any) -> None:
        """提交事务"""
        pass
    
    @abstractmethod
    async def rollback_transaction(self, transaction: Any) -> None:
        """回滚事务"""
        pass


class UserAdapter(DatabaseAdapter[T]):
    """用户数据适配器"""
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[T]:
        """根据用户名获取用户"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[T]:
        """根据邮箱获取用户"""
        pass
    
    @abstractmethod
    async def verify_password(self, user_id: UUID, password: str) -> bool:
        """验证用户密码"""
        pass
    
    @abstractmethod
    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """更新用户密码"""
        pass


class WorkflowAdapter(DatabaseAdapter[T]):
    """工作流数据适配器"""
    
    @abstractmethod
    async def get_by_name_and_version(self, name: str, version: int) -> Optional[T]:
        """根据名称和版本获取工作流"""
        pass
    
    @abstractmethod
    async def get_latest_version(self, name: str) -> Optional[T]:
        """获取最新版本的工作流"""
        pass
    
    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[T]:
        """获取用户的工作流列表"""
        pass
    
    @abstractmethod
    async def list_by_tags(self, tags: List[str]) -> List[T]:
        """根据标签获取工作流列表"""
        pass


class ExecutionAdapter(DatabaseAdapter[T]):
    """执行记录数据适配器"""
    
    @abstractmethod
    async def get_by_temporal_workflow_id(self, temporal_workflow_id: str) -> Optional[T]:
        """根据Temporal工作流ID获取执行记录"""
        pass
    
    @abstractmethod
    async def list_by_workflow(self, workflow_id: UUID) -> List[T]:
        """获取工作流的执行记录列表"""
        pass
    
    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[T]:
        """获取用户的执行记录列表"""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: str) -> List[T]:
        """根据状态获取执行记录列表"""
        pass


class StepExecutionAdapter(DatabaseAdapter[T]):
    """步骤执行数据适配器"""
    
    @abstractmethod
    async def list_by_execution(self, execution_id: UUID) -> List[T]:
        """获取执行记录的步骤列表"""
        pass
    
    @abstractmethod
    async def get_by_execution_and_step(
        self, 
        execution_id: UUID, 
        step_id: str
    ) -> Optional[T]:
        """根据执行ID和步骤ID获取步骤执行记录"""
        pass


class ApprovalAdapter(DatabaseAdapter[T]):
    """审批请求数据适配器"""
    
    @abstractmethod
    async def get_by_token(self, token: str) -> Optional[T]:
        """根据审批令牌获取审批请求"""
        pass
    
    @abstractmethod
    async def list_pending_by_user(self, user_id: UUID) -> List[T]:
        """获取用户的待审批请求列表"""
        pass
    
    @abstractmethod
    async def list_by_execution(self, execution_id: UUID) -> List[T]:
        """获取执行记录的审批请求列表"""
        pass


class LogAdapter(DatabaseAdapter[T]):
    """日志数据适配器"""
    
    @abstractmethod
    async def list_by_execution(
        self,
        execution_id: UUID,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[T]:
        """获取执行记录的日志列表"""
        pass
    
    @abstractmethod
    async def list_by_step(
        self,
        execution_id: UUID,
        step_id: str,
        level: Optional[str] = None
    ) -> List[T]:
        """获取步骤的日志列表"""
        pass