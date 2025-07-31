"""初始数据库Schema

Revision ID: 20250108_000001
Revises: 
Create Date: 2025-01-08 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250108_000001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建枚举类型
    workflow_status = postgresql.ENUM('draft', 'active', 'inactive', 'archived', name='workflowstatus')
    workflow_status.create(op.get_bind())
    
    execution_status = postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', 'paused', name='executionstatus')
    execution_status.create(op.get_bind())
    
    step_status = postgresql.ENUM('pending', 'running', 'completed', 'failed', 'skipped', name='stepstatus')
    step_status.create(op.get_bind())
    
    approval_status = postgresql.ENUM('pending', 'approved', 'rejected', 'expired', name='approvalstatus')
    approval_status.create(op.get_bind())
    
    log_level = postgresql.ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', name='loglevel')
    log_level.create(op.get_bind())

    # 创建用户配置表
    op.create_table('user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('preferences', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_profiles_username', 'user_profiles', ['username'], unique=False)
    op.create_index('idx_user_profiles_created_at', 'user_profiles', ['created_at'], unique=False)
    op.create_unique_constraint('uq_user_profiles_username', 'user_profiles', ['username'])

    # 创建工作流定义表
    op.create_table('workflow_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('yaml_content', sa.Text(), nullable=False),
        sa.Column('parsed_config', sa.JSON(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('status', workflow_status, nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workflow_definitions_created_by', 'workflow_definitions', ['created_by'], unique=False)
    op.create_index('idx_workflow_definitions_status', 'workflow_definitions', ['status'], unique=False)
    op.create_index('idx_workflow_definitions_tags', 'workflow_definitions', ['tags'], unique=False, postgresql_using='gin')
    op.create_index('idx_workflow_definitions_created_at', 'workflow_definitions', ['created_at'], unique=False)
    op.create_unique_constraint('uq_workflow_name_version', 'workflow_definitions', ['name', 'version'])

    # 创建工作流执行表
    op.create_table('workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('temporal_workflow_id', sa.String(length=255), nullable=False),
        sa.Column('temporal_run_id', sa.String(length=255), nullable=False),
        sa.Column('status', execution_status, nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('output_data', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflow_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_workflow_executions_workflow_id', 'workflow_executions', ['workflow_id'], unique=False)
    op.create_index('idx_workflow_executions_status', 'workflow_executions', ['status'], unique=False)
    op.create_index('idx_workflow_executions_created_by', 'workflow_executions', ['created_by'], unique=False)
    op.create_index('idx_workflow_executions_created_at', 'workflow_executions', ['created_at'], unique=False)
    op.create_index('idx_workflow_executions_temporal_workflow_id', 'workflow_executions', ['temporal_workflow_id'], unique=False)
    op.create_unique_constraint('uq_workflow_executions_temporal_workflow_id', 'workflow_executions', ['temporal_workflow_id'])

    # 创建步骤执行表
    op.create_table('step_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_id', sa.String(length=255), nullable=False),
        sa.Column('step_name', sa.String(length=255), nullable=False),
        sa.Column('step_type', sa.String(length=50), nullable=False),
        sa.Column('status', step_status, nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('output_data', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('cost_info', sa.JSON(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_step_executions_execution_id', 'step_executions', ['execution_id'], unique=False)
    op.create_index('idx_step_executions_status', 'step_executions', ['status'], unique=False)
    op.create_index('idx_step_executions_step_type', 'step_executions', ['step_type'], unique=False)
    op.create_unique_constraint('uq_step_execution_execution_step', 'step_executions', ['execution_id', 'step_id'])

    # 创建审批请求表
    op.create_table('approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('context_data', sa.JSON(), nullable=False),
        sa.Column('status', approval_status, nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approval_token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by'], ['user_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_approval_requests_execution_id', 'approval_requests', ['execution_id'], unique=False)
    op.create_index('idx_approval_requests_status', 'approval_requests', ['status'], unique=False)
    op.create_index('idx_approval_requests_token', 'approval_requests', ['approval_token'], unique=False)
    op.create_index('idx_approval_requests_expires_at', 'approval_requests', ['expires_at'], unique=False)
    op.create_unique_constraint('uq_approval_requests_token', 'approval_requests', ['approval_token'])

    # 创建执行日志表
    op.create_table('execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_id', sa.String(length=255), nullable=True),
        sa.Column('level', log_level, nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_execution_logs_execution_id', 'execution_logs', ['execution_id'], unique=False)
    op.create_index('idx_execution_logs_level', 'execution_logs', ['level'], unique=False)
    op.create_index('idx_execution_logs_timestamp', 'execution_logs', ['timestamp'], unique=False)


def downgrade() -> None:
    # 删除表
    op.drop_table('execution_logs')
    op.drop_table('approval_requests')
    op.drop_table('step_executions')
    op.drop_table('workflow_executions')
    op.drop_table('workflow_definitions')
    op.drop_table('user_profiles')
    
    # 删除枚举类型
    op.execute('DROP TYPE IF EXISTS loglevel')
    op.execute('DROP TYPE IF EXISTS approvalstatus')
    op.execute('DROP TYPE IF EXISTS stepstatus')
    op.execute('DROP TYPE IF EXISTS executionstatus')
    op.execute('DROP TYPE IF EXISTS workflowstatus')