#!/bin/bash

# Hospital Risk Management System - Startup Script
# This script starts all services and verifies they are running correctly

echo "=========================================="
echo "Hospital Risk Management System"
echo "Starting all services..."
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo "✅ Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not installed"
    exit 1
fi

echo "✅ docker-compose is available"

# Stop any existing containers
echo ""
echo "Stopping any existing containers..."
docker-compose down

# Start services
echo ""
echo "Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to initialize
echo ""
echo "Waiting for services to initialize..."
sleep 10

# Check service status
echo ""
echo "Checking service status..."
docker-compose ps

# Wait for Kafka to be fully ready
echo ""
echo "Waiting for Kafka to be ready..."
sleep 20

# Verify Kafka topics
echo ""
echo "Verifying Kafka topics..."
docker-compose exec -T kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null

# Check database
echo ""
echo "Checking database connection..."
docker-compose exec -T postgres pg_isready -U hospital_admin -d hospital_risk_db

echo ""
echo "=========================================="
echo "✅ System started successfully!"
echo "=========================================="
echo ""
echo "📊 Dashboard: http://localhost:8501"
echo "🔍 Flink UI: http://localhost:8081"
echo "🗄️  PostgreSQL: localhost:5432"
echo "📡 Kafka: localhost:9092"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop system: docker-compose down"
echo ""
echo "=========================================="

