"""
Standalone Hospital Risk Management System
Runs without Docker - Pure Python implementation
"""

import threading
import time
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path('producers')))
sys.path.insert(0, str(Path('consumers')))

print("=" * 70)
print("HOSPITAL RISK MANAGEMENT SYSTEM - STANDALONE MODE")
print("=" * 70)
print()
print("Starting system components...")
print()

# Check dependencies
try:
    import pandas as pd
    import numpy as np
    from faker import Faker
    print("[OK] Dependencies found")
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("\nPlease install required packages:")
    print("pip install pandas numpy faker")
    sys.exit(1)

# Import our modules
from data_generator import HospitalTransactionGenerator

print("[OK] Modules loaded")
print()

class StandaloneRiskSystem:
    """Standalone risk detection system"""
    
    def __init__(self):
        self.generator = HospitalTransactionGenerator(num_users=50, anomaly_rate=0.15)
        self.transactions = []
        self.alerts = []
        self.running = True
        
    def calculate_risk_score(self, transaction):
        """Simple risk scoring"""
        risk_score = 0
        detection_rules = []
        
        # Amount risk
        if transaction['amount'] > 100000:
            risk_score += 25
            detection_rules.append('HIGH_AMOUNT')
        elif transaction['amount'] > 50000:
            risk_score += 15
            detection_rules.append('ELEVATED_AMOUNT')
            
        # Time risk
        from datetime import datetime
        try:
            ts = datetime.fromisoformat(transaction['timestamp'])
            hour = ts.hour
            if hour >= 23 or hour < 5:
                risk_score += 20
                detection_rules.append('OFF_HOURS_NIGHT')
            elif hour < 8 or hour >= 18:
                risk_score += 10
                detection_rules.append('OFF_HOURS')
        except:
            pass
            
        # Metadata risk
        if transaction['metadata'].get('is_anomaly'):
            risk_score += 30
            detection_rules.append('INJECTED_ANOMALY')
            
        # Classify
        if risk_score >= 70:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'
            
        return {
            'risk_score': min(100, risk_score),
            'risk_level': risk_level,
            'detection_rules': detection_rules
        }
    
    def process_transaction(self, transaction):
        """Process a single transaction"""
        risk_result = self.calculate_risk_score(transaction)
        
        enriched = {
            **transaction,
            'risk_score': risk_result['risk_score'],
            'risk_level': risk_result['risk_level'],
            'detection_rules': risk_result['detection_rules']
        }
        
        self.transactions.append(enriched)
        
        # Generate alert if high risk
        if risk_result['risk_level'] == 'high':
            alert = {
                'transaction_id': transaction['transaction_id'],
                'risk_score': risk_result['risk_score'],
                'user_id': transaction['user_id'],
                'amount': transaction['amount'],
                'rules': risk_result['detection_rules']
            }
            self.alerts.append(alert)
            print(f"[!] HIGH RISK ALERT: {transaction['transaction_id']} - Score: {risk_result['risk_score']:.0f} - ${transaction['amount']:,.2f}")
        
        return enriched
    
    def generate_transactions(self):
        """Generate transactions continuously"""
        count = 0
        while self.running and count < 100:  # Generate 100 transactions
            transaction = self.generator.generate_transaction()
            self.process_transaction(transaction)
            count += 1
            
            if count % 10 == 0:
                print(f"Processed {count} transactions...")
            
            time.sleep(0.1)  # 10 transactions per second
        
        print(f"\n[OK] Generated {count} transactions")
        self.running = False
    
    def save_results(self):
        """Save results to CSV"""
        import pandas as pd
        
        # Save transactions
        if self.transactions:
            df = pd.DataFrame(self.transactions)
            filepath = Path('output') / 'processed_transactions.csv'
            filepath.parent.mkdir(exist_ok=True)
            df.to_csv(filepath, index=False)
            print(f"[OK] Saved {len(df)} transactions to: {filepath}")
        
        # Save alerts
        if self.alerts:
            df_alerts = pd.DataFrame(self.alerts)
            filepath = Path('output') / 'risk_alerts.csv'
            df_alerts.to_csv(filepath, index=False)
            print(f"[OK] Saved {len(df_alerts)} alerts to: {filepath}")
    
    def show_statistics(self):
        """Display system statistics"""
        print()
        print("=" * 70)
        print("SYSTEM STATISTICS")
        print("=" * 70)
        
        if not self.transactions:
            print("No transactions processed")
            return
        
        import pandas as pd
        df = pd.DataFrame(self.transactions)
        
        print(f"\nTotal Transactions: {len(df)}")
        print(f"Total Alerts: {len(self.alerts)}")
        print(f"Alert Rate: {len(self.alerts)/len(df)*100:.1f}%")
        print()
        
        print("Risk Distribution:")
        risk_dist = df['risk_level'].value_counts()
        for level, count in risk_dist.items():
            print(f"  {level.capitalize()}: {count} ({count/len(df)*100:.1f}%)")
        
        print()
        print(f"Average Risk Score: {df['risk_score'].mean():.1f}")
        print(f"Max Risk Score: {df['risk_score'].max():.1f}")
        print()
        
        print("Top 5 Highest Risk Transactions:")
        top5 = df.nlargest(5, 'risk_score')[['transaction_id', 'user_id', 'amount', 'risk_score', 'risk_level']]
        print(top5.to_string(index=False))
        print()
    
    def run(self):
        """Run the system"""
        print("Starting transaction generation...")
        print()
        
        # Start generation
        self.generate_transactions()
        
        # Show results
        self.show_statistics()
        
        # Save results
        self.save_results()
        
        print()
        print("=" * 70)
        print("[OK] SYSTEM RUN COMPLETE")
        print("=" * 70)
        print()
        print("Check 'output/' directory for CSV files")
        print()


def main():
    """Main entry point"""
    try:
        system = StandaloneRiskSystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

