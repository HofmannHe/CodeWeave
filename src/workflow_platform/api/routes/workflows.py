"""
工作流管理API路由

包含工作流的CRUD操作、版本管理、标签管理等功能。
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
import yaml

from ...core.exceptions import ValidationError, DatabaseError
from ...core.logging import get_logger
from ...database.factory import get_workflow_adapter
from ...database.schemas import (
    WorkflowDefinition, WorkflowDefinitionCreate, WorkflowDefinitionUpdate,
    WorkflowStatus, UserProfile
)
from ..schemas import (
    WorkflowDefinitionCreateRequest, WorkflowDefinitionUpdateRequest,
    WorkflowDefinitionResponse, WorkflowListParams, PaginatedResponse,
    MessageResponse, ErrorResponse
)
from ..dependencies import get_current_user, verify_workflow_ownership

logger = get_logger(__name__)
router = APIRouter(prefix="/workflows