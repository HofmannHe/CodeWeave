"""
安全相关工具

包含JWT token生成验证、密码加密等安全功能。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

from .config import settings
from .exceptions import AuthenticationError, ValidationError
from .logging import get_logger

logger = get_logger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expire_minutes = settings.jwt_expire_minutes
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            logger.info(f"创建访问令牌成功，用户: {data.get('sub')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"创建访问令牌失败: {e}")
            raise AuthenticationError("令牌创建失败")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌是否过期
            exp = payload.get("exp")
            if exp is None:
                raise AuthenticationError("令牌格式无效")
            
            if datetime.utcnow() > datetime.fromtimestamp(exp):
                raise AuthenticationError("令牌已过期")
            
            logger.debug(f"令牌验证成功，用户: {payload.get('sub')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"令牌验证失败: {e}")
            raise AuthenticationError("令牌无效")
        except Exception as e:
            logger.error(f"令牌验证异常: {e}")
            raise AuthenticationError("令牌验证失败")
    
    def get_user_id_from_token(self, token: str) -> UUID:
        """从令牌中获取用户ID"""
        payload = self.verify_token(token)
        user_id_str = payload.get("sub")
        
        if not user_id_str:
            raise AuthenticationError("令牌中缺少用户ID")
        
        try:
            return UUID(user_id_str)
        except ValueError:
            raise AuthenticationError("令牌中用户ID格式无效")
    
    def hash_password(self, password: str) -> str:
        """加密密码"""
        if not password:
            raise ValidationError("密码不能为空")
        
        if len(password) < 6:
            raise ValidationError("密码长度不能少于6位")
        
        try:
            hashed = pwd_context.hash(password)
            logger.debug("密码加密成功")
            return hashed
        except Exception as e:
            logger.error(f"密码加密失败: {e}")
            raise ValidationError("密码加密失败")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        if not plain_password or not hashed_password:
            return False
        
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"密码验证结果: {result}")
            return result
        except Exception as e:
            logger.error(f"密码验证异常: {e}")
            return False
    
    def generate_password_reset_token(self, user_id: UUID) -> str:
        """生成密码重置令牌"""
        data = {
            "sub": str(user_id),
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)  # 1小时有效期
        }
        
        try:
            token = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
            logger.info(f"生成密码重置令牌成功，用户: {user_id}")
            return token
        except Exception as e:
            logger.error(f"生成密码重置令牌失败: {e}")
            raise AuthenticationError("密码重置令牌生成失败")
    
    def verify_password_reset_token(self, token: str) -> UUID:
        """验证密码重置令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("type") != "password_reset":
                raise AuthenticationError("令牌类型无效")
            
            # 检查是否过期
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise AuthenticationError("密码重置令牌已过期")
            
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise AuthenticationError("令牌中缺少用户ID")
            
            user_id = UUID(user_id_str)
            logger.info(f"密码重置令牌验证成功，用户: {user_id}")
            return user_id
            
        except JWTError as e:
            logger.warning(f"密码重置令牌验证失败: {e}")
            raise AuthenticationError("密码重置令牌无效")
        except ValueError:
            raise AuthenticationError("令牌中用户ID格式无效")
        except Exception as e:
            logger.error(f"密码重置令牌验证异常: {e}")
            raise AuthenticationError("密码重置令牌验证失败")


# 全局安全管理器实例
security_manager = SecurityManager()


# 便捷函数
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    return security_manager.create_access_token(data, expires_delta)


def verify_token(token: str) -> Dict[str, Any]:
    """验证令牌"""
    return security_manager.verify_token(token)


def get_user_id_from_token(token: str) -> UUID:
    """从令牌中获取用户ID"""
    return security_manager.get_user_id_from_token(token)


def hash_password(password: str) -> str:
    """加密密码"""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return security_manager.verify_password(plain_password, hashed_password)


def generate_password_reset_token(user_id: UUID) -> str:
    """生成密码重置令牌"""
    return security_manager.generate_password_reset_token(user_id)


def verify_password_reset_token(token: str) -> UUID:
    """验证密码重置令牌"""
    return security_manager.verify_password_reset_token(token)