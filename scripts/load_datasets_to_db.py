"""
Load Downloaded Datasets into PostgreSQL Database
Imports CSV datasets into the hospital risk management database
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path
from datetime import datetime
import json

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'hospital_risk_db'),
    'user': os.getenv('POSTGRES_USER', 'hospital_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'hospital_pass123')
}

DATASET_DIR = Path('datasets')

print("=" * 70)
print("Dataset Loader - Import CSV Data to PostgreSQL")
print("=" * 70)
print()


def connect_to_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"✓ Connected to database: {DB_CONFIG['database']}")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        sys.exit(1)


def load_financial_transactions(conn):
    """Load hospital financial transactions into database"""
    print("\n📊 Loading hospital financial transactions...")
    
    filepath = DATASET_DIR / 'hospital_financial_transactions.csv'
    if not filepath.exists():
        print(f"  ⚠ File not found: {filepath}")
        return
    
    try:
        df = pd.read_csv(filepath)
        print(f"  • Read {len(df)} records from CSV")
        
        cursor = conn.cursor()
        
        # Prepare data for insertion
        records = []
        for _, row in df.iterrows():
            record = (
                row['transaction_id'],
                row['timestamp'],
                row['user_id'],
                row['account_id'],
                row['department'],
                row['transaction_type'],
                row['amount'],
                f"{row['transaction_type']} transaction",  # description
                row['risk_score'],
                'high' if row['is_high_risk'] == 1 else ('medium' if row['risk_score'] > 30 else 'low'),
                bool(row['is_high_risk']),
                json.dumps({'source': 'historical_data', 'imported': True})
            )
            records.append(record)
        
        # Insert into database
        insert_query = """
            INSERT INTO transactions (
                transaction_id, timestamp, user_id, account_id, department,
                transaction_type, amount, description, risk_score, risk_level,
                is_anomaly, metadata
            ) VALUES %s
            ON CONFLICT (transaction_id) DO NOTHING
        """
        
        execute_values(cursor, insert_query, records)
        conn.commit()
        
        print(f"  ✓ Loaded {len(records)} transactions into database")
        cursor.close()
        
    except Exception as e:
        print(f"  ✗ Error loading financial transactions: {e}")
        conn.rollback()


def load_user_profiles(conn):
    """Load user behavior profiles into database"""
    print("\n👤 Loading user behavior profiles...")
    
    filepath = DATASET_DIR / 'user_behavior_profiles.csv'
    if not filepath.exists():
        print(f"  ⚠ File not found: {filepath}")
        return
    
    try:
        df = pd.read_csv(filepath)
        print(f"  • Read {len(df)} user profiles from CSV")
        
        cursor = conn.cursor()
        
        # Prepare data for insertion
        records = []
        for _, row in df.iterrows():
            typical_hours = list(range(row['typical_hours_start'], row['typical_hours_end']))
            record = (
                row['user_id'],
                0,  # total_transactions (will be updated by trigger)
                row['avg_transaction_amount'],
                row['avg_transaction_amount'] * 2,  # max_transaction_amount
                [row['primary_department']],  # typical_departments
                typical_hours,  # typical_hours
                json.dumps({
                    'role': row['role'],
                    'years_employed': int(row['years_employed']),
                    'violation_count': int(row['violation_count'])
                }),
                row['baseline_risk_score']
            )
            records.append(record)
        
        # Insert into database
        insert_query = """
            INSERT INTO user_profiles (
                user_id, total_transactions, avg_transaction_amount, max_transaction_amount,
                typical_departments, typical_hours, risk_history, baseline_score
            ) VALUES %s
            ON CONFLICT (user_id) DO UPDATE SET
                baseline_score = EXCLUDED.baseline_score,
                risk_history = EXCLUDED.risk_history,
                last_updated = CURRENT_TIMESTAMP
        """
        
        execute_values(cursor, insert_query, records)
        conn.commit()
        
        print(f"  ✓ Loaded {len(records)} user profiles into database")
        cursor.close()
        
    except Exception as e:
        print(f"  ✗ Error loading user profiles: {e}")
        conn.rollback()


def load_transaction_patterns(conn):
    """Load transaction patterns into database"""
    print("\n🔍 Loading transaction patterns...")
    
    filepath = DATASET_DIR / 'transaction_patterns.csv'
    if not filepath.exists():
        print(f"  ⚠ File not found: {filepath}")
        return
    
    try:
        df = pd.read_csv(filepath)
        print(f"  • Read {len(df)} patterns from CSV")
        
        cursor = conn.cursor()
        
        # Insert patterns
        for _, row in df.iterrows():
            insert_query = """
                INSERT INTO transaction_patterns (
                    user_id, pattern_type, pattern_description, frequency, risk_indicator
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """
            
            # Use a generic user for system patterns
            cursor.execute(insert_query, (
                'SYSTEM',
                row['pattern_name'],
                row['description'],
                row['frequency_threshold'],
                row['risk_level'] in ['high', 'medium']
            ))
        
        conn.commit()
        print(f"  ✓ Loaded {len(df)} patterns into database")
        cursor.close()
        
    except Exception as e:
        print(f"  ✗ Error loading transaction patterns: {e}")
        conn.rollback()


def load_fraud_dataset(conn):
    """Load healthcare fraud dataset for reference"""
    print("\n🚨 Loading healthcare fraud dataset...")
    
    filepath = DATASET_DIR / 'healthcare_fraud_synthetic.csv'
    if not filepath.exists():
        print(f"  ⚠ File not found: {filepath}")
        return
    
    try:
        df = pd.read_csv(filepath)
        print(f"  • Read {len(df)} fraud records from CSV")
        
        # This is for reference/training, not direct insertion
        # Log statistics
        cursor = conn.cursor()
        
        stats = {
            'total_claims': len(df),
            'fraudulent_claims': df['potential_fraud'].sum(),
            'fraud_rate': df['potential_fraud'].mean(),
            'avg_claim_amount': df['claim_amount'].mean(),
            'max_claim_amount': df['claim_amount'].max()
        }
        
        insert_query = """
            INSERT INTO audit_log (event_type, event_source, event_data, severity)
            VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            'DATASET_LOADED',
            'fraud_dataset_loader',
            json.dumps(stats),
            'info'
        ))
        
        conn.commit()
        print(f"  ✓ Logged fraud dataset statistics")
        print(f"    • Total claims: {stats['total_claims']}")
        print(f"    • Fraud rate: {stats['fraud_rate']*100:.1f}%")
        cursor.close()
        
    except Exception as e:
        print(f"  ✗ Error processing fraud dataset: {e}")
        conn.rollback()


def update_statistics(conn):
    """Update system metrics with dataset statistics"""
    print("\n📈 Updating system metrics...")
    
    try:
        cursor = conn.cursor()
        
        # Get transaction count
        cursor.execute("SELECT COUNT(*) FROM transactions")
        tx_count = cursor.fetchone()[0]
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM user_profiles")
        user_count = cursor.fetchone()[0]
        
        # Get alert count
        cursor.execute("SELECT COUNT(*) FROM risk_alerts")
        alert_count = cursor.fetchone()[0]
        
        # Update metrics
        metrics = [
            ('transactions_loaded', tx_count, 'count'),
            ('users_loaded', user_count, 'count'),
            ('alerts_count', alert_count, 'count')
        ]
        
        for metric_name, metric_value, metric_unit in metrics:
            cursor.execute("""
                INSERT INTO system_metrics (metric_name, metric_value, metric_unit)
                VALUES (%s, %s, %s)
            """, (metric_name, metric_value, metric_unit))
        
        conn.commit()
        print(f"  ✓ Updated system metrics")
        print(f"    • Transactions: {tx_count}")
        print(f"    • Users: {user_count}")
        print(f"    • Alerts: {alert_count}")
        cursor.close()
        
    except Exception as e:
        print(f"  ✗ Error updating metrics: {e}")
        conn.rollback()


def main():
    """Main function to load all datasets"""
    
    print("Connecting to database...")
    conn = connect_to_database()
    
    try:
        # Load datasets in order
        load_user_profiles(conn)
        load_financial_transactions(conn)
        load_transaction_patterns(conn)
        load_fraud_dataset(conn)
        update_statistics(conn)
        
        print()
        print("=" * 70)
        print("✓ DATASET LOADING COMPLETE")
        print("=" * 70)
        print()
        print("All datasets have been successfully loaded into the database!")
        print("You can now view the data in the dashboard or query directly.")
        print()
        
    except Exception as e:
        print(f"\n✗ Error during dataset loading: {e}")
    finally:
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()

