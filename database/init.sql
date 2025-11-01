-- Hospital Risk Management Database Schema
-- Initialize database for real-time risk detection system

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    description TEXT,
    risk_score DECIMAL(5, 2) DEFAULT 0.0,
    risk_level VARCHAR(20) DEFAULT 'low',
    is_anomaly BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create risk_alerts table
CREATE TABLE IF NOT EXISTS risk_alerts (
    alert_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) REFERENCES transactions(transaction_id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    risk_score DECIMAL(5, 2) NOT NULL,
    alert_message TEXT NOT NULL,
    detection_rules TEXT[],
    status VARCHAR(20) DEFAULT 'active',
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create user_profiles table for behavior baselines
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(50) PRIMARY KEY,
    total_transactions INTEGER DEFAULT 0,
    avg_transaction_amount DECIMAL(15, 2) DEFAULT 0.0,
    max_transaction_amount DECIMAL(15, 2) DEFAULT 0.0,
    typical_departments TEXT[],
    typical_hours INTEGER[],
    risk_history JSONB,
    baseline_score DECIMAL(5, 2) DEFAULT 50.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    event_data JSONB,
    severity VARCHAR(20) DEFAULT 'info',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transaction_patterns table for ML features
CREATE TABLE IF NOT EXISTS transaction_patterns (
    pattern_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_description TEXT,
    frequency INTEGER DEFAULT 1,
    last_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    risk_indicator BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create system_metrics table for monitoring
CREATE TABLE IF NOT EXISTS system_metrics (
    metric_id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15, 2) NOT NULL,
    metric_unit VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance optimization
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp DESC);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_risk_score ON transactions(risk_score DESC);
CREATE INDEX idx_transactions_risk_level ON transactions(risk_level);
CREATE INDEX idx_transactions_is_anomaly ON transactions(is_anomaly);
CREATE INDEX idx_transactions_department ON transactions(department);

CREATE INDEX idx_risk_alerts_severity ON risk_alerts(severity);
CREATE INDEX idx_risk_alerts_status ON risk_alerts(status);
CREATE INDEX idx_risk_alerts_created_at ON risk_alerts(created_at DESC);
CREATE INDEX idx_risk_alerts_transaction_id ON risk_alerts(transaction_id);

CREATE INDEX idx_user_profiles_baseline_score ON user_profiles(baseline_score);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_event_type ON audit_log(event_type);

CREATE INDEX idx_transaction_patterns_user_id ON transaction_patterns(user_id);
CREATE INDEX idx_transaction_patterns_pattern_type ON transaction_patterns(pattern_type);

CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp DESC);
CREATE INDEX idx_system_metrics_metric_name ON system_metrics(metric_name);

-- Create views for analytics
CREATE OR REPLACE VIEW high_risk_transactions AS
SELECT 
    t.transaction_id,
    t.timestamp,
    t.user_id,
    t.department,
    t.transaction_type,
    t.amount,
    t.risk_score,
    t.risk_level
FROM transactions t
WHERE t.risk_score >= 70
ORDER BY t.timestamp DESC;

CREATE OR REPLACE VIEW recent_alerts AS
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
    t.amount,
    t.department
FROM risk_alerts a
JOIN transactions t ON a.transaction_id = t.transaction_id
WHERE a.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY a.created_at DESC;

CREATE OR REPLACE VIEW transaction_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_amount,
    AVG(risk_score) AS avg_risk_score,
    COUNT(CASE WHEN is_anomaly = TRUE THEN 1 END) AS anomaly_count
FROM transactions
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

CREATE OR REPLACE VIEW user_risk_summary AS
SELECT 
    user_id,
    COUNT(*) AS total_transactions,
    AVG(risk_score) AS avg_risk_score,
    MAX(risk_score) AS max_risk_score,
    COUNT(CASE WHEN is_anomaly = TRUE THEN 1 END) AS anomaly_count,
    MAX(timestamp) AS last_transaction
FROM transactions
GROUP BY user_id
ORDER BY avg_risk_score DESC;

-- Insert initial audit log entry
INSERT INTO audit_log (event_type, event_source, event_data, severity)
VALUES ('SYSTEM_INIT', 'database', '{"message": "Database schema initialized successfully"}', 'info');

-- Insert system metrics initialization
INSERT INTO system_metrics (metric_name, metric_value, metric_unit)
VALUES 
    ('transactions_processed', 0, 'count'),
    ('alerts_generated', 0, 'count'),
    ('avg_processing_time', 0, 'milliseconds');

-- Create function to update user profiles
CREATE OR REPLACE FUNCTION update_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (user_id, total_transactions, avg_transaction_amount, max_transaction_amount)
    VALUES (NEW.user_id, 1, NEW.amount, NEW.amount)
    ON CONFLICT (user_id) 
    DO UPDATE SET
        total_transactions = user_profiles.total_transactions + 1,
        avg_transaction_amount = (user_profiles.avg_transaction_amount * user_profiles.total_transactions + NEW.amount) / (user_profiles.total_transactions + 1),
        max_transaction_amount = GREATEST(user_profiles.max_transaction_amount, NEW.amount),
        last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic user profile updates
CREATE TRIGGER update_user_profile_trigger
AFTER INSERT ON transactions
FOR EACH ROW
EXECUTE FUNCTION update_user_profile();

-- Create function to clean old data (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete transactions older than 90 days
    DELETE FROM transactions WHERE timestamp < NOW() - INTERVAL '90 days';
    
    -- Delete audit logs older than 30 days
    DELETE FROM audit_log WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- Delete system metrics older than 7 days
    DELETE FROM system_metrics WHERE timestamp < NOW() - INTERVAL '7 days';
    
    -- Log cleanup event
    INSERT INTO audit_log (event_type, event_source, event_data, severity)
    VALUES ('DATA_CLEANUP', 'database', '{"message": "Old data cleaned up"}', 'info');
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE transactions IS 'Stores all hospital accounting transactions with risk scores';
COMMENT ON TABLE risk_alerts IS 'High-risk transactions requiring review';
COMMENT ON TABLE user_profiles IS 'User behavior baselines for anomaly detection';
COMMENT ON TABLE audit_log IS 'System events and actions audit trail';
COMMENT ON TABLE transaction_patterns IS 'Detected patterns in transaction behavior';
COMMENT ON TABLE system_metrics IS 'System performance and monitoring metrics';

