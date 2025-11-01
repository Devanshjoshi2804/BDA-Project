"""
Hospital Accounting Transaction Data Generator
Generates realistic synthetic hospital accounting transactions with anomalies
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
from faker import Faker

fake = Faker()


class HospitalTransactionGenerator:
    """Generate synthetic hospital accounting transactions"""
    
    TRANSACTION_TYPES = [
        'billing', 'payment', 'refund', 'transfer', 
        'adjustment', 'insurance_claim', 'payroll', 'procurement'
    ]
    
    DEPARTMENTS = [
        'Emergency', 'Cardiology', 'Neurology', 'Oncology', 
        'Pediatrics', 'Surgery', 'Radiology', 'Laboratory',
        'Pharmacy', 'Administration', 'IT', 'Finance'
    ]
    
    # Normal transaction amount ranges by type
    AMOUNT_RANGES = {
        'billing': (100, 50000),
        'payment': (50, 30000),
        'refund': (50, 5000),
        'transfer': (500, 100000),
        'adjustment': (10, 10000),
        'insurance_claim': (1000, 200000),
        'payroll': (2000, 15000),
        'procurement': (500, 50000)
    }
    
    def __init__(self, num_users: int = 50, anomaly_rate: float = 0.15):
        """
        Initialize the generator
        
        Args:
            num_users: Number of unique users to simulate
            anomaly_rate: Probability of generating an anomalous transaction
        """
        self.num_users = num_users
        self.anomaly_rate = anomaly_rate
        self.users = self._generate_users()
        self.transaction_history = {}
        
    def _generate_users(self) -> List[Dict]:
        """Generate a list of simulated users"""
        users = []
        for i in range(self.num_users):
            users.append({
                'user_id': f'USER_{i:04d}',
                'name': fake.name(),
                'role': random.choice(['accountant', 'admin', 'manager', 'clerk', 'finance_officer']),
                'department': random.choice(self.DEPARTMENTS),
                'typical_transaction_types': random.sample(self.TRANSACTION_TYPES, k=random.randint(2, 4))
            })
        return users
    
    def _is_business_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is within business hours (8 AM - 6 PM, Mon-Fri)"""
        return (timestamp.weekday() < 5 and 8 <= timestamp.hour < 18)
    
    def _generate_normal_transaction(self) -> Dict:
        """Generate a normal (non-anomalous) transaction"""
        user = random.choice(self.users)
        transaction_type = random.choice(user['typical_transaction_types'])
        
        # Generate timestamp within business hours
        now = datetime.now()
        # Random time within last few minutes
        timestamp = now - timedelta(seconds=random.randint(0, 300))
        
        # Adjust to business hours for normal transactions
        if not self._is_business_hours(timestamp):
            timestamp = timestamp.replace(
                hour=random.randint(8, 17),
                minute=random.randint(0, 59)
            )
            # Ensure weekday
            while timestamp.weekday() >= 5:
                timestamp = timestamp - timedelta(days=1)
        
        # Generate amount within normal range
        min_amount, max_amount = self.AMOUNT_RANGES[transaction_type]
        amount = round(random.uniform(min_amount, max_amount), 2)
        
        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'timestamp': timestamp.isoformat(),
            'user_id': user['user_id'],
            'account_id': f'ACC_{random.randint(1000, 9999)}',
            'department': user['department'],
            'transaction_type': transaction_type,
            'amount': amount,
            'description': self._generate_description(transaction_type),
            'metadata': {
                'user_role': user['role'],
                'is_synthetic': True,
                'generation_timestamp': datetime.now().isoformat()
            }
        }
        
        return transaction
    
    def _generate_anomalous_transaction(self) -> Dict:
        """Generate an anomalous transaction with risk indicators"""
        transaction = self._generate_normal_transaction()
        
        # Choose anomaly type
        anomaly_types = [
            'unusual_amount',
            'off_hours',
            'rapid_succession',
            'unusual_type_for_user',
            'high_frequency',
            'suspicious_account'
        ]
        
        anomaly_type = random.choice(anomaly_types)
        
        if anomaly_type == 'unusual_amount':
            # Generate amount 3-10x higher than normal
            transaction_type = transaction['transaction_type']
            min_amount, max_amount = self.AMOUNT_RANGES[transaction_type]
            multiplier = random.uniform(3, 10)
            transaction['amount'] = round(max_amount * multiplier, 2)
            transaction['metadata']['anomaly_type'] = 'unusual_amount'
            
        elif anomaly_type == 'off_hours':
            # Transaction at unusual hours
            timestamp = datetime.now()
            hour = random.choice([0, 1, 2, 3, 4, 5, 22, 23])
            timestamp = timestamp.replace(hour=hour, minute=random.randint(0, 59))
            transaction['timestamp'] = timestamp.isoformat()
            transaction['metadata']['anomaly_type'] = 'off_hours'
            
        elif anomaly_type == 'rapid_succession':
            # Multiple transactions in rapid succession
            transaction['metadata']['anomaly_type'] = 'rapid_succession'
            transaction['metadata']['rapid_count'] = random.randint(5, 15)
            
        elif anomaly_type == 'unusual_type_for_user':
            # Transaction type not typical for this user
            user_typical_types = [u['typical_transaction_types'] for u in self.users 
                                 if u['user_id'] == transaction['user_id']][0]
            unusual_types = [t for t in self.TRANSACTION_TYPES if t not in user_typical_types]
            if unusual_types:
                transaction['transaction_type'] = random.choice(unusual_types)
            transaction['metadata']['anomaly_type'] = 'unusual_type_for_user'
            
        elif anomaly_type == 'high_frequency':
            # Unusually high number of transactions
            transaction['metadata']['anomaly_type'] = 'high_frequency'
            transaction['metadata']['frequency_multiplier'] = random.uniform(3, 8)
            
        elif anomaly_type == 'suspicious_account':
            # Transaction to/from suspicious account
            transaction['account_id'] = f'SUSP_{random.randint(1000, 9999)}'
            transaction['metadata']['anomaly_type'] = 'suspicious_account'
        
        transaction['metadata']['is_anomaly'] = True
        
        return transaction
    
    def generate_transaction(self) -> Dict:
        """Generate a single transaction (normal or anomalous)"""
        if random.random() < self.anomaly_rate:
            return self._generate_anomalous_transaction()
        else:
            return self._generate_normal_transaction()
    
    def generate_batch(self, batch_size: int) -> List[Dict]:
        """Generate a batch of transactions"""
        return [self.generate_transaction() for _ in range(batch_size)]
    
    def _generate_description(self, transaction_type: str) -> str:
        """Generate a realistic description for the transaction"""
        descriptions = {
            'billing': f"Patient billing for {fake.catch_phrase()}",
            'payment': f"Payment received for invoice #{random.randint(10000, 99999)}",
            'refund': f"Refund processed for account {random.randint(1000, 9999)}",
            'transfer': f"Fund transfer between accounts",
            'adjustment': f"Accounting adjustment - {fake.bs()}",
            'insurance_claim': f"Insurance claim #{random.randint(100000, 999999)}",
            'payroll': f"Payroll payment for employee",
            'procurement': f"Procurement of {fake.catch_phrase()}"
        }
        return descriptions.get(transaction_type, "Hospital transaction")
    
    def get_statistics(self) -> Dict:
        """Get generator statistics"""
        return {
            'num_users': self.num_users,
            'anomaly_rate': self.anomaly_rate,
            'transaction_types': len(self.TRANSACTION_TYPES),
            'departments': len(self.DEPARTMENTS)
        }


if __name__ == "__main__":
    # Test the generator
    generator = HospitalTransactionGenerator(num_users=50, anomaly_rate=0.15)
    
    print("Hospital Transaction Generator Test")
    print("=" * 50)
    print(f"Statistics: {generator.get_statistics()}")
    print("\nSample Transactions:")
    
    for i in range(5):
        transaction = generator.generate_transaction()
        print(f"\n{i+1}. {transaction['transaction_type'].upper()}")
        print(f"   Amount: ${transaction['amount']:,.2f}")
        print(f"   User: {transaction['user_id']}")
        print(f"   Department: {transaction['department']}")
        print(f"   Time: {transaction['timestamp']}")
        if transaction['metadata'].get('is_anomaly'):
            print(f"   ⚠️  ANOMALY: {transaction['metadata'].get('anomaly_type')}")

