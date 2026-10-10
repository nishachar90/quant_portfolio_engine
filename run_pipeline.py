"""
run_pipeline.py
Master execution pipeline script.
End-to-end execution: Data Ingestion -> Factor Scoring -> Backtest -> Screener -> Reporting.
"""

import os
import matplotlib.pyplot as plt
import pandas as pd
from src.data_loader import DataLoader
from src.factors import FactorEngine
from src.backtest import BacktestEngine
from src.analytics import PerformanceAnalytics
from src.screener import StockScreener

def main():
    print("=" * 75)
    print(" NIFTY QUANTITATIVE SCREENER & PORTFOLIO ENGINE (V2.0)")
    print(" Dynamic 10Y Indian G-Sec Yields | Zero Look-Ahead | Institutional Frictions")
    print("=" * 75)

    # 1. DATA INGESTION
    print("\n[1/5] Ingesting Historical Market & Benchmark Data...")
    loader = DataLoader()
    stock_prices, benchmark = loader.fetch_price_data()
    daily_rf = loader.fetch_dynamic_gsec_yields(stock_prices.index)
    fundamentals = loader.fetch_point_in_time_fundamentals(stock_prices)
    print(f" Loaded {stock_prices.shape[1]} securities across {len(stock_prices)} trading days.")

    # 2. FACTOR ENGINE
    print("\n[2/5] Initializing Rolling Factor Scoring Engine...")
    factor_engine = FactorEngine(stock_prices, daily_rf, fundamentals)

    # 3. STANDALONE SCREENER EXECUTION
    print("\n[3/5] Running Equity Screener for Today's Market Session...")
    screener = StockScreener(factor_engine)
    full_screener, top_buys = screener.screen_stocks()
    
    print("\n>>> TOP 10 QUALIFYING STOCKS (BUY RECOMMENDATIONS) <<<")
    print(top_buys[['Rank', 'Sector', 'Composite Score', 'Trailing 1Y CAGR (%)', 'Sharpe Ratio', 'ROE (%)']])

    os.makedirs("data/outputs", exist_ok=True)
    full_screener.to_csv("data/outputs/nifty_screener_rankings.csv")
    print(" Full screener results saved to: data/outputs/nifty_screener_rankings.csv")

    # 4. HISTORICAL BACKTESTING
    print("\n[4/5] Executing Dynamic Portfolio Simulation (Friction = 30 bps)...")
    backtest = BacktestEngine(stock_prices, daily_rf, benchmark, factor_engine)
    bnh_port, reb_port, bench_df = backtest.run_simulation()

    # 5. RISK & PERFORMANCE EVALUATION
    print("\n[5/5] Generating Performance Metrics & Risk Statistics...")
    analytics_reb = PerformanceAnalytics(reb_port, bench_df, daily_rf)
    metrics_report = analytics_reb.compute_all_metrics()

    print("\n" + "=" * 50)
    print("     REBALANCED STRATEGY PERFORMANCE SNAPSHOT     ")
    print("=" * 50)
    for k, v in metrics_report.items():
        if isinstance(v, float):
            print(f" {k:<32}: {v:>10.2f}")
        else:
            print(f" {k:<32}: {v}")
    print("=" * 50)

    # Performance export
    pd.DataFrame(list(metrics_report.items()), columns=["Metric", "Value"]).to_csv("data/outputs/portfolio_performance.csv", index=False)

    # --- CHARTS GENERATION ---
    print("\n Generating Performance & Drawdown Figures...")
    plt.figure(figsize=(12, 6))
    plt.plot(reb_port.index, reb_port['portfolio_value'] / 1e5, label="Quant Strategy (Rebalanced, Net 30bps)", color="#1f77b4", lw=2)
    plt.plot(bnh_port.index, bnh_port['portfolio_value'] / 1e5, label="Quant Strategy (Buy & Hold)", color="#ff7f0e", lw=1.5, alpha=0.7)
    plt.plot(bench_df.index, bench_df['benchmark_value'] / 1e5, label="NIFTY 50 Benchmark", color="#2ca02c", lw=1.5, linestyle="--")
    plt.title("NIFTY 50 Quant Portfolio Growth vs Benchmark (Base = ₹10 Lakhs)")
    plt.ylabel("Portfolio Value (₹ Lakhs)")
    plt.xlabel("Date")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("data/outputs/portfolio_cumulative_growth.png", dpi=300)
    plt.close()

    print(" Growth curve saved to: data/outputs/portfolio_cumulative_growth.png")
    print("\n Pipeline execution completed successfully!")

if __name__ == "__main__":
    main()