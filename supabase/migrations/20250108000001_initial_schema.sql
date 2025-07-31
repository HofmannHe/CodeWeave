-- CodeWeave AI工作流平台 - 初始数据库Schema
-- Supabase方案的数据库迁移

-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 创建枚举类型
CREATE TYPE deployment_mode AS ENUM ('supabase', 'self_hosted');
CREATE TYPE workflow_status AS ENUM ('draft', 'active', 'inactive', 'archived');
CREATE TYPE execution_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused');
CREATE TYPE step_status AS ENUM ('pending', 'running', 'completed', 'failed', 'skipped');
CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected', 'expired');

-- 用户配置表 (扩展auth.users)
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 工作流定义表
CREATE TABLE workflow_definitions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    yaml_content TEXT NOT NULL,
    parsed_config JSONB NOT NULL,
    version INTEGER DEFAULT 1,
    status workflow_status DEFAULT 'draft',
    tags TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 索引
    CONSTRAINT workflow_definitions_name_version_unique UNIQUE (name, version)
);

-- 工作流执行表
CREATE TABLE workflow_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    workflow_id UUID REFERENCES workflow_definitions(id) ON DELETE CASCADE,
    temporal_workflow_id VARCHAR(255) UNIQUE NOT NULL,
    temporal_run_id VARCHAR(255) NOT NULL,
    status execution_status DEFAULT 'pending',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 步骤执行表
CREATE TABLE step_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    step_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    status step_status DEFAULT 'pending',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    cost_info JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 索引
    CONSTRAINT step_executions_execution_step_unique UNIQUE (execution_id, step_id)
);

-- 审批请求表
CREATE TABLE approval_requests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    step_id VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    context_data JSONB DEFAULT '{}',
    status approval_status DEFAULT 'pending',
    requested_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    approved_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    approval_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    response_note TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 执行日志表
CREATE TABLE execution_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE CASCADE,
    step_id VARCHAR(255),
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建索引
CREATE INDEX idx_workflow_definitions_created_by ON workflow_definitions(created_by);
CREATE INDEX idx_workflow_definitions_status ON workflow_definitions(status);
CREATE INDEX idx_workflow_definitions_tags ON workflow_definitions USING GIN(tags);
CREATE INDEX idx_workflow_definitions_created_at ON workflow_definitions(created_at);

CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_created_by ON workflow_executions(created_by);
CREATE INDEX idx_workflow_executions_created_at ON workflow_executions(created_at);
CREATE INDEX idx_workflow_executions_temporal_workflow_id ON workflow_executions(temporal_workflow_id);

CREATE INDEX idx_step_executions_execution_id ON step_executions(execution_id);
CREATE INDEX idx_step_executions_status ON step_executions(status);
CREATE INDEX idx_step_executions_step_type ON step_executions(step_type);

CREATE INDEX idx_approval_requests_execution_id ON approval_requests(execution_id);
CREATE INDEX idx_approval_requests_status ON approval_requests(status);
CREATE INDEX idx_approval_requests_token ON approval_requests(approval_token);
CREATE INDEX idx_approval_requests_expires_at ON approval_requests(expires_at);

CREATE INDEX idx_execution_logs_execution_id ON execution_logs(execution_id);
CREATE INDEX idx_execution_logs_level ON execution_logs(level);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(timestamp);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建更新时间触发器
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_definitions_updated_at BEFORE UPDATE ON workflow_definitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflow_executions_updated_at BEFORE UPDATE ON workflow_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_step_executions_updated_at BEFORE UPDATE ON step_executions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_approval_requests_updated_at BEFORE UPDATE ON approval_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 行级安全策略 (RLS)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE step_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_logs ENABLE ROW LEVEL SECURITY;

-- 用户配置策略
CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);

-- 工作流定义策略
CREATE POLICY "Users can view own workflows" ON workflow_definitions FOR SELECT USING (auth.uid() = created_by);
CREATE POLICY "Users can create workflows" ON workflow_definitions FOR INSERT WITH CHECK (auth.uid() = created_by);
CREATE POLICY "Users can update own workflows" ON workflow_definitions FOR UPDATE USING (auth.uid() = created_by);
CREATE POLICY "Users can delete own workflows" ON workflow_definitions FOR DELETE USING (auth.uid() = created_by);

-- 工作流执行策略
CREATE POLICY "Users can view own executions" ON workflow_executions FOR SELECT USING (auth.uid() = created_by);
CREATE POLICY "Users can create executions" ON workflow_executions FOR INSERT WITH CHECK (auth.uid() = created_by);
CREATE POLICY "Users can update own executions" ON workflow_executions FOR UPDATE USING (auth.uid() = created_by);

-- 步骤执行策略
CREATE POLICY "Users can view own step executions" ON step_executions 
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM workflow_executions 
        WHERE workflow_executions.id = step_executions.execution_id 
        AND workflow_executions.created_by = auth.uid()
    )
);

CREATE POLICY "Users can update own step executions" ON step_executions 
FOR UPDATE USING (
    EXISTS (
        SELECT 1 FROM workflow_executions 
        WHERE workflow_executions.id = step_executions.execution_id 
        AND workflow_executions.created_by = auth.uid()
    )
);

CREATE POLICY "Users can insert step executions" ON step_executions 
FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM workflow_executions 
        WHERE workflow_executions.id = step_executions.execution_id 
        AND workflow_executions.created_by = auth.uid()
    )
);

-- 审批请求策略
CREATE POLICY "Users can view related approval requests" ON approval_requests 
FOR SELECT USING (
    auth.uid() = requested_by OR 
    EXISTS (
        SELECT 1 FROM workflow_executions 
        WHERE workflow_executions.id = approval_requests.execution_id 
        AND workflow_executions.created_by = auth.uid()
    )
);

CREATE POLICY "Users can update approval requests" ON approval_requests 
FOR UPDATE USING (
    auth.uid() = requested_by OR 
    EXISTS (
        SELECT 1 FROM workflow_executions 
        WHERE workflow_executions.id = approval_requests.execution_id 
        AND workflow_executions.created_by = auth.uid()
    )
);

-- 执行日志策略
CREATE POLICY "Users can view own execution logs" ON execution_logs 
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM workflow_executions 
        WHERE workflow_executions.id = execution_logs.execution_id 
        AND workflow_executions.created_by = auth.uid()
    )
);

CREATE POLICY "System can insert execution logs" ON execution_logs 
FOR INSERT WITH CHECK (true); -- 系统可以插入日志