"""
src/factors.py
Rolling Multi-Factor Scoring Engine.
Factors: Momentum, Risk-Adjusted, Stability/Risk, Quality, aur Growth.
Important: Pure rolling trailing windows use kiye gaye hain; zero full-sample lookahead.
"""

import numpy as np
import pandas as pd
from typing import Dict
from config.settings import FACTOR_WEIGHTS

class FactorEngine:
    def __init__(self, prices: pd.DataFrame, daily_rf: pd.Series, fundamentals: Dict[str, pd.DataFrame]):
        self.prices = prices
        self.daily_rf = daily_rf
        self.fundamentals = fundamentals
        self.returns = prices.pct_change().fillna(0.0)

    def calculate_trailing_metrics(self, current_date: pd.Timestamp, lookback_days: int = 252) -> pd.DataFrame:
        """
        Kisi ek specific rebalance date par trailing window ke metrics evaluate karta hai.
        """
        # Trailing slice strictly before or at current_date
        sub_prices = self.prices.loc[:current_date].iloc[-lookback_days:]
        sub_returns = self.returns.loc[:current_date].iloc[-lookback_days:]
        sub_rf = self.daily_rf.loc[:current_date].iloc[-lookback_days:]

        tickers = self.prices.columns.tolist()
        metrics = pd.DataFrame(index=tickers)

        # 1. MOMENTUM / PERFORMANCE
        # Trailing 1-Year CAGR
        start_p = sub_prices.iloc[0]
        end_p = sub_prices.iloc[-1]
        cagr = (end_p / start_p) ** (252.0 / len(sub_prices)) - 1.0
        metrics['cagr'] = cagr

        # 2. RISK ADJUSTED RETURN (Dynamic Sharpe & Sortino)
        # Daily Excess Returns: r_e = r_stock - r_f
        excess_returns = sub_returns.sub(sub_rf, axis=0)
        mean_excess = excess_returns.mean()
        std_dev = sub_returns.std()
        
        # Annualized Sharpe
        metrics['sharpe'] = np.where(std_dev > 1e-6, (mean_excess / std_dev) * np.sqrt(252), 0.0)

        # Annualized Sortino (Downside deviation hurdle)
        downside_diff = np.minimum(0.0, excess_returns)
        downside_dev = np.sqrt((downside_diff ** 2).mean())
        metrics['sortino'] = np.where(downside_dev > 1e-6, (mean_excess / downside_dev) * np.sqrt(252), 0.0)

        # 3. RISK & DRAWDOWN STABILITY
        # Volatility (inverted: lower volatility is better)
        metrics['volatility'] = std_dev * np.sqrt(252)

        # Max Drawdown (inverted: shallower drawdown is better)
        cum_ret = (1.0 + sub_returns).cumprod()
        peak = cum_ret.cummax()
        drawdown = (cum_ret - peak) / peak
        metrics['max_drawdown'] = drawdown.min().abs()

        # 4. FUNDAMENTAL QUALITY (Point-In-Time)
        # Point-in-time ROE and Margins as of current_date
        metrics['roe'] = self.fundamentals['roe'].loc[current_date]
        metrics['operating_margin'] = self.fundamentals['operating_margin'].loc[current_date]

        # 5. GROWTH
        metrics['sales_growth'] = self.fundamentals['sales_growth'].loc[current_date]

        return metrics.fillna(0.0)

    def compute_factor_scores(self, metrics: pd.DataFrame) -> pd.Series:
        """
        Cross-sectional percentile ranking (0 to 100) calculate karke
        weighted composite score banata hai.
        """
        # Directional mapping: higher percentile = better stock
        # Positive attributes (higher is better)
        pos_cols = ['cagr', 'sharpe', 'sortino', 'roe', 'operating_margin', 'sales_growth']
        # Negative attributes (lower is better, isiliye rank invert karo)
        neg_cols = ['volatility', 'max_drawdown']

        ranks = pd.DataFrame(index=metrics.index)

        for col in pos_cols:
            # Percentile rank from 0 to 100
            ranks[col] = metrics[col].rank(pct=True) * 100.0

        for col in neg_cols:
            # Lower volatility/drawdown gets 100 percentile rank
            ranks[col] = (1.0 - metrics[col].rank(pct=True)) * 100.0

        # Sub-pillar composite scores
        momentum_score = ranks['cagr']
        risk_adj_score = (ranks['sharpe'] * 0.6) + (ranks['sortino'] * 0.4)
        stability_score = (ranks['volatility'] * 0.5) + (ranks['max_drawdown'] * 0.5)
        quality_score = (ranks['roe'] * 0.5) + (ranks['operating_margin'] * 0.5)
        growth_score = ranks['sales_growth']

        # Master Composite Multi-Factor Score (0 to 100 scale)
        composite_score = (
            momentum_score * FACTOR_WEIGHTS['momentum'] +
            risk_adj_score * FACTOR_WEIGHTS['risk_adjusted'] +
            stability_score * FACTOR_WEIGHTS['risk_stability'] +
            quality_score * FACTOR_WEIGHTS['quality'] +
            growth_score * FACTOR_WEIGHTS['growth']
        )

        return composite_score.sort_values(ascending=False)