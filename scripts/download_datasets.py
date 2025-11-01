"""
Dataset Downloader for Hospital Risk Management System
Downloads and prepares real-world healthcare datasets from Kaggle and other sources
"""

import os
import sys
import requests
import pandas as pd
from pathlib import Path
import json
import zipfile
import io

# Dataset directory
DATASET_DIR = Path("datasets")
DATASET_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("Hospital Risk Management System - Dataset Downloader")
print("=" * 70)
print()

# Note: For Kaggle datasets, you need to:
# 1. Create a Kaggle account
# 2. Get API credentials from https://www.kaggle.com/account
# 3. Place kaggle.json in ~/.kaggle/ or current directory

def download_file(url, filename):
    """Download a file from URL"""
    try:
        print(f"Downloading {filename}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        filepath = DATASET_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded: {filename}")
        return filepath
    except Exception as e:
        print(f"✗ Error downloading {filename}: {e}")
        return None


def create_synthetic_healthcare_fraud_dataset():
    """Create a synthetic healthcare fraud detection dataset"""
    print("\nCreating synthetic healthcare fraud dataset...")
    
    import numpy as np
    from datetime import datetime, timedelta
    
    np.random.seed(42)
    n_records = 5000
    
    # Generate synthetic data
    data = {
        'transaction_id': [f'TXN{i:06d}' for i in range(n_records)],
        'provider_id': [f'PROV{np.random.randint(1, 100):04d}' for _ in range(n_records)],
        'patient_id': [f'PAT{np.random.randint(1, 1000):05d}' for _ in range(n_records)],
        'claim_amount': np.random.lognormal(8, 1.5, n_records),
        'procedure_code': np.random.choice(['99213', '99214', '99215', '99232', '99233', 
                                           '99291', '99292', '99203', '99204'], n_records),
        'diagnosis_code': np.random.choice(['M25.5', 'E11.9', 'I10', 'J44.1', 'F41.9',
                                           'N18.3', 'K21.9', 'G47.33'], n_records),
        'department': np.random.choice(['Emergency', 'Cardiology', 'Neurology', 'Surgery',
                                       'Oncology', 'Pediatrics', 'Orthopedics'], n_records),
        'service_date': [(datetime.now() - timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d') 
                        for _ in range(n_records)],
        'payment_status': np.random.choice(['Paid', 'Pending', 'Rejected', 'Under Review'], 
                                          n_records, p=[0.7, 0.15, 0.1, 0.05]),
    }
    
    # Add fraud indicators (15% fraudulent)
    fraud_indicators = []
    for i in range(n_records):
        is_fraud = np.random.random() < 0.15
        
        if is_fraud:
            # Increase amount for fraudulent claims
            data['claim_amount'][i] *= np.random.uniform(2, 5)
            fraud_indicators.append(1)
        else:
            fraud_indicators.append(0)
    
    data['potential_fraud'] = fraud_indicators
    
    df = pd.DataFrame(data)
    
    # Save to CSV
    filepath = DATASET_DIR / 'healthcare_fraud_synthetic.csv'
    df.to_csv(filepath, index=False)
    print(f"✓ Created synthetic healthcare fraud dataset: {filepath}")
    print(f"  Total records: {len(df)}")
    print(f"  Fraud cases: {df['potential_fraud'].sum()} ({df['potential_fraud'].mean()*100:.1f}%)")
    
    return filepath


def create_hospital_financial_transactions():
    """Create synthetic hospital financial transactions dataset"""
    print("\nCreating hospital financial transactions dataset...")
    
    import numpy as np
    from datetime import datetime, timedelta
    
    np.random.seed(123)
    n_records = 10000
    
    transaction_types = ['billing', 'payment', 'refund', 'transfer', 'adjustment', 
                        'insurance_claim', 'payroll', 'procurement']
    departments = ['Emergency', 'Cardiology', 'Neurology', 'Oncology', 'Pediatrics',
                  'Surgery', 'Radiology', 'Laboratory', 'Pharmacy', 'Administration']
    
    data = {
        'transaction_id': [f'TXN{i:07d}' for i in range(n_records)],
        'timestamp': [(datetime.now() - timedelta(hours=np.random.randint(0, 720))).isoformat() 
                     for _ in range(n_records)],
        'user_id': [f'USER_{np.random.randint(1, 50):04d}' for _ in range(n_records)],
        'account_id': [f'ACC_{np.random.randint(1000, 9999)}' for _ in range(n_records)],
        'department': np.random.choice(departments, n_records),
        'transaction_type': np.random.choice(transaction_types, n_records),
    }
    
    # Generate amounts based on transaction type
    amounts = []
    for tx_type in data['transaction_type']:
        if tx_type == 'billing':
            amount = np.random.lognormal(9, 1.2)
        elif tx_type == 'payment':
            amount = np.random.lognormal(8.5, 1)
        elif tx_type == 'refund':
            amount = np.random.lognormal(7, 0.8)
        elif tx_type == 'transfer':
            amount = np.random.lognormal(10, 1.5)
        elif tx_type == 'insurance_claim':
            amount = np.random.lognormal(11, 1.3)
        elif tx_type == 'payroll':
            amount = np.random.uniform(2000, 15000)
        elif tx_type == 'procurement':
            amount = np.random.lognormal(9.5, 1.4)
        else:
            amount = np.random.lognormal(8, 1)
        amounts.append(round(amount, 2))
    
    data['amount'] = amounts
    
    # Add risk indicators
    risk_scores = []
    for i in range(n_records):
        base_risk = np.random.uniform(10, 40)
        
        # Increase risk for certain conditions
        if amounts[i] > 100000:
            base_risk += 20
        if data['transaction_type'][i] in ['transfer', 'adjustment']:
            base_risk += 10
        
        # Add some high-risk transactions
        if np.random.random() < 0.15:
            base_risk += np.random.uniform(30, 50)
        
        risk_scores.append(min(100, round(base_risk, 2)))
    
    data['risk_score'] = risk_scores
    data['is_high_risk'] = [1 if score >= 70 else 0 for score in risk_scores]
    
    df = pd.DataFrame(data)
    
    # Save to CSV
    filepath = DATASET_DIR / 'hospital_financial_transactions.csv'
    df.to_csv(filepath, index=False)
    print(f"✓ Created hospital financial transactions dataset: {filepath}")
    print(f"  Total records: {len(df)}")
    print(f"  High-risk: {df['is_high_risk'].sum()} ({df['is_high_risk'].mean()*100:.1f}%)")
    print(f"  Avg amount: ${df['amount'].mean():,.2f}")
    
    return filepath


def create_user_behavior_profiles():
    """Create user behavior profiles for baseline analysis"""
    print("\nCreating user behavior profiles...")
    
    import numpy as np
    
    np.random.seed(456)
    n_users = 50
    
    roles = ['accountant', 'admin', 'manager', 'clerk', 'finance_officer']
    departments = ['Emergency', 'Cardiology', 'Neurology', 'Oncology', 'Pediatrics',
                  'Surgery', 'Radiology', 'Laboratory', 'Pharmacy', 'Administration']
    
    data = {
        'user_id': [f'USER_{i:04d}' for i in range(1, n_users + 1)],
        'role': np.random.choice(roles, n_users),
        'primary_department': np.random.choice(departments, n_users),
        'avg_transactions_per_day': np.random.randint(5, 50, n_users),
        'avg_transaction_amount': [round(np.random.lognormal(9, 1), 2) for _ in range(n_users)],
        'typical_hours_start': np.random.randint(7, 10, n_users),
        'typical_hours_end': np.random.randint(16, 19, n_users),
        'baseline_risk_score': [round(np.random.uniform(20, 40), 2) for _ in range(n_users)],
        'years_employed': np.random.randint(1, 20, n_users),
        'violation_count': np.random.choice([0, 0, 0, 0, 1, 2], n_users)  # Most have 0
    }
    
    df = pd.DataFrame(data)
    
    filepath = DATASET_DIR / 'user_behavior_profiles.csv'
    df.to_csv(filepath, index=False)
    print(f"✓ Created user behavior profiles: {filepath}")
    print(f"  Total users: {len(df)}")
    
    return filepath


def create_transaction_patterns():
    """Create common transaction patterns for pattern matching"""
    print("\nCreating transaction patterns dataset...")
    
    patterns = [
        {
            'pattern_id': 'PTN001',
            'pattern_name': 'Late Night Transactions',
            'description': 'Multiple transactions between 11 PM and 5 AM',
            'risk_level': 'high',
            'frequency_threshold': 3,
            'time_window_hours': 6,
            'risk_score_increase': 25
        },
        {
            'pattern_id': 'PTN002',
            'pattern_name': 'Rapid Succession',
            'description': 'Many transactions in short time period',
            'risk_level': 'high',
            'frequency_threshold': 10,
            'time_window_hours': 1,
            'risk_score_increase': 30
        },
        {
            'pattern_id': 'PTN003',
            'pattern_name': 'High Value Spike',
            'description': 'Transaction amount >3x user average',
            'risk_level': 'medium',
            'frequency_threshold': 1,
            'time_window_hours': 24,
            'risk_score_increase': 20
        },
        {
            'pattern_id': 'PTN004',
            'pattern_name': 'Weekend Activity',
            'description': 'Unusual weekend transactions',
            'risk_level': 'medium',
            'frequency_threshold': 5,
            'time_window_hours': 48,
            'risk_score_increase': 15
        },
        {
            'pattern_id': 'PTN005',
            'pattern_name': 'Department Hopping',
            'description': 'Transactions across multiple departments rapidly',
            'risk_level': 'high',
            'frequency_threshold': 4,
            'time_window_hours': 2,
            'risk_score_increase': 25
        },
        {
            'pattern_id': 'PTN006',
            'pattern_name': 'Round Number Amounts',
            'description': 'Many transactions with round amounts (e.g., $10000)',
            'risk_level': 'low',
            'frequency_threshold': 5,
            'time_window_hours': 24,
            'risk_score_increase': 10
        }
    ]
    
    df = pd.DataFrame(patterns)
    
    filepath = DATASET_DIR / 'transaction_patterns.csv'
    df.to_csv(filepath, index=False)
    print(f"✓ Created transaction patterns: {filepath}")
    print(f"  Total patterns: {len(df)}")
    
    return filepath


def create_dataset_summary():
    """Create a summary of all available datasets"""
    print("\nCreating dataset summary...")
    
    summary = {
        'datasets': [
            {
                'name': 'healthcare_fraud_synthetic.csv',
                'description': 'Synthetic healthcare fraud detection dataset',
                'records': 5000,
                'features': ['transaction_id', 'provider_id', 'patient_id', 'claim_amount', 
                           'procedure_code', 'diagnosis_code', 'department', 'potential_fraud'],
                'use_case': 'Training fraud detection models'
            },
            {
                'name': 'hospital_financial_transactions.csv',
                'description': 'Hospital financial transactions with risk scores',
                'records': 10000,
                'features': ['transaction_id', 'timestamp', 'user_id', 'account_id', 
                           'department', 'transaction_type', 'amount', 'risk_score'],
                'use_case': 'Historical transaction analysis and baseline establishment'
            },
            {
                'name': 'user_behavior_profiles.csv',
                'description': 'User behavior baselines and profiles',
                'records': 50,
                'features': ['user_id', 'role', 'primary_department', 'avg_transactions_per_day',
                           'baseline_risk_score', 'typical_hours'],
                'use_case': 'Behavioral anomaly detection'
            },
            {
                'name': 'transaction_patterns.csv',
                'description': 'Known risky transaction patterns',
                'records': 6,
                'features': ['pattern_id', 'pattern_name', 'description', 'risk_level',
                           'frequency_threshold', 'risk_score_increase'],
                'use_case': 'Pattern matching and rule-based detection'
            },
            {
                'name': 'sample_transactions.csv',
                'description': 'Sample transactions for testing',
                'records': 10,
                'features': ['transaction_id', 'timestamp', 'user_id', 'amount', 'department'],
                'use_case': 'System testing and verification'
            }
        ]
    }
    
    filepath = DATASET_DIR / 'dataset_summary.json'
    with open(filepath, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✓ Created dataset summary: {filepath}")
    
    return filepath


def main():
    """Main function to download and create all datasets"""
    
    print("Starting dataset download and generation...")
    print()
    
    # Create synthetic datasets (since Kaggle requires authentication)
    print("GENERATING SYNTHETIC DATASETS")
    print("=" * 70)
    
    datasets_created = []
    
    try:
        # 1. Healthcare fraud dataset
        fp = create_synthetic_healthcare_fraud_dataset()
        if fp:
            datasets_created.append(fp)
    except Exception as e:
        print(f"Error creating fraud dataset: {e}")
    
    try:
        # 2. Hospital financial transactions
        fp = create_hospital_financial_transactions()
        if fp:
            datasets_created.append(fp)
    except Exception as e:
        print(f"Error creating financial transactions: {e}")
    
    try:
        # 3. User behavior profiles
        fp = create_user_behavior_profiles()
        if fp:
            datasets_created.append(fp)
    except Exception as e:
        print(f"Error creating user profiles: {e}")
    
    try:
        # 4. Transaction patterns
        fp = create_transaction_patterns()
        if fp:
            datasets_created.append(fp)
    except Exception as e:
        print(f"Error creating transaction patterns: {e}")
    
    try:
        # 5. Dataset summary
        fp = create_dataset_summary()
        if fp:
            datasets_created.append(fp)
    except Exception as e:
        print(f"Error creating dataset summary: {e}")
    
    # Summary
    print()
    print("=" * 70)
    print("DATASET DOWNLOAD/GENERATION COMPLETE")
    print("=" * 70)
    print(f"\n✓ Successfully created {len(datasets_created)} datasets")
    print(f"✓ Location: {DATASET_DIR.absolute()}")
    print()
    print("Available datasets:")
    for fp in datasets_created:
        size = fp.stat().st_size / 1024  # KB
        print(f"  • {fp.name} ({size:.1f} KB)")
    
    print()
    print("NOTE: For real Kaggle datasets:")
    print("  1. Create account at https://www.kaggle.com/")
    print("  2. Get API credentials from https://www.kaggle.com/account")
    print("  3. Install: pip install kaggle")
    print("  4. Download datasets using Kaggle CLI")
    print()
    print("Recommended Kaggle datasets:")
    print("  • kaggle datasets download -d rohitrox/healthcare-provider-fraud-detection-analysis")
    print("  • kaggle datasets download -d prasad22/healthcare-dataset")
    print("  • kaggle datasets download -d prasad22/daily-transactions-dataset")
    print()


if __name__ == "__main__":
    main()

