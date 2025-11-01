@echo off
REM Hospital Risk Management System - Quick Start (Without Flink)
REM This starts a lighter version that's faster to initialize

echo ==========================================
echo Hospital Risk Management System
echo Quick Start (Lite Version - No Flink)
echo ==========================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

echo [OK] Docker is running

REM Stop any existing containers
echo.
echo Stopping any existing containers...
docker-compose -f docker-compose.lite.yml down 2>nul

REM Start services
echo.
echo Starting services (Lite version - faster startup)...
docker-compose -f docker-compose.lite.yml up -d

REM Wait for services
echo.
echo Waiting for services to initialize...
timeout /t 20 /nobreak >nul

REM Check status
echo.
echo Checking service status...
docker-compose -f docker-compose.lite.yml ps

echo.
echo ==========================================
echo [OK] System started successfully!
echo ==========================================
echo.
echo Dashboard: http://localhost:8501
echo PostgreSQL: localhost:5432
echo Kafka: localhost:9092
echo.
echo NOTE: This is the LITE version (without Flink)
echo For full version with Flink, use start.bat
echo.
echo To view logs: docker-compose -f docker-compose.lite.yml logs -f
echo To stop system: docker-compose -f docker-compose.lite.yml down
echo.
echo ==========================================
pause

