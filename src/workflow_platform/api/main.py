"""
FastAPI应用程序主文件

CodeWeave AI工作流平台的API服务器。
"""

from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.config import settings
from ..core.exceptions import (
    WorkflowError, ValidationError, DatabaseError, 
    AuthenticationError, AuthorizationError
)
from ..core.logging import get_logger
from ..database.factory import get_database_factory
from .routes import auth, workflows, executions
from .schemas import ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时执行
    logger.info("启动CodeWeave API服务器...")
    
    try:
        # 初始化数据库连接
        factory = get_database_factory()
        await factory.initialize()
        await factory.connect_all()
        logger.info("数据库连接初始化完成")
        
        yield
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        raise
    finally:
        # 关闭时执行
        logger.info("关闭CodeWeave API服务器...")
        try:
            factory = get_database_factory()
            await factory.disconnect_all()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")


# 创建FastAPI应用实例
app = FastAPI(
    title="CodeWeave AI工作流平台",
    description="基于AI的智能工作流编排和执行平台",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# 添加可信主机中间件（生产环境）
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.codeweave.ai"]
    )


# 异常处理器
@app.exception_handler(WorkflowError)
async def workflow_error_handler(request: Request, exc: WorkflowError) -> JSONResponse:
    """工作流错误处理器"""
    logger.warning(f"工作流错误: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=exc.error_code or "WORKFLOW_ERROR",
            message=exc.message,
            details=exc.details
        ).dict()
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """验证错误处理器"""
    logger.warning(f"验证错误: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message=exc.message,
            details={"field": exc.field, "value": exc.value} if hasattr(exc, 'field') else None
        ).dict()
    )


@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """认证错误处理器"""
    logger.warning(f"认证错误: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(
            error="AUTHENTICATION_ERROR",
            message=exc.message
        ).dict(),
        headers={"WWW-Authenticate": "Bearer"}
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """授权错误处理器"""
    logger.warning(f"授权错误: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=ErrorResponse(
            error="AUTHORIZATION_ERROR",
            message=exc.message
        ).dict()
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """数据库错误处理器"""
    logger.error(f"数据库错误: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="DATABASE_ERROR",
            message="数据库操作失败" if not settings.debug else exc.message
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """请求验证错误处理器"""
    logger.warning(f"请求验证错误: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="REQUEST_VALIDATION_ERROR",
            message="请求参数验证失败",
            details={"errors": exc.errors()}
        ).dict()
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTP_ERROR",
            message=exc.detail
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="服务器内部错误" if not settings.debug else str(exc)
        ).dict()
    )


# 中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """请求日志中间件"""
    import time
    
    start_time = time.time()
    
    # 记录请求信息
    logger.info(
        f"请求开始: {request.method} {request.url}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent")
        }
    )
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录响应信息
    logger.info(
        f"请求完成: {request.method} {request.url} - {response.status_code}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": round(process_time, 4)
        }
    )
    
    # 添加处理时间头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    try:
        # 检查数据库连接
        factory = get_database_factory()
        user_adapter = factory.get_user_adapter()
        
        # 简单的数据库连接测试
        await user_adapter.count(None, {})
        
        return {
            "status": "healthy",
            "version": settings.app_version,
            "deployment_mode": settings.deployment_mode,
            "timestamp": "2025-01-08T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="服务不可用"
        )


@app.get("/", tags=["系统"])
async def root() -> Dict[str, Any]:
    """根端点"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "基于AI的智能工作流编排和执行平台",
        "docs_url": "/docs" if settings.debug else None,
        "health_url": "/health"
    }


# 注册路由
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(workflows.router, prefix=settings.api_prefix)
app.include_router(executions.router, prefix=settings.api_prefix)

# 如果是开发模式，添加调试信息
if settings.debug:
    @app.get("/debug/config", tags=["调试"])
    async def debug_config() -> Dict[str, Any]:
        """调试配置信息"""
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "deployment_mode": settings.deployment_mode,
            "database_type": settings.database_type,
            "debug": settings.debug,
            "api_prefix": settings.api_prefix,
            "cors_origins": settings.cors_origins
        }


# 添加启动事件处理器
@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info(f"CodeWeave API服务器启动完成")
    logger.info(f"应用名称: {settings.app_name}")
    logger.info(f"版本: {settings.app_version}")
    logger.info(f"部署模式: {settings.deployment_mode}")
    logger.info(f"调试模式: {settings.debug}")
    logger.info(f"API前缀: {settings.api_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("CodeWeave API服务器已关闭")