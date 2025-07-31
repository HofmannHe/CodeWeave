-- CodeWeave AI工作流平台 - 数据库初始化脚本
-- 为开发环境创建必要的数据库和用户

-- 创建应用数据库 (如果不存在)
SELECT 'CREATE DATABASE workflow_platform'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'workflow_platform')\gexec

-- 创建测试数据库
SELECT 'CREATE DATABASE workflow_platform_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'workflow_platform_test')\gexec

-- 创建应用用户 (如果不存在)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'workflow_user') THEN

      CREATE ROLE workflow_user LOGIN PASSWORD 'workflow_password';
   END IF;
END
$do$;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE workflow_platform TO workflow_user;
GRANT ALL PRIVILEGES ON DATABASE workflow_platform_test TO workflow_user;

-- 连接到应用数据库
\c workflow_platform;

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 为应用用户授予schema权限
GRANT ALL ON SCHEMA public TO workflow_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO workflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO workflow_user;

-- 连接到测试数据库
\c workflow_platform_test;

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 为应用用户授予schema权限
GRANT ALL ON SCHEMA public TO workflow_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO workflow_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO workflow_user;