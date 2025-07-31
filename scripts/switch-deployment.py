#!/usr/bin/env python3
"""
CodeWeave AI工作流平台 - 部署方案切换脚本

支持在Supabase方案和自建方案之间切换。
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any
import argparse

# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def log_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def log_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def log_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

class DeploymentSwitcher:
    """部署方案切换器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.env_file = project_root / ".env"
        self.env_example = project_root / ".env.example"
    
    def read_env_file(self, file_path: Path) -> Dict[str, str]:
        """读取环境变量文件"""
        env_vars = {}
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        return env_vars
    
    def write_env_file(self, env_vars: Dict[str, str]):
        """写入环境变量文件"""
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write("# CodeWeave AI工作流平台 - 环境变量配置\n")
            f.write("# 由部署方案切换脚本自动生成\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
    
    def switch_to_supabase(self, supabase_url: str = None, supabase_key: str = None):
        """切换到Supabase方案"""
        log_info("切换到Supabase部署方案...")
        
        # 读取当前环境变量
        env_vars = self.read_env_file(self.env_file) if self.env_file.exists() else {}
        
        # 更新部署相关配置
        env_vars.update({
            'DEPLOYMENT_MODE': 'supabase',
            'DATABASE_TYPE': 'supabase',
        })
        
        # 如果提供了Supabase配置，更新它们
        if supabase_url:
            env_vars['SUPABASE_URL'] = supabase_url
        if supabase_key:
            env_vars['SUPABASE_KEY'] = supabase_key
        
        # 注释掉自建数据库配置
        postgres_keys = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
        for key in postgres_keys:
            if key in env_vars:
                env_vars[f'#{key}'] = env_vars.pop(key)
        
        self.write_env_file(env_vars)
        log_success("已切换到Supabase方案")
        
        # 提示用户配置Supabase
        if not supabase_url or not supabase_key:
            log_warning("请在.env文件中配置以下Supabase参数:")
            log_warning("  SUPABASE_URL=https://your-project.supabase.co")
            log_warning("  SUPABASE_KEY=your_anon_key_here")
            log_warning("  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here")
    
    def switch_to_self_hosted(self):
        """切换到自建方案"""
        log_info("切换到自建部署方案...")
        
        # 读取当前环境变量
        env_vars = self.read_env_file(self.env_file) if self.env_file.exists() else {}
        
        # 更新部署相关配置
        env_vars.update({
            'DEPLOYMENT_MODE': 'self_hosted',
            'DATABASE_TYPE': 'postgresql',
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_DB': 'workflow_platform',
            'POSTGRES_USER': 'postgres',
            'POSTGRES_PASSWORD': 'password',
        })
        
        # 注释掉Supabase配置
        supabase_keys = ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_ROLE_KEY']
        for key in supabase_keys:
            if key in env_vars:
                env_vars[f'#{key}'] = env_vars.pop(key)
        
        # 恢复被注释的PostgreSQL配置
        postgres_keys = ['POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
        for key in postgres_keys:
            commented_key = f'#{key}'
            if commented_key in env_vars:
                env_vars[key] = env_vars.pop(commented_key)
        
        self.write_env_file(env_vars)
        log_success("已切换到自建方案")
        
        log_info("请确保Docker服务正在运行，然后执行:")
        log_info("  ./scripts/start-dev.sh")
    
    def show_current_mode(self):
        """显示当前部署模式"""
        if not self.env_file.exists():
            log_warning("环境变量文件不存在")
            return
        
        env_vars = self.read_env_file(self.env_file)
        deployment_mode = env_vars.get('DEPLOYMENT_MODE', 'unknown')
        database_type = env_vars.get('DATABASE_TYPE', 'unknown')
        
        log_info(f"当前部署模式: {deployment_mode}")
        log_info(f"当前数据库类型: {database_type}")
        
        if deployment_mode == 'supabase':
            supabase_url = env_vars.get('SUPABASE_URL', '未配置')
            log_info(f"Supabase URL: {supabase_url}")
        elif deployment_mode == 'self_hosted':
            postgres_host = env_vars.get('POSTGRES_HOST', '未配置')
            postgres_db = env_vars.get('POSTGRES_DB', '未配置')
            log_info(f"PostgreSQL: {postgres_host}/{postgres_db}")
    
    def create_env_from_example(self):
        """从示例文件创建环境变量文件"""
        if not self.env_example.exists():
            log_error(".env.example文件不存在")
            return False
        
        if self.env_file.exists():
            log_warning(".env文件已存在")
            response = input("是否覆盖现有文件? (y/N): ")
            if response.lower() != 'y':
                return False
        
        shutil.copy2(self.env_example, self.env_file)
        log_success("已从.env.example创建.env文件")
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CodeWeave部署方案切换工具")
    parser.add_argument('mode', choices=['supabase', 'self-hosted', 'status'], 
                       help='部署模式: supabase, self-hosted, 或 status')
    parser.add_argument('--supabase-url', help='Supabase项目URL')
    parser.add_argument('--supabase-key', help='Supabase匿名密钥')
    parser.add_argument('--create-env', action='store_true', 
                       help='从.env.example创建.env文件')
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    switcher = DeploymentSwitcher(project_root)
    
    # 如果需要创建环境变量文件
    if args.create_env:
        switcher.create_env_from_example()
    
    # 执行相应操作
    if args.mode == 'status':
        switcher.show_current_mode()
    elif args.mode == 'supabase':
        switcher.switch_to_supabase(args.supabase_url, args.supabase_key)
    elif args.mode == 'self-hosted':
        switcher.switch_to_self_hosted()
    
    print()
    log_info("切换完成！请重启相关服务以使配置生效。")

if __name__ == "__main__":
    main()