#!/bin/bash

# Log Viewer Script
# Provides easy access to various service logs

echo "=========================================="
echo "Hospital Risk Management System"
echo "Log Viewer"
echo "=========================================="
echo ""
echo "Select which logs to view:"
echo ""
echo "1) All services"
echo "2) Producer (transaction generation)"
echo "3) Risk Processor (risk detection)"
echo "4) Alert Processor"
echo "5) Dashboard"
echo "6) Kafka"
echo "7) PostgreSQL"
echo "8) Flink JobManager"
echo "9) Flink TaskManager"
echo ""
read -p "Enter choice [1-9]: " choice

case $choice in
    1)
        echo "Viewing all service logs..."
        docker-compose logs -f
        ;;
    2)
        echo "Viewing producer logs..."
        docker-compose logs -f producer
        ;;
    3)
        echo "Viewing risk processor logs..."
        docker-compose logs -f risk-processor
        ;;
    4)
        echo "Viewing alert processor logs (included in risk-processor)..."
        docker-compose logs -f risk-processor | grep -i alert
        ;;
    5)
        echo "Viewing dashboard logs..."
        docker-compose logs -f dashboard
        ;;
    6)
        echo "Viewing Kafka logs..."
        docker-compose logs -f kafka
        ;;
    7)
        echo "Viewing PostgreSQL logs..."
        docker-compose logs -f postgres
        ;;
    8)
        echo "Viewing Flink JobManager logs..."
        docker-compose logs -f flink-jobmanager
        ;;
    9)
        echo "Viewing Flink TaskManager logs..."
        docker-compose logs -f flink-taskmanager
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

