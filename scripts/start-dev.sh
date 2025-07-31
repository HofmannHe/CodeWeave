#!/bin/bash
# CodeWeave AI工作流平台 - 开发环境启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否运行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
    log_success "Docker运行正常"
}

# 检查环境变量文件
check_env_file() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning ".env文件不存在，从.env.example复制"
            cp .env.example .env
            log_info "请编辑.env文件配置必要的环境变量"
        else
            log_error ".env.example文件不存在"
            exit 1
        fi
    fi
    log_success "环境变量文件检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p config/temporal
    mkdir -p config/grafana/provisioning
    mkdir -p config/prometheus
    mkdir -p config/loki
    mkdir -p scripts
    mkdir -p logs
    log_success "目录创建完成"
}

# 启动基础服务
start_services() {
    log_info "启动基础服务..."
    
    # 启动核心服务
    docker-compose up -d postgres redis temporal
    
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务健康状态
    log_info "检查服务健康状态..."
    
    # 检查PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_success "PostgreSQL启动成功"
    else
        log_error "PostgreSQL启动失败"
        exit 1
    fi
    
    # 检查Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis启动成功"
    else
        log_error "Redis启动失败"
        exit 1
    fi
    
    # 等待Temporal启动
    log_info "等待Temporal服务启动..."
    sleep 20
    
    log_success "基础服务启动完成"
}

# 启动监控服务 (可选)
start_monitoring() {
    if [ "$1" = "--with-monitoring" ]; then
        log_info "启动监控服务..."
        docker-compose --profile monitoring up -d
        log_success "监控服务启动完成"
        log_info "Grafana: http://localhost:3001 (admin/admin)"
        log_info "Prometheus: http://localhost:9090"
    fi
}

# 显示服务信息
show_services_info() {
    log_success "开发环境启动完成！"
    echo ""
    echo "🚀 服务访问地址:"
    echo "   PostgreSQL:    localhost:5432"
    echo "   Redis:         localhost:6379"
    echo "   Temporal gRPC: localhost:7233"
    echo "   Temporal Web:  http://localhost:8080"
    echo ""
    echo "📝 下一步:"
    echo "   1. 运行数据库迁移: alembic upgrade head"
    echo "   2. 启动API服务: uvicorn src.workflow_platform.api.main:app --reload"
    echo "   3. 启动Worker: python -m src.workflow_platform.workers.main"
    echo ""
    echo "🛑 停止服务: ./scripts/stop-dev.sh"
}

# 主函数
main() {
    log_info "启动CodeWeave开发环境..."
    
    check_docker
    check_env_file
    create_directories
    start_services
    start_monitoring "$1"
    show_services_info
}

# 运行主函数
main "$@"