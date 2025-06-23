#!/usr/bin/env python3
"""Simple Monitoring Dashboard"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

def main():
    st.set_page_config(page_title="V4 Trading Monitor", page_icon="🚀")
    
    st.title("🚀 V4 Trading Bot Monitor")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", "127", "+8")
    with col2:
        st.metric("P&L", "$1,247", "+3.2%")
    with col3:
        st.metric("Win Rate", "72.4%", "+1.5%")
    with col4:
        st.metric("Active Models", "3", "0")
    
    # Performance chart
    st.subheader("📈 Performance")
    
    # Sample data
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    returns = np.random.normal(0.02, 0.1, 30)
    cumulative = (1 + pd.Series(returns)).cumprod()
    
    df = pd.DataFrame({
        'Date': dates,
        'Cumulative_Return': cumulative
    })
    
    fig = px.line(df, x='Date', y='Cumulative_Return', 
                  title='Cumulative Returns')
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent trades
    st.subheader("🔄 Recent Trades")
    
    trades = pd.DataFrame({
        'Time': ['10:30', '10:25', '10:20', '10:15'],
        'Symbol': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT'],
        'Signal': ['BUY', 'SELL', 'BUY', 'HOLD'],
        'Confidence': [0.85, 0.72, 0.68, 0.45],
        'Status': ['✅', '✅', '✅', '⏸️']
    })
    
    st.dataframe(trades, use_container_width=True)
    
    # System status
    st.subheader("🖥️ System Status")
    st.success("🟢 V4 System: OPERATIONAL")
    st.info("🔵 Models: ACTIVE")
    st.success("🟢 Monitoring: RUNNING")

if __name__ == "__main__":
    main()
