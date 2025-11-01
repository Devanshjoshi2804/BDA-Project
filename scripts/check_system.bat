@echo off
REM System Health Check Script for Windows
REM Verifies all components are working correctly

echo ==========================================
echo Hospital Risk Management System
echo Health Check
echo ==========================================
echo.

REM Check Docker
echo 1. Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [X] Docker is NOT running
    pause
    exit /b 1
) else (
    echo [OK] Docker is running
)
echo.

REM Check Services
echo 2. Checking Services...
docker-compose ps | findstr "zookeeper.*Up" >nul && (echo [OK] zookeeper is running) || (echo [X] zookeeper is NOT running)
docker-compose ps | findstr "kafka.*Up" >nul && (echo [OK] kafka is running) || (echo [X] kafka is NOT running)
docker-compose ps | findstr "postgres.*Up" >nul && (echo [OK] postgres is running) || (echo [X] postgres is NOT running)
docker-compose ps | findstr "flink-jobmanager.*Up" >nul && (echo [OK] flink-jobmanager is running) || (echo [X] flink-jobmanager is NOT running)
docker-compose ps | findstr "producer.*Up" >nul && (echo [OK] producer is running) || (echo [X] producer is NOT running)
docker-compose ps | findstr "risk-processor.*Up" >nul && (echo [OK] risk-processor is running) || (echo [X] risk-processor is NOT running)
docker-compose ps | findstr "dashboard.*Up" >nul && (echo [OK] dashboard is running) || (echo [X] dashboard is NOT running)
echo.

REM Check Database
echo 3. Checking Database...
docker-compose exec -T postgres pg_isready -U hospital_admin -d hospital_risk_db >nul 2>&1
if errorlevel 1 (
    echo [X] PostgreSQL is NOT accepting connections
) else (
    echo [OK] PostgreSQL is accepting connections
    for /f %%i in ('docker-compose exec -T postgres psql -U hospital_admin -d hospital_risk_db -t -c "SELECT COUNT(*) FROM transactions;" 2^>nul') do set txn_count=%%i
    echo [OK] Transactions in database: %txn_count%
)
echo.

REM Check Endpoints
echo 4. Checking Endpoints...
curl -s http://localhost:8501 >nul 2>&1
if errorlevel 1 (
    echo [!] Dashboard may not be ready yet at http://localhost:8501
) else (
    echo [OK] Dashboard is accessible at http://localhost:8501
)

curl -s http://localhost:8081 >nul 2>&1
if errorlevel 1 (
    echo [!] Flink UI may not be ready yet at http://localhost:8081
) else (
    echo [OK] Flink UI is accessible at http://localhost:8081
)
echo.

echo ==========================================
echo Health Check Complete
echo ==========================================
pause

