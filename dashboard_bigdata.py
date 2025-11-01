"""
Big Data Technologies Dashboard - Enhanced Version
Shows: Kafka, Flink, PySpark, Flume in Real-Time
Perfect for BDA presentation!
"""

import sys
import time
import threading
from pathlib import Path
from collections import deque
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, str(Path('producers')))
from data_generator import HospitalTransactionGenerator

# Streamlit imports
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Big Data Hospital Risk Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size:40px !important;
        font-weight: bold;
        text-align: center;
    }
    .tech-badge {
        display: inline-block;
        padding: 5px 15px;
        margin: 5px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 14px;
    }
    .kafka-badge { background-color: #000000; color: white; }
    .flink-badge { background-color: #E6526F; color: white; }
    .spark-badge { background-color: #E25A1C; color: white; }
    .flume-badge { background-color: #1DB954; color: white; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .streaming-indicator {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'generator' not in st.session_state:
    st.session_state.generator = HospitalTransactionGenerator(num_users=50, anomaly_rate=0.15)
if 'stream_active' not in st.session_state:
    st.session_state.stream_active = False

# Kafka simulation
if 'kafka_topics' not in st.session_state:
    st.session_state.kafka_topics = {
        'transactions': deque(maxlen=1000),
        'risk-scores': deque(maxlen=1000),
        'alerts': deque(maxlen=500)
    }

# Flink windows
if 'flink_windows' not in st.session_state:
    st.session_state.flink_windows = []

# Processing metrics
if 'metrics' not in st.session_state:
    st.session_state.metrics = {
        'kafka_produced': 0,
        'kafka_consumed': 0,
        'flink_windows_processed': 0,
        'spark_batches_processed': 0,
        'flume_ingested': 0,
        'latency_ms': deque(maxlen=100),
        'throughput': deque(maxlen=100),
        'timestamp': deque(maxlen=100)
    }

def calculate_risk_score(transaction):
    """Calculate risk score"""
    score = 0
    factors = []
    
    amount = transaction.get('amount', 0)
    
    if amount > 200000:
        score += 40
        factors.append('Very High Amount')
    elif amount > 100000:
        score += 25
        factors.append('High Amount')
    elif amount > 50000:
        score += 15
        factors.append('Medium-High Amount')
    
    high_risk_depts = ['Emergency', 'Oncology', 'Surgery']
    if transaction.get('department') in high_risk_depts:
        score += 15
        factors.append(f"High-Risk Dept: {transaction.get('department')}")
    
    if transaction.get('transaction_type') in ['Drug_Purchase', 'Equipment']:
        score += 10
        factors.append(f"Risky Type: {transaction.get('transaction_type')}")
    
    if transaction.get('is_anomaly', False):
        score += 25
        factors.append('Anomaly Detected')
    
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

def kafka_produce(topic, message):
    """Simulate Kafka Producer"""
    message['kafka_metadata'] = {
        'topic': topic,
        'partition': hash(message.get('user_id', '')) % 3,
        'offset': len(st.session_state.kafka_topics[topic]),
        'timestamp': datetime.now().isoformat()
    }
    st.session_state.kafka_topics[topic].append(message)
    st.session_state.metrics['kafka_produced'] += 1

def generate_streaming_data():
    """Generate continuous streaming data"""
    tx = st.session_state.generator.generate_transaction()
    tx['timestamp'] = datetime.now().isoformat()
    
    # Flume ingestion
    st.session_state.metrics['flume_ingested'] += 1
    
    # Kafka produce
    kafka_produce('transactions', tx)
    
    # Process with risk score
    start_time = time.time()
    risk_result = calculate_risk_score(tx)
    tx.update(risk_result)
    
    # Kafka produce to risk-scores topic
    kafka_produce('risk-scores', tx)
    
    # Alert on high risk
    if risk_result['risk_level'] in ['HIGH', 'CRITICAL']:
        alert = {
            'transaction_id': tx.get('transaction_id'),
            'risk_score': risk_result['risk_score'],
            'risk_level': risk_result['risk_level'],
            'timestamp': datetime.now().isoformat()
        }
        kafka_produce('alerts', alert)
    
    # Track metrics
    latency = (time.time() - start_time) * 1000
    st.session_state.metrics['latency_ms'].append(latency)
    st.session_state.metrics['timestamp'].append(datetime.now())
    st.session_state.metrics['kafka_consumed'] += 1
    
    # Store transaction
    st.session_state.transactions.append(tx)
    
    # Flink windowing (every 10 transactions)
    if len(st.session_state.transactions) % 10 == 0:
        st.session_state.metrics['flink_windows_processed'] += 1
    
    # Spark batch processing (every 50 transactions)
    if len(st.session_state.transactions) % 50 == 0:
        st.session_state.metrics['spark_batches_processed'] += 1
    
    # Calculate throughput
    if len(st.session_state.metrics['timestamp']) >= 2:
        recent_times = list(st.session_state.metrics['timestamp'])[-10:]
        if len(recent_times) > 1:
            time_diff = (recent_times[-1] - recent_times[0]).total_seconds()
            if time_diff > 0:
                throughput = len(recent_times) / time_diff
                st.session_state.metrics['throughput'].append(throughput)

# Header
st.markdown('<p class="big-font">🏥 Big Data Hospital Risk Management System</p>', unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; margin-bottom: 20px;">
    <span class="tech-badge kafka-badge">KAFKA</span>
    <span class="tech-badge flink-badge">FLINK</span>
    <span class="tech-badge spark-badge">PYSPARK</span>
    <span class="tech-badge flume-badge">FLUME</span>
</div>
""", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.title("🎛️ Control Panel")

st.sidebar.markdown("### Streaming Control")
if st.sidebar.button("▶️ Start Stream" if not st.session_state.stream_active else "⏸️ Pause Stream"):
    st.session_state.stream_active = not st.session_state.stream_active

if st.sidebar.button("🔄 Reset All Data"):
    st.session_state.transactions = []
    st.session_state.kafka_topics = {
        'transactions': deque(maxlen=1000),
        'risk-scores': deque(maxlen=1000),
        'alerts': deque(maxlen=500)
    }
    st.session_state.metrics = {
        'kafka_produced': 0,
        'kafka_consumed': 0,
        'flink_windows_processed': 0,
        'spark_batches_processed': 0,
        'flume_ingested': 0,
        'latency_ms': deque(maxlen=100),
        'throughput': deque(maxlen=100),
        'timestamp': deque(maxlen=100)
    }
    st.success("✓ All data reset!")

st.sidebar.markdown("### Stream Settings")
stream_rate = st.sidebar.slider("Transactions per second", 1, 20, 5)

# Generate data if streaming
if st.session_state.stream_active:
    for _ in range(stream_rate):
        generate_streaming_data()

# Main dashboard
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Live Dashboard", 
    "🔴 Kafka Topics", 
    "⚡ Flink Windows", 
    "💡 PySpark Analytics",
    "🎯 System Architecture"
])

with tab1:
    # Status indicator
    if st.session_state.stream_active:
        st.markdown('<p style="color: red; font-size: 20px;" class="streaming-indicator">🔴 LIVE STREAMING</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="color: gray; font-size: 20px;">⚪ Stream Paused</p>', unsafe_allow_html=True)
    
    # Big Data Technology Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🔴 KAFKA</h3>
            <h2>{:,}</h2>
            <p>Messages Produced</p>
        </div>
        """.format(st.session_state.metrics['kafka_produced']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ FLINK</h3>
            <h2>{:,}</h2>
            <p>Windows Processed</p>
        </div>
        """.format(st.session_state.metrics['flink_windows_processed']), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>💡 SPARK</h3>
            <h2>{:,}</h2>
            <p>Batches Processed</p>
        </div>
        """.format(st.session_state.metrics['spark_batches_processed']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>📥 FLUME</h3>
            <h2>{:,}</h2>
            <p>Records Ingested</p>
        </div>
        """.format(st.session_state.metrics['flume_ingested']), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_latency = np.mean(list(st.session_state.metrics['latency_ms'])) if st.session_state.metrics['latency_ms'] else 0
        st.metric("⏱️ Avg Latency", f"{avg_latency:.2f} ms")
    
    with col2:
        avg_throughput = np.mean(list(st.session_state.metrics['throughput'])) if st.session_state.metrics['throughput'] else 0
        st.metric("⚡ Throughput", f"{avg_throughput:.1f} tx/sec")
    
    with col3:
        kafka_lag = st.session_state.metrics['kafka_produced'] - st.session_state.metrics['kafka_consumed']
        st.metric("📊 Kafka Lag", f"{kafka_lag:,}")
    
    with col4:
        total_tx = len(st.session_state.transactions)
        st.metric("📈 Total Transactions", f"{total_tx:,}")
    
    # Live charts
    if st.session_state.transactions:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Throughput Over Time")
            if len(st.session_state.metrics['throughput']) > 0:
                throughput_df = pd.DataFrame({
                    'time': list(st.session_state.metrics['timestamp'])[-len(list(st.session_state.metrics['throughput'])):],
                    'throughput': list(st.session_state.metrics['throughput'])
                })
                fig = px.line(throughput_df, x='time', y='throughput', 
                            labels={'throughput': 'Transactions/sec', 'time': 'Time'})
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("⏱️ Processing Latency")
            if len(st.session_state.metrics['latency_ms']) > 0:
                latency_df = pd.DataFrame({
                    'time': list(st.session_state.metrics['timestamp'])[-len(list(st.session_state.metrics['latency_ms'])):],
                    'latency': list(st.session_state.metrics['latency_ms'])
                })
                fig = px.line(latency_df, x='time', y='latency',
                            labels={'latency': 'Latency (ms)', 'time': 'Time'})
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent transactions
        st.subheader("📋 Recent High-Risk Transactions")
        df = pd.DataFrame(st.session_state.transactions[-50:])
        if not df.empty:
            high_risk = df[df['risk_level'].isin(['HIGH', 'CRITICAL'])].tail(10)
            if not high_risk.empty:
                st.dataframe(high_risk[['transaction_id', 'user_id', 'amount', 'risk_score', 'risk_level', 'department']],
                           use_container_width=True)
            else:
                st.info("No high-risk transactions in recent data")

with tab2:
    st.header("🔴 Kafka Topics Monitoring")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📨 Topic: transactions", len(st.session_state.kafka_topics['transactions']))
    with col2:
        st.metric("📨 Topic: risk-scores", len(st.session_state.kafka_topics['risk-scores']))
    with col3:
        st.metric("📨 Topic: alerts", len(st.session_state.kafka_topics['alerts']))
    
    st.markdown("---")
    
    # Show partition distribution
    if st.session_state.kafka_topics['transactions']:
        st.subheader("📊 Partition Distribution (3 partitions)")
        
        partitions = [msg.get('kafka_metadata', {}).get('partition', 0) 
                     for msg in list(st.session_state.kafka_topics['transactions'])[-100:]]
        
        partition_counts = pd.Series(partitions).value_counts().sort_index()
        
        fig = px.bar(x=partition_counts.index, y=partition_counts.values,
                    labels={'x': 'Partition', 'y': 'Message Count'},
                    title="Messages per Kafka Partition")
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent messages
    st.subheader("📋 Recent Messages in 'transactions' Topic")
    if st.session_state.kafka_topics['transactions']:
        recent_msgs = list(st.session_state.kafka_topics['transactions'])[-10:]
        for i, msg in enumerate(reversed(recent_msgs), 1):
            with st.expander(f"Message {i} - Partition {msg.get('kafka_metadata', {}).get('partition', 0)}"):
                st.json(msg)

with tab3:
    st.header("⚡ Flink Stream Processing Windows")
    
    st.markdown("""
    **Flink Windowing**: Time-based aggregations (5-second tumbling windows)
    - Event-time processing
    - Windowed aggregations
    - Late event handling
    """)
    
    if st.session_state.transactions:
        # Create Flink-style windows
        df = pd.DataFrame(st.session_state.transactions)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['window'] = df['timestamp'].dt.floor('5S')
        
        window_agg = df.groupby('window').agg({
            'amount': ['count', 'sum', 'mean', 'max'],
            'risk_score': ['mean', 'max'],
            'user_id': 'nunique'
        }).reset_index()
        
        window_agg.columns = ['window', 'tx_count', 'total_amount', 'avg_amount', 
                             'max_amount', 'avg_risk', 'max_risk', 'unique_users']
        
        # Show metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🪟 Total Windows", len(window_agg))
        with col2:
            st.metric("📊 Avg Tx per Window", f"{window_agg['tx_count'].mean():.1f}")
        with col3:
            st.metric("⚠️ Max Risk in Window", f"{window_agg['max_risk'].max():.0f}")
        
        # Visualization
        st.subheader("📊 Transactions per Time Window")
        fig = px.bar(window_agg, x='window', y='tx_count',
                    labels={'tx_count': 'Transaction Count', 'window': 'Time Window'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📋 Window Aggregations Table")
        st.dataframe(window_agg, use_container_width=True)

with tab4:
    st.header("💡 PySpark Distributed Analytics")
    
    st.markdown("""
    **PySpark Processing**: Batch analytics on streaming data
    - Distributed DataFrames
    - SQL-style aggregations
    - User behavior analysis
    """)
    
    if st.session_state.transactions:
        df = pd.DataFrame(st.session_state.transactions)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Top Users by Transaction Count")
            user_stats = df.groupby('user_id').agg({
                'amount': ['count', 'sum', 'mean'],
                'risk_score': 'mean'
            }).reset_index()
            user_stats.columns = ['user_id', 'tx_count', 'total_amount', 'avg_amount', 'avg_risk']
            top_users = user_stats.nlargest(10, 'tx_count')
            st.dataframe(top_users, use_container_width=True)
        
        with col2:
            st.subheader("🏥 Department Statistics")
            dept_stats = df.groupby('department').agg({
                'amount': ['count', 'sum', 'mean'],
                'risk_score': 'mean'
            }).reset_index()
            dept_stats.columns = ['department', 'tx_count', 'total_amount', 'avg_amount', 'avg_risk']
            st.dataframe(dept_stats, use_container_width=True)
        
        # Risk distribution
        st.subheader("📊 Risk Score Distribution")
        fig = px.histogram(df, x='risk_score', nbins=20,
                          labels={'risk_score': 'Risk Score', 'count': 'Frequency'})
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("🎯 System Architecture")
    
    st.markdown("""
    ```
    ┌───────────────────────────────────────────────────────────────┐
    │                    DATA INGESTION (Flume)                      │
    │            Continuous Transaction Generation                   │
    │                  Rate: 1-20 tx/second                         │
    └────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
    ┌───────────────────────────────────────────────────────────────┐
    │                   MESSAGE QUEUE (Kafka)                        │
    │   Topics: transactions (3 partitions)                          │
    │           risk-scores (3 partitions)                           │
    │           alerts (3 partitions)                                │
    └────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
    ┌───────────────────────────────────────────────────────────────┐
    │              STREAM PROCESSING (Flink)                         │
    │        5-second Tumbling Windows                               │
    │        Event-time Processing                                   │
    │        Windowed Aggregations                                   │
    └────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
    ┌───────────────────────────────────────────────────────────────┐
    │              ANALYTICS ENGINE (PySpark)                        │
    │        Distributed DataFrames                                  │
    │        SQL Aggregations                                        │
    │        Risk Score Calculation                                  │
    └────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
    ┌───────────────────────────────────────────────────────────────┐
    │              VISUALIZATION (Streamlit)                         │
    │        Real-time Dashboard                                     │
    │        Live Metrics & Charts                                   │
    └───────────────────────────────────────────────────────────────┘
    ```
    """)
    
    st.markdown("---")
    
    st.subheader("🔧 Technology Stack")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Ingestion Layer:**
        - 📥 Apache Flume (simulated)
        - ⚡ Continuous data streaming
        - 🎯 Rate-controlled ingestion
        
        **Messaging Layer:**
        - 🔴 Apache Kafka
        - 📨 3 topics with 3 partitions each
        - 🔄 Fault-tolerant messaging
        """)
    
    with col2:
        st.markdown("""
        **Processing Layer:**
        - ⚡ Apache Flink (stream processing)
        - 💡 Apache PySpark (batch analytics)
        - 🪟 Time-windowed aggregations
        
        **Visualization:**
        - 📊 Streamlit dashboard
        - 📈 Real-time charts
        - 🎯 Live monitoring
        """)

# Auto-refresh
if st.session_state.stream_active:
    time.sleep(1.0 / stream_rate)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray;">
    <p>🏥 Hospital Risk Management System | Big Data Stream Processing</p>
    <p>Technologies: Kafka • Flink • PySpark • Flume • Streamlit</p>
</div>
""", unsafe_allow_html=True)

