"""
Kafka Consumer for Risk Detection and Scoring
Consumes transactions, calculates risk scores, and stores results
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, List
import psycopg2
from psycopg2.extras import execute_values
from kafka import KafkaConsumer
from kafka import KafkaProducer
from kafka.errors import KafkaError
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RiskDetectionEngine:
    """Risk detection and scoring engine"""
    
    def __init__(self):
        self.transaction_history = {}
        self.user_baselines = {}
        
    def calculate_risk_score(self, transaction: Dict) -> Dict:
        """
        Calculate risk score for a transaction
        
        Returns:
            Dict with risk_score, risk_level, is_anomaly, detection_rules
        """
        risk_score = 0.0
        detection_rules = []
        
        # Rule 1: Amount-based risk (0-25 points)
        amount_risk = self._check_amount_risk(transaction)
        risk_score += amount_risk['score']
        if amount_risk['triggered']:
            detection_rules.append(amount_risk['rule'])
        
        # Rule 2: Time-based risk (0-20 points)
        time_risk = self._check_time_risk(transaction)
        risk_score += time_risk['score']
        if time_risk['triggered']:
            detection_rules.append(time_risk['rule'])
        
        # Rule 3: Frequency risk (0-25 points)
        frequency_risk = self._check_frequency_risk(transaction)
        risk_score += frequency_risk['score']
        if frequency_risk['triggered']:
            detection_rules.append(frequency_risk['rule'])
        
        # Rule 4: User behavior risk (0-20 points)
        behavior_risk = self._check_behavior_risk(transaction)
        risk_score += behavior_risk['score']
        if behavior_risk['triggered']:
            detection_rules.append(behavior_risk['rule'])
        
        # Rule 5: Metadata-based risk (0-10 points)
        metadata_risk = self._check_metadata_risk(transaction)
        risk_score += metadata_risk['score']
        if metadata_risk['triggered']:
            detection_rules.append(metadata_risk['rule'])
        
        # Classify risk level
        if risk_score >= 70:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        is_anomaly = risk_score >= 50
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'is_anomaly': is_anomaly,
            'detection_rules': detection_rules
        }
    
    def _check_amount_risk(self, transaction: Dict) -> Dict:
        """Check if transaction amount is risky"""
        amount = transaction['amount']
        transaction_type = transaction['transaction_type']
        
        # Define high-risk thresholds by transaction type
        high_risk_thresholds = {
            'billing': 100000,
            'payment': 50000,
            'refund': 10000,
            'transfer': 200000,
            'adjustment': 20000,
            'insurance_claim': 500000,
            'payroll': 30000,
            'procurement': 100000
        }
        
        threshold = high_risk_thresholds.get(transaction_type, 50000)
        
        if amount > threshold * 2:
            return {'score': 25, 'triggered': True, 'rule': 'AMOUNT_EXTREMELY_HIGH'}
        elif amount > threshold:
            return {'score': 15, 'triggered': True, 'rule': 'AMOUNT_HIGH'}
        elif amount > threshold * 0.5:
            return {'score': 5, 'triggered': False, 'rule': None}
        else:
            return {'score': 0, 'triggered': False, 'rule': None}
    
    def _check_time_risk(self, transaction: Dict) -> Dict:
        """Check if transaction time is suspicious"""
        try:
            timestamp = datetime.fromisoformat(transaction['timestamp'])
            hour = timestamp.hour
            weekday = timestamp.weekday()
            
            # High risk: 11 PM - 5 AM
            if hour >= 23 or hour < 5:
                return {'score': 20, 'triggered': True, 'rule': 'TRANSACTION_OFF_HOURS_NIGHT'}
            
            # Medium risk: 6 PM - 11 PM or 5 AM - 7 AM
            elif (18 <= hour < 23) or (5 <= hour < 8):
                return {'score': 10, 'triggered': True, 'rule': 'TRANSACTION_OFF_HOURS'}
            
            # Weekend transactions
            elif weekday >= 5:
                return {'score': 8, 'triggered': True, 'rule': 'TRANSACTION_WEEKEND'}
            
            else:
                return {'score': 0, 'triggered': False, 'rule': None}
                
        except Exception as e:
            logger.warning(f"Error checking time risk: {e}")
            return {'score': 0, 'triggered': False, 'rule': None}
    
    def _check_frequency_risk(self, transaction: Dict) -> Dict:
        """Check transaction frequency for the user"""
        user_id = transaction['user_id']
        
        # Track transactions per user
        if user_id not in self.transaction_history:
            self.transaction_history[user_id] = []
        
        # Add current transaction
        self.transaction_history[user_id].append({
            'timestamp': transaction['timestamp'],
            'amount': transaction['amount']
        })
        
        # Keep only recent transactions (last 1 hour)
        current_time = datetime.now()
        self.transaction_history[user_id] = [
            t for t in self.transaction_history[user_id]
            if (current_time - datetime.fromisoformat(t['timestamp'])).seconds < 3600
        ]
        
        recent_count = len(self.transaction_history[user_id])
        
        # Rapid succession detection
        if recent_count > 20:
            return {'score': 25, 'triggered': True, 'rule': 'HIGH_FREQUENCY_EXTREME'}
        elif recent_count > 10:
            return {'score': 15, 'triggered': True, 'rule': 'HIGH_FREQUENCY'}
        elif recent_count > 5:
            return {'score': 8, 'triggered': True, 'rule': 'MODERATE_FREQUENCY'}
        else:
            return {'score': 0, 'triggered': False, 'rule': None}
    
    def _check_behavior_risk(self, transaction: Dict) -> Dict:
        """Check if transaction deviates from user's normal behavior"""
        user_id = transaction['user_id']
        
        # Build user baseline if not exists
        if user_id not in self.user_baselines:
            self.user_baselines[user_id] = {
                'amounts': [],
                'types': set(),
                'departments': set()
            }
        
        baseline = self.user_baselines[user_id]
        
        # Check if transaction type is unusual for this user
        if baseline['types'] and transaction['transaction_type'] not in baseline['types']:
            type_risk = 10
            type_triggered = True
            type_rule = 'UNUSUAL_TRANSACTION_TYPE'
        else:
            type_risk = 0
            type_triggered = False
            type_rule = None
        
        # Check if department is unusual for this user
        if baseline['departments'] and transaction['department'] not in baseline['departments']:
            dept_risk = 5
        else:
            dept_risk = 0
        
        # Statistical outlier detection on amount
        if len(baseline['amounts']) > 10:
            amounts = np.array(baseline['amounts'])
            mean = np.mean(amounts)
            std = np.std(amounts)
            z_score = abs((transaction['amount'] - mean) / (std + 1e-6))
            
            if z_score > 3:
                amount_risk = 10
            elif z_score > 2:
                amount_risk = 5
            else:
                amount_risk = 0
        else:
            amount_risk = 0
        
        # Update baseline
        baseline['amounts'].append(transaction['amount'])
        baseline['types'].add(transaction['transaction_type'])
        baseline['departments'].add(transaction['department'])
        
        # Keep baseline size manageable
        if len(baseline['amounts']) > 100:
            baseline['amounts'] = baseline['amounts'][-100:]
        
        total_risk = type_risk + dept_risk + amount_risk
        
        return {
            'score': min(total_risk, 20),
            'triggered': type_triggered,
            'rule': type_rule
        }
    
    def _check_metadata_risk(self, transaction: Dict) -> Dict:
        """Check metadata for risk indicators"""
        metadata = transaction.get('metadata', {})
        
        # Check if marked as anomaly in metadata (from generator)
        if metadata.get('is_anomaly'):
            anomaly_type = metadata.get('anomaly_type', 'UNKNOWN')
            return {'score': 10, 'triggered': True, 'rule': f'METADATA_ANOMALY_{anomaly_type.upper()}'}
        
        # Check for suspicious account patterns
        account_id = transaction.get('account_id', '')
        if 'SUSP' in account_id:
            return {'score': 10, 'triggered': True, 'rule': 'SUSPICIOUS_ACCOUNT'}
        
        return {'score': 0, 'triggered': False, 'rule': None}


class RiskConsumer:
    """Kafka consumer for risk detection"""
    
    def __init__(
        self,
        bootstrap_servers: str,
        input_topic: str,
        output_topic: str,
        alerts_topic: str,
        group_id: str,
        postgres_config: Dict
    ):
        """Initialize the risk consumer"""
        
        # Kafka consumer
        try:
            self.consumer = KafkaConsumer(
                input_topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                max_poll_records=100
            )
            logger.info(f"Connected to Kafka consumer at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka consumer: {e}")
            raise
        
        # Kafka producer for risk scores and alerts
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all'
            )
            logger.info("Connected to Kafka producer")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka producer: {e}")
            raise
        
        self.output_topic = output_topic
        self.alerts_topic = alerts_topic
        
        # PostgreSQL connection
        self.postgres_config = postgres_config
        self.db_conn = None
        self.connect_to_database()
        
        # Risk detection engine
        self.risk_engine = RiskDetectionEngine()
        
        self.processed_count = 0
        self.alert_count = 0
        
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(**self.postgres_config)
            self.db_conn.autocommit = False
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def store_transaction(self, transaction: Dict, risk_result: Dict):
        """Store transaction with risk score in database"""
        try:
            cursor = self.db_conn.cursor()
            
            insert_query = """
                INSERT INTO transactions (
                    transaction_id, timestamp, user_id, account_id, department,
                    transaction_type, amount, description, risk_score, risk_level,
                    is_anomaly, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (transaction_id) DO UPDATE SET
                    risk_score = EXCLUDED.risk_score,
                    risk_level = EXCLUDED.risk_level,
                    is_anomaly = EXCLUDED.is_anomaly,
                    processed_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(insert_query, (
                transaction['transaction_id'],
                transaction['timestamp'],
                transaction['user_id'],
                transaction['account_id'],
                transaction['department'],
                transaction['transaction_type'],
                transaction['amount'],
                transaction.get('description', ''),
                risk_result['risk_score'],
                risk_result['risk_level'],
                risk_result['is_anomaly'],
                json.dumps(transaction.get('metadata', {}))
            ))
            
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error storing transaction: {e}")
            self.db_conn.rollback()
            self.connect_to_database()
    
    def store_alert(self, transaction: Dict, risk_result: Dict):
        """Store high-risk alert in database"""
        try:
            cursor = self.db_conn.cursor()
            
            alert_message = f"High-risk {transaction['transaction_type']} transaction of ${transaction['amount']:,.2f} by {transaction['user_id']}"
            
            insert_query = """
                INSERT INTO risk_alerts (
                    transaction_id, alert_type, severity, risk_score,
                    alert_message, detection_rules, metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            severity = 'critical' if risk_result['risk_score'] >= 85 else 'high'
            
            cursor.execute(insert_query, (
                transaction['transaction_id'],
                'ANOMALY_DETECTED',
                severity,
                risk_result['risk_score'],
                alert_message,
                risk_result['detection_rules'],
                json.dumps(transaction.get('metadata', {}))
            ))
            
            self.db_conn.commit()
            cursor.close()
            
            self.alert_count += 1
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
            self.db_conn.rollback()
    
    def process_message(self, message):
        """Process a single message"""
        try:
            transaction = message.value
            
            # Calculate risk score
            risk_result = self.risk_engine.calculate_risk_score(transaction)
            
            # Combine transaction with risk result
            enriched_transaction = {
                **transaction,
                'risk_score': risk_result['risk_score'],
                'risk_level': risk_result['risk_level'],
                'is_anomaly': risk_result['is_anomaly'],
                'detection_rules': risk_result['detection_rules'],
                'processed_timestamp': datetime.now().isoformat()
            }
            
            # Publish to risk-scores topic
            self.producer.send(self.output_topic, value=enriched_transaction)
            
            # Store in database
            self.store_transaction(transaction, risk_result)
            
            # If high risk, publish alert
            if risk_result['risk_level'] == 'high':
                alert = {
                    'transaction_id': transaction['transaction_id'],
                    'alert_type': 'HIGH_RISK_TRANSACTION',
                    'severity': 'critical' if risk_result['risk_score'] >= 85 else 'high',
                    'risk_score': risk_result['risk_score'],
                    'detection_rules': risk_result['detection_rules'],
                    'transaction': enriched_transaction,
                    'alert_timestamp': datetime.now().isoformat()
                }
                
                self.producer.send(self.alerts_topic, value=alert)
                self.store_alert(transaction, risk_result)
                
                logger.warning(
                    f"⚠️  HIGH RISK ALERT - Transaction {transaction['transaction_id']}: "
                    f"Score={risk_result['risk_score']}, Rules={risk_result['detection_rules']}"
                )
            
            self.processed_count += 1
            
            if self.processed_count % 100 == 0:
                logger.info(
                    f"Processed: {self.processed_count}, "
                    f"Alerts: {self.alert_count} "
                    f"({self.alert_count/self.processed_count*100:.1f}%)"
                )
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def run(self):
        """Run the consumer"""
        logger.info("Starting risk consumer...")
        
        try:
            for message in self.consumer:
                self.process_message(message)
                
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close connections"""
        logger.info("Closing consumer...")
        
        try:
            self.consumer.close()
            self.producer.close()
            if self.db_conn:
                self.db_conn.close()
            logger.info("Consumer closed successfully")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")


def main():
    """Main entry point"""
    # Get configuration from environment
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    
    postgres_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'database': os.getenv('POSTGRES_DB', 'hospital_risk_db'),
        'user': os.getenv('POSTGRES_USER', 'hospital_admin'),
        'password': os.getenv('POSTGRES_PASSWORD', 'hospital_pass123')
    }
    
    logger.info("Hospital Risk Consumer")
    logger.info("=" * 60)
    logger.info(f"Kafka Brokers: {bootstrap_servers}")
    logger.info(f"Database: {postgres_config['host']}:{postgres_config['port']}")
    logger.info("=" * 60)
    
    # Wait for services to be ready
    logger.info("Waiting for services to be ready...")
    time.sleep(20)
    
    # Create and run consumer
    try:
        consumer = RiskConsumer(
            bootstrap_servers=bootstrap_servers,
            input_topic='hospital-transactions',
            output_topic='risk-scores',
            alerts_topic='risk-alerts',
            group_id='risk-detection-group',
            postgres_config=postgres_config
        )
        
        consumer.run()
        
    except Exception as e:
        logger.error(f"Failed to start consumer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

