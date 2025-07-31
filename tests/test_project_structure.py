"""
测试项目结构完整性

验证项目目录结构和基础配置是否正确。
"""

import os
import sys
from pathlib import Path
import pytest
import toml

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


class TestProjectStructure:
    """测试项目结构"""
    
    def test_src_directory_exists(self):
        """测试src目录存在"""
        src_dir = project_root / "src"
        assert src_dir.exists(), "src目录不存在"
        assert src_dir.is_dir(), "src不是目录"
    
    def test_workflow_platform_package_exists(self):
        """测试workflow_platform包存在"""
        package_dir = project_root / "src" / "workflow_platform"
        assert package_dir.exists(), "workflow_platform包不存在"
        assert package_dir.is_dir(), "workflow_platform不是目录"
        
        init_file = package_dir / "__init__.py"
        assert init_file.exists(), "workflow_platform包缺少__init__.py"
    
    def test_required_submodules_exist(self):
        """测试必需的子模块存在"""
        base_dir = project_root / "src" / "workflow_platform"
        required_modules = [
            "api",
            "core", 
            "workers",
            "database",
            "integrations",
            "utils"
        ]
        
        for module in required_modules:
            module_dir = base_dir / module
            assert module_dir.exists(), f"{module}模块目录不存在"
            assert module_dir.is_dir(), f"{module}不是目录"
            
            init_file = module_dir / "__init__.py"
            assert init_file.exists(), f"{module}模块缺少__init__.py"
    
    def test_pyproject_toml_exists(self):
        """测试pyproject.toml文件存在"""
        pyproject_file = project_root / "pyproject.toml"
        assert pyproject_file.exists(), "pyproject.toml文件不存在"
    
    def test_pyproject_toml_valid(self):
        """测试pyproject.toml文件格式正确"""
        pyproject_file = project_root / "pyproject.toml"
        
        try:
            config = toml.load(pyproject_file)
        except Exception as e:
            pytest.fail(f"pyproject.toml格式错误: {e}")
        
        # 检查必需的sections
        assert "tool.poetry" in config, "缺少[tool.poetry]section"
        assert "tool.poetry.dependencies" in config, "缺少依赖配置"
        assert "tool.poetry.group.dev.dependencies" in config, "缺少开发依赖配置"
        
        # 检查基本信息
        poetry_config = config["tool.poetry"]
        assert "name" in poetry_config, "缺少项目名称"
        assert "version" in poetry_config, "缺少版本号"
        assert "description" in poetry_config, "缺少项目描述"
    
    def test_core_modules_importable(self):
        """测试核心模块可以导入"""
        try:
            from workflow_platform.core.config import settings
            from workflow_platform.core.exceptions import WorkflowError, ValidationError
            from workflow_platform.core.logging import logger
        except ImportError as e:
            pytest.fail(f"核心模块导入失败: {e}")
    
    def test_settings_configuration(self):
        """测试设置配置正确"""
        from workflow_platform.core.config import settings
        
        # 检查基本配置存在
        assert hasattr(settings, "app_name"), "缺少app_name配置"
        assert hasattr(settings, "app_version"), "缺少app_version配置"
        assert hasattr(settings, "deployment_mode"), "缺少deployment_mode配置"
        assert hasattr(settings, "database_type"), "缺少database_type配置"
        
        # 检查配置值类型正确
        assert isinstance(settings.app_name, str), "app_name应该是字符串"
        assert isinstance(settings.debug, bool), "debug应该是布尔值"
        assert isinstance(settings.api_port, int), "api_port应该是整数"
    
    def test_exceptions_hierarchy(self):
        """测试异常类层次结构正确"""
        from workflow_platform.core.exceptions import (
            WorkflowError,
            ValidationError,
            ConfigurationError,
            DatabaseError,
            TemporalError,
            AIServiceError,
            AuthenticationError,
            AuthorizationError,
            WorkflowExecutionError,
            NotificationError,
        )
        
        # 检查异常继承关系
        assert issubclass(ValidationError, WorkflowError), "ValidationError应该继承WorkflowError"
        assert issubclass(ConfigurationError, WorkflowError), "ConfigurationError应该继承WorkflowError"
        assert issubclass(DatabaseError, WorkflowError), "DatabaseError应该继承WorkflowError"
        assert issubclass(TemporalError, WorkflowError), "TemporalError应该继承WorkflowError"
        assert issubclass(AIServiceError, WorkflowError), "AIServiceError应该继承WorkflowError"
        assert issubclass(AuthenticationError, WorkflowError), "AuthenticationError应该继承WorkflowError"
        assert issubclass(AuthorizationError, WorkflowError), "AuthorizationError应该继承WorkflowError"
        assert issubclass(WorkflowExecutionError, WorkflowError), "WorkflowExecutionError应该继承WorkflowError"
        assert issubclass(NotificationError, WorkflowError), "NotificationError应该继承WorkflowError"
    
    def test_logging_configuration(self):
        """测试日志配置正确"""
        from workflow_platform.core.logging import logger, get_logger
        
        # 检查日志记录器可用
        assert logger is not None, "默认日志记录器不可用"
        
        # 检查可以创建新的日志记录器
        test_logger = get_logger("test")
        assert test_logger is not None, "无法创建新的日志记录器"
        
        # 检查日志记录器有基本方法
        assert hasattr(test_logger, "info"), "日志记录器缺少info方法"
        assert hasattr(test_logger, "error"), "日志记录器缺少error方法"
        assert hasattr(test_logger, "debug"), "日志记录器缺少debug方法"
        assert hasattr(test_logger, "warning"), "日志记录器缺少warning方法"


class TestDependencyConfiguration:
    """测试依赖配置"""
    
    def test_required_dependencies_present(self):
        """测试必需的依赖包存在"""
        pyproject_file = project_root / "pyproject.toml"
        config = toml.load(pyproject_file)
        
        dependencies = config["tool.poetry"]["dependencies"]
        required_deps = [
            "fastapi",
            "uvicorn", 
            "temporalio",
            "sqlalchemy",
            "alembic",
            "psycopg2-binary",
            "redis",
            "pydantic",
            "pydantic-settings",
            "httpx",
            "pyyaml",
            "python-jose",
            "passlib",
            "python-multipart",
            "websockets",
            "structlog",
            "prometheus-client",
            "openai",
            "anthropic",
            "supabase",
            "postgrest",
        ]
        
        for dep in required_deps:
            assert dep in dependencies, f"缺少必需依赖: {dep}"
    
    def test_dev_dependencies_present(self):
        """测试开发依赖包存在"""
        pyproject_file = project_root / "pyproject.toml"
        config = toml.load(pyproject_file)
        
        dev_deps = config["tool.poetry"]["group"]["dev"]["dependencies"]
        required_dev_deps = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "black",
            "isort",
            "mypy",
            "flake8",
            "pre-commit",
        ]
        
        for dep in required_dev_deps:
            assert dep in dev_deps, f"缺少必需开发依赖: {dep}"
    
    def test_tool_configurations_present(self):
        """测试工具配置存在"""
        pyproject_file = project_root / "pyproject.toml"
        config = toml.load(pyproject_file)
        
        required_tools = [
            "tool.black",
            "tool.isort", 
            "tool.mypy",
            "tool.pytest.ini_options",
            "tool.coverage.run",
            "tool.coverage.report",
        ]
        
        for tool in required_tools:
            keys = tool.split(".")
            current = config
            for key in keys:
                assert key in current, f"缺少工具配置: {tool}"
                current = current[key]