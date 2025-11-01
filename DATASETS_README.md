# 📊 Datasets Documentation

## Hospital Risk Management System - Datasets

This document describes all datasets available in the system, both synthetic and real-world based.

---

## 📁 Available Datasets

### 1. Healthcare Fraud Synthetic Dataset
**File**: `datasets/healthcare_fraud_synthetic.csv`
**Size**: ~432 KB | **Records**: 5,000

#### Description
Synthetic healthcare fraud detection dataset mimicking real-world medical claims and billing patterns.

#### Columns
- `transaction_id`: Unique transaction identifier (TXN000001-TXN005000)
- `provider_id`: Healthcare provider ID (PROV0001-PROV0099)
- `patient_id`: Patient identifier (PAT00001-PAT00999)
- `claim_amount`: Claim amount in USD (log-normal distribution)
- `procedure_code`: Medical procedure codes (CPT codes)
- `diagnosis_code`: ICD-10 diagnosis codes
- `department`: Hospital department
- `service_date`: Date of service (last 365 days)
- `payment_status`: Paid, Pending, Rejected, Under Review
- `potential_fraud`: Binary flag (1=fraud, 0=legitimate) - **15% fraud rate**

#### Use Cases
- Training fraud detection models
- Pattern recognition for suspicious claims
- Establishing baseline for normal vs fraudulent behavior
- ML model development and testing

#### Statistics
```
Total Records: 5,000
Fraudulent: 751 (15.0%)
Legitimate: 4,249 (85.0%)
Departments: 7 (Emergency, Cardiology, Neurology, Surgery, etc.)
Procedure Codes: 9 common CPT codes
```

---

### 2. Hospital Financial Transactions Dataset
**File**: `datasets/hospital_financial_transactions.csv`
**Size**: ~922 KB | **Records**: 10,000

#### Description
Comprehensive hospital accounting transactions with pre-calculated risk scores based on multiple factors.

#### Columns
- `transaction_id`: Unique transaction ID (TXN0000001-TXN0010000)
- `timestamp`: Transaction timestamp (ISO 8601 format)
- `user_id`: User who initiated transaction (USER_0001-USER_0050)
- `account_id`: Account identifier (ACC_1000-ACC_9999)
- `department`: Hospital department (10 departments)
- `transaction_type`: Type of transaction (8 types)
- `amount`: Transaction amount in USD
- `risk_score`: Calculated risk score (0-100)
- `is_high_risk`: Binary flag (1=high risk, 0=normal)

#### Transaction Types
1. **billing** - Patient billing entries
2. **payment** - Payment received
3. **refund** - Refund processed
4. **transfer** - Fund transfers
5. **adjustment** - Accounting adjustments
6. **insurance_claim** - Insurance claims
7. **payroll** - Payroll payments
8. **procurement** - Procurement expenses

#### Risk Score Distribution
```
Low Risk (0-30): 93.5%
Medium Risk (31-70): Not explicitly tracked
High Risk (71-100): 6.5% (647 transactions)

Average Amount: $35,250.65
Total Volume: $352.5 Million
```

#### Use Cases
- Historical transaction analysis
- Establishing transaction baselines
- Risk score validation
- Dashboard visualization
- Database seed data

---

### 3. User Behavior Profiles Dataset
**File**: `datasets/user_behavior_profiles.csv`
**Size**: ~3 KB | **Records**: 50

#### Description
User behavior baselines for all 50 simulated hospital users, used for detecting deviations from normal patterns.

#### Columns
- `user_id`: Unique user identifier (USER_0001-USER_0050)
- `role`: User role (accountant, admin, manager, clerk, finance_officer)
- `primary_department`: Main department assignment
- `avg_transactions_per_day`: Average daily transaction count
- `avg_transaction_amount`: Average transaction amount
- `typical_hours_start`: Typical work start hour (7-10 AM)
- `typical_hours_end`: Typical work end hour (4-7 PM)
- `baseline_risk_score`: User's baseline risk score (20-40)
- `years_employed`: Years of employment (1-20)
- `violation_count`: Previous violations (0-2)

#### Use Cases
- Behavioral anomaly detection
- User-specific risk scoring
- Identifying unusual transaction patterns
- Access control and monitoring
- Compliance tracking

#### Profile Statistics
```
Total Users: 50
Roles: 5 different roles
Departments: 10 departments
Most users: 0 violations (clean record)
Average baseline risk: ~30
```

---

### 4. Transaction Patterns Dataset
**File**: `datasets/transaction_patterns.csv`
**Size**: ~0.6 KB | **Records**: 6

#### Description
Known risky transaction patterns used for rule-based detection and pattern matching.

#### Patterns Defined

1. **Late Night Transactions** (PTN001)
   - Risk Level: HIGH
   - Description: Multiple transactions between 11 PM and 5 AM
   - Threshold: 3+ transactions in 6-hour window
   - Risk Score Increase: +25 points

2. **Rapid Succession** (PTN002)
   - Risk Level: HIGH
   - Description: Many transactions in short time period
   - Threshold: 10+ transactions in 1-hour window
   - Risk Score Increase: +30 points

3. **High Value Spike** (PTN003)
   - Risk Level: MEDIUM
   - Description: Transaction amount >3x user average
   - Threshold: 1 transaction in 24-hour window
   - Risk Score Increase: +20 points

4. **Weekend Activity** (PTN004)
   - Risk Level: MEDIUM
   - Description: Unusual weekend transactions
   - Threshold: 5+ transactions in 48-hour window
   - Risk Score Increase: +15 points

5. **Department Hopping** (PTN005)
   - Risk Level: HIGH
   - Description: Transactions across multiple departments rapidly
   - Threshold: 4+ departments in 2-hour window
   - Risk Score Increase: +25 points

6. **Round Number Amounts** (PTN006)
   - Risk Level: LOW
   - Description: Many transactions with round amounts
   - Threshold: 5+ round amounts in 24-hour window
   - Risk Score Increase: +10 points

#### Use Cases
- Rule-based risk detection
- Pattern matching in transaction streams
- Risk score calculation
- Alert generation
- Compliance monitoring

---

### 5. Sample Transactions Dataset
**File**: `datasets/sample_transactions.csv`
**Size**: <1 KB | **Records**: 10

#### Description
Small sample dataset for quick testing and verification of the system.

#### Columns
- `transaction_id`: Transaction ID
- `timestamp`: Transaction time
- `user_id`: User identifier
- `account_id`: Account identifier
- `department`: Department
- `transaction_type`: Type
- `amount`: Amount in USD
- `description`: Transaction description

#### Use Cases
- System testing
- Quick verification
- Development and debugging
- Example data format

---

## 🔄 Data Integration

### Loading Datasets into Database

To load the datasets into the PostgreSQL database:

```bash
# Wait for database to be ready
docker-compose ps postgres

# Run the dataset loader
python scripts/load_datasets_to_db.py
```

This will:
1. ✅ Load user behavior profiles
2. ✅ Import financial transactions (10,000 records)
3. ✅ Store transaction patterns
4. ✅ Log fraud dataset statistics
5. ✅ Update system metrics

### Data Flow

```
CSV Files → Python Script → PostgreSQL Database → Dashboard Visualization
```

---

## 📈 Dataset Statistics Summary

| Dataset | Records | Size | Fraud/Risk Rate |
|---------|---------|------|-----------------|
| Healthcare Fraud | 5,000 | 432 KB | 15.0% fraud |
| Financial Transactions | 10,000 | 922 KB | 6.5% high-risk |
| User Profiles | 50 | 3 KB | Baseline data |
| Transaction Patterns | 6 | 0.6 KB | Rules |
| Sample Data | 10 | <1 KB | Test data |
| **TOTAL** | **15,066** | **~1.3 MB** | - |

---

## 🎯 Real-World Dataset Sources

For production or research use, consider these real datasets:

### Kaggle Datasets (Recommended)

1. **Healthcare Provider Fraud Detection**
   ```bash
   kaggle datasets download -d rohitrox/healthcare-provider-fraud-detection-analysis
   ```

2. **Healthcare Dataset**
   ```bash
   kaggle datasets download -d prasad22/healthcare-dataset
   ```

3. **Daily Transactions Dataset**
   ```bash
   kaggle datasets download -d prasad22/daily-transactions-dataset
   ```

4. **Healthcare Fraud Detection**
   ```bash
   kaggle datasets download -d rohitrox/healthcare-provider-fraud-detection-analysis
   ```

5. **Financial Transactions**
   ```bash
   kaggle datasets download -d teamincribo/financial-transactions
   ```

### Setup Kaggle CLI

1. Create account at https://www.kaggle.com/
2. Get API credentials from https://www.kaggle.com/account
3. Install Kaggle CLI:
   ```bash
   pip install kaggle
   ```
4. Place `kaggle.json` in:
   - Windows: `C:\Users\<username>\.kaggle\`
   - Linux/Mac: `~/.kaggle/`
5. Download datasets using commands above

---

## 🔧 Dataset Generation

All synthetic datasets are generated using `scripts/download_datasets.py`:

```bash
python scripts/download_datasets.py
```

This script:
- ✅ Generates realistic transaction data
- ✅ Injects anomalies at configurable rates
- ✅ Creates user profiles with normal behavior
- ✅ Defines transaction patterns
- ✅ Produces properly formatted CSV files

### Customization

Edit `scripts/download_datasets.py` to adjust:
- Number of records
- Anomaly/fraud rate
- Transaction types
- Amount distributions
- Time ranges

---

## 📊 Data Quality

### Synthetic Data Characteristics

✅ **Realistic distributions**: Log-normal for amounts, normal for times
✅ **Business rules**: Business hours, department assignments
✅ **Anomaly injection**: Controlled fraud/risk rates
✅ **Variety**: Multiple transaction types and departments
✅ **Consistency**: Proper data types and formats
✅ **Scalability**: Can generate millions of records

### Data Validation

The datasets have been validated for:
- ✅ No missing values in critical fields
- ✅ Proper data types (dates, numbers, strings)
- ✅ Valid ranges (amounts > 0, scores 0-100)
- ✅ Referential integrity (user IDs, account IDs)
- ✅ Business logic (hours, dates, departments)

---

## 💡 Usage Tips

### For Development
- Use `sample_transactions.csv` for quick tests
- Load full datasets for realistic testing
- Adjust anomaly rates in generator

### For Demonstration
- Load all datasets for comprehensive view
- Show statistics from dataset summary
- Highlight fraud detection accuracy

### For Production
- Consider real Kaggle datasets
- Blend synthetic with real data
- Implement continuous data validation
- Monitor data quality metrics

---

## 🎓 Academic Reference

These datasets support the implementation of:
- Big data stream processing
- Real-time anomaly detection
- Risk scoring algorithms
- Fraud detection systems
- Healthcare analytics

Based on: **IEEE Paper - "A Big Data Stream-Driven Risk Recognition Approach for Hospital Accounting Management Systems"**

---

## 📞 Dataset Support

### Regenerate Datasets
```bash
python scripts/download_datasets.py
```

### Load into Database
```bash
python scripts/load_datasets_to_db.py
```

### Verify Data
```bash
docker-compose exec postgres psql -U hospital_admin -d hospital_risk_db
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM user_profiles;
```

---

**Last Updated**: October 13, 2024
**Version**: 1.0.0
**Status**: ✅ Complete with 15,066 records across 5 datasets

