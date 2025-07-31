"""
自定义异常类

定义平台使用的所有自定义异常。
"""

from typing import Any, Dict, Optional


class WorkflowError(Exception):
    """工作流相关的基础异常"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(WorkflowError):
    """验证错误"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field
        self.value = value


class ConfigurationError(WorkflowError):
    """配置错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)


class DatabaseError(WorkflowError):
    """数据库错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="DATABASE_ERROR", **kwargs)


class TemporalError(WorkflowError):
    """Temporal工作流引擎错误"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, error_code="TEMPORAL_ERROR", **kwargs)


class AIServiceError(WorkflowError):
    """AI服务调用错误"""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="AI_SERVICE_ERROR", **kwargs)
        self.provider = provider
        self.model = model


class AuthenticationError(WorkflowError):
    """认证错误"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(WorkflowError):
    """授权错误"""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, error_code="AUTHORIZATION_ERROR", **kwargs)


class WorkflowExecutionError(WorkflowError):
    """工作流执行错误"""
    
    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        step_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="WORKFLOW_EXECUTION_ERROR", **kwargs)
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.step_id = step_id


class NotificationError(WorkflowError):
    """通知发送错误"""
    
    def __init__(
        self,
        message: str,
        channel: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, error_code="NOTIFICATION_ERROR", **kwargs)
        self.channel = channel