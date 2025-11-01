# 🧪 Testing Guide

Comprehensive testing guide for the Hospital Risk Management System.

## Table of Contents

1. [Unit Testing](#unit-testing)
2. [Integration Testing](#integration-testing)
3. [End-to-End Testing](#end-to-end-testing)
4. [Performance Testing](#performance-testing)
5. [Manual Testing](#manual-testing)
6. [Troubleshooting Tests](#troubleshooting-tests)

## Unit Testing

### Test Data Generator

```bash
# Test the data generator directly
cd producers
python data_generator.py
```

**Expected Output:**
- Generator statistics
- 5 sample transactions
- Mix of normal and anomalous transactions (15% anomaly rate)
- Proper data structure with all required fields

### Test Database Schema

```bash
# Connect to database
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db

# Run schema tests
\dt  # List tables
\d transactions  # Describe transactions table
\d risk_alerts  # Describe alerts table

# Test views
SELECT * FROM high_risk_transactions LIMIT 5;
SELECT * FROM recent_alerts LIMIT 5;
```

**Expected Results:**
- All 6 tables exist
- Proper column types and constraints
- Views return data correctly
- Indexes are created

## Integration Testing

### Test 1: Kafka Producer-Consumer Flow

```bash
# Terminal 1: Start a console consumer
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic hospital-transactions \
  --from-beginning \
  --max-messages 5
```

**Expected Output:**
- JSON-formatted transaction messages
- Valid transaction structure
- Timestamps, user IDs, amounts visible

### Test 2: Database Integration

```bash
# Check if transactions are being stored
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c \
  "SELECT COUNT(*) as total, 
   COUNT(CASE WHEN risk_level='high' THEN 1 END) as high_risk,
   ROUND(AVG(risk_score), 2) as avg_risk 
   FROM transactions;"
```

**Expected Output:**
- Growing transaction count
- Some high-risk transactions (based on anomaly rate)
- Average risk score between 20-40

### Test 3: Alert Processing

```bash
# Check alerts are being generated
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c \
  "SELECT alert_id, severity, risk_score, alert_message 
   FROM risk_alerts 
   ORDER BY created_at DESC 
   LIMIT 5;"
```

**Expected Output:**
- Alert records with severity levels
- Alert messages describing the risk
- Timestamps showing recent activity

### Test 4: Consumer Processing

```bash
# Monitor risk processor logs
docker-compose logs -f risk-processor | grep "HIGH RISK ALERT"
```

**Expected Output:**
- Periodic high-risk alerts
- Transaction IDs and risk scores
- Detection rules that triggered the alert

## End-to-End Testing

### Test Scenario 1: Normal Transaction Flow

**Steps:**
1. Start the system
2. Wait 2 minutes for transactions to generate
3. Open dashboard at http://localhost:8501
4. Verify metrics are updating

**Success Criteria:**
- ✅ Transaction count > 100
- ✅ Dashboard shows live data
- ✅ Charts are rendering
- ✅ Risk distribution is reasonable (mostly low/medium)

### Test Scenario 2: Anomaly Detection

**Steps:**
1. Monitor producer logs: `docker-compose logs -f producer`
2. Look for anomaly generation messages
3. Check if they appear as high-risk in dashboard
4. Verify alerts are created

**Success Criteria:**
- ✅ Anomalies are generated at ~15% rate
- ✅ Most anomalies are classified as medium/high risk
- ✅ Alerts table shows high-risk transactions
- ✅ Alert processor logs show notifications

### Test Scenario 3: Dashboard Functionality

**Steps:**
1. Open dashboard
2. Enable auto-refresh
3. Set refresh interval to 5 seconds
4. Watch for 1 minute

**Success Criteria:**
- ✅ Metrics update every 5 seconds
- ✅ Charts refresh automatically
- ✅ New transactions appear in table
- ✅ No errors in browser console

### Test Scenario 4: System Recovery

**Steps:**
1. Stop producer: `docker-compose stop producer`
2. Wait 30 seconds
3. Restart producer: `docker-compose start producer`
4. Verify system recovers

**Success Criteria:**
- ✅ Producer reconnects to Kafka
- ✅ Transactions resume flowing
- ✅ No data loss
- ✅ Dashboard continues working

## Performance Testing

### Test 1: Throughput Testing

**Increase transaction rate:**

Edit `docker-compose.yml`:
```yaml
producer:
  environment:
    TRANSACTION_RATE: 100  # 100 transactions/second
```

Restart producer:
```bash
docker-compose restart producer
```

**Monitor performance:**
```bash
# Check processing rate
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c \
  "SELECT 
     DATE_TRUNC('minute', timestamp) as minute,
     COUNT(*) as transactions_per_minute
   FROM transactions
   WHERE timestamp >= NOW() - INTERVAL '5 minutes'
   GROUP BY minute
   ORDER BY minute DESC;"
```

**Success Criteria:**
- ✅ System handles 100 transactions/second
- ✅ No message loss
- ✅ Database keeps up with writes
- ✅ Dashboard remains responsive

### Test 2: Load Testing

**Steps:**
1. Set `TRANSACTION_RATE: 500` in docker-compose.yml
2. Run for 5 minutes
3. Monitor system resources: `docker stats`
4. Check for errors in logs

**Success Criteria:**
- ✅ CPU usage < 80%
- ✅ Memory usage stable
- ✅ No out-of-memory errors
- ✅ Kafka lag remains low

### Test 3: Latency Testing

**Measure end-to-end latency:**

```bash
# Check average processing time
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c \
  "SELECT 
     ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - timestamp))), 3) as avg_latency_seconds
   FROM transactions
   WHERE processed_at IS NOT NULL;"
```

**Success Criteria:**
- ✅ Average latency < 100ms
- ✅ 95th percentile < 200ms
- ✅ No timeout errors

## Manual Testing

### Test Checklist

#### System Startup
- [ ] All services start without errors
- [ ] Kafka topics are created automatically
- [ ] Database schema initializes correctly
- [ ] Producer begins generating data within 30 seconds

#### Data Generation
- [ ] Transactions have realistic values
- [ ] All transaction types are represented
- [ ] Anomalies are generated at expected rate
- [ ] User IDs and departments are diverse

#### Risk Detection
- [ ] High-value transactions get high risk scores
- [ ] Off-hours transactions trigger time-based detection
- [ ] Rapid succession is detected
- [ ] Unusual transaction types are flagged

#### Alert Processing
- [ ] High-risk transactions create alerts
- [ ] Alerts appear in database
- [ ] Alert processor logs show notifications
- [ ] Alert status is updated correctly

#### Dashboard
- [ ] All metrics display correctly
- [ ] Time-series charts show trends
- [ ] Risk distribution pie chart is accurate
- [ ] Department analysis shows data
- [ ] Recent alerts table populates
- [ ] Transaction stream updates in real-time
- [ ] Filters work correctly
- [ ] Auto-refresh functions properly

#### Database
- [ ] Transactions table populates
- [ ] Risk alerts table has entries
- [ ] User profiles are created automatically
- [ ] Audit log records events
- [ ] Views return correct data
- [ ] Indexes improve query performance

### Test Queries

Run these queries to verify data integrity:

```sql
-- Test 1: Data completeness
SELECT 
    COUNT(*) as total,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT department) as unique_departments,
    COUNT(DISTINCT transaction_type) as unique_types
FROM transactions;

-- Test 2: Risk score distribution
SELECT 
    CASE 
        WHEN risk_score < 30 THEN 'Low'
        WHEN risk_score < 70 THEN 'Medium'
        ELSE 'High'
    END as risk_category,
    COUNT(*) as count,
    ROUND(AVG(amount), 2) as avg_amount
FROM transactions
GROUP BY risk_category;

-- Test 3: Anomaly detection rate
SELECT 
    is_anomaly,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM transactions
GROUP BY is_anomaly;

-- Test 4: Alert generation
SELECT 
    severity,
    COUNT(*) as alert_count
FROM risk_alerts
GROUP BY severity;
```

## Troubleshooting Tests

### Issue: No transactions in database

**Debug Steps:**
```bash
# Check producer is running
docker-compose ps producer

# Check producer logs
docker-compose logs producer | tail -50

# Check consumer logs
docker-compose logs risk-processor | tail -50

# Verify Kafka has messages
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic hospital-transactions \
  --max-messages 5
```

### Issue: Dashboard shows no data

**Debug Steps:**
```bash
# Check database has data
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c \
  "SELECT COUNT(*) FROM transactions;"

# Check dashboard logs
docker-compose logs dashboard

# Verify dashboard can connect to database
docker-compose exec dashboard python -c "import psycopg2; print('OK')"
```

### Issue: High memory usage

**Debug Steps:**
```bash
# Check resource usage
docker stats

# Reduce transaction rate
# Edit docker-compose.yml: TRANSACTION_RATE: 5

# Restart services
docker-compose restart
```

### Issue: Kafka lag

**Debug Steps:**
```bash
# Check consumer group lag
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group risk-detection-group

# Increase consumer parallelism
# Scale flink-taskmanager in docker-compose.yml
```

## Automated Test Script

Save as `run_tests.sh`:

```bash
#!/bin/bash

echo "Running Hospital Risk Management System Tests"
echo "=============================================="

# Test 1: Services are running
echo "Test 1: Checking services..."
if docker-compose ps | grep -q "Up"; then
    echo "✓ Services are running"
else
    echo "✗ Services are not running"
    exit 1
fi

# Test 2: Database has data
echo "Test 2: Checking database..."
count=$(docker-compose exec -T postgres psql -U hospital_admin -d hospital_risk_db -t -c "SELECT COUNT(*) FROM transactions;" | tr -d ' ')
if [ "$count" -gt 0 ]; then
    echo "✓ Database has $count transactions"
else
    echo "✗ Database is empty"
    exit 1
fi

# Test 3: Alerts are generated
echo "Test 3: Checking alerts..."
alerts=$(docker-compose exec -T postgres psql -U hospital_admin -d hospital_risk_db -t -c "SELECT COUNT(*) FROM risk_alerts;" | tr -d ' ')
echo "✓ Found $alerts alerts"

# Test 4: Dashboard is accessible
echo "Test 4: Checking dashboard..."
if curl -s http://localhost:8501 > /dev/null; then
    echo "✓ Dashboard is accessible"
else
    echo "✗ Dashboard is not accessible"
    exit 1
fi

echo "=============================================="
echo "All tests passed!"
```

## Performance Benchmarks

Expected performance on recommended hardware (8GB RAM, 4 cores):

| Metric | Expected Value |
|--------|---------------|
| Throughput | 10-100 tx/sec |
| Latency (avg) | < 100ms |
| Latency (p95) | < 200ms |
| Memory (total) | < 4GB |
| CPU (avg) | < 50% |
| Anomaly Detection Rate | ~15% |
| False Positive Rate | < 5% |

## Test Reports

Document your test results:

```markdown
## Test Report - [Date]

### Environment
- Docker Version: 
- System RAM: 
- Transaction Rate: 

### Results
- Total Transactions: 
- High Risk Count: 
- Average Risk Score: 
- System Uptime: 
- Errors: 

### Issues Found
1. [Issue description]
2. [Issue description]

### Recommendations
1. [Recommendation]
2. [Recommendation]
```

---

**For more information**, see the main [README.md](README.md)

