# 🏗️ System Architecture

Detailed architecture documentation for the Hospital Risk Management System.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Components](#components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Design Decisions](#design-decisions)
7. [Scalability](#scalability)
8. [Security](#security)

## Overview

The Hospital Risk Management System is a microservices-based architecture designed for real-time processing of financial transactions with advanced anomaly detection and risk scoring capabilities.

### Key Characteristics

- **Event-Driven**: Uses Apache Kafka for asynchronous message processing
- **Microservices**: Loosely coupled services with single responsibilities
- **Containerized**: All services run in Docker containers for portability
- **Real-Time**: Sub-second latency for risk detection and alerting
- **Scalable**: Horizontal scaling for high throughput scenarios
- **Fault-Tolerant**: Automatic recovery and data persistence

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Hospital Risk Management System                       │
│                         Microservices Architecture                       │
└─────────────────────────────────────────────────────────────────────────┘

┌───────────────────────┐
│   Data Generation     │
│   ┌───────────────┐   │
│   │  Data         │   │
│   │  Generator    │   │      ┌────────────────────────────────┐
│   │  (Python)     │   │      │     Message Streaming Layer     │
│   └───────┬───────┘   │      │                                 │
│           │           │      │  ┌──────────────────────────┐  │
│   ┌───────▼───────┐   │      │  │      Zookeeper          │  │
│   │   Kafka       │   │──────▶  │   (Coordination)        │  │
│   │   Producer    │   │      │  └───────────┬──────────────┘  │
│   └───────────────┘   │      │              │                 │
└───────────────────────┘      │  ┌───────────▼──────────────┐  │
                               │  │    Kafka Broker          │  │
                               │  │  ┌─────────────────────┐ │  │
                               │  │  │ hospital-           │ │  │
                               │  │  │ transactions        │ │  │
                               │  │  ├─────────────────────┤ │  │
                               │  │  │ risk-scores         │ │  │
                               │  │  ├─────────────────────┤ │  │
                               │  │  │ risk-alerts         │ │  │
                               │  │  └─────────────────────┘ │  │
                               │  └──────────┬───────────────┘  │
                               └─────────────┼──────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
                    ▼                        ▼                        ▼
    ┌───────────────────────┐  ┌────────────────────┐  ┌────────────────────┐
    │  Stream Processing    │  │  Risk Detection    │  │  Alert Processing  │
    │  ┌─────────────────┐  │  │  ┌──────────────┐  │  │  ┌──────────────┐  │
    │  │ Flink           │  │  │  │ Risk         │  │  │  │ Alert        │  │
    │  │ JobManager      │  │  │  │ Consumer     │  │  │  │ Processor    │  │
    │  └────────┬────────┘  │  │  │ (Python)     │  │  │  │ (Python)     │  │
    │           │           │  │  └──────┬───────┘  │  │  └──────┬───────┘  │
    │  ┌────────▼────────┐  │  │         │          │  │         │          │
    │  │ Flink           │  │  │  ┌──────▼───────┐  │  │  ┌──────▼───────┐  │
    │  │ TaskManager     │  │  │  │ Risk Engine  │  │  │  │ Notification │  │
    │  │ (Parallel)      │  │  │  │ - Amount     │  │  │  │ Service      │  │
    │  └─────────────────┘  │  │  │ - Time       │  │  │  └──────────────┘  │
    └───────────────────────┘  │  │ - Frequency  │  │  └────────────────────┘
                               │  │ - Behavior   │  │
                               │  │ - Metadata   │  │
                               │  └──────┬───────┘  │
                               └─────────┼──────────┘
                                         │
                                         ▼
                        ┌────────────────────────────────┐
                        │    Persistence Layer           │
                        │  ┌──────────────────────────┐  │
                        │  │     PostgreSQL 14        │  │
                        │  │  ┌────────────────────┐  │  │
                        │  │  │ transactions       │  │  │
                        │  │  │ risk_alerts        │  │  │
                        │  │  │ user_profiles      │  │  │
                        │  │  │ audit_log          │  │  │
                        │  │  │ transaction_patterns│ │  │
                        │  │  │ system_metrics     │  │  │
                        │  │  └────────────────────┘  │  │
                        │  └────────────┬─────────────┘  │
                        └───────────────┼────────────────┘
                                        │
                                        ▼
                        ┌────────────────────────────────┐
                        │   Presentation Layer           │
                        │  ┌──────────────────────────┐  │
                        │  │  Streamlit Dashboard     │  │
                        │  │  ┌────────────────────┐  │  │
                        │  │  │ Metrics            │  │  │
                        │  │  │ Time Series        │  │  │
                        │  │  │ Risk Distribution  │  │  │
                        │  │  │ Alerts Table       │  │  │
                        │  │  │ Transaction Stream │  │  │
                        │  │  └────────────────────┘  │  │
                        │  └──────────────────────────┘  │
                        │                                │
                        │  Port: 8501                    │
                        └────────────────────────────────┘
```

## Components

### 1. Data Generation Layer

#### Synthetic Data Generator
- **Purpose**: Generate realistic hospital accounting transactions
- **Technology**: Python with Faker library
- **Features**:
  - Multiple transaction types (8 types)
  - 12 hospital departments
  - 50 simulated users
  - Configurable anomaly injection (default 15%)
  - Business hours simulation
  - Realistic amount distributions

#### Kafka Producer
- **Purpose**: Publish transactions to Kafka
- **Technology**: kafka-python
- **Features**:
  - Configurable throughput (default 10 tx/sec)
  - Compression (gzip)
  - Guaranteed delivery (acks=all)
  - Automatic retries
  - Transaction batching

### 2. Message Streaming Layer

#### Apache Zookeeper
- **Purpose**: Kafka cluster coordination
- **Version**: 7.5.0 (Confluent)
- **Configuration**:
  - Port: 2181
  - Persistent volumes for data

#### Apache Kafka
- **Purpose**: Distributed event streaming
- **Version**: 7.5.0 (Confluent)
- **Topics**:
  1. `hospital-transactions` - Raw transaction data
  2. `risk-scores` - Processed transactions with risk scores
  3. `risk-alerts` - High-risk alerts
- **Configuration**:
  - 3 partitions per topic
  - Replication factor: 1 (dev), 3 (prod)
  - Retention: 168 hours (7 days)
  - Ports: 9092 (external), 29092 (internal)

### 3. Stream Processing Layer

#### Apache Flink
- **Purpose**: Advanced stream processing and CEP
- **Version**: 1.17.0
- **Components**:
  - JobManager (orchestration)
  - TaskManager (execution, scalable)
- **Features**:
  - Stateful computations
  - Time-windowed operations
  - Checkpointing for fault tolerance
  - Parallel processing (4 task slots)
- **Ports**:
  - JobManager: 8081 (Web UI)

#### Risk Detection Consumer
- **Purpose**: Real-time risk scoring and anomaly detection
- **Technology**: Python
- **Algorithm**: Multi-dimensional risk scoring
  - Amount risk (0-25 points)
  - Time risk (0-20 points)
  - Frequency risk (0-25 points)
  - Behavior risk (0-20 points)
  - Metadata risk (0-10 points)
- **Classification**:
  - Low: 0-30
  - Medium: 31-70
  - High: 71-100

#### Alert Processor
- **Purpose**: Handle high-risk alerts and notifications
- **Technology**: Python
- **Features**:
  - Real-time alert consumption
  - Console notifications
  - Database logging
  - Audit trail maintenance

### 4. Persistence Layer

#### PostgreSQL Database
- **Purpose**: Store transactions, alerts, and analytics
- **Version**: 14
- **Tables**:
  1. `transactions` - All processed transactions
  2. `risk_alerts` - High-risk events
  3. `user_profiles` - User behavior baselines
  4. `audit_log` - System events
  5. `transaction_patterns` - Detected patterns
  6. `system_metrics` - Performance metrics
- **Views**:
  - `high_risk_transactions`
  - `recent_alerts`
  - `transaction_summary`
  - `user_risk_summary`
- **Features**:
  - Automatic indexing
  - Triggers for profile updates
  - Data retention policies
  - JSONB for flexible metadata
- **Port**: 5432

### 5. Presentation Layer

#### Streamlit Dashboard
- **Purpose**: Real-time visualization and monitoring
- **Technology**: Streamlit, Plotly
- **Features**:
  - Live metrics (auto-refresh)
  - Time-series charts
  - Risk distribution visualizations
  - Interactive filters
  - Alert management
  - User risk profiles
- **Port**: 8501

## Data Flow

### 1. Transaction Generation Flow

```
Data Generator → Kafka Producer → hospital-transactions topic
```

1. Data generator creates synthetic transaction
2. Transaction is serialized to JSON
3. Producer publishes to Kafka with transaction_id as key
4. Kafka distributes across partitions

### 2. Risk Detection Flow

```
hospital-transactions → Risk Consumer → Risk Engine → PostgreSQL + risk-scores topic
```

1. Consumer reads from hospital-transactions
2. Risk engine analyzes transaction
3. Multi-dimensional scoring applied
4. Result stored in PostgreSQL
5. Enriched transaction published to risk-scores

### 3. Alert Flow

```
risk-scores → Alert Filter → risk-alerts → Alert Processor → Notifications + Database
```

1. High-risk transactions (score ≥ 70) trigger alerts
2. Alert published to risk-alerts topic
3. Alert processor consumes alert
4. Notification sent (console/email/webhook)
5. Alert stored in database

### 4. Dashboard Flow

```
PostgreSQL ← Dashboard (queries) → User Browser (visualization)
```

1. Dashboard queries PostgreSQL for latest data
2. Data transformed to pandas DataFrames
3. Plotly generates interactive charts
4. Streamlit renders in browser
5. Auto-refresh repeats cycle

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Message Broker | Apache Kafka | 7.5.0 | Event streaming |
| Coordination | Zookeeper | 7.5.0 | Kafka coordination |
| Stream Processing | Apache Flink | 1.17.0 | Complex event processing |
| Database | PostgreSQL | 14 | Persistent storage |
| Dashboard | Streamlit | 1.28.1 | Web visualization |
| Container Platform | Docker | 20.10+ | Containerization |
| Orchestration | Docker Compose | 2.0+ | Multi-container management |

### Python Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| kafka-python | 2.0.2 | Kafka client |
| psycopg2-binary | 2.9.9 | PostgreSQL adapter |
| faker | 20.1.0 | Synthetic data generation |
| pandas | 2.0.3 | Data manipulation |
| plotly | 5.17.0 | Interactive charts |
| numpy | 1.24.3 | Numerical computations |
| streamlit | 1.28.1 | Dashboard framework |

## Design Decisions

### 1. Why Microservices?

**Decision**: Use microservices architecture instead of monolithic
**Rationale**:
- Independent scaling of components
- Technology flexibility per service
- Isolated failure domains
- Easier maintenance and updates
- Better alignment with team structure

### 2. Why Kafka?

**Decision**: Use Apache Kafka for message streaming
**Rationale**:
- High throughput (millions of messages/sec)
- Fault tolerance and durability
- Horizontal scalability
- Replay capability for debugging
- Industry standard for real-time pipelines

### 3. Why PostgreSQL?

**Decision**: Use PostgreSQL over NoSQL databases
**Rationale**:
- ACID transactions for financial data
- Complex queries for analytics
- Mature and reliable
- JSONB for flexible metadata
- Strong consistency guarantees

### 4. Why Streamlit?

**Decision**: Use Streamlit for dashboard vs React/Angular
**Rationale**:
- Rapid development (Python-only)
- Built-in components for data apps
- Easy integration with pandas/plotly
- Auto-reload during development
- Good for internal tools

### 5. Why Docker?

**Decision**: Containerize all components
**Rationale**:
- Consistent environments (dev/prod)
- Easy deployment
- Simplified dependencies
- Portable across platforms
- Resource isolation

### 6. Risk Scoring Algorithm

**Decision**: Multi-dimensional rule-based scoring
**Rationale**:
- Explainable (vs black-box ML)
- Fast (real-time requirements)
- Customizable thresholds
- No training data required
- Easy to audit

## Scalability

### Horizontal Scaling

#### Kafka
```yaml
# Increase partitions
kafka-topics --alter --topic hospital-transactions --partitions 10
```

#### Flink TaskManagers
```yaml
# In docker-compose.yml
flink-taskmanager:
  scale: 4  # 4 parallel task managers
```

#### Consumers
```yaml
# Deploy multiple consumer instances
risk-processor:
  scale: 3  # 3 consumer instances
```

### Vertical Scaling

```yaml
# Increase resource limits
services:
  kafka:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### Performance Optimization

1. **Kafka Tuning**:
   - Increase batch size
   - Enable compression
   - Optimize partition count

2. **Database Optimization**:
   - Index frequently queried columns
   - Partition large tables
   - Connection pooling

3. **Consumer Optimization**:
   - Batch database writes
   - Async processing
   - Parallel processing

### Expected Throughput

| Configuration | Throughput | Latency | Resource Usage |
|---------------|-----------|---------|----------------|
| Minimal (default) | 10 tx/sec | <100ms | 2GB RAM, 2 cores |
| Standard | 100 tx/sec | <200ms | 4GB RAM, 4 cores |
| High | 1000 tx/sec | <500ms | 8GB RAM, 8 cores |
| Maximum | 10,000 tx/sec | <1sec | 16GB RAM, 16 cores |

## Security

### Current Security Measures

1. **Network Isolation**: Docker network for inter-service communication
2. **Database Authentication**: Username/password for PostgreSQL
3. **No External Exposure**: Only dashboard and Flink UI exposed

### Production Security Enhancements

For production deployment, implement:

1. **Authentication & Authorization**:
   - Kafka SASL/SSL authentication
   - PostgreSQL SSL connections
   - Dashboard authentication (OAuth/LDAP)

2. **Encryption**:
   - TLS for Kafka communication
   - Database connection encryption
   - Secrets management (Vault, AWS Secrets)

3. **Network Security**:
   - VPC/private networks
   - Firewall rules
   - API gateway for dashboard

4. **Data Security**:
   - Sensitive data masking
   - Audit logging
   - Data retention policies

5. **Monitoring**:
   - Intrusion detection
   - Anomaly detection in access patterns
   - Security event logging

### Security Configuration Example

```yaml
# Production-ready Kafka with SSL
kafka:
  environment:
    KAFKA_SSL_KEYSTORE_LOCATION: /var/private/ssl/kafka.keystore.jks
    KAFKA_SSL_KEYSTORE_PASSWORD: ${KEYSTORE_PASSWORD}
    KAFKA_SSL_KEY_PASSWORD: ${KEY_PASSWORD}
    KAFKA_SECURITY_PROTOCOL: SSL
```

## Monitoring & Observability

### Metrics to Monitor

1. **System Metrics**:
   - CPU, Memory, Disk usage
   - Network throughput
   - Container health

2. **Application Metrics**:
   - Transaction throughput
   - Processing latency
   - Error rates
   - Queue depths

3. **Business Metrics**:
   - Risk score distribution
   - Alert frequency
   - Anomaly detection rate
   - False positive rate

### Recommended Tools

- **Metrics**: Prometheus + Grafana
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: Jaeger for distributed tracing
- **Alerting**: PagerDuty, Slack integrations

## Future Enhancements

1. **Machine Learning**:
   - Replace rule-based scoring with ML models
   - Continuous learning from feedback
   - Advanced pattern recognition

2. **Advanced Features**:
   - Graph analysis for fraud networks
   - Predictive analytics
   - Automated remediation

3. **Integration**:
   - External APIs for enrichment
   - Integration with existing hospital systems
   - Multi-tenant support

4. **Performance**:
   - In-memory caching (Redis)
   - Pre-aggregated analytics
   - Real-time ML inference

---

**For implementation details**, see [README.md](README.md)
**For testing**, see [TESTING.md](TESTING.md)

