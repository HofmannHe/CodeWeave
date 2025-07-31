#!/usr/bin/env python3
"""
简单的项目结构验证脚本
"""

import os
import sys
from pathlib import Path

def main():
    print("🔍 验证项目结构...")
    
    project_root = Path(__file__).parent
    errors = []
    
    # 检查目录结构
    required_dirs = [
        "src/workflow_platform",
        "src/workflow_platform/api",
        "src/workflow_platform/core", 
        "src/workflow_platform/workers",
        "src/workflow_platform/database",
        "src/workflow_platform/integrations",
        "src/workflow_platform/utils",
        "tests",
    ]
    
    print("\n📁 检查目录结构:")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ❌ {dir_path}")
            errors.append(f"缺少目录: {dir_path}")
    
    # 检查关键文件
    required_files = [
        "pyproject.toml",
        "README.md", 
        ".env.example",
        "src/workflow_platform/__init__.py",
        "src/workflow_platform/core/config.py",
        "src/workflow_platform/core/exceptions.py",
        "tests/test_project_structure.py",
    ]
    
    print("\n📄 检查关键文件:")
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists() and full_path.is_file():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            errors.append(f"缺少文件: {file_path}")
    
    # 尝试导入核心模块
    print("\n🐍 检查Python模块:")
    try:
        sys.path.insert(0, str(project_root / "src"))
        
        # 检查__init__.py文件
        init_file = project_root / "src/workflow_platform/__init__.py"
        if init_file.exists():
            print("  ✓ workflow_platform包初始化文件存在")
        else:
            print("  ❌ workflow_platform包初始化文件不存在")
            errors.append("缺少workflow_platform/__init__.py")
        
        # 检查核心模块文件
        config_file = project_root / "src/workflow_platform/core/config.py"
        if config_file.exists():
            print("  ✓ 核心配置模块存在")
        else:
            print("  ❌ 核心配置模块不存在")
            errors.append("缺少core/config.py")
            
        exceptions_file = project_root / "src/workflow_platform/core/exceptions.py"
        if exceptions_file.exists():
            print("  ✓ 异常处理模块存在")
        else:
            print("  ❌ 异常处理模块不存在")
            errors.append("缺少core/exceptions.py")
            
    except Exception as e:
        print(f"  ❌ 模块检查失败: {e}")
        errors.append(f"模块检查失败: {e}")
    
    # 总结
    print(f"\n📊 验证结果:")
    if errors:
        print(f"  ❌ 发现 {len(errors)} 个问题:")
        for error in errors:
            print(f"    - {error}")
        return False
    else:
        print("  ✅ 项目结构验证通过!")
        print("  🎉 所有必需的目录和文件都存在")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)