# CodeWeave AI工作流平台

一个基于AI的智能工作流编排和执行平台，支持复杂的工作流设计、可视化编辑和自动化执行。

## 🚀 核心特性

- 🎨 **可视化工作流设计器** - 基于React Flow的拖拽式工作流编辑器
- 🤖 **多AI模型支持** - 集成OpenAI、Claude、本地模型等
- 🔄 **复杂工作流支持** - 条件分支、循环迭代、并行执行
- ⚡ **实时执行监控** - 基于Temporal的可靠工作流执行引擎
- 📊 **执行历史追踪** - 完整的工作流执行记录和分析
- 🔌 **灵活的集成** - RESTful API和Webhook支持
- 🚀 **快速部署** - 支持Supabase和自建数据库双方案

## 🏗️ 技术架构

### 后端技术栈
- **Python 3.11+** - 主要开发语言
- **FastAPI** - 高性能Web框架
- **Temporal** - 工作流编排引擎
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和会话存储
- **SQLAlchemy** - ORM框架

### 前端技术栈
- **React 18** - 用户界面框架
- **TypeScript** - 类型安全的JavaScript
- **React Flow** - 工作流可视化组件
- **Ant Design** - UI组件库
- **Zustand** - 状态管理

### 部署选项
- **Supabase方案** - 快速部署，适合MVP和小型项目
- **自建方案** - 完全控制，适合企业级部署

## 🛠️ 开发环境设置

### 环境要求
- Python 3.11+
- Poetry (Python依赖管理)
- Docker & Docker Compose
- Node.js 18+ (前端开发)

### 1. 克隆项目

```bash
git clone <repository-url>
cd CodeWeave
```

### 2. 安装Python依赖

```bash
# 安装Poetry (如果未安装)
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入必要的配置
vim .env
```

### 4. 启动开发服务

```bash
# 启动基础服务 (PostgreSQL, Redis, Temporal)
docker-compose up -d

# 运行数据库迁移
alembic upgrade head

# 启动API服务
uvicorn src.workflow_platform.api.main:app --reload --port 8000

# 启动工作流Worker (新终端)
python -m src.workflow_platform.workers.main
```

### 5. 验证安装

```bash
# 运行测试
pytest

# 检查代码质量
black --check src/
isort --check-only src/
mypy src/
flake8 src/

# 访问API文档
open http://localhost:8000/docs
```

## 📁 项目结构

```
CodeWeave/
├── src/workflow_platform/          # 后端源码
│   ├── api/                       # API路由和控制器
│   ├── core/                      # 核心业务逻辑
│   ├── workers/                   # Temporal工作流和活动
│   ├── database/                  # 数据库模型和迁移
│   ├── integrations/              # 外部服务集成
│   └── utils/                     # 工具函数
├── frontend/                      # 前端源码 (待创建)
├── tests/                         # 测试文件
├── docs/                          # 文档 (待创建)
├── deployment/                    # 部署配置 (待创建)
├── pyproject.toml                 # Python项目配置
├── docker-compose.yml             # 开发环境配置 (待创建)
└── README.md                      # 项目说明
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_project_structure.py

# 运行测试并生成覆盖率报告
pytest --cov=src/workflow_platform --cov-report=html

# 运行特定类型的测试
pytest -m unit          # 单元测试
pytest -m integration   # 集成测试
pytest -m e2e           # 端到端测试
```

### 测试覆盖率目标
- 单元测试覆盖率: >90%
- 集成测试覆盖率: >85%
- 端到端测试覆盖率: >80%

## 🔧 代码质量

### 代码格式化

```bash
# 格式化代码
black src/ tests/
isort src/ tests/

# 检查格式
black --check src/ tests/
isort --check-only src/ tests/
```

### 类型检查

```bash
# 运行类型检查
mypy src/
```

### 代码检查

```bash
# 运行flake8检查
flake8 src/ tests/
```

### Pre-commit Hooks

```bash
# 安装pre-commit hooks
pre-commit install

# 手动运行所有hooks
pre-commit run --all-files
```

## 📚 API文档

启动开发服务器后，可以访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🚀 部署

### 开发环境部署

参考上面的"开发环境设置"部分。

### 生产环境部署

详细的部署指南请参考：[../QUICK_DEPLOY.md](../QUICK_DEPLOY.md)

支持两种部署方案：
1. **Supabase方案** - 快速部署，适合MVP
2. **自建方案** - 完全控制，适合企业级部署

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范

- 遵循PEP 8代码风格
- 使用类型注解
- 编写单元测试
- 更新文档
- 提交信息遵循 [Conventional Commits](https://conventionalcommits.org/)

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Temporal](https://temporal.io/) - 可靠的工作流引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python API框架
- [React Flow](https://reactflow.dev/) - 强大的流程图组件
- [Ant Design](https://ant.design/) - 企业级UI设计语言

## 📞 联系我们

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 邮箱: team@codeweave.ai

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！