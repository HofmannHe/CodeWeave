"""
测试数据库模型和适配器

验证数据模型定义、Schema序列化和适配器功能。
"""

import sys
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from workflow_platform.database.schemas import (
    UserProfile, UserProfileCreate, UserProfileUpdate,
    WorkflowDefinition, WorkflowDefinitionCreate, WorkflowDefinitionUpdate,
    WorkflowExecution, WorkflowExecutionCreate, WorkflowExecutionUpdate,
    StepExecution, StepExecutionCreate, StepExecutionUpdate,
    ApprovalRequest, ApprovalRequestCreate, ApprovalRequestUpdate,
    ExecutionLog, ExecutionLogCreate,
    WorkflowStatus, ExecutionStatus, StepStatus, ApprovalStatus, LogLevel
)


class TestSchemaDefinitions:
    """测试Schema定义"""
    
    def test_user_profile_schema(self):
        """测试用户配置Schema"""
        # 测试创建Schema
        user_data = {
            'username': 'testuser',
            'display_name': '测试用户',
            'timezone': 'Asia/Shanghai',
            'preferences': {'theme': 'dark'}
        }
        
        user_create = UserProfileCreate(**user_data)
        assert user_create.username == 'testuser'
        assert user_create.display_name == '测试用户'
        assert user_create.timezone == 'Asia/Shanghai'
        assert user_create.preferences == {'theme': 'dark'}
        assert isinstance(user_create.id, UUID)
    
    def test_user_profile_validation(self):
        """测试用户配置验证"""
        # 测试用户名长度验证
        with pytest.raises(ValueError):
            UserProfileCreate(username='ab')  # 太短
        
        # 测试显示名称长度验证
        with pytest.raises(ValueError):
            UserProfileCreate(
                username='testuser',
                display_name='x' * 101  # 太长
            )
    
    def test_workflow_definition_schema(self):
        """测试工作流定义Schema"""
        workflow_data = {
            'name': 'test-workflow',
            'description': '测试工作流',
            'yaml_content': 'name: test\nsteps: []',
            'parsed_config': {'name': 'test', 'steps': []},
            'version': 1,
            'status': WorkflowStatus.DRAFT,
            'tags': ['test', 'demo'],
            'created_by': uuid4()
        }
        
        workflow_create = WorkflowDefinitionCreate(**workflow_data)
        assert workflow_create.name == 'test-workflow'
        assert workflow_create.status == WorkflowStatus.DRAFT
        assert workflow_create.tags == ['test', 'demo']
        assert isinstance(workflow_create.id, UUID)
    
    def test_workflow_definition_tags_validation(self):
        """测试工作流标签验证"""
        # 测试标签数量限制
        with pytest.raises(ValueError):
            WorkflowDefinitionCreate(
                name='test',
                yaml_content='test',
                tags=['tag'] * 21,  # 超过20个标签
                created_by=uuid4()
            )
        
        # 测试标签长度限制
        with pytest.raises(ValueError):
            WorkflowDefinitionCreate(
                name='test',
                yaml_content='test',
                tags=['x' * 51],  # 标签太长
                created_by=uuid4()
            )
    
    def test_workflow_execution_schema(self):
        """测试工作流执行Schema"""
        execution_data = {
            'workflow_id': uuid4(),
            'temporal_workflow_id': 'workflow-123',
            'temporal_run_id': 'run-456',
            'status': ExecutionStatus.PENDING,
            'input_data': {'param1': 'value1'},
            'output_data': {},
            'created_by': uuid4()
        }
        
        execution_create = WorkflowExecutionCreate(**execution_data)
        assert execution_create.temporal_workflow_id == 'workflow-123'
        assert execution_create.status == ExecutionStatus.PENDING
        assert execution_create.input_data == {'param1': 'value1'}
        assert isinstance(execution_create.id, UUID)
    
    def test_step_execution_schema(self):
        """测试步骤执行Schema"""
        step_data = {
            'execution_id': uuid4(),
            'step_id': 'step-1',
            'step_name': '测试步骤',
            'step_type': 'ai-call',
            'status': StepStatus.PENDING,
            'input_data': {'prompt': 'test'},
            'output_data': {},
            'cost_info': {'tokens': 0, 'cost': 0.0}
        }
        
        step_create = StepExecutionCreate(**step_data)
        assert step_create.step_id == 'step-1'
        assert step_create.step_type == 'ai-call'
        assert step_create.status == StepStatus.PENDING
        assert step_create.cost_info == {'tokens': 0, 'cost': 0.0}
        assert isinstance(step_create.id, UUID)
    
    def test_approval_request_schema(self):
        """测试审批请求Schema"""
        approval_data = {
            'execution_id': uuid4(),
            'step_id': 'approval-step',
            'title': '请审批',
            'description': '需要人工审批',
            'context_data': {'data': 'test'},
            'status': ApprovalStatus.PENDING,
            'approval_token': 'token-123',
            'requested_by': uuid4()
        }
        
        approval_create = ApprovalRequestCreate(**approval_data)
        assert approval_create.title == '请审批'
        assert approval_create.status == ApprovalStatus.PENDING
        assert approval_create.approval_token == 'token-123'
        assert isinstance(approval_create.id, UUID)
    
    def test_execution_log_schema(self):
        """测试执行日志Schema"""
        log_data = {
            'execution_id': uuid4(),
            'step_id': 'step-1',
            'level': LogLevel.INFO,
            'message': '测试日志消息',
            'metadata': {'key': 'value'}
        }
        
        log_create = ExecutionLogCreate(**log_data)
        assert log_create.level == LogLevel.INFO
        assert log_create.message == '测试日志消息'
        assert log_create.metadata == {'key': 'value'}
        assert isinstance(log_create.id, UUID)
        assert isinstance(log_create.timestamp, datetime)


class TestEnumTypes:
    """测试枚举类型"""
    
    def test_workflow_status_enum(self):
        """测试工作流状态枚举"""
        assert WorkflowStatus.DRAFT == "draft"
        assert WorkflowStatus.ACTIVE == "active"
        assert WorkflowStatus.INACTIVE == "inactive"
        assert WorkflowStatus.ARCHIVED == "archived"
    
    def test_execution_status_enum(self):
        """测试执行状态枚举"""
        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.RUNNING == "running"
        assert ExecutionStatus.COMPLETED == "completed"
        assert ExecutionStatus.FAILED == "failed"
        assert ExecutionStatus.CANCELLED == "cancelled"
        assert ExecutionStatus.PAUSED == "paused"
    
    def test_step_status_enum(self):
        """测试步骤状态枚举"""
        assert StepStatus.PENDING == "pending"
        assert StepStatus.RUNNING == "running"
        assert StepStatus.COMPLETED == "completed"
        assert StepStatus.FAILED == "failed"
        assert StepStatus.SKIPPED == "skipped"
    
    def test_approval_status_enum(self):
        """测试审批状态枚举"""
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.REJECTED == "rejected"
        assert ApprovalStatus.EXPIRED == "expired"
    
    def test_log_level_enum(self):
        """测试日志级别枚举"""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestSchemaUpdates:
    """测试Schema更新"""
    
    def test_user_profile_update(self):
        """测试用户配置更新"""
        update_data = {
            'display_name': '新显示名称',
            'timezone': 'UTC',
            'preferences': {'theme': 'light'}
        }
        
        user_update = UserProfileUpdate(**update_data)
        assert user_update.display_name == '新显示名称'
        assert user_update.timezone == 'UTC'
        assert user_update.preferences == {'theme': 'light'}
    
    def test_workflow_definition_update(self):
        """测试工作流定义更新"""
        update_data = {
            'description': '更新的描述',
            'status': WorkflowStatus.ACTIVE,
            'tags': ['updated', 'active']
        }
        
        workflow_update = WorkflowDefinitionUpdate(**update_data)
        assert workflow_update.description == '更新的描述'
        assert workflow_update.status == WorkflowStatus.ACTIVE
        assert workflow_update.tags == ['updated', 'active']
    
    def test_workflow_execution_update(self):
        """测试工作流执行更新"""
        update_data = {
            'status': ExecutionStatus.COMPLETED,
            'output_data': {'result': 'success'},
            'completed_at': datetime.utcnow()
        }
        
        execution_update = WorkflowExecutionUpdate(**update_data)
        assert execution_update.status == ExecutionStatus.COMPLETED
        assert execution_update.output_data == {'result': 'success'}
        assert isinstance(execution_update.completed_at, datetime)
    
    def test_step_execution_update(self):
        """测试步骤执行更新"""
        update_data = {
            'status': StepStatus.COMPLETED,
            'output_data': {'response': 'AI response'},
            'cost_info': {'tokens': 100, 'cost': 0.01}
        }
        
        step_update = StepExecutionUpdate(**update_data)
        assert step_update.status == StepStatus.COMPLETED
        assert step_update.output_data == {'response': 'AI response'}
        assert step_update.cost_info == {'tokens': 100, 'cost': 0.01}
    
    def test_approval_request_update(self):
        """测试审批请求更新"""
        update_data = {
            'status': ApprovalStatus.APPROVED,
            'approved_by': uuid4(),
            'responded_at': datetime.utcnow(),
            'response_note': '审批通过'
        }
        
        approval_update = ApprovalRequestUpdate(**update_data)
        assert approval_update.status == ApprovalStatus.APPROVED
        assert isinstance(approval_update.approved_by, UUID)
        assert isinstance(approval_update.responded_at, datetime)
        assert approval_update.response_note == '审批通过'


class TestSchemaJsonSerialization:
    """测试Schema JSON序列化"""
    
    def test_user_profile_json_serialization(self):
        """测试用户配置JSON序列化"""
        user_data = {
            'username': 'testuser',
            'display_name': '测试用户',
            'timezone': 'Asia/Shanghai',
            'preferences': {'theme': 'dark'}
        }
        
        user_create = UserProfileCreate(**user_data)
        json_data = user_create.dict()
        
        assert 'id' in json_data
        assert json_data['username'] == 'testuser'
        assert json_data['display_name'] == '测试用户'
        assert json_data['preferences'] == {'theme': 'dark'}
    
    def test_workflow_definition_json_serialization(self):
        """测试工作流定义JSON序列化"""
        workflow_data = {
            'name': 'test-workflow',
            'yaml_content': 'name: test\nsteps: []',
            'parsed_config': {'name': 'test', 'steps': []},
            'status': WorkflowStatus.DRAFT,
            'tags': ['test'],
            'created_by': uuid4()
        }
        
        workflow_create = WorkflowDefinitionCreate(**workflow_data)
        json_data = workflow_create.dict()
        
        assert json_data['name'] == 'test-workflow'
        assert json_data['status'] == 'draft'  # 枚举值序列化
        assert json_data['tags'] == ['test']
        assert 'created_by' in json_data
    
    def test_datetime_serialization(self):
        """测试日期时间序列化"""
        log_data = {
            'execution_id': uuid4(),
            'level': LogLevel.INFO,
            'message': '测试消息',
            'metadata': {}
        }
        
        log_create = ExecutionLogCreate(**log_data)
        json_data = log_create.dict()
        
        assert 'timestamp' in json_data
        assert isinstance(json_data['timestamp'], datetime)


class TestSchemaValidationEdgeCases:
    """测试Schema验证边界情况"""
    
    def test_empty_strings_validation(self):
        """测试空字符串验证"""
        # 工作流名称不能为空
        with pytest.raises(ValueError):
            WorkflowDefinitionCreate(
                name='',
                yaml_content='test',
                created_by=uuid4()
            )
        
        # YAML内容不能为空
        with pytest.raises(ValueError):
            WorkflowDefinitionCreate(
                name='test',
                yaml_content='',
                created_by=uuid4()
            )
    
    def test_optional_fields(self):
        """测试可选字段"""
        # 用户配置的可选字段
        user_create = UserProfileCreate(username='testuser')
        assert user_create.display_name is None
        assert user_create.avatar_url is None
        assert user_create.timezone == 'UTC'  # 默认值
        assert user_create.preferences == {}  # 默认值
        
        # 工作流定义的可选字段
        workflow_create = WorkflowDefinitionCreate(
            name='test',
            yaml_content='test',
            created_by=uuid4()
        )
        assert workflow_create.description is None
        assert workflow_create.version == 1  # 默认值
        assert workflow_create.status == WorkflowStatus.DRAFT  # 默认值
        assert workflow_create.tags == []  # 默认值
    
    def test_default_values(self):
        """测试默认值"""
        # 步骤执行的默认值
        step_create = StepExecutionCreate(
            execution_id=uuid4(),
            step_id='test',
            step_name='test',
            step_type='test'
        )
        assert step_create.status == StepStatus.PENDING
        assert step_create.input_data == {}
        assert step_create.output_data == {}
        assert step_create.cost_info == {}
        
        # 审批请求的默认值
        approval_create = ApprovalRequestCreate(
            execution_id=uuid4(),
            step_id='test',
            title='test',
            approval_token='token',
            requested_by=uuid4()
        )
        assert approval_create.status == ApprovalStatus.PENDING
        assert approval_create.context_data == {}