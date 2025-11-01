"""
Real-Time Hospital Risk Management Dashboard
Displays live metrics, transactions, and alerts
"""

import os
import json
import time
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
from kafka import KafkaConsumer
import threading
from collections import deque

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
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
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


class DatabaseConnection:
    """Handle PostgreSQL database connections"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'hospital_risk_db'),
            'user': os.getenv('POSTGRES_USER', 'hospital_admin'),
            'password': os.getenv('POSTGRES_PASSWORD', 'hospital_pass123')
        }
    
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(**self.config)
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        try:
            conn = self.get_connection()
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Database error: {e}")
            return pd.DataFrame()


@st.cache_resource
def get_db():
    """Get cached database connection"""
    return DatabaseConnection()


def load_metrics():
    """Load current system metrics"""
    db = get_db()
    
    # Total transactions
    total_query = "SELECT COUNT(*) as count FROM transactions"
    total_df = db.execute_query(total_query)
    total_transactions = total_df['count'].iloc[0] if not total_df.empty else 0
    
    # High risk count
    high_risk_query = "SELECT COUNT(*) as count FROM transactions WHERE risk_level = 'high'"
    high_risk_df = db.execute_query(high_risk_query)
    high_risk_count = high_risk_df['count'].iloc[0] if not high_risk_df.empty else 0
    
    # Average risk score
    avg_risk_query = "SELECT AVG(risk_score) as avg_risk FROM transactions"
    avg_risk_df = db.execute_query(avg_risk_query)
    avg_risk_score = avg_risk_df['avg_risk'].iloc[0] if not avg_risk_df.empty else 0
    
    # Active alerts
    alerts_query = "SELECT COUNT(*) as count FROM risk_alerts WHERE status = 'active'"
    alerts_df = db.execute_query(alerts_query)
    active_alerts = alerts_df['count'].iloc[0] if not alerts_df.empty else 0
    
    # Transactions in last hour
    recent_query = """
        SELECT COUNT(*) as count 
        FROM transactions 
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
    """
    recent_df = db.execute_query(recent_query)
    recent_count = recent_df['count'].iloc[0] if not recent_df.empty else 0
    
    return {
        'total_transactions': int(total_transactions),
        'high_risk_count': int(high_risk_count),
        'avg_risk_score': float(avg_risk_score) if avg_risk_score else 0.0,
        'active_alerts': int(active_alerts),
        'recent_count': int(recent_count)
    }


def load_recent_transactions(limit=100):
    """Load recent transactions"""
    db = get_db()
    query = """
        SELECT 
            transaction_id,
            timestamp,
            user_id,
            department,
            transaction_type,
            amount,
            risk_score,
            risk_level,
            is_anomaly
        FROM transactions
        ORDER BY timestamp DESC
        LIMIT %s
    """
    return db.execute_query(query, (limit,))


def load_recent_alerts(limit=50):
    """Load recent alerts"""
    db = get_db()
    query = """
        SELECT 
            a.alert_id,
            a.transaction_id,
            a.alert_type,
            a.severity,
            a.risk_score,
            a.alert_message,
            a.created_at,
            t.user_id,
            t.amount,
            t.department
        FROM risk_alerts a
        JOIN transactions t ON a.transaction_id = t.transaction_id
        ORDER BY a.created_at DESC
        LIMIT %s
    """
    return db.execute_query(query, (limit,))


def load_time_series_data():
    """Load transaction time series data"""
    db = get_db()
    query = """
        SELECT 
            DATE_TRUNC('minute', timestamp) as time_bucket,
            COUNT(*) as transaction_count,
            AVG(risk_score) as avg_risk_score,
            COUNT(CASE WHEN is_anomaly = TRUE THEN 1 END) as anomaly_count
        FROM transactions
        WHERE timestamp >= NOW() - INTERVAL '1 hour'
        GROUP BY time_bucket
        ORDER BY time_bucket
    """
    return db.execute_query(query)


def load_risk_distribution():
    """Load risk level distribution"""
    db = get_db()
    query = """
        SELECT 
            risk_level,
            COUNT(*) as count
        FROM transactions
        GROUP BY risk_level
    """
    return db.execute_query(query)


def load_department_stats():
    """Load statistics by department"""
    db = get_db()
    query = """
        SELECT 
            department,
            COUNT(*) as transaction_count,
            AVG(risk_score) as avg_risk_score,
            SUM(amount) as total_amount
        FROM transactions
        GROUP BY department
        ORDER BY avg_risk_score DESC
        LIMIT 10
    """
    return db.execute_query(query)


def load_user_risk_summary():
    """Load user risk summary"""
    db = get_db()
    query = """
        SELECT 
            user_id,
            COUNT(*) as total_transactions,
            AVG(risk_score) as avg_risk_score,
            MAX(risk_score) as max_risk_score,
            COUNT(CASE WHEN is_anomaly = TRUE THEN 1 END) as anomaly_count
        FROM transactions
        GROUP BY user_id
        ORDER BY avg_risk_score DESC
        LIMIT 15
    """
    return db.execute_query(query)


def main():
    """Main dashboard function"""
    
    # Title
    st.title("🏥 Hospital Accounting Risk Management Dashboard")
    st.markdown("Real-time monitoring of financial transactions and risk detection")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        auto_refresh = st.checkbox("Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh interval (seconds)", 2, 30, 5)
        
        st.header("📊 Filters")
        risk_filter = st.multiselect(
            "Risk Level",
            ['low', 'medium', 'high'],
            default=['low', 'medium', 'high']
        )
        
        st.header("ℹ️ About")
        st.info(
            "This dashboard provides real-time monitoring of hospital "
            "accounting transactions with advanced risk detection and anomaly scoring."
        )
    
    # Auto-refresh logic
    if auto_refresh:
        placeholder = st.empty()
        
        while True:
            with placeholder.container():
                render_dashboard(risk_filter)
            
            time.sleep(refresh_interval)
    else:
        render_dashboard(risk_filter)


def render_dashboard(risk_filter):
    """Render the dashboard content"""
    
    # Load metrics
    metrics = load_metrics()
    
    # Top metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Transactions",
            f"{metrics['total_transactions']:,}",
            delta=f"+{metrics['recent_count']} (1h)"
        )
    
    with col2:
        st.metric(
            "High Risk",
            f"{metrics['high_risk_count']:,}",
            delta=None
        )
    
    with col3:
        risk_score = metrics['avg_risk_score']
        st.metric(
            "Avg Risk Score",
            f"{risk_score:.1f}",
            delta=None
        )
    
    with col4:
        st.metric(
            "Active Alerts",
            f"{metrics['active_alerts']:,}",
            delta=None
        )
    
    with col5:
        throughput = metrics['recent_count'] / 60 if metrics['recent_count'] > 0 else 0
        st.metric(
            "Throughput",
            f"{throughput:.1f}/min",
            delta=None
        )
    
    # Divider
    st.divider()
    
    # Time series chart
    st.subheader("📈 Transaction Flow (Last Hour)")
    
    time_series_df = load_time_series_data()
    
    if not time_series_df.empty:
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Transaction Count', 'Average Risk Score'),
            vertical_spacing=0.15
        )
        
        fig.add_trace(
            go.Scatter(
                x=time_series_df['time_bucket'],
                y=time_series_df['transaction_count'],
                mode='lines+markers',
                name='Transactions',
                line=dict(color='#1f77b4', width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=time_series_df['time_bucket'],
                y=time_series_df['avg_risk_score'],
                mode='lines+markers',
                name='Avg Risk Score',
                line=dict(color='#ff7f0e', width=2)
            ),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Risk Score", row=2, col=1)
        
        fig.update_layout(height=500, showlegend=True)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transaction data available yet. Waiting for data stream...")
    
    # Two column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Risk Level Distribution")
        risk_dist_df = load_risk_distribution()
        
        if not risk_dist_df.empty:
            colors = {'low': '#00cc00', 'medium': '#ffa500', 'high': '#ff4b4b'}
            risk_dist_df['color'] = risk_dist_df['risk_level'].map(colors)
            
            fig = px.pie(
                risk_dist_df,
                values='count',
                names='risk_level',
                color='risk_level',
                color_discrete_map=colors,
                hole=0.4
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No risk distribution data available")
    
    with col2:
        st.subheader("🏢 Risk by Department")
        dept_df = load_department_stats()
        
        if not dept_df.empty:
            fig = px.bar(
                dept_df.head(8),
                x='department',
                y='avg_risk_score',
                color='avg_risk_score',
                color_continuous_scale='Reds',
                labels={'avg_risk_score': 'Avg Risk Score'}
            )
            fig.update_layout(height=350, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No department data available")
    
    # Recent alerts
    st.subheader("🚨 Recent High-Risk Alerts")
    
    alerts_df = load_recent_alerts(20)
    
    if not alerts_df.empty:
        # Format the dataframe
        alerts_display = alerts_df[['alert_id', 'user_id', 'amount', 'department', 
                                     'risk_score', 'severity', 'alert_message', 'created_at']]
        alerts_display['amount'] = alerts_display['amount'].apply(lambda x: f"${x:,.2f}")
        alerts_display['risk_score'] = alerts_display['risk_score'].apply(lambda x: f"{x:.2f}")
        alerts_display['created_at'] = pd.to_datetime(alerts_display['created_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(
            alerts_display,
            use_container_width=True,
            height=300
        )
    else:
        st.success("✅ No recent high-risk alerts")
    
    # Recent transactions
    st.subheader("💳 Recent Transactions")
    
    transactions_df = load_recent_transactions(50)
    
    if not transactions_df.empty:
        # Filter by risk level
        filtered_df = transactions_df[transactions_df['risk_level'].isin(risk_filter)]
        
        # Format the dataframe
        display_df = filtered_df[['transaction_id', 'timestamp', 'user_id', 'department',
                                   'transaction_type', 'amount', 'risk_score', 'risk_level']]
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
        display_df['risk_score'] = display_df['risk_score'].apply(lambda x: f"{x:.2f}")
        display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
    else:
        st.info("No transaction data available")
    
    # Top risky users
    st.subheader("👤 Top Risky Users")
    
    user_risk_df = load_user_risk_summary()
    
    if not user_risk_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.dataframe(
                user_risk_df[['user_id', 'total_transactions', 'avg_risk_score', 'anomaly_count']],
                use_container_width=True,
                height=300
            )
        
        with col2:
            fig = px.scatter(
                user_risk_df,
                x='total_transactions',
                y='avg_risk_score',
                size='anomaly_count',
                color='avg_risk_score',
                hover_data=['user_id'],
                color_continuous_scale='Reds',
                labels={
                    'total_transactions': 'Total Transactions',
                    'avg_risk_score': 'Average Risk Score'
                }
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No user data available")
    
    # Footer
    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

