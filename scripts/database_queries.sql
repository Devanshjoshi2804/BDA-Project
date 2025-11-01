-- Hospital Risk Management System
-- Useful Database Queries

-- ========================================
-- Transaction Statistics
-- ========================================

-- Total transaction count by risk level
SELECT 
    risk_level,
    COUNT(*) as count,
    ROUND(AVG(risk_score), 2) as avg_risk_score,
    ROUND(AVG(amount), 2) as avg_amount
FROM transactions
GROUP BY risk_level
ORDER BY risk_level;

-- Transactions per hour (last 24 hours)
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as transaction_count,
    ROUND(AVG(risk_score), 2) as avg_risk_score,
    COUNT(CASE WHEN is_anomaly = TRUE THEN 1 END) as anomaly_count
FROM transactions
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;

-- Top 10 highest risk transactions
SELECT 
    transaction_id,
    timestamp,
    user_id,
    department,
    transaction_type,
    amount,
    risk_score,
    risk_level
FROM transactions
ORDER BY risk_score DESC
LIMIT 10;

-- ========================================
-- User Analysis
-- ========================================

-- Top 10 riskiest users
SELECT 
    user_id,
    COUNT(*) as total_transactions,
    ROUND(AVG(risk_score), 2) as avg_risk_score,
    MAX(risk_score) as max_risk_score,
    COUNT(CASE WHEN is_anomaly = TRUE THEN 1 END) as anomaly_count,
    ROUND(SUM(amount), 2) as total_amount
FROM transactions
GROUP BY user_id
ORDER BY avg_risk_score DESC
LIMIT 10;

-- User transaction patterns
SELECT 
    user_id,
    transaction_type,
    COUNT(*) as count,
    ROUND(AVG(amount), 2) as avg_amount,
    ROUND(AVG(risk_score), 2) as avg_risk_score
FROM transactions
GROUP BY user_id, transaction_type
ORDER BY user_id, count DESC;

-- ========================================
-- Department Analysis
-- ========================================

-- Risk by department
SELECT 
    department,
    COUNT(*) as transaction_count,
    ROUND(AVG(risk_score), 2) as avg_risk_score,
    COUNT(CASE WHEN risk_level = 'high' THEN 1 END) as high_risk_count,
    ROUND(SUM(amount), 2) as total_amount
FROM transactions
GROUP BY department
ORDER BY avg_risk_score DESC;

-- Department activity by hour
SELECT 
    department,
    EXTRACT(HOUR FROM timestamp) as hour,
    COUNT(*) as transaction_count
FROM transactions
GROUP BY department, hour
ORDER BY department, hour;

-- ========================================
-- Alert Analysis
-- ========================================

-- Recent high-risk alerts
SELECT 
    a.alert_id,
    a.transaction_id,
    a.alert_type,
    a.severity,
    a.risk_score,
    a.alert_message,
    a.status,
    a.created_at,
    t.user_id,
    t.department,
    t.amount
FROM risk_alerts a
JOIN transactions t ON a.transaction_id = t.transaction_id
ORDER BY a.created_at DESC
LIMIT 20;

-- Alert summary by severity
SELECT 
    severity,
    COUNT(*) as count,
    ROUND(AVG(risk_score), 2) as avg_risk_score
FROM risk_alerts
GROUP BY severity
ORDER BY severity;

-- Alerts by detection rule
SELECT 
    UNNEST(detection_rules) as rule,
    COUNT(*) as count
FROM risk_alerts
GROUP BY rule
ORDER BY count DESC;

-- ========================================
-- Anomaly Detection
-- ========================================

-- Anomaly distribution by type
SELECT 
    metadata->>'anomaly_type' as anomaly_type,
    COUNT(*) as count,
    ROUND(AVG(risk_score), 2) as avg_risk_score
FROM transactions
WHERE is_anomaly = TRUE
GROUP BY anomaly_type
ORDER BY count DESC;

-- Anomalies by time of day
SELECT 
    EXTRACT(HOUR FROM timestamp) as hour,
    COUNT(*) as anomaly_count,
    ROUND(AVG(risk_score), 2) as avg_risk_score
FROM transactions
WHERE is_anomaly = TRUE
GROUP BY hour
ORDER BY hour;

-- ========================================
-- Performance Metrics
-- ========================================

-- Processing throughput (transactions per minute, last hour)
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    COUNT(*) as transactions_per_minute
FROM transactions
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY minute
ORDER BY minute DESC
LIMIT 10;

-- Average processing time
SELECT 
    ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - timestamp))), 2) as avg_processing_time_seconds
FROM transactions
WHERE processed_at IS NOT NULL;

-- System metrics
SELECT 
    metric_name,
    metric_value,
    metric_unit,
    timestamp
FROM system_metrics
ORDER BY timestamp DESC
LIMIT 20;

-- ========================================
-- Data Quality Checks
-- ========================================

-- Check for null values
SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN user_id IS NULL THEN 1 END) as null_user_id,
    COUNT(CASE WHEN amount IS NULL THEN 1 END) as null_amount,
    COUNT(CASE WHEN risk_score IS NULL THEN 1 END) as null_risk_score
FROM transactions;

-- Check for duplicate transactions
SELECT 
    transaction_id,
    COUNT(*) as duplicate_count
FROM transactions
GROUP BY transaction_id
HAVING COUNT(*) > 1;

-- ========================================
-- Audit Trail
-- ========================================

-- Recent system events
SELECT 
    log_id,
    event_type,
    event_source,
    severity,
    timestamp
FROM audit_log
ORDER BY timestamp DESC
LIMIT 20;

-- Event summary by type
SELECT 
    event_type,
    COUNT(*) as count,
    MIN(timestamp) as first_occurrence,
    MAX(timestamp) as last_occurrence
FROM audit_log
GROUP BY event_type
ORDER BY count DESC;

-- ========================================
-- Views
-- ========================================

-- High risk transactions (using view)
SELECT * FROM high_risk_transactions LIMIT 20;

-- Recent alerts (using view)
SELECT * FROM recent_alerts LIMIT 20;

-- Transaction summary (using view)
SELECT * FROM transaction_summary LIMIT 24;

-- User risk summary (using view)
SELECT * FROM user_risk_summary LIMIT 20;

