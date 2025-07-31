"""
Pydantic Schema定义

通用的数据模型Schema，支持双方案部署。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


# 枚举类型定义
class DeploymentMode(str, Enum):
    """部署模式"""
    SUPABASE = "supabase"
    SELF_HOSTED = "self_hosted"


class WorkflowStatus(str, Enum):
    """工作流状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ApprovalStatus(str, Enum):
    """审批状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# 基础Schema类
class BaseSchema(BaseModel):
    """基础Schema类"""
    
    class Config:
        # 允许使用枚举值
        use_enum_values = True
        # 验证赋值
        validate_assignment = True
        # 允许从ORM对象创建
        from_attributes = True
        # JSON编码器
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class TimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# 用户相关Schema
class UserProfileBase(BaseSchema):
    """用户配置基础Schema"""
    username: str = Field(..., min_length=3, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    timezone: str = Field(default="UTC", max_length=50)
    preferences: Dict[str, Any] = Field(default_factory=dict)


class UserProfileCreate(UserProfileBase):
    """创建用户配置Schema"""
    id: UUID = Field(default_factory=uuid4)


class UserProfileUpdate(BaseSchema):
    """更新用户配置Schema"""
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=50)
    preferences: Optional[Dict[str, Any]] = None


class UserProfile(UserProfileBase, TimestampMixin):
    """用户配置Schema"""
    id: UUID


# 工作流相关Schema
class WorkflowDefinitionBase(BaseSchema):
    """工作流定义基础Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    yaml_content: str = Field(..., min_length=1)
    parsed_config: Dict[str, Any] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)
    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT)
    tags: List[str] = Field(default_factory=list)
    
    @validator('tags')
    def validate_tags(cls, v):
        """验证标签"""
        if len(v) > 20:
            raise ValueError("标签数量不能超过20个")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("标签长度不能超过50个字符")
        return v


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    """创建工作流定义Schema"""
    id: UUID = Field(default_factory=uuid4)
    created_by: UUID


class WorkflowDefinitionUpdate(BaseSchema):
    """更新工作流定义Schema"""
    description: Optional[str] = None
    yaml_content: Optional[str] = None
    parsed_config: Optional[Dict[str, Any]] = None
    status: Optional[WorkflowStatus] = None
    tags: Optional[List[str]] = None


class WorkflowDefinition(WorkflowDefinitionBase, TimestampMixin):
    """工作流定义Schema"""
    id: UUID
    created_by: Optional[UUID] = None


# 工作流执行相关Schema
class WorkflowExecutionBase(BaseSchema):
    """工作流执行基础Schema"""
    workflow_id: UUID
    temporal_workflow_id: str = Field(..., max_length=255)
    temporal_run_id: str = Field(..., max_length=255)
    status: ExecutionStatus = Field(default=ExecutionStatus.PENDING)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowExecutionCreate(WorkflowExecutionBase):
    """创建工作流执行Schema"""
    id: UUID = Field(default_factory=uuid4)
    created_by: UUID


class WorkflowExecutionUpdate(BaseSchema):
    """更新工作流执行Schema"""
    status: Optional[ExecutionStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowExecution(WorkflowExecutionBase, TimestampMixin):
    """工作流执行Schema"""
    id: UUID
    created_by: Optional[UUID] = None


# 步骤执行相关Schema
class StepExecutionBase(BaseSchema):
    """步骤执行基础Schema"""
    execution_id: UUID
    step_id: str = Field(..., max_length=255)
    step_name: str = Field(..., max_length=255)
    step_type: str = Field(..., max_length=50)
    status: StepStatus = Field(default=StepStatus.PENDING)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    cost_info: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StepExecutionCreate(StepExecutionBase):
    """创建步骤执行Schema"""
    id: UUID = Field(default_factory=uuid4)


class StepExecutionUpdate(BaseSchema):
    """更新步骤执行Schema"""
    status: Optional[StepStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    cost_info: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StepExecution(StepExecutionBase, TimestampMixin):
    """步骤执行Schema"""
    id: UUID


# 审批请求相关Schema
class ApprovalRequestBase(BaseSchema):
    """审批请求基础Schema"""
    execution_id: UUID
    step_id: str = Field(..., max_length=255)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    approval_token: str = Field(..., max_length=255)
    expires_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_note: Optional[str] = None


class ApprovalRequestCreate(ApprovalRequestBase):
    """创建审批请求Schema"""
    id: UUID = Field(default_factory=uuid4)
    requested_by: UUID


class ApprovalRequestUpdate(BaseSchema):
    """更新审批请求Schema"""
    status: Optional[ApprovalStatus] = None
    approved_by: Optional[UUID] = None
    responded_at: Optional[datetime] = None
    response_note: Optional[str] = None


class ApprovalRequest(ApprovalRequestBase, TimestampMixin):
    """审批请求Schema"""
    id: UUID
    requested_by: Optional[UUID] = None
    approved_by: Optional[UUID] = None


# 执行日志相关Schema
class ExecutionLogBase(BaseSchema):
    """执行日志基础Schema"""
    execution_id: UUID
    step_id: Optional[str] = Field(None, max_length=255)
    level: LogLevel
    message: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutionLogCreate(ExecutionLogBase):
    """创建执行日志Schema"""
    id: UUID = Field(default_factory=uuid4)


class ExecutionLog(ExecutionLogBase):
    """执行日志Schema"""
    id: UUID


# 响应Schema
class PaginatedResponse(BaseSchema, Generic[T]):
    """分页响应Schema"""
    items: List[T]
    total: int
    page: int = Field(ge=1)
    size: int = Field(ge=1, le=100)
    pages: int
    
    @validator('pages', always=True)
    def calculate_pages(cls, v, values):
        """计算总页数"""
        total = values.get('total', 0)
        size = values.get('size', 10)
        return (total + size - 1) // size if total > 0 else 0


class ErrorResponse(BaseSchema):
    """错误响应Schema"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseSchema):
    """成功响应Schema"""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)