#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
銘柄スクリーニング機能
FundamentalAnalyzer の財務データを用いて、PER/PBR/ROE/配当利回り/時価総額などで絞り込み
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from analysis.fundamental_analyzer import FundamentalAnalyzer
from core.stock_data_fetcher import JapaneseStockDataFetcher


@dataclass
class ScreenerCriteria:
    sectors: Optional[List[str]] = None
    pe_range: Tuple[float, float] = (0.0, 1000.0)
    pb_range: Tuple[float, float] = (0.0, 1000.0)
    roe_min: float = 0.0
    dividend_yield_min: float = 0.0
    market_cap_min: float = 0.0  # 単位: 円
    market_cap_max: float = float("inf")
    debt_to_equity_max: float = float("inf")
    current_ratio_min: float = 0.0
    pe_ntm_range: Tuple[float, float] = (0.0, 1000.0)
    sort_by: str = "roe"  # roe, dividend_yield, pe_ratio, pb_ratio, market_cap, pe_ratio_ntm, upside
    sort_ascending: bool = False
    limit: int = 100
    compute_upside_to_target: bool = False


class StockScreener:
    """銘柄スクリーニングのロジック"""

    def __init__(self, fetcher: Optional[JapaneseStockDataFetcher] = None):
        self.fetcher = fetcher or JapaneseStockDataFetcher()
        self.fundamental_analyzer = FundamentalAnalyzer(self.fetcher)
        self.financial_data = self.fundamental_analyzer.financial_data

    def list_sectors(self) -> List[str]:
        sectors = sorted({d.get("sector", "") for d in self.financial_data.values()})
        return [s for s in sectors if s]

    def screen(self, criteria: ScreenerCriteria) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []

        for ticker, data in self.financial_data.items():
            sector = data.get("sector")
            if criteria.sectors and sector not in criteria.sectors:
                continue

            pe = float(data.get("pe_ratio", 0) or 0)
            if not (criteria.pe_range[0] <= pe <= criteria.pe_range[1]):
                continue

            pb = float(data.get("pb_ratio", 0) or 0)
            if not (criteria.pb_range[0] <= pb <= criteria.pb_range[1]):
                continue

            roe = float(data.get("roe", 0) or 0)
            if roe < criteria.roe_min:
                continue

            div_yield = float(data.get("dividend_yield", 0) or 0)
            if div_yield < criteria.dividend_yield_min:
                continue

            mcap = float(data.get("market_cap", 0) or 0)
            if not (criteria.market_cap_min <= mcap <= criteria.market_cap_max):
                continue

            de = float(data.get("debt_to_equity", 0) or 0)
            if de > criteria.debt_to_equity_max:
                continue

            cr = float(data.get("current_ratio", 0) or 0)
            if cr < criteria.current_ratio_min:
                continue

            pe_ntm = float(data.get("pe_ratio_ntm", 0) or 0)
            if not (criteria.pe_ntm_range[0] <= pe_ntm <= criteria.pe_ntm_range[1]):
                continue

            row: Dict[str, Any] = {
                "ticker": ticker,
                "company_name": data.get("company_name", ""),
                "sector": sector,
                "market_cap": mcap,
                "pe_ratio": pe,
                "pe_ratio_ntm": pe_ntm,
                "pb_ratio": pb,
                "roe": roe,
                "dividend_yield": div_yield,
                "debt_to_equity": de,
                "current_ratio": cr,
                "target_price": float(data.get("target_price", 0) or 0),
            }

            if criteria.compute_upside_to_target and row["target_price"] > 0:
                latest = self.fetcher.get_latest_price(ticker, source="stooq")
                if "error" not in latest and latest.get("close"):
                    current_price = float(latest["close"])  # type: ignore
                    if current_price > 0:
                        row["upside"] = (row["target_price"] - current_price) / current_price * 100.0
                    else:
                        row["upside"] = 0.0
                else:
                    row["upside"] = 0.0

            rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        valid_sort_cols = {
            "roe": "roe",
            "dividend_yield": "dividend_yield",
            "pe_ratio": "pe_ratio",
            "pb_ratio": "pb_ratio",
            "market_cap": "market_cap",
            "pe_ratio_ntm": "pe_ratio_ntm",
            "upside": "upside",
        }
        sort_col = valid_sort_cols.get(criteria.sort_by, "roe")
        if sort_col in df.columns:
            df = df.sort_values(by=sort_col, ascending=criteria.sort_ascending, kind="mergesort")

        if criteria.limit and criteria.limit > 0:
            df = df.head(criteria.limit)

        return df.reset_index(drop=True)


