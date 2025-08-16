#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from sqlalchemy import select, func, case

from src.security.db import get_session_factory
from src.portfolio.models import PortfolioModel, HoldingModel
from src.core.stock_data_fetcher import JapaneseStockDataFetcher


@dataclass
class HoldingView:
    code: str
    avg_price: float
    quantity: int
    market_price: float
    market_value: float
    pnl: float


class PortfolioService:
    def __init__(self):
        self._session_factory = get_session_factory()
        self._fetcher = JapaneseStockDataFetcher()

    def get_or_create_portfolio(self, user_id: str, name: str = "default") -> int:
        with self._session_factory() as session:
            m = session.execute(
                select(PortfolioModel).where(
                    PortfolioModel.user_id == user_id, PortfolioModel.name == name
                )
            ).scalar_one_or_none()
            if m:
                return m.id
            m = PortfolioModel(user_id=user_id, name=name)
            session.add(m)
            session.commit()
            return m.id

    def add_trade(self, portfolio_id: int, code: str, side: str, price: float, quantity: int) -> None:
        side = side.upper()
        if side not in ("BUY", "SELL"):
            raise ValueError("side must be BUY or SELL")
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        if not code.isdigit() or len(code) != 4:
            raise ValueError("code must be 4-digit ticker")

        with self._session_factory() as session:
            h = HoldingModel(
                portfolio_id=portfolio_id, code=code, side=side, price=price, quantity=quantity
            )
            session.add(h)
            session.commit()

    def get_positions(self, portfolio_id: int) -> List[HoldingView]:
        # 集計: 加重平均価格・数量
        with self._session_factory() as session:
            net_amount_expr = func.sum(
                case(
                    (HoldingModel.side == "BUY", HoldingModel.price * HoldingModel.quantity),
                    (HoldingModel.side == "SELL", -HoldingModel.price * HoldingModel.quantity),
                    else_=0,
                )
            ).label("net_amount")
            net_qty_expr = func.sum(
                case(
                    (HoldingModel.side == "BUY", HoldingModel.quantity),
                    (HoldingModel.side == "SELL", -HoldingModel.quantity),
                    else_=0,
                )
            ).label("net_qty")

            rows = session.execute(
                select(
                    HoldingModel.code,
                    net_amount_expr,
                    net_qty_expr,
                )
                .where(HoldingModel.portfolio_id == portfolio_id)
                .group_by(HoldingModel.code)
            ).all()

        results: List[HoldingView] = []
        for code, net_amount, net_qty in rows:
            if net_qty <= 0:
                continue
            avg_price = (net_amount or 0) / net_qty if net_qty else 0.0

            latest = self._fetcher.get_latest_price(code, "stooq")
            market_price = float(latest.get("close", 0.0)) if isinstance(latest, dict) else 0.0
            market_value = market_price * net_qty
            pnl = (market_price - avg_price) * net_qty

            results.append(
                HoldingView(
                    code=code,
                    avg_price=avg_price,
                    quantity=int(net_qty),
                    market_price=market_price,
                    market_value=market_value,
                    pnl=pnl,
                )
            )
        return results


