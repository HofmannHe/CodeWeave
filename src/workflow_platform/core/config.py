"""
应用程序配置

支持双方案部署：Supabase和自建数据库。
"""

from enum import Enum
from typing import Optional, List
from pydantic import Field, validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class DeploymentMode(str, Enum):
    """部署模式"""
    SUPABASE = "supabase"
    SELF_HOSTED = "self_hosted"


class DatabaseType(str, Enum):
    """数据库类型"""
    POSTGRESQL = "postgresql"
    SUPABASE = "supabase"


class Settings(BaseSettings):
    """应用程序设置"""
    
    # 基础配置
    app_name: str = "CodeWeave AI工作流平台"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # 部署配置
    deployment_mode: DeploymentMode = DeploymentMode.SELF_HOSTED
    database_type: DatabaseType = DatabaseType.POSTGRESQL
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    
    # 数据库配置 (自建方案)
    database_url: Optional[str] = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "workflow_platform"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    
    # Supabase配置
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Temporal配置
    temporal_host: str = "localhost"
    temporal_port: int = 7233
    temporal_namespace: str = "default"
    temporal_task_queue: str = "workflow-task-queue"
    
    # Temporal Cloud配置 (可选)
    temporal_cloud_endpoint: Optional[str] = None
    temporal_cloud_namespace: Optional[str] = None
    temporal_cloud_api_key: Optional[str] = None
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # AI服务配置
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # 通知配置
    slack_webhook_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS配置
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    @validator("database_url", pre=True)
    def build_database_url(cls, v, values):
        """构建数据库URL"""
        if v:
            return v
        
        if values.get("database_type") == DatabaseType.POSTGRESQL:
            host = values.get("postgres_host", "localhost")
            port = values.get("postgres_port", 5432)
            db = values.get("postgres_db", "workflow_platform")
            user = values.get("postgres_user", "postgres")
            password = values.get("postgres_password", "password")
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        
        return None
    
    @validator("redis_url", pre=True)
    def build_redis_url(cls, v, values):
        """构建Redis URL"""
        if v and v != "redis://localhost:6379/0":
            return v
        
        host = values.get("redis_host", "localhost")
        port = values.get("redis_port", 6379)
        db = values.get("redis_db", 0)
        password = values.get("redis_password")
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        else:
            return f"redis://{host}:{port}/{db}"
    
    @property
    def is_supabase_mode(self) -> bool:
        """是否为Supabase模式"""
        return self.deployment_mode == DeploymentMode.SUPABASE
    
    @property
    def is_self_hosted_mode(self) -> bool:
        """是否为自建模式"""
        return self.deployment_mode == DeploymentMode.SELF_HOSTED
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 全局设置实例
settings = Settings()