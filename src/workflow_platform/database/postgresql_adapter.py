"""
PostgreSQL数据库适配器实现

用于自建方案的PostgreSQL数据库适配器。
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID
from datetime import datetime

from sqlalchemy import create_engine, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..core.exceptions import DatabaseError, ValidationError
from ..core.logging import get_logger
from .adapters import (
    DatabaseAdapter, UserAdapter, WorkflowAdapter, 
    ExecutionAdapter, StepExecutionAdapter, ApprovalAdapter, LogAdapter
)
from .models import (
    Base, UserProfile, WorkflowDefinition, WorkflowExecution,
    StepExecution, ApprovalRequest, ExecutionLog
)
from .schemas import (
    UserProfile as UserProfileSchema,
    WorkflowDefinition as WorkflowDefinitionSchema,
    WorkflowExecution as WorkflowExecutionSchema,
    StepExecution as StepExecutionSchema,
    ApprovalRequest as ApprovalRequestSchema,
    ExecutionLog as ExecutionLogSchema,
)

logger = get_logger(__name__)
T = TypeVar('T')


class PostgreSQLAdapter(DatabaseAdapter[T]):
    """PostgreSQL数据库适配器基类"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self.engine = None
        self.SessionLocal = None
        self._model_class = None
        self._schema_class = None
    
    async def connect(self) -> None:
        """建立数据库连接"""
        try:
            database_url = self.connection_config.get('database_url')
            if not database_url:
                raise DatabaseError("数据库URL未配置")
            
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=self.connection_config.get('echo', False)
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # 创建表（如果不存在）
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("PostgreSQL数据库连接成功")
            
        except Exception as e:
            logger.error(f"PostgreSQL数据库连接失败: {e}")
            raise DatabaseError(f"数据库连接失败: {e}")
    
    async def disconnect(self) -> None:
        """关闭数据库连接"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("PostgreSQL数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        if not self.SessionLocal:
            raise DatabaseError("数据库未连接")
        return self.SessionLocal()
    
    def _model_to_schema(self, model_instance) -> T:
        """将模型实例转换为Schema"""
        if not self._schema_class:
            raise DatabaseError("Schema类未设置")
        return self._schema_class.from_orm(model_instance)
    
    def _schema_to_model(self, schema_instance: T):
        """将Schema转换为模型实例"""
        if not self._model_class:
            raise DatabaseError("模型类未设置")
        return self._model_class(**schema_instance.dict(exclude_unset=True))
    
    async def create(self, model: T) -> T:
        """创建记录"""
        session = self.get_session()
        try:
            db_model = self._schema_to_model(model)
            session.add(db_model)
            session.commit()
            session.refresh(db_model)
            return self._model_to_schema(db_model)
        except IntegrityError as e:
            session.rollback()
            logger.error(f"创建记录失败，违反唯一约束: {e}")
            raise ValidationError(f"记录已存在或违反唯一约束: {e}")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"创建记录失败: {e}")
            raise DatabaseError(f"创建记录失败: {e}")
        finally:
            session.close()
    
    async def get_by_id(self, model_class: Type[T], record_id: UUID) -> Optional[T]:
        """根据ID获取记录"""
        session = self.get_session()
        try:
            db_model = session.query(self._model_class).filter(
                self._model_class.id == record_id
            ).first()
            
            if db_model:
                return self._model_to_schema(db_model)
            return None
        except SQLAlchemyError as e:
            logger.error(f"根据ID获取记录失败: {e}")
            raise DatabaseError(f"获取记录失败: {e}")
        finally:
            session.close()
    
    async def get_by_field(
        self, 
        model_class: Type[T], 
        field_name: str, 
        field_value: Any
    ) -> Optional[T]:
        """根据字段值获取记录"""
        session = self.get_session()
        try:
            field = getattr(self._model_class, field_name)
            db_model = session.query(self._model_class).filter(
                field == field_value
            ).first()
            
            if db_model:
                return self._model_to_schema(db_model)
            return None
        except AttributeError:
            raise ValidationError(f"字段 {field_name} 不存在")
        except SQLAlchemyError as e:
            logger.error(f"根据字段获取记录失败: {e}")
            raise DatabaseError(f"获取记录失败: {e}")
        finally:
            session.close()
    
    async def list_records(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """列出记录"""
        session = self.get_session()
        try:
            query = session.query(self._model_class)
            
            # 应用过滤器
            if filters:
                for field_name, field_value in filters.items():
                    if hasattr(self._model_class, field_name):
                        field = getattr(self._model_class, field_name)
                        query = query.filter(field == field_value)
            
            # 应用排序
            if order_by:
                if order_by.startswith('-'):
                    field_name = order_by[1:]
                    if hasattr(self._model_class, field_name):
                        field = getattr(self._model_class, field_name)
                        query = query.order_by(desc(field))
                else:
                    if hasattr(self._model_class, order_by):
                        field = getattr(self._model_class, order_by)
                        query = query.order_by(asc(field))
            
            # 应用分页
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            db_models = query.all()
            return [self._model_to_schema(model) for model in db_models]
            
        except SQLAlchemyError as e:
            logger.error(f"列出记录失败: {e}")
            raise DatabaseError(f"列出记录失败: {e}")
        finally:
            session.close()
    
    async def update(self, model: T) -> T:
        """更新记录"""
        session = self.get_session()
        try:
            model_dict = model.dict(exclude_unset=True)
            record_id = model_dict.get('id')
            
            if not record_id:
                raise ValidationError("更新记录必须提供ID")
            
            db_model = session.query(self._model_class).filter(
                self._model_class.id == record_id
            ).first()
            
            if not db_model:
                raise ValidationError(f"记录不存在: {record_id}")
            
            # 更新字段
            for field_name, field_value in model_dict.items():
                if hasattr(db_model, field_name) and field_name != 'id':
                    setattr(db_model, field_name, field_value)
            
            session.commit()
            session.refresh(db_model)
            return self._model_to_schema(db_model)
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"更新记录失败: {e}")
            raise DatabaseError(f"更新记录失败: {e}")
        finally:
            session.close()
    
    async def delete(self, model_class: Type[T], record_id: UUID) -> bool:
        """删除记录"""
        session = self.get_session()
        try:
            db_model = session.query(self._model_class).filter(
                self._model_class.id == record_id
            ).first()
            
            if not db_model:
                return False
            
            session.delete(db_model)
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"删除记录失败: {e}")
            raise DatabaseError(f"删除记录失败: {e}")
        finally:
            session.close()
    
    async def count(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计记录数量"""
        session = self.get_session()
        try:
            query = session.query(self._model_class)
            
            # 应用过滤器
            if filters:
                for field_name, field_value in filters.items():
                    if hasattr(self._model_class, field_name):
                        field = getattr(self._model_class, field_name)
                        query = query.filter(field == field_value)
            
            return query.count()
            
        except SQLAlchemyError as e:
            logger.error(f"统计记录数量失败: {e}")
            raise DatabaseError(f"统计记录数量失败: {e}")
        finally:
            session.close()
    
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """执行原始SQL查询"""
        session = self.get_session()
        try:
            result = session.execute(query, params or {})
            session.commit()
            return result.fetchall()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"执行原始查询失败: {e}")
            raise DatabaseError(f"执行查询失败: {e}")
        finally:
            session.close()
    
    async def begin_transaction(self) -> Session:
        """开始事务"""
        session = self.get_session()
        session.begin()
        return session
    
    async def commit_transaction(self, transaction: Session) -> None:
        """提交事务"""
        try:
            transaction.commit()
        except SQLAlchemyError as e:
            transaction.rollback()
            raise DatabaseError(f"提交事务失败: {e}")
        finally:
            transaction.close()
    
    async def rollback_transaction(self, transaction: Session) -> None:
        """回滚事务"""
        try:
            transaction.rollback()
        finally:
            transaction.close()


# 具体适配器实现
class PostgreSQLUserAdapter(PostgreSQLAdapter, UserAdapter):
    """PostgreSQL用户适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._model_class = UserProfile
        self._schema_class = UserProfileSchema
    
    async def get_by_username(self, username: str) -> Optional[UserProfileSchema]:
        """根据用户名获取用户"""
        return await self.get_by_field(UserProfileSchema, 'username', username)
    
    async def get_by_email(self, email: str) -> Optional[UserProfileSchema]:
        """根据邮箱获取用户"""
        # 注意：这里假设email存储在preferences中
        session = self.get_session()
        try:
            db_model = session.query(UserProfile).filter(
                UserProfile.preferences['email'].astext == email
            ).first()
            
            if db_model:
                return self._model_to_schema(db_model)
            return None
        except SQLAlchemyError as e:
            logger.error(f"根据邮箱获取用户失败: {e}")
            raise DatabaseError(f"获取用户失败: {e}")
        finally:
            session.close()
    
    async def verify_password(self, user_id: UUID, password: str) -> bool:
        """验证用户密码"""
        # 注意：这里需要实现密码验证逻辑
        # 实际实现中应该使用哈希密码比较
        session = self.get_session()
        try:
            user = session.query(UserProfile).filter(
                UserProfile.id == user_id
            ).first()
            
            if not user:
                return False
            
            # 这里应该实现实际的密码验证逻辑
            stored_password = user.preferences.get('password_hash')
            # 使用passlib或类似库进行密码验证
            return True  # 临时返回True
            
        except SQLAlchemyError as e:
            logger.error(f"验证密码失败: {e}")
            return False
        finally:
            session.close()
    
    async def update_password(self, user_id: UUID, new_password: str) -> bool:
        """更新用户密码"""
        # 注意：这里需要实现密码更新逻辑
        session = self.get_session()
        try:
            user = session.query(UserProfile).filter(
                UserProfile.id == user_id
            ).first()
            
            if not user:
                return False
            
            # 这里应该实现密码哈希和存储逻辑
            # user.preferences['password_hash'] = hash_password(new_password)
            session.commit()
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"更新密码失败: {e}")
            return False
        finally:
            session.close()


class PostgreSQLWorkflowAdapter(PostgreSQLAdapter, WorkflowAdapter):
    """PostgreSQL工作流适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._model_class = WorkflowDefinition
        self._schema_class = WorkflowDefinitionSchema
    
    async def get_by_name_and_version(self, name: str, version: int) -> Optional[WorkflowDefinitionSchema]:
        """根据名称和版本获取工作流"""
        session = self.get_session()
        try:
            db_model = session.query(WorkflowDefinition).filter(
                and_(
                    WorkflowDefinition.name == name,
                    WorkflowDefinition.version == version
                )
            ).first()
            
            if db_model:
                return self._model_to_schema(db_model)
            return None
        except SQLAlchemyError as e:
            logger.error(f"根据名称和版本获取工作流失败: {e}")
            raise DatabaseError(f"获取工作流失败: {e}")
        finally:
            session.close()
    
    async def get_latest_version(self, name: str) -> Optional[WorkflowDefinitionSchema]:
        """获取最新版本的工作流"""
        session = self.get_session()
        try:
            db_model = session.query(WorkflowDefinition).filter(
                WorkflowDefinition.name == name
            ).order_by(desc(WorkflowDefinition.version)).first()
            
            if db_model:
                return self._model_to_schema(db_model)
            return None
        except SQLAlchemyError as e:
            logger.error(f"获取最新版本工作流失败: {e}")
            raise DatabaseError(f"获取工作流失败: {e}")
        finally:
            session.close()
    
    async def list_by_user(self, user_id: UUID) -> List[WorkflowDefinitionSchema]:
        """获取用户的工作流列表"""
        return await self.list_records(
            WorkflowDefinitionSchema,
            filters={'created_by': user_id},
            order_by='-created_at'
        )
    
    async def list_by_tags(self, tags: List[str]) -> List[WorkflowDefinitionSchema]:
        """根据标签获取工作流列表"""
        session = self.get_session()
        try:
            db_models = session.query(WorkflowDefinition).filter(
                WorkflowDefinition.tags.overlap(tags)
            ).all()
            
            return [self._model_to_schema(model) for model in db_models]
        except SQLAlchemyError as e:
            logger.error(f"根据标签获取工作流失败: {e}")
            raise DatabaseError(f"获取工作流失败: {e}")
        finally:
            session.close()


class PostgreSQLExecutionAdapter(PostgreSQLAdapter, ExecutionAdapter):
    """PostgreSQL执行记录适配器"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        super().__init__(connection_config)
        self._model_class = WorkflowExecution
        self._schema_class = WorkflowExecutionSchema
    
    async def get_by_temporal_workflow_id(self, temporal_workflow_id: str) -> Optional[WorkflowExecutionSchema]:
        """根据Temporal工作流ID获取执行记录"""
        return await self.get_by_field(
            WorkflowExecutionSchema, 
            'temporal_workflow_id', 
            temporal_workflow_id
        )
    
    async def list_by_workflow(self, workflow_id: UUID) -> List[WorkflowExecutionSchema]:
        """获取工作流的执行记录列表"""
        return await self.list_records(
            WorkflowExecutionSchema,
            filters={'workflow_id': workflow_id},
            order_by='-created_at'
        )
    
    async def list_by_user(self, user_id: UUID) -> List[WorkflowExecutionSchema]:
        """获取用户的执行记录列表"""
        return await self.list_records(
            WorkflowExecutionSchema,
            filters={'created_by': user_id},
            order_by='-created_at'
        )
    
    async def list_by_status(self, status: str) -> List[WorkflowExecutionSchema]:
        """根据状态获取执行记录列表"""
        return await self.list_records(
            WorkflowExecutionSchema,
            filters={'status': status},
            order_by='-created_at'
        )