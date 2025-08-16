#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from unittest.mock import patch
import tempfile
from pathlib import Path


def test_portfolio_positions(monkeypatch):
    # ENV 準備
    monkeypatch.setenv("JWT_SECRET_KEY", "dev")
    monkeypatch.setenv("SECURITY_PASSWORD", "pw")
    monkeypatch.setenv("SECURITY_SALT", "salt")
    # 一時DBを使用（テスト間の汚染回避）
    tmp = Path(tempfile.gettempdir()) / "portfolio_test.sqlite3"
    if tmp.exists():
        try:
            tmp.unlink()
        except Exception:
            pass
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp).replace("\\", "/"))

    from src.portfolio.portfolio_service import PortfolioService

    svc = PortfolioService()
    pid = svc.get_or_create_portfolio("user1", "default")

    svc.add_trade(pid, "7203", "BUY", 1000.0, 10)
    svc.add_trade(pid, "7203", "BUY", 1100.0, 10)
    svc.add_trade(pid, "7203", "SELL", 1050.0, 5)

    # 最新株価は 1200 と仮定
    with patch("src.portfolio.portfolio_service.JapaneseStockDataFetcher.get_latest_price", return_value={"close": 1200.0}):
        positions = svc.get_positions(pid)

    # 残数量 = (10+10-5)=15, 加重平均 = (1000*10+1100*10-1050*5)/15 = (10000+11000-5250)/15 = 15750/15 = 1050
    pos = next(p for p in positions if p.code == "7203")
    assert pos.quantity == 15
    assert round(pos.avg_price, 2) == 1050.0
    assert pos.market_price == 1200.0
    assert round(pos.pnl, 2) == round((1200.0 - 1050.0) * 15, 2)


