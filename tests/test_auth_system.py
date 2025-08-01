"""
测试认证和授权系统

验证JWT token生成验证、密码加密、用户注册登录等功能。
"""

import sys
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from workflow_platform.core.security import (
    SecurityManager, create_access_token, verify_token,
    hash_password, verify_password, generate_password_reset_token,
    verify_password_reset_token
)
from workflow_platform.core.exceptions import AuthenticationError, ValidationError
from workflow_platform.api.schemas i