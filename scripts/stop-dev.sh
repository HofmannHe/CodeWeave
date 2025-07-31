#!/bin/bash
# CodeWeave AI工作流平台 - 开发环境停止脚本

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

# 停止服务
stop_services() {
    log_info "停止CodeWeave开发环境..."
    
    # 停止所有服务
    if [ "$1" = "--remove-volumes" ]; then
        log_warning "停止服务并删除数据卷..."
        docker-compose down -v
        log_warning "所有数据已删除"
    else
        docker-compose down
        log_info "服务已停止，数据卷保留"
    fi
    
    log_success "开发环境已停止"
}

# 清理资源
cleanup_resources() {
    if [ "$1" = "--cleanup" ]; then
        log_info "清理Docker资源..."
        
        # 删除未使用的容器
        docker container prune -f
        
        # 删除未使用的镜像
        docker image prune -f
        
        # 删除未使用的网络
        docker network prune -f
        
        log_success "资源清理完成"
    fi
}

# 显示帮助信息
show_help() {
    echo "CodeWeave开发环境停止脚本"
    echo ""
    echo "用法:"
    echo "  ./scripts/stop-dev.sh                    # 停止服务，保留数据"
    echo "  ./scripts/stop-dev.sh --remove-volumes   # 停止服务并删除所有数据"
    echo "  ./scripts/stop-dev.sh --cleanup          # 停止服务并清理Docker资源"
    echo "  ./scripts/stop-dev.sh --help             # 显示帮助信息"
    echo ""
}

# 主函数
main() {
    case "$1" in
        --help)
            show_help
            ;;
        --remove-volumes)
            stop_services --remove-volumes
            ;;
        --cleanup)
            stop_services
            cleanup_resources --cleanup
            ;;
        "")
            stop_services
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"