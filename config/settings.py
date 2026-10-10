"""
config/settings.py
Global configuration settings for universe, constraints, backtest aur factor weights.
"""

from typing import Dict, List

# --- UNIVERSE SELECTION ---
# Default universe: NIFTY 50, NIFTY 100, ya NIFTY 250
ACTIVE_UNIVERSE = "NIFTY50"

# NSE Tickers with NIFTY 50 (Expandable to NIFTY 100 & 250)
UNIVERSES: Dict[str, List[str]] = {
    "NIFTY50": [
        "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
        "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "BAJFINANCE.NS", "BEL.NS", "BHARTIARTL.NS",
        "BPCL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS",
        "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
        "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
        "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS",
        "M&M.NS", "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS",
        "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SHRIRAMFIN.NS",
        "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TCS.NS",
        "TECHM.NS", "TITAN.NS", "TRENT.NS", "ULTRACEMCO.NS", "WIPRO.NS"
    ]
}

BENCHMARK_TICKER = "^NSEI"               # NIFTY 50 Benchmark Index
BOND_YIELD_TICKER = "IN10YT=RR"          # India 10-Year Benchmark G-Sec Yield

# --- SECTOR MAPPING ---
# Sector aur business type concentration constraints ke liye mapping
SECTOR_MAP: Dict[str, str] = {
    "ADANIENT.NS": "Metals & Mining", "ADANIPORTS.NS": "Services", "APOLLOHOSP.NS": "Healthcare",
    "ASIANPAINT.NS": "Consumer Durables", "AXISBANK.NS": "Financial Services",
    "BAJAJ-AUTO.NS": "Automobile", "BAJAJFINSV.NS": "Financial Services", "BAJFINANCE.NS": "Financial Services",
    "BEL.NS": "Capital Goods", "BHARTIARTL.NS": "Telecommunication", "BPCL.NS": "Oil & Gas",
    "BRITANNIA.NS": "FMCG", "CIPLA.NS": "Healthcare", "COALINDIA.NS": "Oil & Gas",
    "DRREDDY.NS": "Healthcare", "EICHERMOT.NS": "Automobile", "GRASIM.NS": "Construction Materials",
    "HCLTECH.NS": "IT", "HDFCBANK.NS": "Financial Services", "HDFCLIFE.NS": "Financial Services",
    "HEROMOTOCO.NS": "Automobile", "HINDALCO.NS": "Metals & Mining", "HINDUNILVR.NS": "FMCG",
    "ICICIBANK.NS": "Financial Services", "INDUSINDBK.NS": "Financial Services", "INFY.NS": "IT",
    "ITC.NS": "FMCG", "JSWSTEEL.NS": "Metals & Mining", "KOTAKBANK.NS": "Financial Services",
    "LT.NS": "Construction", "M&M.NS": "Automobile", "MARUTI.NS": "Automobile",
    "NESTLEIND.NS": "FMCG", "NTPC.NS": "Power", "ONGC.NS": "Oil & Gas",
    "POWERGRID.NS": "Power", "RELIANCE.NS": "Oil & Gas", "SBILIFE.NS": "Financial Services",
    "SBIN.NS": "Financial Services", "SHRIRAMFIN.NS": "Financial Services", "SUNPHARMA.NS": "Healthcare",
    "TATACONSUM.NS": "FMCG", "TATAMOTORS.NS": "Automobile", "TATASTEEL.NS": "Metals & Mining",
    "TCS.NS": "IT", "TECHM.NS": "IT", "TITAN.NS": "Consumer Durables", "TRENT.NS": "Consumer Services",
    "ULTRACEMCO.NS": "Construction Materials", "WIPRO.NS": "IT"
}

# --- DATE WINDOWS ---
START_DATE = "2018-01-01"
END_DATE = "2026-09-30"
REBALANCE_FREQ = "QE"                    # Quarterly rebalancing: Quarter-End

# --- PORTFOLIO & RISK CONSTRAINTS ---
TARGET_HOLDINGS = 10
MIN_WEIGHT = 0.05                        # Minimum 5% per stock
MAX_WEIGHT = 0.15                        # Maximum 15% per stock
SECTOR_CAP = 0.30                        # Kisi ek sector mein max 30% exposure
HOLDING_BAND_BUFFER = 5                  # Rank buffer: agar stock top 15 me hai to churn mat karo

# --- TRANSACTION FRICTION ---
TRANSACTION_COST_BPS = 30                # 30 bps round-trip (STT, Stamp Duty, Slippage, GST)

# --- MULTI-FACTOR WEIGHTS ---
# Top-level factor allocation: 5 Core pillars (Total = 1.0)
FACTOR_WEIGHTS = {
    "momentum": 0.25,                    # CAGR & Trend strength
    "risk_adjusted": 0.25,               # Historical Sharpe & Sortino
    "risk_stability": 0.15,              # Lower Volatility & Shallower Drawdown
    "quality": 0.20,                     # ROE & Operating Margins
    "growth": 0.15                       # Sales/Revenue Growth
}

# Fundamental data reporting lag (SEBI listing disclosure rule: 45 to 60 days)
FUNDAMENTAL_LAG_DAYS = 60