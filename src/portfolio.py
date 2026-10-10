"""
src/portfolio.py
Constrained Portfolio Construction & Allocation Engine.
Rules:
- Target 10 holdings (Range: 8-12)
- Min weight: 5%, Max weight: 15%
- Sector limit: 30% max
- Rank buffer: Agar existing stock top 15 me hai, to replace mat karo (Prevents excessive turnover)
"""

import pandas as pd
from typing import Dict, List
from config.settings import (
    TARGET_HOLDINGS, MIN_WEIGHT, MAX_WEIGHT, SECTOR_CAP,
    SECTOR_MAP, HOLDING_BAND_BUFFER
)

class PortfolioOptimizer:
    def __init__(self):
        self.sector_map = SECTOR_MAP

    def construct_portfolio(
        self,
        ranked_scores: pd.Series,
        current_holdings: List[str] = None
    ) -> Dict[str, float]:
        """
        Ranked factor scores se portfolio select karta hai aur sector bounds apply karta hai.
        """
        if current_holdings is None:
            current_holdings = []

        selected_stocks: List[str] = []
        sector_allocations: Dict[str, int] = {}
        max_stocks_per_sector = int(TARGET_HOLDINGS * SECTOR_CAP) # Max 3 stocks per sector

        # 1. HOLDING BUFFER CHECK:
        # Purani holdings jo abhi bhi competitive hain (within buffer rank) unko retain karo
        retained = []
        for stock in current_holdings:
            if stock in ranked_scores.index:
                stock_rank = ranked_scores.index.get_loc(stock) + 1
                if stock_rank <= (TARGET_HOLDINGS + HOLDING_BAND_BUFFER):
                    sector = self.sector_map.get(stock, "Others")
                    if sector_allocations.get(sector, 0) < max_stocks_per_sector:
                        retained.append(stock)
                        sector_allocations[sector] = sector_allocations.get(sector, 0) + 1

        selected_stocks.extend(retained)

        # 2. FRESH CANDIDATE SELECTION
        for stock in ranked_scores.index:
            if len(selected_stocks) >= TARGET_HOLDINGS:
                break
            if stock in selected_stocks:
                continue

            sector = self.sector_map.get(stock, "Others")
            current_sector_count = sector_allocations.get(sector, 0)

            # Check karo ki sector cap cross na ho
            if current_sector_count < max_stocks_per_sector:
                selected_stocks.append(stock)
                sector_allocations[sector] = current_sector_count + 1

        # 3. WEIGHT ALLOCATION (Score-Proportional with Min/Max Bounds)
        raw_scores = ranked_scores.loc[selected_stocks]
        score_sum = raw_scores.sum()
        
        # Initial proportional weights
        weights = (raw_scores / score_sum).to_dict()

        # Clip karo weights ko between 5% and 15%
        for s in weights:
            weights[s] = max(MIN_WEIGHT, min(MAX_WEIGHT, weights[s]))

        # Normalize taaki total sum exactly 1.0 (100%) bane
        total_w = sum(weights.values())
        final_weights = {s: w / total_w for s, w in weights.items()}

        return final_weights