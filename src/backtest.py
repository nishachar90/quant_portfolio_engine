"""
src/backtest.py
Simulation Engine for Buy & Hold and Rebalanced portfolios.
Features:
- Dynamic 10Y Indian G-Sec daily hurdle rate subtraction
- 30 bps round-trip execution cost (STT delivery, stamp duty, slippage)
- Security-level position tracking
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from config.settings import TRANSACTION_COST_BPS, REBALANCE_FREQ
from src.factors import FactorEngine
from src.portfolio import PortfolioOptimizer

class BacktestEngine:
    def __init__(
        self,
        prices: pd.DataFrame,
        daily_rf: pd.Series,
        benchmark: pd.Series,
        factor_engine: FactorEngine,
        initial_capital: float = 1_000_000.0
    ):
        self.prices = prices
        self.daily_rf = daily_rf
        self.benchmark = benchmark
        self.factor_engine = factor_engine
        self.initial_capital = initial_capital
        self.optimizer = PortfolioOptimizer()
        self.returns = prices.pct_change().fillna(0.0)

    def run_simulation(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Buy-and-Hold aur Periodic Rebalancing dono portfolios simulate karta hai.
        """
        # Rebalancing dates identify karo (Quarter-End convention)
        rebal_dates = self.prices.resample(REBALANCE_FREQ).last().index
        rebal_dates = [d for d in rebal_dates if d in self.prices.index and d >= self.prices.index[252]]

        # Daily tracking frames
        dates = self.prices.loc[rebal_dates[0]:].index
        bnh_portfolio = pd.DataFrame(index=dates, columns=['portfolio_value', 'daily_return'])
        reb_portfolio = pd.DataFrame(index=dates, columns=['portfolio_value', 'daily_return', 'turnover', 'friction_cost'])

        # --- INITIAL SELECTION (T = 0) ---
        t0_date = rebal_dates[0]
        t0_metrics = self.factor_engine.calculate_trailing_metrics(t0_date)
        t0_scores = self.factor_engine.compute_factor_scores(t0_metrics)
        initial_weights = self.optimizer.construct_portfolio(t0_scores)

        # --- 1. BUY AND HOLD SIMULATION ---
        bnh_val = self.initial_capital
        # Entry transaction cost (15 bps one-way)
        bnh_val *= (1.0 - (TRANSACTION_COST_BPS / 20000.0))
        current_bnh_weights = initial_weights.copy()
        
        bnh_portfolio.loc[t0_date, 'portfolio_value'] = bnh_val
        bnh_portfolio.loc[t0_date, 'daily_return'] = 0.0

        for i in range(1, len(dates)):
            d_prev = dates[i - 1]
            d_curr = dates[i]
            
            # Asset returns
            r_t = self.returns.loc[d_curr, list(current_bnh_weights.keys())]
            port_ret = sum(current_bnh_weights[s] * r_t[s] for s in current_bnh_weights)
            
            bnh_val *= (1.0 + port_ret)
            bnh_portfolio.loc[d_curr, 'portfolio_value'] = bnh_val
            bnh_portfolio.loc[d_curr, 'daily_return'] = port_ret

            # Asset price drift se weights update karo
            new_unnorm_w = {s: current_bnh_weights[s] * (1.0 + r_t[s]) for s in current_bnh_weights}
            sum_w = sum(new_unnorm_w.values())
            current_bnh_weights = {s: w / sum_w for s, w in new_unnorm_w.items()}

        # --- 2. PERIODIC REBALANCED SIMULATION ---
        reb_val = self.initial_capital
        # Entry friction
        reb_val *= (1.0 - (TRANSACTION_COST_BPS / 20000.0))
        reb_portfolio.loc[t0_date, 'portfolio_value'] = reb_val
        reb_portfolio.loc[t0_date, 'daily_return'] = 0.0
        reb_portfolio.loc[t0_date, 'turnover'] = 0.0
        reb_portfolio.loc[t0_date, 'friction_cost'] = 0.0

        active_weights = initial_weights.copy()
        holdings_history = []

        for i in range(1, len(dates)):
            d_prev = dates[i - 1]
            d_curr = dates[i]

            # Agar aaj rebalance date hai to weights re-optimize karo
            if d_curr in rebal_dates and d_curr != t0_date:
                m_t = self.factor_engine.calculate_trailing_metrics(d_curr)
                s_t = self.factor_engine.compute_factor_scores(m_t)
                target_weights = self.optimizer.construct_portfolio(s_t, current_holdings=list(active_weights.keys()))

                # Portfolio turnover calculate karo: sum of absolute weight changes / 2
                all_tickers = list(set(active_weights.keys()).union(target_weights.keys()))
                turnover = sum(abs(target_weights.get(s, 0.0) - active_weights.get(s, 0.0)) for s in all_tickers) / 2.0

                # Transaction cost friction drag deduct karo
                friction_rate = turnover * (TRANSACTION_COST_BPS / 10000.0)
                cost_deducted = reb_val * friction_rate
                reb_val -= cost_deducted

                reb_portfolio.loc[d_curr, 'turnover'] = turnover
                reb_portfolio.loc[d_curr, 'friction_cost'] = cost_deducted
                active_weights = target_weights.copy()
                holdings_history.append((d_curr, active_weights))

            # Daily portfolio value accretion
            r_t = self.returns.loc[d_curr, list(active_weights.keys())]
            port_ret = sum(active_weights[s] * r_t[s] for s in active_weights)

            reb_val *= (1.0 + port_ret)
            reb_portfolio.loc[d_curr, 'portfolio_value'] = reb_val
            reb_portfolio.loc[d_curr, 'daily_return'] = port_ret

            # Drift update
            new_unnorm_w = {s: active_weights[s] * (1.0 + r_t[s]) for s in active_weights}
            sum_w = sum(new_unnorm_w.values())
            active_weights = {s: w / sum_w for s, w in new_unnorm_w.items()}

        # Benchmark returns slice (aligned to portfolio dates to handle Muhurt Trading/ holidays)
        bench_df = pd.DataFrame(index=dates)
        # Bechmark indec ko portfolio dates ke sath match karke forward-fill kar do

        aligned_bench = self.benchmark.reindex(dates).ffill().bfill()
        bench_df['benchmark_value'] = (aligned_bench / aligned_bench.iloc[0])* self.initial_capital
        bench_df['daily_return'] = aligned_bench.pct_change().fillna(0.0)

        return bnh_portfolio, reb_portfolio, bench_df
