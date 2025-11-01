"""
Alert Processor - Consumes and processes risk alerts
Monitors high-risk transactions and sends notifications
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict
from kafka import KafkaConsumer
import psycopg2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertProcessor:
    """Process and handle risk alerts"""
    
    def __init__(
        self,
        bootstrap_servers: str,
        alerts_topic: str,
        group_id: str,
        postgres_config: Dict
    ):
        """Initialize the alert processor"""
        
        # Kafka consumer for alerts
        try:
            self.consumer = KafkaConsumer(
                alerts_topic,
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            logger.info(f"Connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
        
        # PostgreSQL connection
        self.postgres_config = postgres_config
        self.db_conn = None
        self.connect_to_database()
        
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
    
    def process_alert(self, alert: Dict):
        """Process a single alert"""
        try:
            transaction = alert.get('transaction', {})
            
            # Log the alert
            logger.warning(
                f"\n{'='*70}\n"
                f"🚨 CRITICAL ALERT 🚨\n"
                f"Transaction ID: {alert['transaction_id']}\n"
                f"Risk Score: {alert['risk_score']:.2f}\n"
                f"Severity: {alert['severity'].upper()}\n"
                f"User: {transaction.get('user_id', 'Unknown')}\n"
                f"Amount: ${transaction.get('amount', 0):,.2f}\n"
                f"Type: {transaction.get('transaction_type', 'Unknown')}\n"
                f"Department: {transaction.get('department', 'Unknown')}\n"
                f"Detection Rules: {', '.join(alert.get('detection_rules', []))}\n"
                f"Time: {alert.get('alert_timestamp', '')}\n"
                f"{'='*70}\n"
            )
            
            # Update alert status in database
            self.update_alert_status(alert)
            
            # Log to audit trail
            self.log_to_audit(alert)
            
            # Send notification (implementation placeholder)
            self.send_notification(alert)
            
            self.alert_count += 1
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    def update_alert_status(self, alert: Dict):
        """Update alert status in database"""
        try:
            cursor = self.db_conn.cursor()
            
            # Find the alert by transaction_id and update
            update_query = """
                UPDATE risk_alerts
                SET status = 'notified',
                    metadata = metadata || %s::jsonb
                WHERE transaction_id = %s
                AND status = 'active'
            """
            
            metadata_update = json.dumps({
                'notified_at': datetime.now().isoformat(),
                'notification_method': 'console_log'
            })
            
            cursor.execute(update_query, (metadata_update, alert['transaction_id']))
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
            self.db_conn.rollback()
    
    def log_to_audit(self, alert: Dict):
        """Log alert to audit trail"""
        try:
            cursor = self.db_conn.cursor()
            
            insert_query = """
                INSERT INTO audit_log (
                    event_type, event_source, event_data, severity
                ) VALUES (
                    %s, %s, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                'RISK_ALERT_PROCESSED',
                'alert_processor',
                json.dumps(alert),
                alert.get('severity', 'high')
            ))
            
            self.db_conn.commit()
            cursor.close()
            
        except Exception as e:
            logger.error(f"Error logging to audit: {e}")
            self.db_conn.rollback()
    
    def send_notification(self, alert: Dict):
        """
        Send notification for the alert
        This is a placeholder - implement actual notification methods
        (email, SMS, webhook, Slack, etc.)
        """
        # In a production system, you would integrate with:
        # - Email service (SMTP, SendGrid, AWS SES)
        # - SMS service (Twilio, AWS SNS)
        # - Messaging platforms (Slack, Teams)
        # - Webhook endpoints
        # - Mobile push notifications
        
        # For now, we just log it prominently
        logger.info(f"📧 Notification sent for alert {alert['transaction_id']}")
    
    def run(self):
        """Run the alert processor"""
        logger.info("Starting alert processor...")
        logger.info("Monitoring for high-risk alerts...")
        
        try:
            for message in self.consumer:
                alert = message.value
                self.process_alert(alert)
                
                if self.alert_count % 10 == 0 and self.alert_count > 0:
                    logger.info(f"Total alerts processed: {self.alert_count}")
                
        except KeyboardInterrupt:
            logger.info("Alert processor interrupted by user")
        except Exception as e:
            logger.error(f"Alert processor error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close connections"""
        logger.info("Closing alert processor...")
        
        try:
            self.consumer.close()
            if self.db_conn:
                self.db_conn.close()
            logger.info(f"Alert processor closed. Total alerts: {self.alert_count}")
        except Exception as e:
            logger.error(f"Error closing alert processor: {e}")


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
    
    logger.info("Hospital Alert Processor")
    logger.info("=" * 60)
    logger.info(f"Kafka Brokers: {bootstrap_servers}")
    logger.info(f"Database: {postgres_config['host']}:{postgres_config['port']}")
    logger.info("=" * 60)
    
    # Wait for services to be ready
    logger.info("Waiting for services to be ready...")
    time.sleep(25)
    
    # Create and run processor
    try:
        processor = AlertProcessor(
            bootstrap_servers=bootstrap_servers,
            alerts_topic='risk-alerts',
            group_id='alert-processor-group',
            postgres_config=postgres_config
        )
        
        processor.run()
        
    except Exception as e:
        logger.error(f"Failed to start alert processor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

