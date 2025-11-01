# 🚀 Quick Start Guide

Get the Hospital Risk Management System up and running in 5 minutes!

## Prerequisites

✅ Docker Desktop installed and running ([Download here](https://www.docker.com/products/docker-desktop))
✅ 8GB+ RAM available
✅ 10GB+ free disk space

## Step 1: Start the System

### Windows
Double-click `start.bat` or run in PowerShell:
```powershell
.\start.bat
```

### macOS/Linux
```bash
chmod +x start.sh
./start.sh
```

### Manual Start
```bash
docker-compose up -d
```

## Step 2: Wait for Initialization

The system takes about 30-60 seconds to fully initialize. You'll see:
- ✅ Zookeeper starting
- ✅ Kafka broker starting
- ✅ PostgreSQL initializing
- ✅ Kafka topics being created
- ✅ Producer starting to generate data
- ✅ Consumers processing transactions
- ✅ Dashboard launching

## Step 3: Access the Dashboard

Open your browser and go to:
```
http://localhost:8501
```

You should see the real-time dashboard with:
- Transaction metrics
- Risk scores
- Live charts
- Recent alerts

## Step 4: Verify Everything is Working

### Check Services Status
```bash
docker-compose ps
```

All services should show "Up" status.

### View Logs
```bash
# All logs
docker-compose logs -f

# Producer logs (transaction generation)
docker-compose logs -f producer

# Consumer logs (risk detection)
docker-compose logs -f risk-processor

# Dashboard logs
docker-compose logs -f dashboard
```

### Check Database
```bash
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db

# Then run:
SELECT COUNT(*) FROM transactions;
SELECT * FROM risk_alerts ORDER BY created_at DESC LIMIT 5;
```

## Step 5: Explore the Dashboard

### Key Features to Check

1. **Top Metrics Bar**
   - Watch the transaction count increase
   - Monitor active alerts
   - Check average risk score

2. **Transaction Flow Chart**
   - Real-time transaction volume
   - Risk score trends over time

3. **Risk Distribution**
   - Pie chart showing low/medium/high risk breakdown

4. **Recent Alerts Table**
   - High-risk transactions flagged automatically

5. **Transaction Stream**
   - Live feed of recent transactions

### Dashboard Controls

- **Auto-refresh**: Toggle on/off (top-left sidebar)
- **Refresh Interval**: Adjust update frequency (2-30 seconds)
- **Risk Filter**: Filter transactions by risk level

## Common Issues & Solutions

### ❌ Dashboard not loading

**Solution:**
```bash
# Check if port 8501 is available
docker-compose restart dashboard
docker-compose logs dashboard
```

### ❌ No data showing

**Solution:**
```bash
# Verify producer is running
docker-compose logs producer

# Check database has data
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db -c "SELECT COUNT(*) FROM transactions;"

# Restart consumer if needed
docker-compose restart risk-processor
```

### ❌ Services won't start

**Solution:**
```bash
# Stop everything
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

### ❌ Kafka connection errors

**Solution:**
```bash
# Wait longer for Kafka to initialize (it takes 20-30 seconds)
sleep 30

# Check Kafka is running
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Restart if needed
docker-compose restart kafka
```

## Stopping the System

### Windows
```powershell
.\stop.bat
```

### macOS/Linux
```bash
./stop.sh
```

### Manual Stop
```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## Next Steps

### Customize Configuration

Edit `docker-compose.yml` to adjust:

```yaml
producer:
  environment:
    TRANSACTION_RATE: 50    # Increase to 50 transactions/second
    ANOMALY_RATE: 0.20      # Increase anomaly rate to 20%
```

Then restart:
```bash
docker-compose restart producer
```

### Monitor Flink

Access Flink Web UI:
```
http://localhost:8081
```

### Access PostgreSQL

```bash
# Connect to database
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db

# Useful queries
SELECT COUNT(*) as total, risk_level FROM transactions GROUP BY risk_level;
SELECT * FROM high_risk_transactions LIMIT 10;
SELECT * FROM user_risk_summary;
```

### View Kafka Topics

```bash
# List topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume messages
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic hospital-transactions --from-beginning --max-messages 5
```

## System Architecture Quick Reference

```
Producer (generates data)
    ↓
Kafka (streams data)
    ↓
Risk Processor (analyzes & scores)
    ↓
PostgreSQL (stores results)
    ↓
Dashboard (visualizes data)
```

## Getting Help

1. Check the main [README.md](README.md) for detailed documentation
2. Review logs: `docker-compose logs`
3. Verify services: `docker-compose ps`
4. Check resource usage: `docker stats`

## Success Checklist

- [ ] Docker Desktop is running
- [ ] All services started successfully (`docker-compose ps` shows all "Up")
- [ ] Dashboard accessible at http://localhost:8501
- [ ] Transaction count increasing in dashboard
- [ ] Alerts appearing for high-risk transactions
- [ ] Charts updating in real-time

If all checkboxes are ✅, congratulations! Your system is running perfectly! 🎉

## Performance Tips

### For Better Performance:
- Allocate more RAM to Docker (Docker Settings → Resources)
- Increase CPU cores for Docker
- Use SSD for Docker volumes
- Close unnecessary applications

### For Load Testing:
```yaml
# Edit docker-compose.yml
producer:
  environment:
    TRANSACTION_RATE: 100  # 100 transactions/second
```

---

**Need more help?** See the full [README.md](README.md) for comprehensive documentation.

