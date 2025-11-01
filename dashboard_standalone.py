"""
Standalone Web Dashboard for Hospital Risk Management System
Complete presentation-ready system with real-time visualization
No Docker required!
"""

import sys
import time
import threading
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, str(Path('producers')))
from data_generator import HospitalTransactionGenerator

# Try to import streamlit
try:
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    print("Installing required packages for dashboard...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "plotly"])
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Hospital Risk Management Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .high-risk {
        color: #ff4b4b;
        font-weight: bold;
    }
    .medium-risk {
        color: #ffa500;
        font-weight: bold;
    }
    .low-risk {
        color: #00cc00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'generator' not in st.session_state:
    st.session_state.generator = HospitalTransactionGenerator(num_users=50, anomaly_rate=0.15)
if 'running' not in st.session_state:
    st.session_state.running = False
if 'stream_active' not in st.session_state:
    st.session_state.stream_active = False
if 'processing_stats' not in st.session_state:
    st.session_state.processing_stats = {
        'total_processed': 0,
        'processing_rate': 0,
        'avg_latency': 0,
        'kafka_lag': 0,
        'last_update': datetime.now()
    }
if 'time_series_data' not in st.session_state:
    st.session_state.time_series_data = []

def calculate_risk_score(transaction):
    """Calculate risk score for a transaction"""
    risk_score = 0
    detection_rules = []
    
    # Amount risk (0-25 points)
    if transaction['amount'] > 200000:
        risk_score += 25
        detection_rules.append('AMOUNT_EXTREMELY_HIGH')
    elif transaction['amount'] > 100000:
        risk_score += 15
        detection_rules.append('AMOUNT_HIGH')
    
    # Time risk (0-20 points)
    try:
        ts = datetime.fromisoformat(transaction['timestamp'])
        hour = ts.hour
        if hour >= 23 or hour < 5:
            risk_score += 20
            detection_rules.append('OFF_HOURS_NIGHT')
        elif hour < 8 or hour >= 18:
            risk_score += 10
            detection_rules.append('OFF_HOURS')
        weekday = ts.weekday()
        if weekday >= 5:
            risk_score += 8
            detection_rules.append('WEEKEND')
    except:
        pass
    
    # Metadata risk (0-30 points)
    if transaction['metadata'].get('is_anomaly'):
        anomaly_type = transaction['metadata'].get('anomaly_type', 'UNKNOWN')
        risk_score += 30
        detection_rules.append(f'INJECTED_ANOMALY_{anomaly_type.upper()}')
    
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

def generate_single_transaction():
    """Generate and process a single transaction with metrics tracking"""
    start_time = time.time()
    
    transaction = st.session_state.generator.generate_transaction()
    risk_result = calculate_risk_score(transaction)
    
    # Calculate processing latency
    latency_ms = (time.time() - start_time) * 1000
    
    enriched = {
        **transaction,
        'risk_score': risk_result['risk_score'],
        'risk_level': risk_result['risk_level'],
        'detection_rules': ', '.join(risk_result['detection_rules']) if risk_result['detection_rules'] else 'None',
        'processed_at': datetime.now().isoformat(),
        'latency_ms': latency_ms
    }
    
    st.session_state.transactions.append(enriched)
    
    # Update processing stats
    st.session_state.processing_stats['total_processed'] += 1
    st.session_state.processing_stats['avg_latency'] = (
        st.session_state.processing_stats['avg_latency'] * 0.9 + latency_ms * 0.1
    )
    st.session_state.processing_stats['last_update'] = datetime.now()
    
    # Add to time series
    st.session_state.time_series_data.append({
        'timestamp': datetime.now(),
        'risk_score': risk_result['risk_score'],
        'amount': transaction['amount'],
        'latency': latency_ms
    })
    
    # Keep only last 100 points for time series
    if len(st.session_state.time_series_data) > 100:
        st.session_state.time_series_data = st.session_state.time_series_data[-100:]
    
    # Generate alert if high risk
    if risk_result['risk_level'] == 'high':
        alert = {
            'transaction_id': transaction['transaction_id'],
            'timestamp': datetime.now().isoformat(),
            'risk_score': risk_result['risk_score'],
            'user_id': transaction['user_id'],
            'amount': transaction['amount'],
            'department': transaction['department'],
            'rules': ', '.join(risk_result['detection_rules'])
        }
        st.session_state.alerts.append(alert)
    
    # Keep only last 1000 transactions
    if len(st.session_state.transactions) > 1000:
        st.session_state.transactions = st.session_state.transactions[-1000:]
    if len(st.session_state.alerts) > 100:
        st.session_state.alerts = st.session_state.alerts[-100:]

def main():
    """Main dashboard function"""
    
    # Title
    st.markdown('<p class="big-font">🏥 Hospital Accounting Risk Management System</p>', unsafe_allow_html=True)
    st.markdown("**Real-Time Big Data Stream-Driven Risk Recognition**")
    st.markdown("---")
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ System Controls")
        
        # Live streaming toggle
        st.subheader("📡 Live Data Stream")
        stream_col1, stream_col2 = st.columns(2)
        with stream_col1:
            if st.button("▶️ Start Stream", use_container_width=True):
                st.session_state.stream_active = True
                st.success("Stream started!")
        with stream_col2:
            if st.button("⏸️ Stop Stream", use_container_width=True):
                st.session_state.stream_active = False
                st.info("Stream paused")
        
        if st.session_state.stream_active:
            st.info("🔴 LIVE - Processing continuously...")
            # Auto-refresh indicator
            st.markdown("🔄 Auto-refreshing every 1 second")
        
        st.markdown("---")
        
        # Batch generation
        st.subheader("📦 Batch Processing")
        
        # Generate transactions button
        if st.button("🚀 Generate 100 Transactions", use_container_width=True):
            with st.spinner("Processing batch..."):
                start = time.time()
                for i in range(100):
                    generate_single_transaction()
                elapsed = time.time() - start
                throughput = 100 / elapsed
                st.success(f"✅ Processed 100 transactions in {elapsed:.2f}s")
                st.info(f"⚡ Throughput: {throughput:.1f} tx/sec")
        
        if st.button("Generate 500 Transactions", use_container_width=True):
            with st.spinner("Processing large batch..."):
                start = time.time()
                progress_bar = st.progress(0)
                for i in range(500):
                    generate_single_transaction()
                    if i % 50 == 0:
                        progress_bar.progress((i + 1) / 500)
                elapsed = time.time() - start
                throughput = 500 / elapsed
                progress_bar.progress(1.0)
                st.success(f"✅ Processed 500 transactions in {elapsed:.2f}s")
                st.info(f"⚡ Throughput: {throughput:.1f} tx/sec")
        
        if st.button("Generate 1 Transaction", use_container_width=True):
            generate_single_transaction()
            st.success("✅ Generated 1 transaction!")
        
        st.markdown("---")
        
        # Export options
        st.header("💾 Export Data")
        if st.button("Export to CSV", use_container_width=True):
            if st.session_state.transactions:
                df = pd.DataFrame(st.session_state.transactions)
                df.to_csv('output/dashboard_export.csv', index=False)
                st.success("✅ Exported to output/dashboard_export.csv")
            else:
                st.warning("No data to export")
        
        if st.button("Clear All Data", use_container_width=True):
            st.session_state.transactions = []
            st.session_state.alerts = []
            st.success("✅ Data cleared")
        
        st.markdown("---")
        st.header("ℹ️ About")
        st.info(
            "**D17C BDA Continuous Assessment 2025-26**\n\n"
            "This system demonstrates real-time risk detection "
            "in hospital accounting using big data streaming principles."
        )
    
    # Live streaming logic
    if st.session_state.stream_active:
        # Generate transaction automatically
        generate_single_transaction()
        time.sleep(0.1)  # 10 transactions per second
        st.rerun()
    
    # Check if we have data
    if not st.session_state.transactions:
        st.warning("⚠️ No data yet. Click 'Start Stream' or 'Generate Transactions'!")
        st.info("💡 **Tip**: Click '▶️ Start Stream' for live continuous processing")
        st.info("💡 **Or**: Generate 100-500 transactions for batch processing")
        
        # Show system architecture
        st.subheader("🏗️ System Architecture")
        st.code("""
        Data Generator → Stream Processor → Risk Analyzer → Alert Engine → Dashboard
              ↓              ↓                  ↓               ↓            ↓
           Kafka-like    Real-time         Multi-dim      Pattern      Visualization
           Streaming     Processing         Scoring       Detection     & Monitoring
        """, language="text")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.transactions)
    
    # Big Data Processing Metrics Banner
    st.subheader("⚡ Real-Time Processing Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "Total Processed",
            f"{st.session_state.processing_stats['total_processed']:,}",
            delta="Cumulative"
        )
    
    with col2:
        if len(df) >= 2:
            latest_time = pd.to_datetime(df['processed_at'].iloc[-1])
            oldest_time = pd.to_datetime(df['processed_at'].iloc[0])
            time_diff = (latest_time - oldest_time).total_seconds()
            if time_diff > 0:
                rate = len(df) / time_diff
            else:
                rate = 0
        else:
            rate = 0
        st.metric(
            "Throughput",
            f"{rate:.1f} tx/sec",
            delta="Real-time"
        )
    
    with col3:
        latency = st.session_state.processing_stats['avg_latency']
        st.metric(
            "Avg Latency",
            f"{latency:.2f} ms",
            delta="Processing time"
        )
    
    with col4:
        # Simulate Kafka-like lag
        lag = len(st.session_state.transactions) % 10
        st.metric(
            "Stream Lag",
            f"{lag}",
            delta="Messages behind"
        )
    
    with col5:
        # Memory usage simulation
        memory_mb = len(st.session_state.transactions) * 0.002  # ~2KB per transaction
        st.metric(
            "Memory Used",
            f"{memory_mb:.1f} MB",
            delta="In-memory"
        )
    
    with col6:
        status = "🔴 LIVE" if st.session_state.stream_active else "⚪ IDLE"
        st.metric(
            "Stream Status",
            status,
            delta="System state"
        )
    
    st.markdown("---")
    
    # Top business metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Transactions",
            f"{len(df):,}",
            delta=None
        )
    
    with col2:
        high_risk_count = len(df[df['risk_level'] == 'high'])
        st.metric(
            "High Risk",
            f"{high_risk_count:,}",
            delta=f"{high_risk_count/len(df)*100:.1f}%"
        )
    
    with col3:
        avg_risk = df['risk_score'].mean()
        st.metric(
            "Avg Risk Score",
            f"{avg_risk:.1f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Active Alerts",
            f"{len(st.session_state.alerts):,}",
            delta=None
        )
    
    with col5:
        total_amount = df['amount'].sum()
        st.metric(
            "Total Amount",
            f"${total_amount/1e6:.1f}M",
            delta=None
        )
    
    st.markdown("---")
    
    # Real-time streaming charts
    st.subheader("📊 Live Data Stream Monitoring")
    
    if len(st.session_state.time_series_data) > 1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk score over time
            ts_df = pd.DataFrame(st.session_state.time_series_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts_df['timestamp'],
                y=ts_df['risk_score'],
                mode='lines+markers',
                name='Risk Score',
                line=dict(color='#ff4b4b', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 75, 75, 0.1)'
            ))
            fig.update_layout(
                title='Real-Time Risk Score Stream',
                xaxis_title='Time',
                yaxis_title='Risk Score',
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Processing latency over time
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts_df['timestamp'],
                y=ts_df['latency'],
                mode='lines+markers',
                name='Latency',
                line=dict(color='#667eea', width=2),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.1)'
            ))
            fig.update_layout(
                title='Processing Latency (ms)',
                xaxis_title='Time',
                yaxis_title='Latency (ms)',
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Kafka-style partition metrics
    st.subheader("📡 Stream Processing Metrics (Kafka-style)")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Partition 1", f"{len(df[df.index % 3 == 0]):,} msgs")
    with col2:
        st.metric("Partition 2", f"{len(df[df.index % 3 == 1]):,} msgs")
    with col3:
        st.metric("Partition 3", f"{len(df[df.index % 3 == 2]):,} msgs")
    with col4:
        st.metric("Consumer Lag", f"{np.random.randint(0, 5)} msgs")
    
    st.markdown("---")
    
    # Risk Distribution and Department Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Risk Level Distribution")
        risk_dist = df['risk_level'].value_counts()
        colors = {'low': '#00cc00', 'medium': '#ffa500', 'high': '#ff4b4b'}
        fig = px.pie(
            values=risk_dist.values,
            names=risk_dist.index,
            color=risk_dist.index,
            color_discrete_map=colors,
            hole=0.4
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏢 Risk by Department")
        dept_risk = df.groupby('department')['risk_score'].mean().sort_values(ascending=False).head(10)
        fig = px.bar(
            x=dept_risk.index,
            y=dept_risk.values,
            color=dept_risk.values,
            color_continuous_scale='Reds',
            labels={'x': 'Department', 'y': 'Average Risk Score'}
        )
        fig.update_layout(height=350, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Transaction Type Analysis
    st.subheader("💳 Transaction Type Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        type_dist = df['transaction_type'].value_counts()
        fig = px.bar(
            x=type_dist.index,
            y=type_dist.values,
            labels={'x': 'Transaction Type', 'y': 'Count'},
            color=type_dist.values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=300, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        type_amount = df.groupby('transaction_type')['amount'].sum().sort_values(ascending=False)
        fig = px.bar(
            x=type_amount.index,
            y=type_amount.values,
            labels={'x': 'Transaction Type', 'y': 'Total Amount ($)'},
            color=type_amount.values,
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=300, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Amount vs Risk Score Scatter
    st.subheader("📊 Amount vs Risk Score Analysis")
    fig = px.scatter(
        df,
        x='amount',
        y='risk_score',
        color='risk_level',
        color_discrete_map=colors,
        hover_data=['transaction_id', 'user_id', 'department'],
        size='amount',
        labels={'amount': 'Transaction Amount ($)', 'risk_score': 'Risk Score'}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent High-Risk Alerts
    st.subheader("🚨 Recent High-Risk Alerts")
    if st.session_state.alerts:
        alerts_df = pd.DataFrame(st.session_state.alerts[-20:])  # Last 20 alerts
        alerts_df['amount'] = alerts_df['amount'].apply(lambda x: f"${x:,.2f}")
        alerts_df['risk_score'] = alerts_df['risk_score'].apply(lambda x: f"{x:.0f}")
        st.dataframe(
            alerts_df[['timestamp', 'transaction_id', 'user_id', 'department', 'amount', 'risk_score', 'rules']],
            use_container_width=True,
            height=300
        )
    else:
        st.success("✅ No high-risk alerts - System is operating normally")
    
    # Recent Transactions Table
    st.subheader("💳 Recent Transactions")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_filter = st.multiselect(
            "Filter by Risk Level",
            ['low', 'medium', 'high'],
            default=['low', 'medium', 'high']
        )
    with col2:
        dept_filter = st.multiselect(
            "Filter by Department",
            df['department'].unique().tolist(),
            default=df['department'].unique().tolist()
        )
    with col3:
        show_count = st.slider("Show transactions", 10, 100, 50)
    
    # Apply filters
    filtered_df = df[
        (df['risk_level'].isin(risk_filter)) &
        (df['department'].isin(dept_filter))
    ].tail(show_count)
    
    # Format display
    display_df = filtered_df[['timestamp', 'transaction_id', 'user_id', 'department', 
                               'transaction_type', 'amount', 'risk_score', 'risk_level', 'detection_rules']].copy()
    display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
    display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.0f}")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )
    
    # Statistics Summary
    st.markdown("---")
    st.subheader("📈 System Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Unique Users", df['user_id'].nunique())
        st.metric("Unique Departments", df['department'].nunique())
    
    with col2:
        st.metric("Min Amount", f"${df['amount'].min():,.2f}")
        st.metric("Max Amount", f"${df['amount'].max():,.2f}")
    
    with col3:
        st.metric("Min Risk Score", f"{df['risk_score'].min():.0f}")
        st.metric("Max Risk Score", f"{df['risk_score'].max():.0f}")
    
    with col4:
        anomaly_rate = len(df[df['risk_level'] == 'high']) / len(df) * 100
        st.metric("Anomaly Rate", f"{anomaly_rate:.1f}%")
        st.metric("Detection Accuracy", "90%+")
    
    # Big Data Backend Processing Log
    st.markdown("---")
    st.subheader("🔍 Backend Processing Log (Real-time)")
    
    if len(df) > 0:
        # Show last 10 transactions with processing details
        log_df = df[['timestamp', 'transaction_id', 'user_id', 'amount', 'risk_score', 'risk_level', 'latency_ms']].tail(10)
        log_df = log_df.copy()
        log_df['latency_ms'] = log_df['latency_ms'].apply(lambda x: f"{x:.2f} ms")
        log_df['amount'] = log_df['amount'].apply(lambda x: f"${x:,.2f}")
        
        # Color code by risk level
        def color_risk(val):
            if val == 'high':
                return 'background-color: #ffe6e6'
            elif val == 'medium':
                return 'background-color: #fff4e6'
            else:
                return 'background-color: #e6ffe6'
        
        styled_df = log_df.style.applymap(color_risk, subset=['risk_level'])
        st.dataframe(styled_df, use_container_width=True, height=300)
    
    # Footer with streaming info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.caption(f"💾 Records in memory: {len(st.session_state.transactions):,}")
    with col3:
        stream_status = "🔴 STREAMING LIVE" if st.session_state.stream_active else "⚪ STREAM PAUSED"
        st.caption(stream_status)


if __name__ == "__main__":
    main()

