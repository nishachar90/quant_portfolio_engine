"""
dashboard.py
NIFTY Quantitative Portfolio & Screener Dashboard.
Ye frontend app backend outputs (CSV, Parquet, Images) ko interactive web page me dikhata hai.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="NIFTY Quant Dashboard", page_icon="📈", layout="wide")

# --- DATA LOADING FUNCTIONS ---
# st.cache_data use karte hain taaki data baar-baar load na karna pade (fast performance)
@st.cache_data
def load_data():
    screener_path = "data/outputs/nifty_screener_rankings.csv"
    perf_path = "data/outputs/portfolio_performance.csv"
    prices_path = "data/cache/NIFTY50_prices.parquet"
    
    # Screener data load karo
    if os.path.exists(screener_path):
        df_screener = pd.read_csv(screener_path)
        # Unnamed: 0 ko Ticker bana do
        if 'Unnamed: 0' in df_screener.columns:
            df_screener.rename(columns={'Unnamed: 0': 'Ticker'}, inplace=True)
    else:
        df_screener = pd.DataFrame()

    # Performance metrics load karo
    df_perf = pd.read_csv(perf_path) if os.path.exists(perf_path) else pd.DataFrame()
    
    # Historical prices load karo comparison chart ke liye
    df_prices = pd.read_parquet(prices_path) if os.path.exists(prices_path) else pd.DataFrame()
    
    return df_screener, df_perf, df_prices

df_screener, df_perf, df_prices = load_data()

# --- HEADER ---
st.title("📈 NIFTY Quantitative Portfolio Dashboard")
st.markdown("Yeh dashboard tumhare 5-factor quant model aur backtest engine ka live interactive view hai.")

# Agar data missing hai to error dikhao
if df_screener.empty:
    st.error("⚠️ Data nahi mila! Pehle 'python3 run_pipeline.py' run karo taaki outputs generate ho sakein.")
    st.stop()

# --- TABS SETUP ---
tab1, tab2, tab3 = st.tabs(["📊 Stock Screener", "⚖️ Stock Comparison", "🚀 Portfolio Performance"])

# ==========================================
# TAB 1: STOCK SCREENER
# ==========================================
with tab1:
    st.header("🔍 NIFTY 50 Stock Screener")
    
    # Filters ke liye columns
    col1, col2 = st.columns(2)
    with col1:
        if 'Sector' in df_screener.columns:
            sector_filter = st.multiselect("Filter by Sector", options=df_screener['Sector'].unique())
        else:
            sector_filter = []
    with col2:
        if 'Action' in df_screener.columns:
            action_filter = st.multiselect("Filter by Action (Buy/Hold/Sell)", options=df_screener['Action'].unique(), default=["BUY (Top Decile)"])
        else:
            action_filter = []
    
    # Filter apply karo
    filtered_df = df_screener.copy()
    if sector_filter:
        filtered_df = filtered_df[filtered_df['Sector'].isin(sector_filter)]
    if action_filter:
        filtered_df = filtered_df[filtered_df['Action'].isin(action_filter)]
        
    # Dataframe display (Interactive Table)
    st.dataframe(
        filtered_df.style.background_gradient(cmap="Greens", subset=["Composite Score", "Trailing 1Y CAGR (%)", "ROE (%)"]),
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# TAB 2: STOCK COMPARISON
# ==========================================
with tab2:
    st.header("⚖️ Compare Stocks")
    
    # Dropdown to select stocks
    if 'Ticker' in df_screener.columns:
        available_tickers = df_screener['Ticker'].tolist()
    else:
        available_tickers = df_screener.index.tolist()
        
    selected_stocks = st.multiselect("Select 2 or more stocks to compare:", available_tickers, default=available_tickers[:2] if len(available_tickers)>=2 else available_tickers)
    
    if len(selected_stocks) >= 2:
        # 1. PRICE COMPARISON CHART (Normalized to 100)
        st.subheader("📈 Relative Price Performance (Base 100)")
        if not df_prices.empty:
            # Check if selected stocks exist in prices columns
            valid_stocks = [s for s in selected_stocks if s in df_prices.columns]
            if valid_stocks:
                price_subset = df_prices[valid_stocks].dropna()
                # Normalize to 100 at the start of the window
                if not price_subset.empty:
                    normalized_prices = (price_subset / price_subset.iloc[0]) * 100
                    
                    fig_price = px.line(normalized_prices, x=normalized_prices.index, y=valid_stocks)
                    fig_price.update_layout(yaxis_title="Normalized Value", xaxis_title="Date", legend_title="Tickers")
                    st.plotly_chart(fig_price, use_container_width=True)
            else:
                st.warning("Selected stocks price data cache me nahi mila.")
        else:
            st.warning("Price data cache me nahi mila.")

        # 2. FUNDAMENTAL & FACTOR COMPARISON METRICS
        st.subheader("📊 Factor Scores Breakdown")
        if 'Ticker' in df_screener.columns:
            compare_df = df_screener[df_screener['Ticker'].isin(selected_stocks)].set_index('Ticker')
        else:
            compare_df = df_screener.loc[df_screener.index.isin(selected_stocks)]
            
        # Select columns for Bar Chart comparison
        metrics_to_plot = ["Trailing 1Y CAGR (%)", "ROE (%)", "Operating Margin (%)", "Sharpe Ratio"]
        
        col_charts = st.columns(2)
        for i, metric in enumerate(metrics_to_plot):
            if metric in compare_df.columns:
                with col_charts[i % 2]:
                    fig_bar = px.bar(compare_df, x=compare_df.index, y=metric, color=compare_df.index, title=f"Comparison: {metric}")
                    st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Bhai, compare karne ke liye kam se kam 2 stocks select karo upar dropdown se.")

# ==========================================
# TAB 3: PORTFOLIO PERFORMANCE
# ==========================================
with tab3:
    st.header("🚀 Backtest Performance & Analytics")
    
    # Top Level Metrics in Columns
    if not df_perf.empty:
        # Convert df_perf to dictionary for easy access
        perf_dict = dict(zip(df_perf['Metric'], df_perf['Value']))
        
        # Values alag variable me le liye taaki f-string issue na aaye
        cagr_val = perf_dict.get('CAGR (%)', 0)
        bench_cagr_val = perf_dict.get('Benchmark CAGR (%)', 0)
        alpha_val = perf_dict.get("Jensen's Alpha (%)", 0)
        max_dd_val = perf_dict.get('Maximum Drawdown (%)', 0)
        sharpe_val = perf_dict.get('Dynamic Sharpe (10Y G-Sec)', 0)
        
        # 3 Rows of Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("CAGR", f"{cagr_val:.2f}%", f"vs NIFTY {bench_cagr_val:.2f}%")
        m2.metric("Jensen's Alpha", f"{alpha_val:.2f}%")
        m3.metric("Max Drawdown", f"{max_dd_val:.2f}%")
        m4.metric("Dynamic Sharpe", f"{sharpe_val:.2f}")
        
        # Show Full Table
        with st.expander("🔍 View Detailed Institutional Metrics"):
            st.table(df_perf)
    else:
        st.warning("Performance metrics file nahi mili.")

    # Show the generated static Plotly/Matplotlib image from backend
    st.subheader("📉 Cumulative Portfolio Growth vs Benchmark")
    chart_path = "data/outputs/portfolio_cumulative_growth.png"
    if os.path.exists(chart_path):
        st.image(chart_path, use_container_width=True)
    else:
        st.info("Portfolio growth chart image data/outputs/ folder me nahi mili.")
