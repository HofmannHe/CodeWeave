"""
数据库适配器工厂

根据配置创建相应的数据库适配器实例。
"""

from typing import Dict, Any, Union

from ..core.config import settings, DeploymentMode
from ..core.exceptions import ConfigurationError
from ..core.logging import get_logger

from .adapters import (
    UserAdapter, WorkflowAdapter, ExecutionAdapter,
    StepExecutionAdapter, ApprovalAdapter, LogAdapter
)
from .postgresql_adapter import (
    PostgreSQLUserAdapter, PostgreSQLWorkflowAdapter, PostgreSQLExecutionAdapter
)
from .supabase_adapter import (
    SupabaseUserAdapter, SupabaseWorkflowAdapter, SupabaseExecutionAdapter,
    SupabaseStepExecutionAdapter, SupabaseApprovalAdapter, SupabaseLogAdapter
)

logger = get_logger(__name__)


class DatabaseAdapterFactory:
    """数据库适配器工厂类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self._adapters = {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        if settings.deployment_mode == DeploymentMode.SUPABASE:
            return {
                'deployment_mode': settings.deployment_mode,
                'supabase_url': settings.supabase_url,
                'supabase_key': settings.supabase_key,
                'supabase_service_role_key': settings.supabase_service_role_key,
            }
        else:
            return {
                'deployment_mode': settings.deployment_mode,
                'database_url': settings.database_url,
                'echo': settings.debug,
            }
    
    def _validate_config(self) -> None:
        """验证配置"""
        deployment_mode = self.config.get('deployment_mode')
        
        if deployment_mode == DeploymentMode.SUPABASE:
            required_keys = ['supabase_url', 'supabase_key']
            for key in required_keys:
                if not self.config.get(key):
                    raise ConfigurationError(f"Supabase方案缺少必需配置: {key}")
        
        elif deployment_mode == DeploymentMode.SELF_HOSTED:
            if not self.config.get('database_url'):
                raise ConfigurationError("自建方案缺少数据库URL配置")
        
        else:
            raise ConfigurationError(f"不支持的部署模式: {deployment_mode}")
    
    async def initialize(self) -> None:
        """初始化工厂"""
        self._validate_config()
        logger.info(f"数据库适配器工厂初始化完成，部署模式: {self.config.get('deployment_mode')}")
    
    def get_user_adapter(self) -> UserAdapter:
        """获取用户适配器"""
        if 'user' not in self._adapters:
            if self.config.get('deployment_mode') == DeploymentMode.SUPABASE:
                self._adapters['user'] = SupabaseUserAdapter(self.config)
            else:
                self._adapters['user'] = PostgreSQLUserAdapter(self.config)
        
        return self._adapters['user']
    
    def get_workflow_adapter(self) -> WorkflowAdapter:
        """获取工作流适配器"""
        if 'workflow' not in self._adapters:
            if self.config.get('deployment_mode') == DeploymentMode.SUPABASE:
                self._adapters['workflow'] = SupabaseWorkflowAdapter(self.config)
            else:
                self._adapters['workflow'] = PostgreSQLWorkflowAdapter(self.config)
        
        return self._adapters['workflow']
    
    def get_execution_adapter(self) -> ExecutionAdapter:
        """获取执行记录适配器"""
        if 'execution' not in self._adapters:
            if self.config.get('deployment_mode') == DeploymentMode.SUPABASE:
                self._adapters['execution'] = SupabaseExecutionAdapter(self.config)
            else:
                self._adapters['execution'] = PostgreSQLExecutionAdapter(self.config)
        
        return self._adapters['execution']
    
    def get_step_execution_adapter(self) -> StepExecutionAdapter:
        """获取步骤执行适配器"""
        if 'step_execution' not in self._adapters:
            if self.config.get('deployment_mode') == DeploymentMode.SUPABASE:
                self._adapters['step_execution'] = SupabaseStepExecutionAdapter(self.config)
            else:
                # PostgreSQL步骤执行适配器需要实现
                raise NotImplementedError("PostgreSQL步骤执行适配器尚未实现")
        
        return self._adapters['step_execution']
    
    def get_approval_adapter(self) -> ApprovalAdapter:
        """获取审批请求适配器"""
        if 'approval' not in self._adapters:
            if self.config.get('deployment_mode') == DeploymentMode.SUPABASE:
                self._adapters['approval'] = SupabaseApprovalAdapter(self.config)
            else:
                # PostgreSQL审批适配器需要实现
                raise NotImplementedError("PostgreSQL审批适配器尚未实现")
        
        return self._adapters['approval']
    
    def get_log_adapter(self) -> LogAdapter:
        """获取日志适配器"""
        if 'log' not in self._adapters:
            if self.config.get('deployment_mode') == DeploymentMode.SUPABASE:
                self._adapters['log'] = SupabaseLogAdapter(self.config)
            else:
                # PostgreSQL日志适配器需要实现
                raise NotImplementedError("PostgreSQL日志适配器尚未实现")
        
        return self._adapters['log']
    
    async def connect_all(self) -> None:
        """连接所有适配器"""
        for adapter in self._adapters.values():
            await adapter.connect()
        
        logger.info("所有数据库适配器连接成功")
    
    async def disconnect_all(self) -> None:
        """断开所有适配器连接"""
        for adapter in self._adapters.values():
            await adapter.disconnect()
        
        logger.info("所有数据库适配器连接已断开")
    
    def clear_cache(self) -> None:
        """清除适配器缓存"""
        self._adapters.clear()
        logger.info("数据库适配器缓存已清除")


# 全局工厂实例
_factory_instance: DatabaseAdapterFactory = None


def get_database_factory() -> DatabaseAdapterFactory:
    """获取数据库适配器工厂实例"""
    global _factory_instance
    
    if _factory_instance is None:
        _factory_instance = DatabaseAdapterFactory()
    
    return _factory_instance


def set_database_factory(factory: DatabaseAdapterFactory) -> None:
    """设置数据库适配器工厂实例（用于测试）"""
    global _factory_instance
    _factory_instance = factory


# 便捷函数
async def get_user_adapter() -> UserAdapter:
    """获取用户适配器"""
    factory = get_database_factory()
    await factory.initialize()
    return factory.get_user_adapter()


async def get_workflow_adapter() -> WorkflowAdapter:
    """获取工作流适配器"""
    factory = get_database_factory()
    await factory.initialize()
    return factory.get_workflow_adapter()


async def get_execution_adapter() -> ExecutionAdapter:
    """获取执行记录适配器"""
    factory = get_database_factory()
    await factory.initialize()
    return factory.get_execution_adapter()


async def get_step_execution_adapter() -> StepExecutionAdapter:
    """获取步骤执行适配器"""
    factory = get_database_factory()
    await factory.initialize()
    return factory.get_step_execution_adapter()


async def get_approval_adapter() -> ApprovalAdapter:
    """获取审批请求适配器"""
    factory = get_database_factory()
    await factory.initialize()
    return factory.get_approval_adapter()


async def get_log_adapter() -> LogAdapter:
    """获取日志适配器"""
    factory = get_database_factory()
    await factory.initialize()
    return factory.get_log_adapter()