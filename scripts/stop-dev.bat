@echo off
REM CodeWeave AI工作流平台 - Windows开发环境停止脚本

setlocal enabledelayedexpansion

echo [INFO] 停止CodeWeave开发环境...

REM 检查参数
if "%1"=="--remove-volumes" (
    echo [WARNING] 停止服务并删除数据卷...
    docker-compose down -v
    echo [WARNING] 所有数据已删除
) else if "%1"=="--cleanup" (
    docker-compose down
    echo [INFO] 清理Docker资源...
    docker container prune -f
    docker image prune -f
    docker network prune -f
    echo [SUCCESS] 资源清理完成
) else if "%1"=="--help" (
    echo CodeWeave开发环境停止脚本
    echo.
    echo 用法:
    echo   scripts\stop-dev.bat                    # 停止服务，保留数据
    echo   scripts\stop-dev.bat --remove-volumes   # 停止服务并删除所有数据
    echo   scripts\stop-dev.bat --cleanup          # 停止服务并清理Docker资源
    echo   scripts\stop-dev.bat --help             # 显示帮助信息
    echo.
    goto :end
) else (
    docker-compose down
    echo [INFO] 服务已停止，数据卷保留
)

echo [SUCCESS] 开发环境已停止

:end
pause