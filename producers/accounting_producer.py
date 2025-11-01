"""
Kafka Producer for Hospital Accounting Transactions
Continuously generates and publishes transactions to Kafka
"""

import os
import sys
import json
import time
import logging
from typing import Dict
from kafka import KafkaProducer
from kafka.errors import KafkaError
from data_generator import HospitalTransactionGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HospitalTransactionProducer:
    """Kafka producer for hospital accounting transactions"""
    
    def __init__(
        self,
        bootstrap_servers: str = 'localhost:9092',
        topic: str = 'hospital-transactions',
        transaction_rate: int = 10,
        anomaly_rate: float = 0.15
    ):
        """
        Initialize the Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Kafka topic to publish to
            transaction_rate: Transactions per second
            anomaly_rate: Probability of anomalous transactions
        """
        self.topic = topic
        self.transaction_rate = transaction_rate
        self.interval = 1.0 / transaction_rate
        
        # Initialize Kafka producer with retry configuration
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=5,
                max_in_flight_requests_per_connection=1,
                compression_type='gzip',
                linger_ms=10,
                batch_size=16384
            )
            logger.info(f"Connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise
        
        # Initialize transaction generator
        self.generator = HospitalTransactionGenerator(
            num_users=50,
            anomaly_rate=anomaly_rate
        )
        
        self.transaction_count = 0
        self.anomaly_count = 0
        self.error_count = 0
        
    def on_send_success(self, record_metadata):
        """Callback for successful message delivery"""
        logger.debug(
            f"Message delivered to {record_metadata.topic} "
            f"partition {record_metadata.partition} "
            f"offset {record_metadata.offset}"
        )
    
    def on_send_error(self, excp):
        """Callback for failed message delivery"""
        logger.error(f"Failed to deliver message: {excp}")
        self.error_count += 1
    
    def send_transaction(self, transaction: Dict):
        """
        Send a single transaction to Kafka
        
        Args:
            transaction: Transaction dictionary to send
        """
        try:
            # Use transaction_id as key for partitioning
            key = transaction['transaction_id']
            
            # Send to Kafka asynchronously
            future = self.producer.send(
                self.topic,
                key=key,
                value=transaction
            )
            
            # Add callbacks
            future.add_callback(self.on_send_success)
            future.add_errback(self.on_send_error)
            
            self.transaction_count += 1
            
            if transaction['metadata'].get('is_anomaly'):
                self.anomaly_count += 1
            
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            self.error_count += 1
    
    def run(self, duration_seconds: int = None):
        """
        Run the producer continuously
        
        Args:
            duration_seconds: Run for specified duration (None = infinite)
        """
        logger.info(f"Starting producer - {self.transaction_rate} transactions/sec")
        logger.info(f"Publishing to topic: {self.topic}")
        
        start_time = time.time()
        
        try:
            while True:
                # Check duration limit
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    logger.info("Duration limit reached")
                    break
                
                # Generate and send transaction
                transaction = self.generator.generate_transaction()
                self.send_transaction(transaction)
                
                # Log progress every 100 transactions
                if self.transaction_count % 100 == 0:
                    self.log_statistics()
                
                # Rate limiting
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("Producer interrupted by user")
        except Exception as e:
            logger.error(f"Producer error: {e}")
        finally:
            self.close()
    
    def log_statistics(self):
        """Log current statistics"""
        anomaly_rate = (self.anomaly_count / self.transaction_count * 100) if self.transaction_count > 0 else 0
        logger.info(
            f"Stats - Total: {self.transaction_count}, "
            f"Anomalies: {self.anomaly_count} ({anomaly_rate:.1f}%), "
            f"Errors: {self.error_count}"
        )
    
    def close(self):
        """Close the producer and flush remaining messages"""
        logger.info("Closing producer...")
        self.log_statistics()
        
        try:
            # Flush any pending messages
            self.producer.flush(timeout=10)
            self.producer.close()
            logger.info("Producer closed successfully")
        except Exception as e:
            logger.error(f"Error closing producer: {e}")


def main():
    """Main entry point"""
    # Get configuration from environment variables
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    topic = os.getenv('KAFKA_TOPIC', 'hospital-transactions')
    transaction_rate = int(os.getenv('TRANSACTION_RATE', '10'))
    anomaly_rate = float(os.getenv('ANOMALY_RATE', '0.15'))
    
    logger.info("Hospital Transaction Producer")
    logger.info("=" * 60)
    logger.info(f"Kafka Brokers: {bootstrap_servers}")
    logger.info(f"Topic: {topic}")
    logger.info(f"Transaction Rate: {transaction_rate}/sec")
    logger.info(f"Anomaly Rate: {anomaly_rate * 100}%")
    logger.info("=" * 60)
    
    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    time.sleep(15)
    
    # Create and run producer
    try:
        producer = HospitalTransactionProducer(
            bootstrap_servers=bootstrap_servers,
            topic=topic,
            transaction_rate=transaction_rate,
            anomaly_rate=anomaly_rate
        )
        
        producer.run()
        
    except Exception as e:
        logger.error(f"Failed to start producer: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

