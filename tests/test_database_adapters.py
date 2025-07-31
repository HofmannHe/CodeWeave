"""
测试数据库适配器

验证数据库适配器的功能和工厂模式。
"""

import sys
import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from workflow_platform.core.config import DeploymentMode
from workflow_platform.core.exceptions import DatabaseError, ConfigurationError
from workflow_platform.database.factory import DatabaseAdapterFactory
from workflow_platform.database.schemas import (
    UserProfileCreate, WorkflowDefinitionCreate, WorkflowExecutionCreate
)


class TestDatabaseAdapterFactory:
    """测试数据库适配器工厂"""
    
    def test_factory_initialization_supabase(self):
        """测试Supabase方案工厂初始化"""
        config = {
            'deployment_mode': DeploymentMode.SUPABASE,
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test-key'
        }
        
        factory = DatabaseAdapterFactory(config)
        assert factory.config == config
    
    def test_factory_initialization_self_hosted(self):
        """测试自建方案工厂初始化"""
        config = {
            'deployment_mode': DeploymentMode.SELF_HOSTED,
            'database_url': 'postgresql://user:pass@localhost/db'
        }
        
        factory = DatabaseAdapterFactory(config)
        assert factory.config == config
    
    @pytest.mark.asyncio
    async def test_factory_validation_supabase_missing_config(self):
        """测试Supabase方案缺少配置的验证"""
        config = {
            'deployment_mode': DeploymentMode.SUPABASE,
            # 缺少supabase_url和supabase_key
        }
        
        factory = DatabaseAdapterFactory(config)
        
        with pytest.raises(ConfigurationError):
            await factory.initialize()
    
    @pytest.mark.asyncio
    async def test_factory_validation_self_hosted_missing_config(self):
        """测试自建方案缺少配置的验证"""
        config = {
            'deployment_mode': DeploymentMode.SELF_HOSTED,
            # 缺少database_url
        }
        
        factory = DatabaseAdapterFactory(config)
        
        with pytest.raises(ConfigurationError):
            await factory.initialize()
    
    @pytest.mark.asyncio
    async def test_factory_validation_invalid_deployment_mode(self):
        """测试无效部署模式的验证"""
        config = {
            'deployment_mode': 'invalid_mode',
        }
        
        factory = DatabaseAdapterFactory(config)
        
        with pytest.raises(ConfigurationError):
            await factory.initialize()
    
    def test_get_user_adapter_supabase(self):
        """测试获取Supabase用户适配器"""
        config = {
            'deployment_mode': DeploymentMode.SUPABASE,
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test-key'
        }
        
        factory = DatabaseAdapterFactory(config)
        adapter = factory.get_user_adapter()
        
        # 检查适配器类型
        from workflow_platform.database.supabase_adapter import SupabaseUserAdapter
        assert isinstance(adapter, SupabaseUserAdapter)
    
    def test_get_user_adapter_postgresql(self):
        """测试获取PostgreSQL用户适配器"""
        config = {
            'deployment_mode': DeploymentMode.SELF_HOSTED,
            'database_url': 'postgresql://user:pass@localhost/db'
        }
        
        factory = DatabaseAdapterFactory(config)
        adapter = factory.get_user_adapter()
        
        # 检查适配器类型
        from workflow_platform.database.postgresql_adapter import PostgreSQLUserAdapter
        assert isinstance(adapter, PostgreSQLUserAdapter)
    
    def test_get_workflow_adapter_supabase(self):
        """测试获取Supabase工作流适配器"""
        config = {
            'deployment_mode': DeploymentMode.SUPABASE,
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test-key'
        }
        
        factory = DatabaseAdapterFactory(config)
        adapter = factory.get_workflow_adapter()
        
        # 检查适配器类型
        from workflow_platform.database.supabase_adapter import SupabaseWorkflowAdapter
        assert isinstance(adapter, SupabaseWorkflowAdapter)
    
    def test_get_workflow_adapter_postgresql(self):
        """测试获取PostgreSQL工作流适配器"""
        config = {
            'deployment_mode': DeploymentMode.SELF_HOSTED,
            'database_url': 'postgresql://user:pass@localhost/db'
        }
        
        factory = DatabaseAdapterFactory(config)
        adapter = factory.get_workflow_adapter()
        
        # 检查适配器类型
        from workflow_platform.database.postgresql_adapter import PostgreSQLWorkflowAdapter
        assert isinstance(adapter, PostgreSQLWorkflowAdapter)
    
    def test_adapter_caching(self):
        """测试适配器缓存"""
        config = {
            'deployment_mode': DeploymentMode.SUPABASE,
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test-key'
        }
        
        factory = DatabaseAdapterFactory(config)
        
        # 第一次获取
        adapter1 = factory.get_user_adapter()
        # 第二次获取应该返回同一个实例
        adapter2 = factory.get_user_adapter()
        
        assert adapter1 is adapter2
    
    def test_clear_cache(self):
        """测试清除适配器缓存"""
        config = {
            'deployment_mode': DeploymentMode.SUPABASE,
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test-key'
        }
        
        factory = DatabaseAdapterFactory(config)
        
        # 获取适配器
        adapter1 = factory.get_user_adapter()
        
        # 清除缓存
        factory.clear_cache()
        
        # 再次获取应该是新实例
        adapter2 = factory.get_user_adapter()
        
        assert adapter1 is not adapter2


class TestAdapterAbstractMethods:
    """测试适配器抽象方法"""
    
    def test_database_adapter_abstract_methods(self):
        """测试数据库适配器抽象方法"""
        from workflow_platform.database.adapters import DatabaseAdapter
        
        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            DatabaseAdapter({})
    
    def test_user_adapter_abstract_methods(self):
        """测试用户适配器抽象方法"""
        from workflow_platform.database.adapters import UserAdapter
        
        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            UserAdapter({})
    
    def test_workflow_adapter_abstract_methods(self):
        """测试工作流适配器抽象方法"""
        from workflow_platform.database.adapters import WorkflowAdapter
        
        # 不能直接实例化抽象类
        with pytest.raises(TypeError):
            WorkflowAdapter({})


class TestSupabaseAdapterMethods:
    """测试Supabase适配器方法"""
    
    @pytest.fixture
    def supabase_config(self):
        """Supabase配置夹具"""
        return {
            'deployment_mode': DeploymentMode.SUPABASE,
            'supabase_url': 'https://test.supabase.co',
            'supabase_key': 'test-key'
        }
    
    @pytest.fixture
    def mock_supabase_client(self):
        """模拟Supabase客户端"""
        with patch('workflow_platform.database.supabase_adapter.create_client') as mock_create:
            mock_client = Mock()
            mock_create.return_value = mock_client
            yield mock_client
    
    @pytest.mark.asyncio
    async def test_supabase_user_adapter_connect(self, supabase_config, mock_supabase_client):
        """测试Supabase用户适配器连接"""
        from workflow_platform.database.supabase_adapter import SupabaseUserAdapter
        
        # 设置模拟响应
        mock_table = Mock()
        mock_table.select.return_value.limit.return_value.execute.return_value.data = []
        mock_supabase_client.table.return_value = mock_table
        
        adapter = SupabaseUserAdapter(supabase_config)
        await adapter.connect()
        
        assert adapter.client is not None
    
    @pytest.mark.asyncio
    async def test_supabase_user_adapter_create(self, supabase_config, mock_supabase_client):
        """测试Supabase用户适配器创建用户"""
        from workflow_platform.database.supabase_adapter import SupabaseUserAdapter
        
        # 设置模拟响应
        mock_table = Mock()
        mock_table.select.return_value.limit.return_value.execute.return_value.data = []
        mock_table.insert.return_value.execute.return_value.data = [
            {
                'id': str(uuid4()),
                'username': 'testuser',
                'display_name': '测试用户',
                'timezone': 'UTC',
                'preferences': {},
                'created_at': '2025-01-08T00:00:00Z',
                'updated_at': '2025-01-08T00:00:00Z'
            }
        ]
        mock_supabase_client.table.return_value = mock_table
        
        adapter = SupabaseUserAdapter(supabase_config)
        await adapter.connect()
        
        user_data = UserProfileCreate(username='testuser')
        result = await adapter.create(user_data)
        
        assert result.username == 'testuser'
    
    @pytest.mark.asyncio
    async def test_supabase_user_adapter_get_by_id(self, supabase_config, mock_supabase_client):
        """测试Supabase用户适配器根据ID获取用户"""
        from workflow_platform.database.supabase_adapter import SupabaseUserAdapter
        
        user_id = uuid4()
        
        # 设置模拟响应
        mock_table = Mock()
        mock_table.select.return_value.limit.return_value.execute.return_value.data = []
        mock_table.select.return_value.eq.return_value.execute.return_value.data = [
            {
                'id': str(user_id),
                'username': 'testuser',
                'display_name': '测试用户',
                'timezone': 'UTC',
                'preferences': {},
                'created_at': '2025-01-08T00:00:00Z',
                'updated_at': '2025-01-08T00:00:00Z'
            }
        ]
        mock_supabase_client.table.return_value = mock_table
        
        adapter = SupabaseUserAdapter(supabase_config)
        await adapter.connect()
        
        from workflow_platform.database.schemas import UserProfile
        result = await adapter.get_by_id(UserProfile, user_id)
        
        assert result is not None
        assert result.username == 'testuser'


class TestPostgreSQLAdapterMethods:
    """测试PostgreSQL适配器方法"""
    
    @pytest.fixture
    def postgresql_config(self):
        """PostgreSQL配置夹具"""
        return {
            'deployment_mode': DeploymentMode.SELF_HOSTED,
            'database_url': 'postgresql://user:pass@localhost/test_db'
        }
    
    @pytest.mark.asyncio
    async def test_postgresql_user_adapter_initialization(self, postgresql_config):
        """测试PostgreSQL用户适配器初始化"""
        from workflow_platform.database.postgresql_adapter import PostgreSQLUserAdapter
        
        adapter = PostgreSQLUserAdapter(postgresql_config)
        
        assert adapter.connection_config == postgresql_config
        assert adapter._model_class is not None
        assert adapter._schema_class is not None
    
    @pytest.mark.asyncio
    async def test_postgresql_workflow_adapter_initialization(self, postgresql_config):
        """测试PostgreSQL工作流适配器初始化"""
        from workflow_platform.database.postgresql_adapter import PostgreSQLWorkflowAdapter
        
        adapter = PostgreSQLWorkflowAdapter(postgresql_config)
        
        assert adapter.connection_config == postgresql_config
        assert adapter._model_class is not None
        assert adapter._schema_class is not None


class TestAdapterErrorHandling:
    """测试适配器错误处理"""
    
    @pytest.mark.asyncio
    async def test_supabase_adapter_connection_error(self):
        """测试Supabase适配器连接错误"""
        from workflow_platform.database.supabase_adapter import SupabaseUserAdapter
        
        # 无效配置
        config = {
            'deployment_mode': DeploymentMode.SUPABASE,
            # 缺少必需配置
        }
        
        adapter = SupabaseUserAdapter(config)
        
        with pytest.raises(DatabaseError):
            await adapter.connect()
    
    @pytest.mark.asyncio
    async def test_postgresql_adapter_connection_error(self):
        """测试PostgreSQL适配器连接错误"""
        from workflow_platform.database.postgresql_adapter import PostgreSQLUserAdapter
        
        # 无效数据库URL
        config = {
            'deployment_mode': DeploymentMode.SELF_HOSTED,
            'database_url': 'invalid://url'
        }
        
        adapter = PostgreSQLUserAdapter(config)
        
        with pytest.raises(DatabaseError):
            await adapter.connect()


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    @pytest.mark.asyncio
    async def test_get_user_adapter_function(self):
        """测试获取用户适配器便捷函数"""
        from workflow_platform.database.factory import get_user_adapter, set_database_factory
        
        # 创建模拟工厂
        mock_factory = Mock()
        mock_factory.initialize = AsyncMock()
        mock_adapter = Mock()
        mock_factory.get_user_adapter.return_value = mock_adapter
        
        # 设置模拟工厂
        set_database_factory(mock_factory)
        
        # 调用便捷函数
        result = await get_user_adapter()
        
        # 验证调用
        mock_factory.initialize.assert_called_once()
        mock_factory.get_user_adapter.assert_called_once()
        assert result == mock_adapter
    
    @pytest.mark.asyncio
    async def test_get_workflow_adapter_function(self):
        """测试获取工作流适配器便捷函数"""
        from workflow_platform.database.factory import get_workflow_adapter, set_database_factory
        
        # 创建模拟工厂
        mock_factory = Mock()
        mock_factory.initialize = AsyncMock()
        mock_adapter = Mock()
        mock_factory.get_workflow_adapter.return_value = mock_adapter
        
        # 设置模拟工厂
        set_database_factory(mock_factory)
        
        # 调用便捷函数
        result = await get_workflow_adapter()
        
        # 验证调用
        mock_factory.initialize.assert_called_once()
        mock_factory.get_workflow_adapter.assert_called_once()
        assert result == mock_adapter