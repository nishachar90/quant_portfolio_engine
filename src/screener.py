"""
src/screener.py
Standalone Indian Equity Screener Module.
Current universe (NIFTY 50, 100, 250) ko rank karke
Buy / Hold / Sell filter tags generate karta hai.
"""

import pandas as pd
from typing import Tuple
from config.settings import SECTOR_MAP
from src.factors import FactorEngine

class StockScreener:
    def __init__(self, factor_engine: FactorEngine):
        self.factor_engine = factor_engine

    def screen_stocks(self, as_of_date: pd.Timestamp = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Latest trading date par pure universe ko screen aur categorize karta hai.
        """
        if as_of_date is None:
            as_of_date = self.factor_engine.prices.index[-1]

        # Trailing 1Y metrics aur scores calculate karo
        metrics = self.factor_engine.calculate_trailing_metrics(as_of_date)
        scores = self.factor_engine.compute_factor_scores(metrics)

        screener_df = pd.DataFrame(index=scores.index)
        screener_df['Composite Score'] = scores.round(2)
        screener_df['Sector'] = [SECTOR_MAP.get(s, "Others") for s in screener_df.index]
        screener_df['Trailing 1Y CAGR (%)'] = (metrics['cagr'] * 100.0).round(2)
        screener_df['Sharpe Ratio'] = metrics['sharpe'].round(2)
        screener_df['Volatility (%)'] = (metrics['volatility'] * 100.0).round(2)
        screener_df['Max Drawdown (%)'] = (metrics['max_drawdown'] * 100.0).round(2)
        screener_df['ROE (%)'] = (metrics['roe'] * 100.0).round(2)
        screener_df['Operating Margin (%)'] = (metrics['operating_margin'] * 100.0).round(2)

        # Action tag assign karo
        # Top 10 = BUY, Next 10 (Rank 11-20) = HOLD, Baaki = AVOID / SELL
        ranks = pd.Series(range(1, len(screener_df) + 1), index=screener_df.index)
        screener_df['Rank'] = ranks
        
        screener_df['Action'] = screener_df['Rank'].apply(
            lambda r: "BUY (Top Decile)" if r <= 10 else ("HOLD (Quality Watchlist)" if r <= 20 else "AVOID / SELL")
        )

        top_buys = screener_df[screener_df['Action'].str.startswith("BUY")]
        return screener_df, top_buys