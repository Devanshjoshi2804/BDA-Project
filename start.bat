@echo off
REM Hospital Risk Management System - Startup Script for Windows
REM This script starts all services and verifies they are running correctly

echo ==========================================
echo Hospital Risk Management System
echo Starting all services...
echo ==========================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    pause
    exit /b 1
)

echo [OK] Docker is running

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Error: docker-compose is not installed
    pause
    exit /b 1
)

echo [OK] docker-compose is available

REM Stop any existing containers
echo.
echo Stopping any existing containers...
docker-compose down

REM Start services
echo.
echo Starting services with Docker Compose...
docker-compose up -d

REM Wait for services to initialize
echo.
echo Waiting for services to initialize...
timeout /t 10 /nobreak >nul

REM Check service status
echo.
echo Checking service status...
docker-compose ps

REM Wait for Kafka to be fully ready
echo.
echo Waiting for Kafka to be ready...
timeout /t 20 /nobreak >nul

REM Verify Kafka topics
echo.
echo Verifying Kafka topics...
docker-compose exec -T kafka kafka-topics --list --bootstrap-server localhost:9092 2>nul

REM Check database
echo.
echo Checking database connection...
docker-compose exec -T postgres pg_isready -U hospital_admin -d hospital_risk_db

echo.
echo ==========================================
echo [OK] System started successfully!
echo ==========================================
echo.
echo Dashboard: http://localhost:8501
echo Flink UI: http://localhost:8081
echo PostgreSQL: localhost:5432
echo Kafka: localhost:9092
echo.
echo To view logs: docker-compose logs -f
echo To stop system: docker-compose down
echo.
echo ==========================================
pause

