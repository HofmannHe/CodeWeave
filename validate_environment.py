#!/usr/bin/env python3
"""
开发环境验证脚本

验证Docker Compose配置、Supabase配置和脚本是否正确。
"""

import os
import sys
import yaml
from pathlib import Path

def main():
    print("🔍 验证开发环境配置...")
    
    project_root = Path(__file__).parent
    errors = []
    
    # 检查Docker Compose配置
    print("\n📦 检查Docker Compose配置:")
    compose_file = project_root / "docker-compose.yml"
    if compose_file.exists():
        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 检查必需服务
            services = config.get("services", {})
            required_services = ["postgres", "redis", "temporal", "temporal-web"]
            
            for service in required_services:
                if service in services:
                    print(f"  ✓ {service} 服务已配置")
                else:
                    print(f"  ❌ {service} 服务缺失")
                    errors.append(f"缺少服务: {service}")
            
            # 检查网络和数据卷
            if "networks" in config:
                print("  ✓ 网络配置存在")
            else:
                print("  ❌ 网络配置缺失")
                errors.append("缺少网络配置")
            
            if "volumes" in config:
                print("  ✓ 数据卷配置存在")
            else:
                print("  ❌ 数据卷配置缺失")
                errors.append("缺少数据卷配置")
                
        except Exception as e:
            print(f"  ❌ Docker Compose配置解析失败: {e}")
            errors.append(f"Docker Compose配置错误: {e}")
    else:
        print("  ❌ docker-compose.yml文件不存在")
        errors.append("缺少docker-compose.yml文件")
    
    # 检查Supabase配置
    print("\n🗄️ 检查Supabase配置:")
    supabase_config = project_root / "supabase" / "config.toml"
    if supabase_config.exists():
        print("  ✓ Supabase配置文件存在")
    else:
        print("  ❌ Supabase配置文件不存在")
        errors.append("缺少Supabase配置文件")
    
    # 检查迁移文件
    migration_dir = project_root / "supabase" / "migrations"
    if migration_dir.exists():
        migration_files = list(migration_dir.glob("*.sql"))
        if migration_files:
            print(f"  ✓ 找到 {len(migration_files)} 个迁移文件")
        else:
            print("  ❌ 没有找到迁移文件")
            errors.append("缺少数据库迁移文件")
    else:
        print("  ❌ 迁移目录不存在")
        errors.append("缺少迁移目录")
    
    # 检查启动脚本
    print("\n🚀 检查启动脚本:")
    scripts = [
        ("scripts/start-dev.sh", "Linux/macOS启动脚本"),
        ("scripts/stop-dev.sh", "Linux/macOS停止脚本"),
        ("scripts/start-dev.bat", "Windows启动脚本"),
        ("scripts/stop-dev.bat", "Windows停止脚本"),
        ("scripts/switch-deployment.py", "部署切换脚本"),
        ("scripts/init-db.sql", "数据库初始化脚本"),
    ]
    
    for script_path, description in scripts:
        script_file = project_root / script_path
        if script_file.exists():
            print(f"  ✓ {description}")
        else:
            print(f"  ❌ {description} 不存在")
            errors.append(f"缺少脚本: {script_path}")
    
    # 检查配置文件
    print("\n⚙️ 检查配置文件:")
    config_files = [
        ("config/temporal/development-sql.yaml", "Temporal配置"),
        ("config/prometheus/prometheus.yml", "Prometheus配置"),
        ("config/loki/loki-config.yml", "Loki配置"),
        ("config/grafana/provisioning/datasources/datasources.yml", "Grafana数据源配置"),
    ]
    
    for config_path, description in config_files:
        config_file = project_root / config_path
        if config_file.exists():
            print(f"  ✓ {description}")
        else:
            print(f"  ❌ {description} 不存在")
            errors.append(f"缺少配置: {config_path}")
    
    # 检查环境变量模板
    print("\n🔧 检查环境变量配置:")
    env_example = project_root / ".env.example"
    if env_example.exists():
        with open(env_example, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_vars = [
            "DEPLOYMENT_MODE",
            "DATABASE_TYPE", 
            "POSTGRES_HOST",
            "SUPABASE_URL",
            "TEMPORAL_HOST",
            "JWT_SECRET_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if var in content:
                print(f"  ✓ {var}")
            else:
                print(f"  ❌ {var} 缺失")
                missing_vars.append(var)
        
        if missing_vars:
            errors.extend([f"环境变量缺失: {var}" for var in missing_vars])
    else:
        print("  ❌ .env.example文件不存在")
        errors.append("缺少环境变量模板")
    
    # 总结
    print(f"\n📊 验证结果:")
    if errors:
        print(f"  ❌ 发现 {len(errors)} 个问题:")
        for error in errors:
            print(f"    - {error}")
        return False
    else:
        print("  ✅ 开发环境配置验证通过!")
        print("  🎉 所有必需的配置文件和脚本都存在")
        print("\n🚀 下一步:")
        print("  1. 复制环境变量: cp .env.example .env")
        print("  2. 编辑配置: vim .env")
        print("  3. 启动环境: ./scripts/start-dev.sh")
        return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)