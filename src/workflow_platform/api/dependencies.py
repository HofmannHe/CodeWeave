"""
API依赖项

包含认证、权限验证等依赖项。
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..core.exceptions import AuthenticationError, DatabaseError
from ..core.security import get_user_id_from_token
from ..core.logging import get_logger
from ..database.factory import get_user_adapter
from ..database.schemas import UserProfile

logger = get_logger(__name__)

# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UUID:
    """获取当前用户ID"""
    if not credentials:
        logger.warning("请求缺少认证令牌")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = get_user_id_from_token(credentials.credentials)
        logger.debug(f"从令牌中获取用户ID: {user_id}")
        return user_id
    except AuthenticationError as e:
        logger.warning(f"令牌验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id)
) -> UserProfile:
    """获取当前用户信息"""
    try:
        user_adapter = await get_user_adapter()
        user = await user_adapter.get_by_id(UserProfile, user_id)
        
        if not user:
            logger.warning(f"用户不存在: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
            )
        
        logger.debug(f"获取当前用户信息: {user.username}")
        return user
        
    except DatabaseError as e:
        logger.error(f"获取用户信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败",
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserProfile]:
    """获取可选的当前用户信息（用于可选认证的端点）"""
    if not credentials:
        return None
    
    try:
        user_id = get_user_id_from_token(credentials.credentials)
        user_adapter = await get_user_adapter()
        user = await user_adapter.get_by_id(UserProfile, user_id)
        
        if user:
            logger.debug(f"获取可选用户信息: {user.username}")
        
        return user
        
    except (AuthenticationError, DatabaseError) as e:
        logger.debug(f"可选用户认证失败: {e}")
        return None


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, required_permissions: list = None):
        self.required_permissions = required_permissions or []
    
    async def __call__(self, current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
        """检查用户权限"""
        # 这里可以实现具体的权限检查逻辑
        # 目前简单返回用户信息
        
        if self.required_permissions:
            user_permissions = current_user.preferences.get('permissions', [])
            
            for permission in self.required_permissions:
                if permission not in user_permissions:
                    logger.warning(f"用户 {current_user.username} 缺少权限: {permission}")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少权限: {permission}",
                    )
        
        return current_user


# 预定义的权限检查器
def require_permissions(*permissions: str):
    """要求特定权限的装饰器工厂"""
    return PermissionChecker(list(permissions))


# 常用权限检查器
require_admin = require_permissions("admin")
require_workflow_create = require_permissions("workflow:create")
require_workflow_edit = require_permissions("workflow:edit")
require_workflow_delete = require_permissions("workflow:delete")
require_workflow_execute = require_permissions("workflow:execute")


class ResourceOwnerChecker:
    """资源所有者检查器"""
    
    def __init__(self, resource_type: str):
        self.resource_type = resource_type
    
    async def check_ownership(
        self, 
        resource_id: UUID, 
        current_user: UserProfile
    ) -> bool:
        """检查用户是否拥有资源"""
        try:
            if self.resource_type == "workflow":
                workflow_adapter = await get_workflow_adapter()
                workflow = await workflow_adapter.get_by_id(WorkflowDefinition, resource_id)
                return workflow and workflow.created_by == current_user.id
            
            elif self.resource_type == "execution":
                execution_adapter = await get_execution_adapter()
                execution = await execution_adapter.get_by_id(WorkflowExecution, resource_id)
                return execution and execution.created_by == current_user.id
            
            else:
                logger.warning(f"未知的资源类型: {self.resource_type}")
                return False
                
        except DatabaseError as e:
            logger.error(f"检查资源所有权失败: {e}")
            return False


# 资源所有者检查器实例
workflow_owner_checker = ResourceOwnerChecker("workflow")
execution_owner_checker = ResourceOwnerChecker("execution")


async def verify_workflow_ownership(
    workflow_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfile:
    """验证工作流所有权"""
    is_owner = await workflow_owner_checker.check_ownership(workflow_id, current_user)
    
    if not is_owner:
        logger.warning(f"用户 {current_user.username} 尝试访问不属于自己的工作流: {workflow_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此工作流",
        )
    
    return current_user


async def verify_execution_ownership(
    execution_id: UUID,
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfile:
    """验证执行记录所有权"""
    is_owner = await execution_owner_checker.check_ownership(execution_id, current_user)
    
    if not is_owner:
        logger.warning(f"用户 {current_user.username} 尝试访问不属于自己的执行记录: {execution_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此执行记录",
        )
    
    return current_user


# 导入必要的模块（避免循环导入）
from ..database.factory import get_workflow_adapter, get_execution_adapter
from ..database.schemas import WorkflowDefinition, WorkflowExecution