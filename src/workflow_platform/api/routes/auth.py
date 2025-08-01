"""
认证相关API路由

包含用户注册、登录、密码管理等功能。
"""

from datetime import timedelta
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from ...core.exceptions import (
    AuthenticationError, ValidationError, DatabaseError
)
from ...core.security import (
    create_access_token, hash_password, verify_password,
    generate_password_reset_token, verify_password_reset_token
)
from ...core.config import settings
from ...core.logging import get_logger
from ...database.factory import get_user_adapter
from ...database.schemas import (
    UserProfile, UserProfileCreate, UserProfileUpdate
)
from ..schemas import (
    UserRegisterRequest, UserLoginRequest, UserLoginResponse,
    UserProfileResponse, UserProfileUpdateRequest,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirmRequest,
    MessageResponse, ErrorResponse
)
from ..dependencies import get_current_user, get_current_user_id

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户"
)
async def register_user(request: UserRegisterRequest) -> UserProfileResponse:
    """用户注册"""
    try:
        user_adapter = await get_user_adapter()
        
        # 检查用户名是否已存在
        existing_user = await user_adapter.get_by_username(request.username)
        if existing_user:
            logger.warning(f"用户名已存在: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        existing_email = await user_adapter.get_by_email(request.email)
        if existing_email:
            logger.warning(f"邮箱已存在: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        
        # 加密密码
        hashed_password = hash_password(request.password)
        
        # 创建用户
        user_data = UserProfileCreate(
            username=request.username,
            display_name=request.display_name,
            timezone=request.timezone,
            preferences={
                'email': request.email,
                'password_hash': hashed_password
            }
        )
        
        user = await user_adapter.create(user_data)
        
        logger.info(f"用户注册成功: {user.username}")
        
        # 返回用户信息（不包含密码）
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            email=request.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            timezone=user.timezone,
            preferences={k: v for k, v in user.preferences.items() if k != 'password_hash'},
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except ValidationError as e:
        logger.warning(f"用户注册验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"用户注册数据库错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post(
    "/login",
    response_model=UserLoginResponse,
    summary="用户登录",
    description="用户登录获取访问令牌"
)
async def login_user(request: UserLoginRequest) -> UserLoginResponse:
    """用户登录"""
    try:
        user_adapter = await get_user_adapter()
        
        # 尝试通过用户名或邮箱查找用户
        user = await user_adapter.get_by_username(request.username)
        if not user:
            user = await user_adapter.get_by_email(request.username)
        
        if not user:
            logger.warning(f"登录失败，用户不存在: {request.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 验证密码
        stored_password = user.preferences.get('password_hash')
        if not stored_password or not verify_password(request.password, stored_password):
            logger.warning(f"登录失败，密码错误: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 创建访问令牌
        access_token_expires = timedelta(minutes=settings.jwt_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        
        logger.info(f"用户登录成功: {user.username}")
        
        # 返回登录响应
        return UserLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
            user=UserProfileResponse(
                id=user.id,
                username=user.username,
                email=user.preferences.get('email'),
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                timezone=user.timezone,
                preferences={k: v for k, v in user.preferences.items() if k != 'password_hash'},
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
        
    except DatabaseError as e:
        logger.error(f"用户登录数据库错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息"
)
async def get_current_user_info(
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfileResponse:
    """获取当前用户信息"""
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.preferences.get('email'),
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        timezone=current_user.timezone,
        preferences={k: v for k, v in current_user.preferences.items() if k != 'password_hash'},
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.put(
    "/me",
    response_model=UserProfileResponse,
    summary="更新当前用户信息",
    description="更新当前登录用户的个人信息"
)
async def update_current_user_info(
    request: UserProfileUpdateRequest,
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfileResponse:
    """更新当前用户信息"""
    try:
        user_adapter = await get_user_adapter()
        
        # 准备更新数据
        update_data = UserProfileUpdate()
        if request.display_name is not None:
            update_data.display_name = request.display_name
        if request.avatar_url is not None:
            update_data.avatar_url = request.avatar_url
        if request.timezone is not None:
            update_data.timezone = request.timezone
        if request.preferences is not None:
            # 合并偏好设置，保留密码哈希
            new_preferences = current_user.preferences.copy()
            new_preferences.update(request.preferences)
            update_data.preferences = new_preferences
        
        # 更新用户信息
        updated_user = await user_adapter.update(
            UserProfile(
                id=current_user.id,
                username=current_user.username,
                display_name=update_data.display_name or current_user.display_name,
                avatar_url=update_data.avatar_url or current_user.avatar_url,
                timezone=update_data.timezone or current_user.timezone,
                preferences=update_data.preferences or current_user.preferences,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at
            )
        )
        
        logger.info(f"用户信息更新成功: {current_user.username}")
        
        return UserProfileResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.preferences.get('email'),
            display_name=updated_user.display_name,
            avatar_url=updated_user.avatar_url,
            timezone=updated_user.timezone,
            preferences={k: v for k, v in updated_user.preferences.items() if k != 'password_hash'},
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
    except ValidationError as e:
        logger.warning(f"用户信息更新验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"用户信息更新数据库错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败，请稍后重试"
        )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="修改密码",
    description="修改当前用户的密码"
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: UserProfile = Depends(get_current_user)
) -> MessageResponse:
    """修改密码"""
    try:
        user_adapter = await get_user_adapter()
        
        # 验证当前密码
        stored_password = current_user.preferences.get('password_hash')
        if not stored_password or not verify_password(request.current_password, stored_password):
            logger.warning(f"修改密码失败，当前密码错误: {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="当前密码错误"
            )
        
        # 加密新密码
        new_password_hash = hash_password(request.new_password)
        
        # 更新密码
        new_preferences = current_user.preferences.copy()
        new_preferences['password_hash'] = new_password_hash
        
        await user_adapter.update(
            UserProfile(
                id=current_user.id,
                username=current_user.username,
                display_name=current_user.display_name,
                avatar_url=current_user.avatar_url,
                timezone=current_user.timezone,
                preferences=new_preferences,
                created_at=current_user.created_at,
                updated_at=current_user.updated_at
            )
        )
        
        logger.info(f"密码修改成功: {current_user.username}")
        
        return MessageResponse(message="密码修改成功")
        
    except ValidationError as e:
        logger.warning(f"密码修改验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"密码修改数据库错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败，请稍后重试"
        )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="请求密码重置",
    description="发送密码重置邮件"
)
async def request_password_reset(request: PasswordResetRequest) -> MessageResponse:
    """请求密码重置"""
    try:
        user_adapter = await get_user_adapter()
        
        # 查找用户
        user = await user_adapter.get_by_email(request.email)
        if not user:
            # 为了安全，即使用户不存在也返回成功消息
            logger.info(f"密码重置请求，用户不存在: {request.email}")
            return MessageResponse(message="如果邮箱存在，重置链接已发送")
        
        # 生成重置令牌
        reset_token = generate_password_reset_token(user.id)
        
        # TODO: 发送重置邮件
        # 这里应该集成邮件服务发送重置链接
        logger.info(f"密码重置令牌生成成功: {user.username}, token: {reset_token}")
        
        return MessageResponse(message="如果邮箱存在，重置链接已发送")
        
    except DatabaseError as e:
        logger.error(f"密码重置请求数据库错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="请求失败，请稍后重试"
        )


@router.post(
    "/reset-password/confirm",
    response_model=MessageResponse,
    summary="确认密码重置",
    description="使用重置令牌设置新密码"
)
async def confirm_password_reset(request: PasswordResetConfirmRequest) -> MessageResponse:
    """确认密码重置"""
    try:
        # 验证重置令牌
        user_id = verify_password_reset_token(request.token)
        
        user_adapter = await get_user_adapter()
        user = await user_adapter.get_by_id(UserProfile, user_id)
        
        if not user:
            logger.warning(f"密码重置确认失败，用户不存在: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置令牌无效"
            )
        
        # 加密新密码
        new_password_hash = hash_password(request.new_password)
        
        # 更新密码
        new_preferences = user.preferences.copy()
        new_preferences['password_hash'] = new_password_hash
        
        await user_adapter.update(
            UserProfile(
                id=user.id,
                username=user.username,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                timezone=user.timezone,
                preferences=new_preferences,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
        
        logger.info(f"密码重置成功: {user.username}")
        
        return MessageResponse(message="密码重置成功")
        
    except AuthenticationError as e:
        logger.warning(f"密码重置确认失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        logger.warning(f"密码重置验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DatabaseError as e:
        logger.error(f"密码重置数据库错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码重置失败，请稍后重试"
        )