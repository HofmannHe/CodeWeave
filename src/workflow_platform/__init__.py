"""
CodeWeave AI工作流平台

一个基于AI的智能工作流编排和执行平台，支持复杂的工作流设计、可视化编辑和自动化执行。
"""

__version__ = "0.1.0"
__author__ = "CodeWeave Team"
__email__ = "team@codeweave.ai"

# 导出主要组件
from .core.config import settings
from .core.exceptions import WorkflowError, ValidationError

__all__ = [
    "settings",
    "WorkflowError", 
    "ValidationError",
]