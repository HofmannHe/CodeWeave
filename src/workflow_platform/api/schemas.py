"""
API Schema定义

用于API请求和响应的Pydantic Schema。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator, EmailStr

from ..database.schemas import (
    BaseSchema, WorkflowStatus, ExecutionStatus, StepStatus, ApprovalStatus
)


# 认证相关Schema
class UserRegisterRequest(BaseSchema):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    timezone: str = Field(default="UTC", max_length=50, description="时区")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v.lower()


class UserLoginRequest(BaseSchema):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserLoginResponse(BaseSchema):
    """用户登录响应"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")
    user: 'UserProfileResponse' = Field(..., description="用户信息")


class PasswordChangeRequest(BaseSchema):
    """密码修改请求"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class PasswordResetRequest(BaseSchema):
    """密码重置请求"""
    email: EmailStr = Field(..., description="邮箱地址")


class PasswordResetConfirmRequest(BaseSchema):
    """密码重置确认请求"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")


class UserProfileResponse(BaseSchema):
    """用户配置响应"""
    id: UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱地址")
    display_name: Optional[str] = Field(None, description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    timezone: str = Field(..., description="时区")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UserProfileUpdateRequest(BaseSchema):
    """用户配置更新请求"""
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    timezone: Optional[str] = Field(None, max_length=50, description="时区")
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好")


# 工作流相关Schema
class WorkflowDefinitionCreateRequest(BaseSchema):
    """工作流定义创建请求"""
    name: str = Field(..., min_length=1, max_length=255, description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    yaml_content: str = Field(..., min_length=1, description="YAML配置内容")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    
    @validator('tags')
    def validate_tags(cls, v):
        """验证标签"""
        if len(v) > 20:
            raise ValueError("标签数量不能超过20个")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("标签长度不能超过50个字符")
        return v


class WorkflowDefinitionUpdateRequest(BaseSchema):
    """工作流定义更新请求"""
    description: Optional[str] = Field(None, description="工作流描述")
    yaml_content: Optional[str] = Field(None, min_length=1, description="YAML配置内容")
    status: Optional[WorkflowStatus] = Field(None, description="工作流状态")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    @validator('tags')
    def validate_tags(cls, v):
        """验证标签"""
        if v is not None:
            if len(v) > 20:
                raise ValueError("标签数量不能超过20个")
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("标签长度不能超过50个字符")
        return v


class WorkflowDefinitionResponse(BaseSchema):
    """工作流定义响应"""
    id: UUID = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    yaml_content: str = Field(..., description="YAML配置内容")
    parsed_config: Dict[str, Any] = Field(..., description="解析后的配置")
    version: int = Field(..., description="版本号")
    status: WorkflowStatus = Field(..., description="工作流状态")
    tags: List[str] = Field(..., description="标签列表")
    created_by: Optional[UUID] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class WorkflowExecutionCreateRequest(BaseSchema):
    """工作流执行创建请求"""
    workflow_id: UUID = Field(..., description="工作流ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="输入数据")


class WorkflowExecutionUpdateRequest(BaseSchema):
    """工作流执行更新请求"""
    status: Optional[ExecutionStatus] = Field(None, description="执行状态")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    error_message: Optional[str] = Field(None, description="错误信息")


class WorkflowExecutionResponse(BaseSchema):
    """工作流执行响应"""
    id: UUID = Field(..., description="执行ID")
    workflow_id: UUID = Field(..., description="工作流ID")
    temporal_workflow_id: str = Field(..., description="Temporal工作流ID")
    temporal_run_id: str = Field(..., description="Temporal运行ID")
    status: ExecutionStatus = Field(..., description="执行状态")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    output_data: Dict[str, Any] = Field(..., description="输出数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_by: Optional[UUID] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class StepExecutionResponse(BaseSchema):
    """步骤执行响应"""
    id: UUID = Field(..., description="步骤执行ID")
    execution_id: UUID = Field(..., description="工作流执行ID")
    step_id: str = Field(..., description="步骤ID")
    step_name: str = Field(..., description="步骤名称")
    step_type: str = Field(..., description="步骤类型")
    status: StepStatus = Field(..., description="步骤状态")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    output_data: Dict[str, Any] = Field(..., description="输出数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    cost_info: Dict[str, Any] = Field(..., description="成本信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ApprovalRequestResponse(BaseSchema):
    """审批请求响应"""
    id: UUID = Field(..., description="审批请求ID")
    execution_id: UUID = Field(..., description="工作流执行ID")
    step_id: str = Field(..., description="步骤ID")
    title: str = Field(..., description="审批标题")
    description: Optional[str] = Field(None, description="审批描述")
    context_data: Dict[str, Any] = Field(..., description="上下文数据")
    status: ApprovalStatus = Field(..., description="审批状态")
    requested_by: Optional[UUID] = Field(None, description="请求者ID")
    approved_by: Optional[UUID] = Field(None, description="审批者ID")
    approval_token: str = Field(..., description="审批令牌")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    responded_at: Optional[datetime] = Field(None, description="响应时间")
    response_note: Optional[str] = Field(None, description="响应备注")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ApprovalActionRequest(BaseSchema):
    """审批操作请求"""
    action: str = Field(..., description="操作类型: approve | reject")
    note: Optional[str] = Field(None, description="审批备注")
    
    @validator('action')
    def validate_action(cls, v):
        """验证操作类型"""
        if v not in ['approve', 'reject']:
            raise ValueError("操作类型必须是 approve 或 reject")
        return v


# 分页和查询Schema
class PaginationParams(BaseSchema):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")


class WorkflowListParams(PaginationParams):
    """工作流列表查询参数"""
    status: Optional[WorkflowStatus] = Field(None, description="工作流状态")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    search: Optional[str] = Field(None, description="搜索关键词")


class ExecutionListParams(PaginationParams):
    """执行列表查询参数"""
    workflow_id: Optional[UUID] = Field(None, description="工作流ID")
    status: Optional[ExecutionStatus] = Field(None, description="执行状态")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")


class PaginatedResponse(BaseSchema):
    """分页响应"""
    items: List[Any] = Field(..., description="数据项")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


# 通用响应Schema
class MessageResponse(BaseSchema):
    """消息响应"""
    message: str = Field(..., description="消息内容")
    success: bool = Field(default=True, description="是否成功")


class ErrorResponse(BaseSchema):
    """错误响应"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")


# WebSocket消息Schema
class WebSocketMessage(BaseSchema):
    """WebSocket消息"""
    type: str = Field(..., description="消息类型")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="时间戳")


class ExecutionStatusUpdate(BaseSchema):
    """执行状态更新消息"""
    execution_id: UUID = Field(..., description="执行ID")
    status: ExecutionStatus = Field(..., description="执行状态")
    step_updates: List[Dict[str, Any]] = Field(default_factory=list, description="步骤更新")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="进度百分比")


# 更新前向引用
UserLoginResponse.model_rebuild()