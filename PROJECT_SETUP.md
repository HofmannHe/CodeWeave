# CodeWeave 项目初始化指南

这是 CodeWeave AI工作流平台的实际代码项目。

## 项目结构

根据设计文档，项目应该包含以下结构：

```
CodeWeave/
├── src/workflow_platform/          # 后端源码
│   ├── api/                       # API路由和控制器
│   ├── core/                      # 核心业务逻辑
│   ├── workers/                   # Temporal工作流和活动
│   └── database/                  # 数据库模型和迁移
├── frontend/                      # 前端源码
│   ├── src/components/           # React组件
│   ├── src/pages/               # 页面组件
│   └── src/services/            # API服务
├── tests/                        # 测试文件
├── docs/                         # 文档
├── deployment/                   # 部署配置
├── pyproject.toml               # Python项目配置
├── package.json                 # 前端项目配置
├── docker-compose.yml           # 开发环境配置
├── Dockerfile                   # 容器化配置
└── README.md                    # 项目说明
```

## 初始化步骤

1. **创建Python项目配置**
   ```bash
   # 创建 pyproject.toml
   # 参考 ../design/ 目录中的配置模板
   ```

2. **创建前端项目**
   ```bash
   # 创建 React + TypeScript 项目
   npx create-react-app frontend --template typescript
   ```

3. **设置开发环境**
   ```bash
   # 创建 docker-compose.yml
   # 配置 PostgreSQL, Redis, Temporal 等服务
   ```

4. **实现核心功能**
   - 参考 `../design/` 目录中的详细设计文档
   - 按照 `../tasks.md` 中的任务清单逐步实现

## 设计文档参考

- [需求文档](../.kiro/specs/ai-workflow-platform/requirements.md)
- [总体设计](../.kiro/specs/ai-workflow-platform/design.md)
- [开发任务](../.kiro/specs/ai-workflow-platform/tasks.md)
- [数据库设计](../.kiro/specs/ai-workflow-platform/database-design.md)
- [后端设计](../.kiro/specs/ai-workflow-platform/backend-design.md)
- [前端设计](../.kiro/specs/ai-workflow-platform/frontend-design.md)

## 开发流程

1. 阅读设计文档，理解系统架构
2. 按照任务清单，逐步实现功能
3. 编写测试，确保代码质量
4. 参考部署指南，配置生产环境

## 注意事项

- 本项目是 CodeWeaveDesign 的子模块
- 所有设计文档和规格说明都在父项目中
- 实际代码实现应该严格按照设计文档进行
- 如需修改设计，请先更新父项目中的设计文档