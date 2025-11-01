# 🚢 Deployment Guide

Comprehensive deployment guide for production and development environments.

## Table of Contents

1. [Development Deployment](#development-deployment)
2. [Production Deployment](#production-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Configuration Management](#configuration-management)
5. [Monitoring Setup](#monitoring-setup)
6. [Backup & Recovery](#backup--recovery)
7. [Maintenance](#maintenance)

## Development Deployment

### Local Development Setup

#### Prerequisites

- Docker Desktop 20.10+
- 8GB RAM minimum
- 10GB disk space
- Git (for version control)

#### Quick Start

```bash
# Clone/navigate to project
cd "D:\bda project"

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Development Configuration

For development, edit `docker-compose.yml`:

```yaml
services:
  producer:
    environment:
      TRANSACTION_RATE: 5  # Slower rate for development
      ANOMALY_RATE: 0.20   # Higher anomaly rate for testing
```

#### Hot Reload

For code changes without restart:

```yaml
# Mount code as volume
producer:
  volumes:
    - ./producers:/app  # Changes reflect automatically
    
dashboard:
  volumes:
    - ./dashboard:/app  # Streamlit auto-reloads
```

### IDE Integration

#### VS Code

1. Install Docker extension
2. Open project folder
3. Use integrated terminal for docker commands

`.vscode/settings.json`:
```json
{
  "python.pythonPath": "python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black"
}
```

#### PyCharm

1. Configure Docker as remote interpreter
2. Set up run configurations for services
3. Enable Docker integration

## Production Deployment

### Pre-Production Checklist

- [ ] Security review completed
- [ ] Load testing passed
- [ ] Backup strategy defined
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Rollback plan prepared
- [ ] SSL certificates obtained
- [ ] DNS configured

### Production Configuration

#### 1. Create Production Compose File

`docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    restart: always
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-logs:/var/lib/zookeeper/log
    networks:
      - kafka-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    restart: always
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 2
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_NUM_PARTITIONS: 5
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
    volumes:
      - kafka-data:/var/lib/kafka/data
    networks:
      - kafka-network
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  postgres:
    image: postgres:14
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: hospital_risk_db
      POSTGRES_INITDB_ARGS: "--encoding=UTF8"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backups:/backups
    networks:
      - kafka-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  producer:
    build: ./producers
    restart: always
    depends_on:
      - kafka
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
      TRANSACTION_RATE: ${TRANSACTION_RATE:-50}
      ANOMALY_RATE: ${ANOMALY_RATE:-0.15}
    networks:
      - kafka-network

  risk-processor:
    build: ./consumers
    restart: always
    depends_on:
      - kafka
      - postgres
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: hospital_risk_db
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    networks:
      - kafka-network
    deploy:
      replicas: 3  # Multiple instances for high availability

  dashboard:
    build: ./dashboard
    restart: always
    depends_on:
      - postgres
    ports:
      - "80:8501"  # Expose on port 80
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: hospital_risk_db
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    networks:
      - kafka-network

volumes:
  zookeeper-data:
    driver: local
  zookeeper-logs:
    driver: local
  kafka-data:
    driver: local
  postgres-data:
    driver: local

networks:
  kafka-network:
    driver: bridge
```

#### 2. Environment Variables

`.env.prod`:
```bash
# Security
POSTGRES_USER=prod_admin
POSTGRES_PASSWORD=<strong-password>

# Performance
TRANSACTION_RATE=100
ANOMALY_RATE=0.15

# Kafka
KAFKA_REPLICATION_FACTOR=3
KAFKA_MIN_INSYNC_REPLICAS=2

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
```

#### 3. Deploy to Production

```bash
# Load environment
export $(cat .env.prod | xargs)

# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Kubernetes Deployment

For Kubernetes, use Helm charts:

#### Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

#### Create Helm Chart

`helm/values.yaml`:

```yaml
kafka:
  enabled: true
  replicaCount: 3
  resources:
    limits:
      memory: 8Gi
      cpu: 4
  persistence:
    enabled: true
    size: 100Gi

postgres:
  enabled: true
  resources:
    limits:
      memory: 4Gi
      cpu: 2
  persistence:
    enabled: true
    size: 50Gi

producer:
  replicaCount: 2
  image:
    repository: hospital-risk-producer
    tag: latest
  env:
    transactionRate: 100
    anomalyRate: 0.15

riskProcessor:
  replicaCount: 3
  image:
    repository: hospital-risk-processor
    tag: latest

dashboard:
  replicaCount: 2
  image:
    repository: hospital-risk-dashboard
    tag: latest
  service:
    type: LoadBalancer
    port: 80
```

#### Deploy with Helm

```bash
# Create namespace
kubectl create namespace hospital-risk

# Install chart
helm install hospital-risk ./helm -n hospital-risk

# Check status
kubectl get pods -n hospital-risk

# Access dashboard
kubectl port-forward svc/dashboard 8501:80 -n hospital-risk
```

## Cloud Deployment

### AWS Deployment

#### Architecture

```
Internet → ALB → ECS (Dashboard)
                   ↓
              MSK (Kafka) ← ECS (Producers/Consumers)
                   ↓
              RDS (PostgreSQL)
```

#### 1. Setup Infrastructure

Use Terraform:

`main.tf`:
```hcl
provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "hospital-risk-vpc"
  }
}

# MSK (Managed Kafka)
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "hospital-risk-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = aws_subnet.private[*].id
    security_groups = [aws_security_group.kafka.id]
    
    storage_info {
      ebs_storage_info {
        volume_size = 100
      }
    }
  }
}

# RDS (PostgreSQL)
resource "aws_db_instance" "postgres" {
  identifier           = "hospital-risk-db"
  engine              = "postgres"
  engine_version      = "14.7"
  instance_class      = "db.t3.large"
  allocated_storage   = 100
  storage_encrypted   = true
  
  db_name  = "hospital_risk_db"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "hospital-risk-cluster"
}

# ECS Task Definitions (producers, consumers, dashboard)
resource "aws_ecs_task_definition" "producer" {
  family                   = "hospital-risk-producer"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  
  container_definitions = jsonencode([{
    name  = "producer"
    image = "${aws_ecr_repository.producer.repository_url}:latest"
    environment = [
      {
        name  = "KAFKA_BOOTSTRAP_SERVERS"
        value = aws_msk_cluster.kafka.bootstrap_brokers
      }
    ]
  }])
}

# Application Load Balancer for Dashboard
resource "aws_lb" "main" {
  name               = "hospital-risk-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}
```

#### 2. Deploy to AWS

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply

# Get endpoints
terraform output
```

### Azure Deployment

#### Architecture

```
Internet → App Gateway → AKS (Containers)
                           ↓
                Event Hubs (Kafka) ← AKS
                           ↓
              Azure Database for PostgreSQL
```

#### Deploy with Azure CLI

```bash
# Create resource group
az group create --name hospital-risk-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group hospital-risk-rg \
  --name hospital-risk-aks \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Create Event Hubs (Kafka)
az eventhubs namespace create \
  --name hospital-risk-events \
  --resource-group hospital-risk-rg \
  --location eastus \
  --sku Standard

# Create PostgreSQL
az postgres flexible-server create \
  --resource-group hospital-risk-rg \
  --name hospital-risk-db \
  --location eastus \
  --admin-user dbadmin \
  --admin-password <password> \
  --sku-name Standard_D2s_v3 \
  --version 14 \
  --storage-size 128

# Deploy containers
kubectl apply -f k8s/
```

### GCP Deployment

#### Architecture

```
Internet → Cloud Load Balancer → GKE (Containers)
                                    ↓
                    Pub/Sub (alternative to Kafka) ← GKE
                                    ↓
                    Cloud SQL (PostgreSQL)
```

#### Deploy with gcloud

```bash
# Create GKE cluster
gcloud container clusters create hospital-risk-cluster \
  --num-nodes=3 \
  --machine-type=n1-standard-4 \
  --zone=us-central1-a

# Create Cloud SQL instance
gcloud sql instances create hospital-risk-db \
  --database-version=POSTGRES_14 \
  --tier=db-n1-standard-4 \
  --region=us-central1

# Deploy application
kubectl apply -f gke/
```

## Configuration Management

### Environment-Specific Configuration

Use config files per environment:

```
config/
├── development.yaml
├── staging.yaml
└── production.yaml
```

### Secrets Management

#### Using Docker Secrets

```yaml
secrets:
  db_password:
    external: true

services:
  postgres:
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
```

#### Using AWS Secrets Manager

```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Use in application
db_password = get_secret('hospital-risk/db-password')
```

## Monitoring Setup

### Prometheus + Grafana

`monitoring/docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"

volumes:
  prometheus-data:
  grafana-data:
```

### Configure Alerts

`alertmanager.yml`:

```yaml
route:
  receiver: 'team-email'
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@hospital.com'
        from: 'alerts@hospital.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@hospital.com'
        auth_password: '<password>'

  - name: 'slack'
    slack_configs:
      - api_url: '<webhook-url>'
        channel: '#alerts'
```

## Backup & Recovery

### Database Backups

#### Automated Backup Script

`scripts/backup_db.sh`:

```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
CONTAINER="postgres"

# Create backup
docker-compose exec -T $CONTAINER pg_dump \
  -U hospital_admin \
  -d hospital_risk_db \
  -F c \
  -f /backups/backup_$DATE.dump

# Compress
gzip $BACKUP_DIR/backup_$DATE.dump

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "*.dump.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.dump.gz"
```

#### Restore from Backup

```bash
# Stop services
docker-compose stop risk-processor producer

# Restore database
docker-compose exec -T postgres pg_restore \
  -U hospital_admin \
  -d hospital_risk_db \
  -c \
  /backups/backup_20241013_120000.dump

# Restart services
docker-compose start risk-processor producer
```

### Kafka Backup

#### Export Kafka Data

```bash
# Export topic data
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic hospital-transactions \
  --from-beginning \
  --max-messages 10000 \
  > kafka_backup_$(date +%Y%m%d).json
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor system health
- Check error logs
- Verify backup completion

#### Weekly
- Review performance metrics
- Update security patches
- Clean old logs

#### Monthly
- Database optimization
- Capacity planning review
- Security audit

### Maintenance Scripts

`scripts/maintenance.sh`:

```bash
#!/bin/bash

echo "Starting maintenance tasks..."

# Clean old logs
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c \
  "DELETE FROM audit_log WHERE timestamp < NOW() - INTERVAL '30 days';"

# Vacuum database
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c \
  "VACUUM ANALYZE;"

# Clean old Kafka data (if needed)
# Kafka auto-deletes based on retention policy

echo "Maintenance completed"
```

### Update Deployment

```bash
# Pull latest code
git pull

# Rebuild images
docker-compose build

# Rolling update (zero downtime)
docker-compose up -d --no-deps --build producer
docker-compose up -d --no-deps --build risk-processor
docker-compose up -d --no-deps --build dashboard
```

---

**For architecture details**, see [ARCHITECTURE.md](ARCHITECTURE.md)
**For testing procedures**, see [TESTING.md](TESTING.md)

