@echo off
REM CodeWeave AI工作流平台 - Windows开发环境启动脚本

setlocal enabledelayedexpansion

echo [INFO] 启动CodeWeave开发环境...

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)
echo [SUCCESS] Docker运行正常

REM 检查环境变量文件
if not exist ".env" (
    if exist ".env.example" (
        echo [WARNING] .env文件不存在，从.env.example复制
        copy ".env.example" ".env" >nul
        echo [INFO] 请编辑.env文件配置必要的环境变量
    ) else (
        echo [ERROR] .env.example文件不存在
        pause
        exit /b 1
    )
)
echo [SUCCESS] 环境变量文件检查完成

REM 创建必要的目录
echo [INFO] 创建必要的目录...
if not exist "config\temporal" mkdir "config\temporal"
if not exist "config\grafana\provisioning" mkdir "config\grafana\provisioning"
if not exist "config\prometheus" mkdir "config\prometheus"
if not exist "config\loki" mkdir "config\loki"
if not exist "logs" mkdir "logs"
echo [SUCCESS] 目录创建完成

REM 启动基础服务
echo [INFO] 启动基础服务...
docker-compose up -d postgres redis temporal

echo [INFO] 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务健康状态
echo [INFO] 检查服务健康状态...

REM 检查PostgreSQL
docker-compose exec -T postgres pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PostgreSQL启动失败
    pause
    exit /b 1
)
echo [SUCCESS] PostgreSQL启动成功

REM 检查Redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis启动失败
    pause
    exit /b 1
)
echo [SUCCESS] Redis启动成功

REM 等待Temporal启动
echo [INFO] 等待Temporal服务启动...
timeout /t 20 /nobreak >nul

echo [SUCCESS] 基础服务启动完成

REM 检查是否启动监控服务
if "%1"=="--with-monitoring" (
    echo [INFO] 启动监控服务...
    docker-compose --profile monitoring up -d
    echo [SUCCESS] 监控服务启动完成
    echo [INFO] Grafana: http://localhost:3001 (admin/admin)
    echo [INFO] Prometheus: http://localhost:9090
)

REM 显示服务信息
echo.
echo [SUCCESS] 开发环境启动完成！
echo.
echo 🚀 服务访问地址:
echo    PostgreSQL:    localhost:5432
echo    Redis:         localhost:6379
echo    Temporal gRPC: localhost:7233
echo    Temporal Web:  http://localhost:8080
echo.
echo 📝 下一步:
echo    1. 运行数据库迁移: alembic upgrade head
echo    2. 启动API服务: uvicorn src.workflow_platform.api.main:app --reload
echo    3. 启动Worker: python -m src.workflow_platform.workers.main
echo.
echo 🛑 停止服务: scripts\stop-dev.bat
echo.

pause