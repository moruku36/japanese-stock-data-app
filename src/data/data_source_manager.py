#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
データソース管理システム（改善版）
フォールバック機構、ローカルキャッシュ、データ一貫性検証を実装
"""

import asyncio
import logging
import hashlib
import json
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import requests

# オプショナルインポート（依存関係が利用可能な場合のみ）
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import pandas_datareader.data as web
    PANDAS_DATAREADER_AVAILABLE = True
except ImportError:
    PANDAS_DATAREADER_AVAILABLE = False

# 設定とユーティリティをインポート
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, '..', '..'))

from config.config import config
from utils.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity

logger = logging.getLogger(__name__)

class DataSourceStatus(Enum):
    """データソースの状態"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"

class DataSourceType(Enum):
    """データソースの種類"""
    YAHOO_FINANCE = "yahoo_finance"
    STOOQ = "stooq"
    BLOOMBERG = "bloomberg"
    REUTERS = "reuters"
    ALPHA_VANTAGE = "alpha_vantage"
    LOCAL_CACHE = "local_cache"

@dataclass
class DataSourceInfo:
    """データソース情報"""
    name: str
    type: DataSourceType
    priority: int  # 優先度（低い数値ほど高優先）
    status: DataSourceStatus
    url: str
    timeout: int
    retry_count: int
    last_check: datetime
    success_rate: float
    response_time: float
    rate_limit: Optional[int] = None
    api_key: Optional[str] = None

@dataclass
class DataValidationResult:
    """データ検証結果"""
    is_valid: bool
    confidence_score: float
    inconsistencies: List[str]
    source: DataSourceType
    timestamp: datetime

class DataSourceManager:
    """データソース管理クラス（改善版）"""
    
    def __init__(self, cache_dir: str = "cache", error_handler: ErrorHandler = None):
        """
        初期化
        
        Args:
            cache_dir (str): キャッシュディレクトリ
            error_handler (ErrorHandler): エラーハンドラー
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.error_handler = error_handler or ErrorHandler()
        
        # データソース設定
        self.data_sources = self._initialize_data_sources()
        self.fallback_chain = self._build_fallback_chain()
        
        # 統計とメトリクス
        self.request_stats = {}
        self.validation_history = []
        self.cache_hit_rate = 0.0
        
        logger.info("データソース管理システムを初期化しました")
    
    def _initialize_data_sources(self) -> Dict[DataSourceType, DataSourceInfo]:
        """データソースを初期化"""
        sources = {}
        
        # Yahoo Finance
        sources[DataSourceType.YAHOO_FINANCE] = DataSourceInfo(
            name="Yahoo Finance",
            type=DataSourceType.YAHOO_FINANCE,
            priority=1,
            status=DataSourceStatus.ONLINE,
            url="https://query1.finance.yahoo.com",
            timeout=30,
            retry_count=3,
            last_check=datetime.now(),
            success_rate=0.95,
            response_time=1.2
        )
        
        # Stooq
        sources[DataSourceType.STOOQ] = DataSourceInfo(
            name="Stooq",
            type=DataSourceType.STOOQ,
            priority=2,
            status=DataSourceStatus.ONLINE,
            url="https://stooq.com",
            timeout=30,
            retry_count=3,
            last_check=datetime.now(),
            success_rate=0.90,
            response_time=2.1
        )
        
        # Alpha Vantage
        sources[DataSourceType.ALPHA_VANTAGE] = DataSourceInfo(
            name="Alpha Vantage",
            type=DataSourceType.ALPHA_VANTAGE,
            priority=3,
            status=DataSourceStatus.ONLINE,
            url="https://www.alphavantage.co",
            timeout=30,
            retry_count=2,
            last_check=datetime.now(),
            success_rate=0.88,
            response_time=3.5,
            rate_limit=500,
            api_key=config.get("advanced_apis.alphavantage.api_key", "")
        )
        
        # ローカルキャッシュ
        sources[DataSourceType.LOCAL_CACHE] = DataSourceInfo(
            name="Local Cache",
            type=DataSourceType.LOCAL_CACHE,
            priority=0,  # 最高優先度
            status=DataSourceStatus.ONLINE,
            url="local://cache",
            timeout=1,
            retry_count=1,
            last_check=datetime.now(),
            success_rate=1.0,
            response_time=0.1
        )
        
        return sources
    
    def _build_fallback_chain(self) -> List[DataSourceType]:
        """フォールバックチェーンを構築"""
        # 優先度順にソート（キャッシュは除く）
        sources = [
            source for source in self.data_sources.values()
            if source.type != DataSourceType.LOCAL_CACHE
        ]
        sources.sort(key=lambda x: x.priority)
        
        return [DataSourceType.LOCAL_CACHE] + [source.type for source in sources]
    
    async def get_stock_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        株価データを取得（フォールバック機構付き）
        
        Args:
            symbol (str): 銘柄コード
            period (str): 期間
            
        Returns:
            Optional[pd.DataFrame]: 株価データ
        """
        cache_key = self._generate_cache_key(symbol, period)
        
        # フォールバックチェーンを順番に試行
        for source_type in self.fallback_chain:
            try:
                data = await self._fetch_from_source(source_type, symbol, period, cache_key)
                
                if data is not None:
                    # データ検証
                    validation = self._validate_data(data, source_type)
                    
                    if validation.is_valid:
                        # キャッシュに保存（ローカルキャッシュ以外の場合）
                        if source_type != DataSourceType.LOCAL_CACHE:
                            await self._save_to_cache(cache_key, data)
                        
                        # 統計更新
                        self._update_stats(source_type, True)
                        
                        logger.info(f"データ取得成功: {symbol} from {source_type.value}")
                        return data
                    else:
                        logger.warning(f"データ検証失敗: {symbol} from {source_type.value}")
                        
            except Exception as e:
                logger.error(f"データ取得エラー: {symbol} from {source_type.value}: {e}")
                self._update_stats(source_type, False)
                continue
        
        # 全てのソースで失敗
        logger.error(f"全データソースでの取得に失敗: {symbol}")
        return None
    
    async def _fetch_from_source(
        self, 
        source_type: DataSourceType, 
        symbol: str, 
        period: str,
        cache_key: str
    ) -> Optional[pd.DataFrame]:
        """特定のソースからデータを取得"""
        
        if source_type == DataSourceType.LOCAL_CACHE:
            return await self._load_from_cache(cache_key)
        
        elif source_type == DataSourceType.YAHOO_FINANCE:
            return await self._fetch_yahoo_finance(symbol, period)
        
        elif source_type == DataSourceType.STOOQ:
            return await self._fetch_stooq(symbol, period)
        
        elif source_type == DataSourceType.ALPHA_VANTAGE:
            return await self._fetch_alpha_vantage(symbol, period)
        
        return None
    
    async def _fetch_yahoo_finance(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Yahoo Financeからデータを取得"""
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinanceライブラリが利用できません")
            return None
            
        try:
            # 日本株の場合、.Tサフィックスを追加
            if not symbol.endswith('.T') and len(symbol) == 4 and symbol.isdigit():
                symbol = f"{symbol}.T"
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if not data.empty:
                return data
            
        except Exception as e:
            logger.error(f"Yahoo Finance取得エラー: {symbol}: {e}")
        
        return None
    
    async def _fetch_stooq(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Stooqからデータを取得"""
        if not PANDAS_DATAREADER_AVAILABLE:
            logger.warning("pandas_datareaderライブラリが利用できません")
            return None
            
        try:
            # Stooq用のシンボル変換
            stooq_symbol = f"{symbol}.JP"
            
            # pandas_datareaderを使用してデータ取得
            end_date = datetime.now()
            
            # 期間変換
            period_days = {
                "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
                "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
            }
            
            days = period_days.get(period, 365)
            start_date = end_date - timedelta(days=days)
            
            # データ取得（同期処理をasyncで実行）
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                lambda: web.DataReader(stooq_symbol, 'stooq', start_date, end_date)
            )
            
            if not data.empty:
                return data
                
        except Exception as e:
            logger.error(f"Stooq取得エラー: {symbol}: {e}")
        
        return None
    
    async def _fetch_alpha_vantage(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Alpha Vantageからデータを取得"""
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttpライブラリが利用できません")
            return None
            
        try:
            source_info = self.data_sources[DataSourceType.ALPHA_VANTAGE]
            if not source_info.api_key:
                logger.warning("Alpha Vantage APIキーが設定されていません")
                return None
            
            # API呼び出し制限チェック
            if not self._check_rate_limit(DataSourceType.ALPHA_VANTAGE):
                logger.warning("Alpha Vantage APIレート制限に到達")
                return None
            
            url = f"{source_info.url}/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": f"{symbol}.TYO",  # 東京証券取引所
                "apikey": source_info.api_key,
                "outputsize": "full"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=source_info.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "Time Series (Daily)" in data:
                            df = pd.DataFrame.from_dict(
                                data["Time Series (Daily)"], 
                                orient='index'
                            )
                            df.index = pd.to_datetime(df.index)
                            df = df.astype(float)
                            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                            
                            return df.sort_index()
            
        except Exception as e:
            logger.error(f"Alpha Vantage取得エラー: {symbol}: {e}")
        
        return None
    
    def _validate_data(self, data: pd.DataFrame, source: DataSourceType) -> DataValidationResult:
        """データの一貫性を検証"""
        inconsistencies = []
        confidence_score = 1.0
        
        try:
            # 基本的な検証
            if data.empty:
                inconsistencies.append("データが空です")
                confidence_score = 0.0
            
            # OHLC検証
            if 'High' in data.columns and 'Low' in data.columns:
                invalid_high_low = data[data['High'] < data['Low']]
                if not invalid_high_low.empty:
                    inconsistencies.append(f"高値 < 安値の不整合: {len(invalid_high_low)}件")
                    confidence_score -= 0.1
            
            # 終値の妥当性チェック
            if 'Close' in data.columns:
                close_prices = data['Close']
                
                # 異常値検出（前日比±50%以上の変動）
                price_change = close_prices.pct_change().abs()
                extreme_changes = price_change[price_change > 0.5]
                
                if not extreme_changes.empty:
                    inconsistencies.append(f"極端な価格変動: {len(extreme_changes)}件")
                    confidence_score -= 0.05
                
                # ゼロや負の価格
                invalid_prices = close_prices[close_prices <= 0]
                if not invalid_prices.empty:
                    inconsistencies.append(f"無効な価格: {len(invalid_prices)}件")
                    confidence_score -= 0.2
            
            # 日付の連続性チェック
            date_gaps = pd.Timedelta(days=5)  # 5日以上の間隔
            if len(data) > 1:
                large_gaps = data.index.to_series().diff()[lambda x: x > date_gaps]
                if not large_gaps.empty:
                    inconsistencies.append(f"大きな日付間隔: {len(large_gaps)}件")
                    confidence_score -= 0.05
            
            # 最小信頼度を保証
            confidence_score = max(0.0, confidence_score)
            
            is_valid = confidence_score >= 0.7  # 70%以上で有効とする
            
        except Exception as e:
            logger.error(f"データ検証エラー: {e}")
            inconsistencies.append(f"検証処理エラー: {str(e)}")
            confidence_score = 0.0
            is_valid = False
        
        result = DataValidationResult(
            is_valid=is_valid,
            confidence_score=confidence_score,
            inconsistencies=inconsistencies,
            source=source,
            timestamp=datetime.now()
        )
        
        # 検証履歴を保存
        self.validation_history.append(result)
        if len(self.validation_history) > 1000:
            self.validation_history.pop(0)
        
        return result
    
    def _generate_cache_key(self, symbol: str, period: str) -> str:
        """キャッシュキーを生成"""
        key_data = f"{symbol}_{period}_{datetime.now().strftime('%Y-%m-%d')}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def _load_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """キャッシュからデータを読み込み"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if cache_file.exists():
                # キャッシュの有効期限チェック（24時間）
                if time.time() - cache_file.stat().st_mtime < 86400:
                    data = pd.read_pickle(cache_file)
                    logger.debug(f"キャッシュヒット: {cache_key}")
                    return data
                else:
                    # 期限切れキャッシュを削除
                    cache_file.unlink()
                    logger.debug(f"期限切れキャッシュを削除: {cache_key}")
            
        except Exception as e:
            logger.error(f"キャッシュ読み込みエラー: {cache_key}: {e}")
        
        return None
    
    async def _save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """データをキャッシュに保存"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            data.to_pickle(cache_file)
            logger.debug(f"キャッシュ保存: {cache_key}")
            
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {cache_key}: {e}")
    
    def _check_rate_limit(self, source_type: DataSourceType) -> bool:
        """APIレート制限をチェック"""
        source_info = self.data_sources.get(source_type)
        if not source_info or not source_info.rate_limit:
            return True
        
        # 簡易的なレート制限実装（実際にはRedis等を使用推奨）
        current_time = time.time()
        key = f"rate_limit_{source_type.value}"
        
        if key not in self.request_stats:
            self.request_stats[key] = []
        
        # 過去24時間のリクエスト数をチェック
        day_ago = current_time - 86400
        self.request_stats[key] = [
            req_time for req_time in self.request_stats[key] 
            if req_time > day_ago
        ]
        
        if len(self.request_stats[key]) >= source_info.rate_limit:
            return False
        
        self.request_stats[key].append(current_time)
        return True
    
    def _update_stats(self, source_type: DataSourceType, success: bool):
        """統計を更新"""
        source_info = self.data_sources.get(source_type)
        if not source_info:
            return
        
        # 成功率を更新（指数移動平均）
        alpha = 0.1
        new_value = 1.0 if success else 0.0
        source_info.success_rate = (
            alpha * new_value + (1 - alpha) * source_info.success_rate
        )
        
        source_info.last_check = datetime.now()
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """データソースの状態を取得"""
        status = {}
        
        for source_type, source_info in self.data_sources.items():
            status[source_type.value] = {
                "name": source_info.name,
                "status": source_info.status.value,
                "success_rate": round(source_info.success_rate, 3),
                "response_time": round(source_info.response_time, 2),
                "last_check": source_info.last_check.isoformat()
            }
        
        return status
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """データ検証の要約を取得"""
        if not self.validation_history:
            return {"total": 0, "valid": 0, "average_confidence": 0.0}
        
        total = len(self.validation_history)
        valid = sum(1 for v in self.validation_history if v.is_valid)
        avg_confidence = sum(v.confidence_score for v in self.validation_history) / total
        
        return {
            "total": total,
            "valid": valid,
            "validity_rate": round(valid / total, 3),
            "average_confidence": round(avg_confidence, 3)
        }

# グローバルインスタンス
data_source_manager = DataSourceManager()

if __name__ == "__main__":
    # テスト実行
    async def test():
        manager = DataSourceManager()
        data = await manager.get_stock_data("7203", "1mo")
        if data is not None:
            print(f"データ取得成功: {len(data)}行")
            print(data.head())
        else:
            print("データ取得失敗")
        
        print("\nソース状態:")
        print(json.dumps(manager.get_source_status(), indent=2, ensure_ascii=False))
        
        print("\n検証要約:")
        print(json.dumps(manager.get_validation_summary(), indent=2, ensure_ascii=False))
    
    asyncio.run(test())
