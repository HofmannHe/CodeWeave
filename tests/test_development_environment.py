"""
测试开发环境配置

验证Docker Compose配置、Supabase配置和启动脚本是否正确。
"""

import os
import sys
import yaml
import subprocess
from pathlib import Path
import pytest

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestDockerComposeConfiguration:
    """测试Docker Compose配置"""
    
    def test_docker_compose_file_exists(self):
        """测试docker-compose.yml文件存在"""
        compose_file = project_root / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml文件不存在"
    
    def test_docker_compose_file_valid(self):
        """测试docker-compose.yml文件格式正确"""
        compose_file = project_root / "docker-compose.yml"
        
        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            pytest.fail(f"docker-compose.yml格式错误: {e}")
        
        # 检查必需的sections
        assert "version" in config, "缺少version字段"
        assert "services" in config, "缺少services字段"
        assert "volumes" in config, "缺少volumes字段"
        assert "networks" in config, "缺少networks字段"
    
    def test_required_services_defined(self):
        """测试必需的服务已定义"""
        compose_file = project_root / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", {})
        required_services = [
            "postgres",
            "redis", 
            "temporal",
            "temporal-web"
        ]
        
        for service in required_services:
            assert service in services, f"缺少必需服务: {service}"
    
    def test_postgres_service_configuration(self):
        """测试PostgreSQL服务配置"""
        compose_file = project_root / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        postgres = config["services"]["postgres"]
        
        # 检查基本配置
        assert "image" in postgres, "PostgreSQL服务缺少image配置"
        assert "environment" in postgres, "PostgreSQL服务缺少environment配置"
        assert "ports" in postgres, "PostgreSQL服务缺少ports配置"
        assert "volumes" in postgres, "PostgreSQL服务缺少volumes配置"
        assert "healthcheck" in postgres, "PostgreSQL服务缺少healthcheck配置"
        
        # 检查环境变量
        env = postgres["environment"]
        required_env_vars = [
            "POSTGRES_DB",
            "POSTGRES_USER", 
            "POSTGRES_PASSWORD"
        ]
        
        for var in required_env_vars:
            assert var in env, f"PostgreSQL服务缺少环境变量: {var}"
    
    def test_redis_service_configuration(self):
        """测试Redis服务配置"""
        compose_file = project_root / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        redis = config["services"]["redis"]
        
        # 检查基本配置
        assert "image" in redis, "Redis服务缺少image配置"
        assert "ports" in redis, "Redis服务缺少ports配置"
        assert "volumes" in redis, "Redis服务缺少volumes配置"
        assert "healthcheck" in redis, "Redis服务缺少healthcheck配置"
    
    def test_temporal_service_configuration(self):
        """测试Temporal服务配置"""
        compose_file = project_root / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        temporal = config["services"]["temporal"]
        
        # 检查基本配置
        assert "image" in temporal, "Temporal服务缺少image配置"
        assert "depends_on" in temporal, "Temporal服务缺少depends_on配置"
        assert "environment" in temporal, "Temporal服务缺少environment配置"
        assert "ports" in temporal, "Temporal服务缺少ports配置"
        
        # 检查依赖关系
        depends_on = temporal["depends_on"]
        assert "postgres" in depends_on, "Temporal服务应该依赖PostgreSQL"


class TestSupabaseConfiguration:
    """测试Supabase配置"""
    
    def test_supabase_config_file_exists(self):
        """测试Supabase配置文件存在"""
        config_file = project_root / "supabase" / "config.toml"
        assert config_file.exists(), "supabase/config.toml文件不存在"
    
    def test_supabase_migration_exists(self):
        """测试Supabase迁移文件存在"""
        migration_dir = project_root / "supabase" / "migrations"
        assert migration_dir.exists(), "supabase/migrations目录不存在"
        
        # 检查是否有迁移文件
        migration_files = list(migration_dir.glob("*.sql"))
        assert len(migration_files) > 0, "没有找到Supabase迁移文件"
    
    def test_initial_migration_content(self):
        """测试初始迁移文件内容"""
        migration_file = project_root / "supabase" / "migrations" / "20250108000001_initial_schema.sql"
        assert migration_file.exists(), "初始迁移文件不存在"
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键表是否定义
        required_tables = [
            "user_profiles",
            "workflow_definitions",
            "workflow_executions", 
            "step_executions",
            "approval_requests",
            "execution_logs"
        ]
        
        for table in required_tables:
            assert f"CREATE TABLE {table}" in content, f"迁移文件中缺少表定义: {table}"


class TestScriptsConfiguration:
    """测试启动脚本配置"""
    
    def test_start_script_exists(self):
        """测试启动脚本存在"""
        start_script = project_root / "scripts" / "start-dev.sh"
        start_script_bat = project_root / "scripts" / "start-dev.bat"
        
        assert start_script.exists(), "start-dev.sh脚本不存在"
        assert start_script_bat.exists(), "start-dev.bat脚本不存在"
    
    def test_stop_script_exists(self):
        """测试停止脚本存在"""
        stop_script = project_root / "scripts" / "stop-dev.sh"
        stop_script_bat = project_root / "scripts" / "stop-dev.bat"
        
        assert stop_script.exists(), "stop-dev.sh脚本不存在"
        assert stop_script_bat.exists(), "stop-dev.bat脚本不存在"
    
    def test_switch_deployment_script_exists(self):
        """测试部署方案切换脚本存在"""
        switch_script = project_root / "scripts" / "switch-deployment.py"
        assert switch_script.exists(), "switch-deployment.py脚本不存在"
    
    def test_database_init_script_exists(self):
        """测试数据库初始化脚本存在"""
        init_script = project_root / "scripts" / "init-db.sql"
        assert init_script.exists(), "init-db.sql脚本不存在"
    
    def test_scripts_executable(self):
        """测试脚本文件可执行"""
        scripts = [
            "scripts/start-dev.sh",
            "scripts/stop-dev.sh",
        ]
        
        for script_path in scripts:
            script_file = project_root / script_path
            if script_file.exists():
                # 在Unix系统上检查执行权限
                if os.name != 'nt':  # 不是Windows
                    stat_info = script_file.stat()
                    assert stat_info.st_mode & 0o111, f"脚本文件不可执行: {script_path}"


class TestEnvironmentConfiguration:
    """测试环境配置"""
    
    def test_env_example_file_exists(self):
        """测试环境变量示例文件存在"""
        env_example = project_root / ".env.example"
        assert env_example.exists(), ".env.example文件不存在"
    
    def test_env_example_contains_required_vars(self):
        """测试环境变量示例文件包含必需变量"""
        env_example = project_root / ".env.example"
        
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_vars = [
            "DEPLOYMENT_MODE",
            "DATABASE_TYPE",
            "POSTGRES_HOST",
            "POSTGRES_PORT", 
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "SUPABASE_URL",
            "SUPABASE_KEY",
            "REDIS_HOST",
            "REDIS_PORT",
            "TEMPORAL_HOST",
            "TEMPORAL_PORT",
            "JWT_SECRET_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY"
        ]
        
        for var in required_vars:
            assert var in content, f"环境变量示例文件缺少变量: {var}"
    
    def test_dual_deployment_support(self):
        """测试双方案部署支持"""
        env_example = project_root / ".env.example"
        
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查Supabase方案配置
        assert "DEPLOYMENT_MODE=supabase" in content or "supabase" in content, "缺少Supabase方案配置"
        assert "SUPABASE_URL" in content, "缺少Supabase URL配置"
        
        # 检查自建方案配置
        assert "DEPLOYMENT_MODE=self_hosted" in content or "self_hosted" in content, "缺少自建方案配置"
        assert "POSTGRES_HOST" in content, "缺少PostgreSQL配置"


class TestConfigurationFiles:
    """测试配置文件"""
    
    def test_temporal_config_exists(self):
        """测试Temporal配置文件存在"""
        temporal_config = project_root / "config" / "temporal" / "development-sql.yaml"
        assert temporal_config.exists(), "Temporal配置文件不存在"
    
    def test_temporal_config_valid(self):
        """测试Temporal配置文件格式正确"""
        temporal_config = project_root / "config" / "temporal" / "development-sql.yaml"
        
        try:
            with open(temporal_config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            pytest.fail(f"Temporal配置文件格式错误: {e}")
        
        # 检查是否有配置项
        assert isinstance(config, dict), "Temporal配置应该是字典格式"
        assert len(config) > 0, "Temporal配置不能为空"


class TestDeploymentSwitcher:
    """测试部署方案切换器"""
    
    def test_switch_deployment_script_importable(self):
        """测试部署切换脚本可以导入"""
        switch_script = project_root / "scripts" / "switch-deployment.py"
        
        # 添加scripts目录到Python路径
        scripts_dir = project_root / "scripts"
        sys.path.insert(0, str(scripts_dir))
        
        try:
            # 尝试导入脚本中的类
            spec = __import__('switch-deployment', fromlist=['DeploymentSwitcher'])
            DeploymentSwitcher = getattr(spec, 'DeploymentSwitcher')
            
            # 创建实例
            switcher = DeploymentSwitcher(project_root)
            assert switcher is not None, "无法创建DeploymentSwitcher实例"
            
        except ImportError as e:
            pytest.fail(f"无法导入部署切换脚本: {e}")
        except Exception as e:
            pytest.fail(f"部署切换脚本导入失败: {e}")
        finally:
            # 清理Python路径
            if str(scripts_dir) in sys.path:
                sys.path.remove(str(scripts_dir))