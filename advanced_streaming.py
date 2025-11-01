"""
Advanced Big Data Streaming with PySpark, Kafka, Flink Integration
Real-time stream processing for hospital risk management
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import threading

# Try to import PySpark
try:
    from pyspark.sql import SparkSession
    from pyspark.sql.functions import col, from_json, to_json, struct, window, avg, count, sum as _sum
    from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
    PYSPARK_AVAILABLE = True
except ImportError:
    print("PySpark not installed. Install with: pip install pyspark")
    PYSPARK_AVAILABLE = False

# Try to import Kafka
try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.admin import KafkaAdminClient, NewTopic
    KAFKA_AVAILABLE = True
except ImportError:
    print("Kafka-python not installed. Install with: pip install kafka-python")
    KAFKA_AVAILABLE = False

import pandas as pd
import numpy as np

# Add paths
sys.path.insert(0, str(Path('producers')))
from data_generator import HospitalTransactionGenerator


class BigDataStreamProcessor:
    """
    Advanced Big Data Stream Processor
    Integrates: PySpark Structured Streaming, Kafka, Flink-style processing
    """
    
    def __init__(self, kafka_bootstrap='localhost:9092'):
        self.kafka_bootstrap = kafka_bootstrap
        self.generator = HospitalTransactionGenerator(num_users=50, anomaly_rate=0.15)
        self.running = False
        
        # Initialize Spark if available
        if PYSPARK_AVAILABLE:
            self.spark = self._init_spark()
        else:
            self.spark = None
            
        # Initialize Kafka if available
        if KAFKA_AVAILABLE:
            self.producer = self._init_kafka_producer()
            self.consumer = None
        else:
            self.producer = None
            
        # In-memory buffer for Kafka-less mode
        self.buffer = []
        
    def _init_spark(self):
        """Initialize Spark Session with Structured Streaming"""
        print("Initializing PySpark Structured Streaming...")
        
        try:
            spark = SparkSession.builder \
                .appName("HospitalRiskStreamProcessor") \
                .config("spark.sql.streaming.checkpointLocation", "./spark-checkpoints") \
                .config("spark.streaming.stopGracefullyOnShutdown", "true") \
                .config("spark.sql.adaptive.enabled", "true") \
                .config("spark.sql.shuffle.partitions", "3") \
                .master("local[*]") \
                .getOrCreate()
            
            spark.sparkContext.setLogLevel("WARN")
            print("✓ PySpark initialized successfully")
            return spark
        except Exception as e:
            print(f"Error initializing Spark: {e}")
            return None
    
    def _init_kafka_producer(self):
        """Initialize Kafka Producer"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.kafka_bootstrap,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            print(f"✓ Kafka Producer connected to {self.kafka_bootstrap}")
            return producer
        except Exception as e:
            print(f"Note: Kafka not available ({e}), using in-memory buffer")
            return None
    
    def create_kafka_topics(self):
        """Create Kafka topics if Kafka is available"""
        if not KAFKA_AVAILABLE:
            return
            
        try:
            admin = KafkaAdminClient(bootstrap_servers=self.kafka_bootstrap)
            
            topics = [
                NewTopic(name='hospital-transactions', num_partitions=3, replication_factor=1),
                NewTopic(name='risk-scores', num_partitions=3, replication_factor=1),
                NewTopic(name='risk-alerts', num_partitions=3, replication_factor=1),
            ]
            
            admin.create_topics(new_topics=topics, validate_only=False)
            print("✓ Kafka topics created: hospital-transactions, risk-scores, risk-alerts")
        except Exception as e:
            print(f"Topics may already exist: {e}")
    
    def produce_to_kafka(self, transaction):
        """Produce transaction to Kafka"""
        if self.producer:
            try:
                self.producer.send('hospital-transactions', value=transaction)
                return True
            except Exception as e:
                print(f"Error producing to Kafka: {e}")
                return False
        else:
            # Use in-memory buffer
            self.buffer.append(transaction)
            return True
    
    def calculate_risk_with_spark(self, transactions_df):
        """
        Calculate risk scores using PySpark DataFrame operations
        Simulates Flink-style stream processing
        """
        if not self.spark:
            return None
        
        try:
            # Convert to Spark DataFrame
            spark_df = self.spark.createDataFrame(transactions_df)
            
            # Flink-style windowed aggregations
            # 1. Calculate per-user statistics
            user_stats = spark_df.groupBy("user_id").agg(
                count("*").alias("tx_count"),
                avg("amount").alias("avg_amount"),
                _sum("amount").alias("total_amount")
            )
            
            # 2. Calculate per-department statistics
            dept_stats = spark_df.groupBy("department").agg(
                count("*").alias("dept_tx_count"),
                avg("amount").alias("dept_avg_amount")
            )
            
            # 3. Risk scoring with Spark SQL
            spark_df.createOrReplaceTempView("transactions")
            
            risk_query = """
            SELECT 
                transaction_id,
                user_id,
                department,
                amount,
                transaction_type,
                CASE 
                    WHEN amount > 200000 THEN 95
                    WHEN amount > 100000 THEN 75
                    WHEN amount > 50000 THEN 50
                    ELSE 25
                END as risk_score,
                CASE 
                    WHEN amount > 200000 THEN 'high'
                    WHEN amount > 100000 THEN 'high'
                    WHEN amount > 50000 THEN 'medium'
                    ELSE 'low'
                END as risk_level
            FROM transactions
            """
            
            risk_df = self.spark.sql(risk_query)
            
            return {
                'risk_scores': risk_df.toPandas(),
                'user_stats': user_stats.toPandas(),
                'dept_stats': dept_stats.toPandas()
            }
        except Exception as e:
            print(f"Error in Spark processing: {e}")
            return None
    
    def flink_style_windowing(self, transactions_df, window_size='5 seconds'):
        """
        Simulate Flink-style time-windowed processing
        """
        if not self.spark:
            return None
        
        try:
            spark_df = self.spark.createDataFrame(transactions_df)
            spark_df = spark_df.withColumn("timestamp", col("timestamp").cast(TimestampType()))
            
            # Time-windowed aggregations (Flink-style)
            windowed_df = spark_df \
                .groupBy(window(col("timestamp"), window_size)) \
                .agg(
                    count("*").alias("window_count"),
                    avg("amount").alias("window_avg_amount"),
                    avg("risk_score").alias("window_avg_risk")
                )
            
            return windowed_df.toPandas()
        except Exception as e:
            print(f"Error in windowing: {e}")
            return None
    
    def start_streaming_producer(self, duration=60, rate=10):
        """
        Start continuous data streaming (Kafka Producer / Flume-style)
        
        Args:
            duration: How long to stream (seconds)
            rate: Transactions per second
        """
        print(f"\n{'='*70}")
        print("STARTING BIG DATA STREAM PRODUCER")
        print(f"{'='*70}")
        print(f"Rate: {rate} transactions/second")
        print(f"Duration: {duration} seconds")
        print(f"Target: {'Kafka' if self.producer else 'In-Memory Buffer'}")
        print()
        
        self.running = True
        count = 0
        start_time = time.time()
        
        try:
            while self.running and (time.time() - start_time) < duration:
                # Generate transaction
                transaction = self.generator.generate_transaction()
                
                # Add processing metadata
                transaction['stream_metadata'] = {
                    'producer_timestamp': datetime.now().isoformat(),
                    'partition': count % 3,  # Simulate Kafka partitioning
                    'offset': count
                }
                
                # Produce to stream
                self.produce_to_kafka(transaction)
                count += 1
                
                if count % 10 == 0:
                    elapsed = time.time() - start_time
                    actual_rate = count / elapsed if elapsed > 0 else 0
                    print(f"Produced {count} messages | Rate: {actual_rate:.1f} msg/sec")
                
                # Rate limiting
                time.sleep(1.0 / rate)
                
        except KeyboardInterrupt:
            print("\nStreaming stopped by user")
        
        self.running = False
        elapsed = time.time() - start_time
        
        print(f"\n{'='*70}")
        print("STREAMING COMPLETE")
        print(f"{'='*70}")
        print(f"Total Messages: {count}")
        print(f"Elapsed Time: {elapsed:.2f} seconds")
        print(f"Average Rate: {count/elapsed:.1f} msg/sec")
        print()
        
        return count
    
    def process_with_pyspark(self):
        """
        Process buffered data with PySpark
        """
        if not self.buffer:
            print("No data in buffer")
            return None
        
        print(f"\n{'='*70}")
        print("PROCESSING WITH PYSPARK")
        print(f"{'='*70}")
        print(f"Records to process: {len(self.buffer)}")
        
        # Convert buffer to DataFrame
        df = pd.DataFrame(self.buffer)
        
        # Add risk scores
        df['risk_score'] = df['amount'].apply(
            lambda x: 95 if x > 200000 else (75 if x > 100000 else (50 if x > 50000 else 25))
        )
        df['risk_level'] = df['risk_score'].apply(
            lambda x: 'high' if x >= 70 else ('medium' if x >= 30 else 'low')
        )
        
        # Process with Spark
        if self.spark:
            results = self.calculate_risk_with_spark(df)
            
            if results:
                print("\n✓ PySpark Processing Complete")
                print(f"  Risk Scores Calculated: {len(results['risk_scores'])}")
                print(f"  Unique Users: {len(results['user_stats'])}")
                print(f"  Unique Departments: {len(results['dept_stats'])}")
                
                # Show top risky transactions
                print("\n📊 Top 5 High-Risk Transactions:")
                top_risk = results['risk_scores'].nlargest(5, 'risk_score')
                print(top_risk[['transaction_id', 'user_id', 'amount', 'risk_score', 'risk_level']].to_string(index=False))
                
                # Show user statistics
                print("\n👤 User Statistics (Top 5 by transaction count):")
                top_users = results['user_stats'].nlargest(5, 'tx_count')
                print(top_users.to_string(index=False))
                
                return results
        
        return df
    
    def demonstrate_flink_processing(self):
        """
        Demonstrate Flink-style stream processing concepts
        """
        print(f"\n{'='*70}")
        print("FLINK-STYLE STREAM PROCESSING DEMO")
        print(f"{'='*70}")
        
        if not self.buffer:
            print("No data available. Run producer first.")
            return
        
        df = pd.DataFrame(self.buffer)
        
        # Add timestamps if not present
        if 'timestamp' not in df.columns or pd.isna(df['timestamp']).any():
            df['timestamp'] = pd.date_range(start=datetime.now(), periods=len(df), freq='100ms')
        
        # Add risk scores
        df['risk_score'] = df['amount'].apply(
            lambda x: 95 if x > 200000 else (75 if x > 100000 else (50 if x > 50000 else 25))
        )
        
        print("\n🔄 Windowed Aggregations (Flink-style):")
        
        # Simulate Flink windows
        if self.spark:
            windowed = self.flink_style_windowing(df)
            if windowed is not None and len(windowed) > 0:
                print(windowed.to_string(index=False))
        else:
            # Manual windowing
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # 5-second windows
            windowed = df.resample('5S').agg({
                'amount': ['count', 'mean', 'sum'],
                'risk_score': 'mean'
            })
            
            print(windowed.head(10))
        
        print("\n✓ Flink-style processing complete")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.producer:
            self.producer.close()
        if self.spark:
            self.spark.stop()


def main():
    """
    Main demonstration of Big Data streaming technologies
    """
    print("="*70)
    print("BIG DATA STREAMING DEMO")
    print("Hospital Risk Management with PySpark, Kafka, Flink")
    print("="*70)
    print()
    
    # Check available technologies
    print("🔍 Checking Available Technologies:")
    print(f"  PySpark: {'✓ Available' if PYSPARK_AVAILABLE else '✗ Not installed'}")
    print(f"  Kafka: {'✓ Available' if KAFKA_AVAILABLE else '✗ Not installed'}")
    print()
    
    if not PYSPARK_AVAILABLE:
        print("💡 To enable PySpark: pip install pyspark")
    if not KAFKA_AVAILABLE:
        print("💡 To enable Kafka: pip install kafka-python")
    
    print()
    
    # Initialize processor
    processor = BigDataStreamProcessor()
    
    try:
        # Step 1: Stream data production (Kafka/Flume-style)
        print("STEP 1: Data Stream Production")
        processor.start_streaming_producer(duration=10, rate=10)  # 10 seconds, 10 tx/sec
        
        # Step 2: Process with PySpark
        print("\nSTEP 2: Batch Processing with PySpark")
        results = processor.process_with_pyspark()
        
        # Step 3: Demonstrate Flink-style processing
        print("\nSTEP 3: Stream Processing (Flink-style)")
        processor.demonstrate_flink_processing()
        
        # Step 4: Save results
        if processor.buffer:
            df = pd.DataFrame(processor.buffer)
            output_path = Path('output') / 'bigdata_streaming_results.csv'
            output_path.parent.mkdir(exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"\n✓ Results saved to: {output_path}")
        
        print(f"\n{'='*70}")
        print("DEMO COMPLETE!")
        print(f"{'='*70}")
        print("\n📊 Summary:")
        print(f"  Total messages processed: {len(processor.buffer)}")
        print(f"  Technologies demonstrated:")
        print(f"    • Kafka-style messaging ✓")
        print(f"    • PySpark processing {'✓' if PYSPARK_AVAILABLE else '(simulated)'}")
        print(f"    • Flink-style windowing {'✓' if PYSPARK_AVAILABLE else '(manual)'}")
        print(f"    • Stream partitioning ✓")
        print(f"    • Real-time aggregations ✓")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        processor.cleanup()


if __name__ == "__main__":
    main()

