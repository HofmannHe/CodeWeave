#!/usr/bin/env python3
"""
项目结构验证脚本

验证项目结构是否符合要求。
"""

import sys
from pathlib import Path

def validate_project_structure():
    """验证项目结构"""
    project_root = Path(__file__).parent
    errors = []
    
    # 检查必需的目录
    required_dirs = [
        "src",
        "src/workflow_platform",
        "src/workflow_platform/api",
        "src/workflow_platform/core",
        "src/workflow_platform/workers",
        "src/workflow_platform/database",
        "src/workflow_platform/integrations",
        "src/workflow_platform/utils",
        "tests",
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            errors.append(f"缺少目录: {dir_path}")
        elif not full_path.is_dir():
            errors.append(f"{dir_path} 不是目录")
    
    # 检查必需的文件
    required_files = [
        "pyproject.toml",
        "README.md",
        ".env.example",
        ".pre-commit-config.yaml",
        "src/workflow_platform/__init__.py",
        "src/workflow_platform/core/__init__.py",
        "src/workflow_platform/core/config.py",
        "src/workflow_platform/core/exceptions.py",
        "src/workflow_platform/core/logging.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_project_structure.py",
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            errors.append(f"缺少文件: {file_path}")
        elif not full_path.is_file():
            errors.append(f"{file_path} 不是文件")
    
    # 检查pyproject.toml内容
    try:
        import toml
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            config = toml.load(pyproject_path)
            
            # 检查必需的sections
            required_sections = [
                "tool.poetry",
                "tool.poetry.dependencies",
                "tool.poetry.group.dev.dependencies",
                "tool.black",
                "tool.isort",
                "tool.mypy",
                "tool.pytest.ini_options",
            ]
            
            for section in required_sections:
                keys = section.split(".")
                current = config
                for key in keys:
                    if key not in current:
                        errors.append(f"pyproject.toml缺少section: {section}")
                        break
                    current = current[key]
    except ImportError:
        print("警告: 无法导入toml模块，跳过pyproject.toml验证")
    except Exception as e:
        errors.append(f"pyproject.toml验证失败: {e}")
    
    # 检查Python模块是否可以导入
    try:
        sys.path.insert(0, str(project_root / "src"))
        
        # 尝试导入核心模块
        from workflow_platform.core.config import Settings
        from workflow_platform.core.exceptions import WorkflowError
        
        # 创建设置实例
        settings = Settings()
        print(f"✓ 成功导入核心模块，应用名称: {settings.app_name}")
        
    except Exception as e:
        errors.append(f"模块导入失败: {e}")
    
    return errors

def main():
    """主函数"""
    print("🔍 验证项目结构...")
    
    errors = validate_project_structure()
    
    if errors:
        print("\n❌ 发现以下问题:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✅ 项目结构验证通过!")
        print("📁 所有必需的目录和文件都存在")
        print("⚙️ 配置文件格式正确")
        print("🐍 Python模块可以正常导入")

if __name__ == "__main__":
    main()