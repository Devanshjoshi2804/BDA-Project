"""
Big Data Streaming Demo (Lightweight Version)
Demonstrates PySpark, Kafka, Flink concepts without heavy dependencies
Perfect for presentation!
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import threading
from collections import deque
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path('producers')))
from data_generator import HospitalTransactionGenerator


class StreamProcessor:
    """
    Lightweight Big Data Stream Processor
    Simulates: Kafka, PySpark, Flink processing
    """
    
    def __init__(self):
        self.generator = HospitalTransactionGenerator(num_users=50, anomaly_rate=0.15)
        self.running = False
        
        # Kafka-style buffers (simulated topics)
        self.kafka_topics = {
            'transactions': deque(maxlen=1000),
            'risk-scores': deque(maxlen=1000),
            'alerts': deque(maxlen=500)
        }
        
        # Processing metrics
        self.metrics = {
            'messages_produced': 0,
            'messages_consumed': 0,
            'high_risk_alerts': 0,
            'processing_latency_ms': [],
            'throughput_per_sec': []
        }
        
        # Flink-style windowing state
        self.window_buffer = []
        self.window_results = []
        
    def kafka_produce(self, topic, message):
        """Simulate Kafka Producer"""
        message['kafka_metadata'] = {
            'topic': topic,
            'partition': hash(message.get('user_id', '')) % 3,  # 3 partitions
            'offset': len(self.kafka_topics[topic]),
            'timestamp': datetime.now().isoformat()
        }
        self.kafka_topics[topic].append(message)
        self.metrics['messages_produced'] += 1
        
    def kafka_consume(self, topic):
        """Simulate Kafka Consumer"""
        if self.kafka_topics[topic]:
            self.metrics['messages_consumed'] += 1
            return self.kafka_topics[topic].popleft()
        return None
    
    def pyspark_process_batch(self, transactions):
        """
        Simulate PySpark DataFrame operations
        """
        if not transactions:
            return None
        
        df = pd.DataFrame(transactions)
        
        # PySpark-style SQL aggregations
        results = {
            'total_count': len(df),
            'total_amount': df['amount'].sum(),
            'avg_amount': df['amount'].mean(),
            
            # Group by user (like PySpark groupBy)
            'user_stats': df.groupby('user_id').agg({
                'amount': ['count', 'sum', 'mean', 'max'],
                'transaction_id': 'count'
            }).reset_index(),
            
            # Group by department
            'dept_stats': df.groupby('department').agg({
                'amount': ['count', 'sum', 'mean'],
                'transaction_id': 'count'
            }).reset_index(),
            
            # Group by transaction type
            'type_stats': df.groupby('transaction_type').agg({
                'amount': ['count', 'sum', 'mean']
            }).reset_index()
        }
        
        return results
    
    def flink_windowing(self, transactions, window_size_sec=5):
        """
        Simulate Flink Time-Windowed Processing
        """
        if not transactions:
            return []
        
        df = pd.DataFrame(transactions)
        
        # Ensure timestamp column
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.date_range(start=datetime.now(), periods=len(df), freq='100ms')
        else:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Sort by event time (Flink's event-time processing)
        df = df.sort_values('timestamp')
        
        # Create time windows
        df['window'] = df['timestamp'].dt.floor(f'{window_size_sec}S')
        
        # Windowed aggregations (Flink-style)
        window_agg = df.groupby('window').agg({
            'amount': ['count', 'sum', 'mean', 'max', 'min'],
            'risk_score': ['mean', 'max'],
            'user_id': 'nunique'
        }).reset_index()
        
        window_agg.columns = ['window', 'tx_count', 'total_amount', 'avg_amount', 
                             'max_amount', 'min_amount', 'avg_risk', 'max_risk', 'unique_users']
        
        return window_agg
    
    def calculate_risk_score(self, transaction):
        """Advanced risk scoring algorithm"""
        score = 0
        factors = []
        
        amount = transaction.get('amount', 0)
        
        # Amount-based risk
        if amount > 200000:
            score += 40
            factors.append('Very high amount')
        elif amount > 100000:
            score += 25
            factors.append('High amount')
        elif amount > 50000:
            score += 15
            factors.append('Medium-high amount')
        
        # Department risk patterns
        high_risk_depts = ['Emergency', 'Oncology', 'Surgery']
        if transaction.get('department') in high_risk_depts:
            score += 15
            factors.append(f"High-risk dept: {transaction.get('department')}")
        
        # Transaction type patterns
        if transaction.get('transaction_type') in ['Drug_Purchase', 'Equipment']:
            score += 10
            factors.append(f"Risky type: {transaction.get('transaction_type')}")
        
        # Time-based anomalies (simulated)
        hour = datetime.now().hour
        if hour < 6 or hour > 22:
            score += 20
            factors.append('Off-hours transaction')
        
        # Random anomaly factor (from generator)
        if transaction.get('is_anomaly', False):
            score += 25
            factors.append('Anomaly detected')
        
        # Determine risk level
        if score >= 70:
            risk_level = 'CRITICAL'
        elif score >= 50:
            risk_level = 'HIGH'
        elif score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'risk_score': min(score, 100),
            'risk_level': risk_level,
            'risk_factors': factors
        }
    
    def flume_style_ingestion(self, duration=30, rate=10):
        """
        Simulate Flume-style continuous data ingestion
        """
        print(f"\n{'='*70}")
        print("FLUME-STYLE DATA INGESTION")
        print(f"{'='*70}")
        print(f"Duration: {duration} seconds")
        print(f"Rate: {rate} transactions/second")
        print(f"Target: Kafka topic 'transactions'")
        print()
        
        start_time = time.time()
        count = 0
        
        try:
            while (time.time() - start_time) < duration:
                # Generate transaction
                tx = self.generator.generate_transaction()
                
                # Add timestamp
                tx['timestamp'] = datetime.now().isoformat()
                
                # Produce to Kafka
                self.kafka_produce('transactions', tx)
                count += 1
                
                if count % 10 == 0:
                    elapsed = time.time() - start_time
                    actual_rate = count / elapsed if elapsed > 0 else 0
                    print(f"[FLUME] Ingested {count} records | Rate: {actual_rate:.1f} tx/sec | "
                          f"Kafka Queue: {len(self.kafka_topics['transactions'])}")
                
                time.sleep(1.0 / rate)
                
        except KeyboardInterrupt:
            print("\nIngestion stopped by user")
        
        elapsed = time.time() - start_time
        print(f"\n[FLUME] Ingestion complete: {count} records in {elapsed:.2f}s")
        print(f"[FLUME] Average throughput: {count/elapsed:.1f} tx/sec")
        
        return count
    
    def stream_processor(self, duration=30):
        """
        Continuous stream processing (Kafka + Flink + PySpark)
        """
        print(f"\n{'='*70}")
        print("STREAM PROCESSING ENGINE")
        print(f"{'='*70}")
        print("Technologies: Kafka Consumer + Flink Windowing + PySpark Analytics")
        print()
        
        start_time = time.time()
        processed = 0
        batch = []
        
        try:
            while (time.time() - start_time) < duration:
                # Kafka consume
                tx = self.kafka_consume('transactions')
                
                if tx:
                    proc_start = time.time()
                    
                    # Calculate risk (PySpark-style processing)
                    risk_result = self.calculate_risk_score(tx)
                    tx.update(risk_result)
                    
                    # Add to batch for windowing
                    batch.append(tx)
                    self.window_buffer.append(tx)
                    
                    # Produce to risk-scores topic
                    self.kafka_produce('risk-scores', tx)
                    
                    # Alert on high risk
                    if risk_result['risk_level'] in ['HIGH', 'CRITICAL']:
                        alert = {
                            'transaction_id': tx.get('transaction_id'),
                            'risk_score': risk_result['risk_score'],
                            'risk_level': risk_result['risk_level'],
                            'factors': risk_result['risk_factors'],
                            'timestamp': datetime.now().isoformat()
                        }
                        self.kafka_produce('alerts', alert)
                        self.metrics['high_risk_alerts'] += 1
                    
                    # Track latency
                    latency = (time.time() - proc_start) * 1000
                    self.metrics['processing_latency_ms'].append(latency)
                    
                    processed += 1
                    
                    if processed % 20 == 0:
                        avg_latency = np.mean(self.metrics['processing_latency_ms'][-100:])
                        print(f"[PROCESSOR] Processed {processed} | Avg latency: {avg_latency:.2f}ms | "
                              f"Alerts: {self.metrics['high_risk_alerts']}")
                
                else:
                    time.sleep(0.01)  # Brief pause if no messages
                
        except KeyboardInterrupt:
            print("\nProcessor stopped by user")
        
        print(f"\n[PROCESSOR] Processing complete: {processed} transactions")
        
        # Final Flink-style windowing
        if batch:
            print("\n[FLINK] Running windowed aggregations...")
            window_results = self.flink_windowing(batch)
            print(f"[FLINK] Generated {len(window_results)} time windows")
            self.window_results = window_results
        
        return processed
    
    def run_full_pipeline(self, duration=30, rate=10):
        """
        Run complete Big Data pipeline
        """
        print(f"\n{'='*80}")
        print(" "*20 + "BIG DATA STREAMING PIPELINE")
        print(f"{'='*80}")
        print("\nTechnologies:")
        print("  [1] Flume-style Ingestion  --> Data Collection")
        print("  [2] Kafka Messaging       --> Topic: transactions, risk-scores, alerts")
        print("  [3] Flink Streaming       --> Time-windowed processing")
        print("  [4] PySpark Analytics     --> Risk scoring & aggregations")
        print()
        
        # Run ingestion and processing in parallel
        ingestion_thread = threading.Thread(
            target=self.flume_style_ingestion,
            args=(duration, rate)
        )
        
        processor_thread = threading.Thread(
            target=self.stream_processor,
            args=(duration + 5,)  # Run slightly longer to consume all
        )
        
        # Start both
        ingestion_thread.start()
        time.sleep(1)  # Brief delay before starting consumer
        processor_thread.start()
        
        # Wait for completion
        ingestion_thread.join()
        processor_thread.join()
        
        # Final analytics
        self.show_analytics()
    
    def show_analytics(self):
        """Display final analytics"""
        print(f"\n{'='*80}")
        print(" "*25 + "FINAL ANALYTICS")
        print(f"{'='*80}")
        
        print("\n📊 KAFKA METRICS:")
        print(f"  Total messages produced: {self.metrics['messages_produced']}")
        print(f"  Total messages consumed: {self.metrics['messages_consumed']}")
        print(f"  Remaining in queue: {sum(len(q) for q in self.kafka_topics.values())}")
        
        print("\n⚡ PROCESSING METRICS:")
        if self.metrics['processing_latency_ms']:
            latencies = self.metrics['processing_latency_ms']
            print(f"  Average latency: {np.mean(latencies):.2f} ms")
            print(f"  P50 latency: {np.percentile(latencies, 50):.2f} ms")
            print(f"  P95 latency: {np.percentile(latencies, 95):.2f} ms")
            print(f"  P99 latency: {np.percentile(latencies, 99):.2f} ms")
        
        print(f"\n🚨 ALERTS:")
        print(f"  High-risk alerts generated: {self.metrics['high_risk_alerts']}")
        
        # Show Flink window results
        if len(self.window_results) > 0:
            print(f"\n🔄 FLINK TIME WINDOWS:")
            print(f"  Total windows: {len(self.window_results)}")
            print("\n  Top 5 windows by transaction count:")
            top_windows = self.window_results.nlargest(5, 'tx_count')
            print(top_windows[['window', 'tx_count', 'total_amount', 'avg_risk', 'unique_users']].to_string(index=False))
        
        # PySpark batch analytics
        if self.window_buffer:
            print(f"\n💡 PYSPARK BATCH ANALYTICS:")
            batch_results = self.pyspark_process_batch(self.window_buffer)
            
            if batch_results:
                print(f"  Total transactions analyzed: {batch_results['total_count']}")
                print(f"  Total amount: ${batch_results['total_amount']:,.2f}")
                print(f"  Average amount: ${batch_results['avg_amount']:,.2f}")
                
                print("\n  Top 5 users by transaction count:")
                top_users = batch_results['user_stats'].nlargest(5, ('amount', 'count'))
                print(top_users.head().to_string(index=False))
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save all results to files"""
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        # Save transactions
        if self.window_buffer:
            df = pd.DataFrame(self.window_buffer)
            df.to_csv(output_dir / 'bigdata_transactions.csv', index=False)
            print(f"\n✓ Saved transactions: output/bigdata_transactions.csv")
        
        # Save window results
        if len(self.window_results) > 0:
            self.window_results.to_csv(output_dir / 'flink_windows.csv', index=False)
            print(f"✓ Saved Flink windows: output/flink_windows.csv")
        
        # Save alerts
        if self.kafka_topics['alerts']:
            alerts_df = pd.DataFrame(list(self.kafka_topics['alerts']))
            alerts_df.to_csv(output_dir / 'risk_alerts.csv', index=False)
            print(f"✓ Saved alerts: output/risk_alerts.csv")
        
        # Save metrics
        metrics_df = pd.DataFrame({
            'metric': ['messages_produced', 'messages_consumed', 'high_risk_alerts',
                      'avg_latency_ms', 'p95_latency_ms'],
            'value': [
                self.metrics['messages_produced'],
                self.metrics['messages_consumed'],
                self.metrics['high_risk_alerts'],
                np.mean(self.metrics['processing_latency_ms']) if self.metrics['processing_latency_ms'] else 0,
                np.percentile(self.metrics['processing_latency_ms'], 95) if self.metrics['processing_latency_ms'] else 0
            ]
        })
        metrics_df.to_csv(output_dir / 'processing_metrics.csv', index=False)
        print(f"✓ Saved metrics: output/processing_metrics.csv")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print(" "*15 + "BIG DATA TECHNOLOGIES DEMONSTRATION")
    print(" "*10 + "Hospital Risk Management - Complete Stack")
    print("="*80)
    print("\nStack: Flume + Kafka + Flink + PySpark")
    print("Mode: Lightweight (no external dependencies)")
    print()
    
    processor = StreamProcessor()
    
    try:
        # Run for 30 seconds at 10 tx/sec = ~300 transactions
        processor.run_full_pipeline(duration=30, rate=10)
        
        print(f"\n{'='*80}")
        print(" "*25 + "DEMO COMPLETE!")
        print(f"{'='*80}")
        print("\n✅ Successfully demonstrated:")
        print("   • Flume-style continuous data ingestion")
        print("   • Kafka distributed messaging (3 topics)")
        print("   • Flink time-windowed stream processing")
        print("   • PySpark distributed analytics")
        print("   • Real-time risk detection & alerting")
        print("\n📁 Results saved in output/ directory")
        print("\n💡 For live visualization, run: streamlit run dashboard_standalone.py")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

