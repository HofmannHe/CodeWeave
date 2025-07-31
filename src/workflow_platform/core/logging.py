"""
结构化日志配置

使用structlog实现结构化JSON日志记录。
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import EventDict, Processor

from .config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加应用程序上下文信息"""
    event_dict["app"] = settings.app_name
    event_dict["version"] = settings.app_version
    event_dict["deployment_mode"] = settings.deployment_mode
    return event_dict


def add_correlation_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """添加关联ID（如果存在）"""
    # 这里可以从上下文变量中获取关联ID
    # 例如从FastAPI的Request对象或Temporal的工作流上下文
    return event_dict


def configure_logging() -> None:
    """配置结构化日志"""
    
    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # 配置structlog处理器
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_app_context,
        add_correlation_id,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """获取结构化日志记录器"""
    return structlog.get_logger(name)


# 配置日志（在模块导入时执行）
configure_logging()

# 导出默认日志记录器
logger = get_logger(__name__)