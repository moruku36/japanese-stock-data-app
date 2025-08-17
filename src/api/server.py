#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI ベースの軽量 REST API サーバー

エンドポイント:
  - GET  /health                       ヘルスチェック
  - GET  /stocks/{ticker}/latest       最新株価情報
  - GET  /stocks/{ticker}/history      ヒストリカル株価 (OHLCV)
  - POST /screener                     銘柄スクリーニング

認証:
  - ヘッダー `X-API-Key: <key>`
  - 環境変数 `API_KEYS` (カンマ区切り) または `API_KEY` に一致するキーのみ許可

簡易レート制限:
  - 1分あたりのリクエスト数を `RATE_LIMIT_PER_MINUTE` (既定: 60) で制限
  - キー + IP 単位のウィンドウカウンタ
"""

from __future__ import annotations

import os
import time
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    # ランタイムで PYTHONPATH=/app/src を前提に絶対インポート
    from core.stock_data_fetcher import JapaneseStockDataFetcher
    from analysis.screener import StockScreener, ScreenerCriteria as ScreenerCriteriaDataclass
except Exception:  # ローカル実行時フォールバック
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "src"))
    from core.stock_data_fetcher import JapaneseStockDataFetcher
    from analysis.screener import StockScreener, ScreenerCriteria as ScreenerCriteriaDataclass


API_TITLE = "Japanese Stock Data API"
API_VERSION = "0.1.0"

app = FastAPI(title=API_TITLE, version=API_VERSION)

# CORS (必要なら環境変数で制御)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# -----------------------------
# 認証 / レート制限
# -----------------------------
def _load_api_keys() -> List[str]:
    keys_env = os.getenv("API_KEYS") or os.getenv("API_KEY") or ""
    keys = [k.strip() for k in keys_env.split(",") if k.strip()]
    # 開発用のデフォルトキー（明示的に許可した場合のみ）
    if not keys and os.getenv("ALLOW_DEV_API_KEY", "false").lower() in ("1", "true", "yes"):
        keys = ["dev-api-key"]
    return keys


API_KEYS = _load_api_keys()
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

_rate_state: Dict[str, Dict[str, Any]] = {}


def _rate_limited(req: Request, api_key: str) -> None:
    ip = req.client.host if req.client else "unknown"
    key = f"{api_key}:{ip}"

    now = int(time.time())
    window = now // 60
    state = _rate_state.get(key)
    if state is None or state["window"] != window:
        _rate_state[key] = {"window": window, "count": 1}
        return

    state["count"] += 1
    if state["count"] > RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


async def require_api_key(x_api_key: Optional[str] = Header(None), request: Request = None) -> str:
    if not API_KEYS:
        # キー未設定時はローカル用途向けに許可（本番は必ず設定）
        return ""

    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

    # レート制限
    _rate_limited(request, x_api_key)
    return x_api_key


# -----------------------------
# Pydantic モデル
# -----------------------------
class ScreenerCriteriaModel(BaseModel):
    sectors: Optional[List[str]] = Field(default=None)
    pe_range: Optional[List[float]] = Field(default=None, min_items=2, max_items=2)
    pb_range: Optional[List[float]] = Field(default=None, min_items=2, max_items=2)
    roe_min: Optional[float] = 0.0
    dividend_yield_min: Optional[float] = 0.0
    market_cap_min: Optional[float] = 0.0
    market_cap_max: Optional[float] = None
    debt_to_equity_max: Optional[float] = None
    current_ratio_min: Optional[float] = 0.0
    pe_ntm_range: Optional[List[float]] = Field(default=None, min_items=2, max_items=2)
    sort_by: Optional[str] = "roe"
    sort_ascending: Optional[bool] = False
    limit: Optional[int] = 100
    compute_upside_to_target: Optional[bool] = False


# -----------------------------
# 依存: 共有インスタンス
# -----------------------------
_fetcher = JapaneseStockDataFetcher()
_screener = StockScreener(_fetcher)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "version": API_VERSION, "time": int(time.time())}


@app.get("/stocks/{ticker}/latest")
async def get_latest_price(ticker: str, source: str = "stooq", api_key: str = Depends(require_api_key)) -> Dict[str, Any]:
    data = _fetcher.get_latest_price(ticker, source=source)
    if isinstance(data, dict) and data.get("error"):
        raise HTTPException(status_code=404, detail=str(data.get("error")))
    return data


@app.get("/stocks/{ticker}/history")
async def get_history(
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    source: str = "stooq",
    api_key: str = Depends(require_api_key),
) -> Dict[str, Any]:
    if source == "stooq":
        df = _fetcher.fetch_stock_data_stooq(ticker, start, end)
    elif source == "yahoo":
        df = _fetcher.fetch_stock_data_yahoo(ticker, start, end)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No data")

    items = []
    for idx, row in df.iterrows():
        items.append({
            "date": idx.strftime("%Y-%m-%d"),
            "open": float(row.get("Open", 0)),
            "high": float(row.get("High", 0)),
            "low": float(row.get("Low", 0)),
            "close": float(row.get("Close", 0)),
            "volume": int(row.get("Volume", 0)) if "Volume" in df.columns else 0,
        })

    return {"ticker": ticker, "source": source, "items": items}


@app.post("/screener")
async def post_screener(criteria: ScreenerCriteriaModel, api_key: str = Depends(require_api_key)) -> Dict[str, Any]:
    # dataclass へ写像
    dc = ScreenerCriteriaDataclass(
        sectors=criteria.sectors,
        pe_range=tuple(criteria.pe_range) if criteria.pe_range else (0.0, 1000.0),
        pb_range=tuple(criteria.pb_range) if criteria.pb_range else (0.0, 1000.0),
        roe_min=float(criteria.roe_min or 0.0),
        dividend_yield_min=float(criteria.dividend_yield_min or 0.0),
        market_cap_min=float(criteria.market_cap_min or 0.0),
        market_cap_max=float(criteria.market_cap_max) if criteria.market_cap_max is not None else float("inf"),
        debt_to_equity_max=float(criteria.debt_to_equity_max) if criteria.debt_to_equity_max is not None else float("inf"),
        current_ratio_min=float(criteria.current_ratio_min or 0.0),
        pe_ntm_range=tuple(criteria.pe_ntm_range) if criteria.pe_ntm_range else (0.0, 1000.0),
        sort_by=criteria.sort_by or "roe",
        sort_ascending=bool(criteria.sort_ascending),
        limit=int(criteria.limit or 100),
        compute_upside_to_target=bool(criteria.compute_upside_to_target or False),
    )

    df = _screener.screen(dc)
    if df is None or df.empty:
        return {"count": 0, "items": []}

    items = df.to_dict(orient="records")
    return {"count": len(items), "items": items}


# Uvicorn 実行用
def run():  # pragma: no cover
    import uvicorn
    uvicorn.run("api.server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)


if __name__ == "__main__":  # pragma: no cover
    run()


