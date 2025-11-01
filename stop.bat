@echo off
REM Hospital Risk Management System - Stop Script for Windows

echo ==========================================
echo Stopping Hospital Risk Management System
echo ==========================================

REM Stop all services
docker-compose down

echo.
echo [OK] All services stopped
echo.
echo To remove all data: docker-compose down -v
echo ==========================================
pause

