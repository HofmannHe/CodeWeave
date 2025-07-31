"""
pytest配置文件

包含测试夹具和配置。
"""

import pytest
from typing import Generator
from unittest.mock import Mock

from workflow_platform.core.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """测试用的设置配置"""
    return Settings(
        debug=True,
        database_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/1",
        jwt_secret_key="test-secret-key",
        log_level="DEBUG",
    )


@pytest.fixture
def mock_temporal_client() -> Mock:
    """模拟Temporal客户端"""
    return Mock()


@pytest.fixture
def mock_ai_client() -> Mock:
    """模拟AI服务客户端"""
    return Mock()


@pytest.fixture
def sample_workflow_yaml() -> str:
    """示例工作流YAML"""
    return """
name: test-workflow
description: 测试工作流

steps:
  - id: step1
    type: ai-call
    description: AI分析步骤
    config:
      provider: openai
      model: gpt-4
      prompt: "分析以下内容: {{ input.content }}"
      
  - id: step2
    type: http-request
    description: HTTP请求步骤
    config:
      method: POST
      url: "https://api.example.com/webhook"
      body:
        result: "{{ steps.step1.output }}"
"""