#!/bin/bash

# System Health Check Script
# Verifies all components are working correctly

echo "=========================================="
echo "Hospital Risk Management System"
echo "Health Check"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    service_name=$1
    if docker-compose ps | grep -q "$service_name.*Up"; then
        echo -e "${GREEN}✓${NC} $service_name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name is NOT running"
        return 1
    fi
}

# Check Docker
echo "1. Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker is running"
else
    echo -e "${RED}✗${NC} Docker is NOT running"
    exit 1
fi
echo ""

# Check Services
echo "2. Checking Services..."
check_service "zookeeper"
check_service "kafka"
check_service "postgres"
check_service "flink-jobmanager"
check_service "flink-taskmanager"
check_service "producer"
check_service "risk-processor"
check_service "dashboard"
echo ""

# Check Kafka Topics
echo "3. Checking Kafka Topics..."
topics=$(docker-compose exec -T kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null)
if echo "$topics" | grep -q "hospital-transactions"; then
    echo -e "${GREEN}✓${NC} hospital-transactions topic exists"
else
    echo -e "${RED}✗${NC} hospital-transactions topic missing"
fi
if echo "$topics" | grep -q "risk-scores"; then
    echo -e "${GREEN}✓${NC} risk-scores topic exists"
else
    echo -e "${RED}✗${NC} risk-scores topic missing"
fi
if echo "$topics" | grep -q "risk-alerts"; then
    echo -e "${GREEN}✓${NC} risk-alerts topic exists"
else
    echo -e "${RED}✗${NC} risk-alerts topic missing"
fi
echo ""

# Check Database
echo "4. Checking Database..."
if docker-compose exec -T postgres pg_isready -U hospital_admin -d hospital_risk_db > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PostgreSQL is accepting connections"
    
    # Check transaction count
    txn_count=$(docker-compose exec -T postgres psql -U hospital_admin -d hospital_risk_db -t -c "SELECT COUNT(*) FROM transactions;" 2>/dev/null | tr -d ' ')
    echo -e "${GREEN}✓${NC} Transactions in database: $txn_count"
    
    # Check alert count
    alert_count=$(docker-compose exec -T postgres psql -U hospital_admin -d hospital_risk_db -t -c "SELECT COUNT(*) FROM risk_alerts;" 2>/dev/null | tr -d ' ')
    echo -e "${GREEN}✓${NC} Alerts in database: $alert_count"
else
    echo -e "${RED}✗${NC} PostgreSQL is NOT accepting connections"
fi
echo ""

# Check Endpoints
echo "5. Checking Endpoints..."
if curl -s http://localhost:8501 > /dev/null; then
    echo -e "${GREEN}✓${NC} Dashboard is accessible at http://localhost:8501"
else
    echo -e "${YELLOW}⚠${NC} Dashboard may not be ready yet at http://localhost:8501"
fi

if curl -s http://localhost:8081 > /dev/null; then
    echo -e "${GREEN}✓${NC} Flink UI is accessible at http://localhost:8081"
else
    echo -e "${YELLOW}⚠${NC} Flink UI may not be ready yet at http://localhost:8081"
fi
echo ""

# Summary
echo "=========================================="
echo "Health Check Complete"
echo "=========================================="

