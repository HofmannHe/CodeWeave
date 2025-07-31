"""
SQLAlchemy数据模型定义

用于自建方案的数据库模型。
"""

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, 
    JSON, String, Text, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .schemas import (
    WorkflowStatus, ExecutionStatus, StepStatus, 
    ApprovalStatus, LogLevel
)

Base = declarative_base()


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserProfile(Base, TimestampMixin):
    """用户配置表"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    avatar_url = Column(Text)
    timezone = Column(String(50), default="UTC", nullable=False)
    preferences = Column(JSON, default=dict, nullable=False)
    
    # 关系
    created_workflows = relationship("WorkflowDefinition", back_populates="creator")
    executions = relationship("WorkflowExecution", back_populates="creator")
    requested_approvals = relationship(
        "ApprovalRequest", 
        foreign_keys="ApprovalRequest.requested_by",
        back_populates="requester"
    )
    approved_requests = relationship(
        "ApprovalRequest",
        foreign_keys="ApprovalRequest.approved_by", 
        back_populates="approver"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_user_profiles_username', 'username'),
        Index('idx_user_profiles_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UserProfile(id={self.id}, username='{self.username}')>"


class WorkflowDefinition(Base, TimestampMixin):
    """工作流定义表"""
    __tablename__ = "workflow_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    yaml_content = Column(Text, nullable=False)
    parsed_config = Column(JSON, default=dict, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False, index=True)
    tags = Column(ARRAY(String), default=list, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    
    # 关系
    creator = relationship("UserProfile", back_populates="created_workflows")
    executions = relationship("WorkflowExecution", back_populates="workflow")
    
    # 约束和索引
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_workflow_name_version'),
        Index('idx_workflow_definitions_created_by', 'created_by'),
        Index('idx_workflow_definitions_status', 'status'),
        Index('idx_workflow_definitions_tags', 'tags', postgresql_using='gin'),
        Index('idx_workflow_definitions_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<WorkflowDefinition(id={self.id}, name='{self.name}', version={self.version})>"


class WorkflowExecution(Base, TimestampMixin):
    """工作流执行表"""
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id", ondelete="CASCADE"), nullable=False)
    temporal_workflow_id = Column(String(255), unique=True, nullable=False, index=True)
    temporal_run_id = Column(String(255), nullable=False)
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False, index=True)
    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_by = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    
    # 关系
    workflow = relationship("WorkflowDefinition", back_populates="executions")
    creator = relationship("UserProfile", back_populates="executions")
    step_executions = relationship("StepExecution", back_populates="execution", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="execution", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_executions_workflow_id', 'workflow_id'),
        Index('idx_workflow_executions_status', 'status'),
        Index('idx_workflow_executions_created_by', 'created_by'),
        Index('idx_workflow_executions_created_at', 'created_at'),
        Index('idx_workflow_executions_temporal_workflow_id', 'temporal_workflow_id'),
    )
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, temporal_workflow_id='{self.temporal_workflow_id}')>"


class StepExecution(Base, TimestampMixin):
    """步骤执行表"""
    __tablename__ = "step_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(String(255), nullable=False)
    step_name = Column(String(255), nullable=False)
    step_type = Column(String(50), nullable=False, index=True)
    status = Column(Enum(StepStatus), default=StepStatus.PENDING, nullable=False, index=True)
    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text)
    cost_info = Column(JSON, default=dict, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="step_executions")
    
    # 约束和索引
    __table_args__ = (
        UniqueConstraint('execution_id', 'step_id', name='uq_step_execution_execution_step'),
        Index('idx_step_executions_execution_id', 'execution_id'),
        Index('idx_step_executions_status', 'status'),
        Index('idx_step_executions_step_type', 'step_type'),
    )
    
    def __repr__(self):
        return f"<StepExecution(id={self.id}, step_id='{self.step_id}', status='{self.status}')>"


class ApprovalRequest(Base, TimestampMixin):
    """审批请求表"""
    __tablename__ = "approval_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    context_data = Column(JSON, default=dict, nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False, index=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id", ondelete="SET NULL"))
    approval_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), index=True)
    responded_at = Column(DateTime(timezone=True))
    response_note = Column(Text)
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="approval_requests")
    requester = relationship("UserProfile", foreign_keys=[requested_by], back_populates="requested_approvals")
    approver = relationship("UserProfile", foreign_keys=[approved_by], back_populates="approved_requests")
    
    # 索引
    __table_args__ = (
        Index('idx_approval_requests_execution_id', 'execution_id'),
        Index('idx_approval_requests_status', 'status'),
        Index('idx_approval_requests_token', 'approval_token'),
        Index('idx_approval_requests_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<ApprovalRequest(id={self.id}, title='{self.title}', status='{self.status}')>"


class ExecutionLog(Base):
    """执行日志表"""
    __tablename__ = "execution_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(String(255))
    level = Column(Enum(LogLevel), nullable=False, index=True)
    message = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # 关系
    execution = relationship("WorkflowExecution", back_populates="logs")
    
    # 索引
    __table_args__ = (
        Index('idx_execution_logs_execution_id', 'execution_id'),
        Index('idx_execution_logs_level', 'level'),
        Index('idx_execution_logs_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<ExecutionLog(id={self.id}, level='{self.level}', message='{self.message[:50]}...')>"


# 创建所有表的函数
def create_tables(engine):
    """创建所有数据库表"""
    Base.metadata.create_all(bind=engine)


# 删除所有表的函数
def drop_tables(engine):
    """删除所有数据库表"""
    Base.metadata.drop_all(bind=engine)