#!/bin/bash

# Hospital Risk Management System - Stop Script

echo "=========================================="
echo "Stopping Hospital Risk Management System"
echo "=========================================="

# Stop all services
docker-compose down

echo ""
echo "✅ All services stopped"
echo ""
echo "To remove all data: docker-compose down -v"
echo "=========================================="

