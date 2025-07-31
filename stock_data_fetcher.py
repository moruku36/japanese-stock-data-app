import os
import datetime as dt
import pandas as pd
import pandas_datareader.data as web
from typing import Optional, Dict, Any, List
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp

# 設定とユーティリティをインポート
from config import config
from utils import (
    RetryHandler, OptimizedCache, DataValidator, FileManager, 
    ProgressBar, PerformanceMonitor, performance_monitor, 
    MemoryOptimizer, BatchProcessor
)

logger = logging.getLogger(__name__)

class JapaneseStockDataFetcher:
    """日本の株価データを取得するクラス（最適化版）"""
    
    def __init__(self, data_dir: str = None, max_workers: int = 5):
        """
        初期化
        
        Args:
            data_dir (str): データ保存ディレクトリ（Noneの場合は設定から取得）
            max_workers (int): 並行処理の最大ワーカー数
        """
        self.data_dir = data_dir or config.get("data.directory", "stock_data")
        self.max_workers = max_workers
        self.file_manager = FileManager(self.data_dir)
        self.cache = OptimizedCache(
            max_size=config.get("search.max_results", 1000),
            ttl_hours=config.get("search.cache_ttl_hours", 24)
        )
        self.retry_handler = RetryHandler()
        self.batch_processor = BatchProcessor(batch_size=5)
        self._ensure_data_dir()
        
        # パフォーマンス監視
        self.performance_monitor = PerformanceMonitor()
    
    def _ensure_data_dir(self):
        """データ保存ディレクトリを作成"""
        self.file_manager.ensure_directory(self.data_dir)
        logger.info(f"データディレクトリを確認しました: {self.data_dir}")
    
    @performance_monitor
    def fetch_stock_data_stooq(self, 
                              ticker_symbol: str, 
                              start_date: str = None, 
                              end_date: str = None) -> pd.DataFrame:
        """
        stooqから株価データを取得（最適化版）
        
        Args:
            ticker_symbol (str): 銘柄コード（例: "4784"）
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）
            
        Returns:
            pd.DataFrame: 株価データ
        """
        # データ検証
        if not DataValidator.validate_ticker_symbol(ticker_symbol):
            raise ValueError(f"無効な銘柄コード: {ticker_symbol}")
        
        # デフォルトの日付設定
        if start_date is None:
            start_date = '2024-01-01'
        if end_date is None:
            end_date = dt.date.today().strftime('%Y-%m-%d')
        
        # 日付範囲の検証
        if not DataValidator.validate_date_range(start_date, end_date):
            raise ValueError(f"無効な日付範囲: {start_date} から {end_date}")
        
        # キャッシュキーを生成
        cache_key = f"stooq_{ticker_symbol}_{start_date}_{end_date}"
        
        # キャッシュから取得を試行
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"キャッシュから最新株価を取得: {ticker_symbol}")
            return cached_data
        
        # データソースが有効かチェック
        if not config.is_data_source_enabled("stooq"):
            raise ValueError("stooqデータソースが無効になっています")
        
        # リトライ設定を取得
        retry_config = config.get_retry_config("stooq")
        
        def _fetch_data():
            # stooq用の銘柄コード形式
            ticker_symbol_dr = f"{ticker_symbol}.JP"
            
            logger.info(f"stooqからデータを取得中: {ticker_symbol_dr} ({start_date} から {end_date})")
            
            # データ取得
            df = web.DataReader(ticker_symbol_dr, data_source='stooq', 
                               start=start_date, end=end_date)
            
            # データ検証
            if not DataValidator.validate_dataframe(df, ['Open', 'High', 'Low', 'Close', 'Volume']):
                raise ValueError("取得したデータが無効です")
            
            # 銘柄コードを追加
            df.insert(0, "code", ticker_symbol, allow_duplicates=False)
            
            # 日付順にソート
            df = df.sort_index()
            
            # メモリ最適化
            df = MemoryOptimizer.optimize_dataframe(df)
            
            logger.info(f"stooqからデータ取得成功: {len(df)}件のデータ")
            return df
        
        # リトライ付きでデータ取得
        df = self.retry_handler.execute(_fetch_data)
        
        # キャッシュに保存
        self.cache.set(cache_key, df)
        
        return df
    
    @performance_monitor
    def fetch_multiple_stocks(self, ticker_symbols: List[str], 
                            start_date: str = None, 
                            end_date: str = None,
                            source: str = "stooq") -> Dict[str, pd.DataFrame]:
        """
        複数銘柄のデータを並行取得
        
        Args:
            ticker_symbols (List[str]): 銘柄コードのリスト
            start_date (str): 開始日
            end_date (str): 終了日
            source (str): データソース
            
        Returns:
            Dict[str, pd.DataFrame]: 銘柄コードをキーとしたデータフレーム辞書
        """
        results = {}
        
        def fetch_single_stock(ticker):
            try:
                if source == "stooq":
                    df = self.fetch_stock_data_stooq(ticker, start_date, end_date)
                elif source == "yahoo":
                    df = self.fetch_stock_data_yahoo(ticker, start_date, end_date)
                else:
                    raise ValueError(f"サポートされていないデータソース: {source}")
                return ticker, df
            except Exception as e:
                logger.error(f"銘柄 {ticker} のデータ取得に失敗: {e}")
                return ticker, None
        
        # 並行処理でデータ取得
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {
                executor.submit(fetch_single_stock, ticker): ticker 
                for ticker in ticker_symbols
            }
            
            for future in as_completed(future_to_ticker):
                ticker, df = future.result()
                if df is not None:
                    results[ticker] = df
        
        return results
    
    @performance_monitor
    def get_latest_price(self, ticker_symbol: str, source: str = "stooq") -> Dict[str, Any]:
        """
        最新株価を取得（最適化版）
        
        Args:
            ticker_symbol (str): 銘柄コード
            source (str): データソース
            
        Returns:
            Dict[str, Any]: 最新株価情報
        """
        # キャッシュキー
        cache_key = f"latest_{ticker_symbol}_{source}"
        
        # キャッシュから取得を試行
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            # 最新のデータを取得（過去30日分）
            end_date = dt.date.today().strftime('%Y-%m-%d')
            start_date = (dt.date.today() - dt.timedelta(days=30)).strftime('%Y-%m-%d')
            
            if source == "stooq":
                df = self.fetch_stock_data_stooq(ticker_symbol, start_date, end_date)
            elif source == "yahoo":
                df = self.fetch_stock_data_yahoo(ticker_symbol, start_date, end_date)
            else:
                raise ValueError(f"サポートされていないデータソース: {source}")
            
            if df.empty:
                return {"error": "データが見つかりません"}
            
            # 最新のデータを取得
            latest = df.iloc[-1]
            
            result = {
                "ticker": ticker_symbol,
                "source": source,
                "date": latest.name.strftime('%Y-%m-%d'),
                "open": float(latest['Open']),
                "high": float(latest['High']),
                "low": float(latest['Low']),
                "close": float(latest['Close']),
                "volume": int(latest['Volume']) if 'Volume' in latest else 0,
                "change": float(latest['Close'] - df.iloc[-2]['Close']) if len(df) > 1 else 0,
                "change_percent": float((latest['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close'] * 100) if len(df) > 1 else 0
            }
            
            # キャッシュに保存（1時間TTL）
            self.cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"最新株価の取得に失敗: {ticker_symbol}, {source}, {e}")
            return {"error": str(e)}
    
    def fetch_stock_data_yahoo(self, 
                              ticker_symbol: str, 
                              start_date: str = None, 
                              end_date: str = None) -> pd.DataFrame:
        """
        Yahoo Financeから株価データを取得
        
        Args:
            ticker_symbol (str): 銘柄コード（例: "4784"）
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）
            
        Returns:
            pd.DataFrame: 株価データ
        """
        # データ検証
        if not DataValidator.validate_ticker_symbol(ticker_symbol):
            raise ValueError(f"無効な銘柄コード: {ticker_symbol}")
        
        # デフォルトの日付設定
        if start_date is None:
            start_date = '2024-01-01'
        if end_date is None:
            end_date = dt.date.today().strftime('%Y-%m-%d')
        
        # 日付範囲の検証
        if not DataValidator.validate_date_range(start_date, end_date):
            raise ValueError(f"無効な日付範囲: {start_date} から {end_date}")
        
        # キャッシュキーを生成
        cache_key = f"yahoo_{ticker_symbol}_{start_date}_{end_date}"
        
        # キャッシュから取得を試行
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"キャッシュからデータを取得: {ticker_symbol}")
            return cached_data
        
        # データソースが有効かチェック
        if not config.is_data_source_enabled("yahoo"):
            logger.warning("Yahoo Financeデータソースが無効になっています")
            return pd.DataFrame()
        
        # リトライ設定を取得
        retry_config = config.get_retry_config("yahoo")
        
        def _fetch_data():
            # Yahoo Finance用の銘柄コード形式
            ticker_symbol_dr = f"{ticker_symbol}.T"
            
            logger.info(f"Yahoo Financeからデータを取得中: {ticker_symbol_dr} ({start_date} から {end_date})")
            
            # データ取得
            df = web.DataReader(ticker_symbol_dr, data_source='yahoo', 
                               start=start_date, end=end_date)
            
            # データ検証
            if not DataValidator.validate_dataframe(df, ['Open', 'High', 'Low', 'Close', 'Volume']):
                raise ValueError("取得したデータが無効です")
            
            # 銘柄コードを追加
            df.insert(0, "code", ticker_symbol, allow_duplicates=False)
            
            logger.info(f"Yahoo Financeからデータ取得成功: {len(df)}件のデータ")
            return df
        
        try:
            # リトライ付きでデータ取得
            df = self.retry_handler.execute(_fetch_data)
            
            # キャッシュに保存
            self.cache.set(cache_key, df)
            
            return df
            
        except Exception as e:
            logger.warning(f"Yahoo Financeからのデータ取得に失敗しました: {e}")
            logger.info("stooqの使用をお勧めします。Yahoo Financeは現在アクセス制限があります。")
            # 空のDataFrameを返す
            return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, ticker_symbol: str, source: str = "stooq"):
        """
        データをCSVファイルに保存
        
        Args:
            df (pd.DataFrame): 保存するデータ
            ticker_symbol (str): 銘柄コード
            source (str): データソース（"stooq" または "yahoo"）
        """
        filename = f"{source}_stock_data_{ticker_symbol}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        df.to_csv(filepath, encoding='utf-8-sig')
        logger.info(f"データを保存しました: {filepath}")
    
    def compare_sources(self, ticker_symbol: str) -> Dict[str, Any]:
        """
        stooqとYahoo Financeの両方からデータを取得して比較
        
        Args:
            ticker_symbol (str): 銘柄コード
            
        Returns:
            Dict[str, Any]: 比較結果
        """
        try:
            stooq_data = self.get_latest_price(ticker_symbol, "stooq")
            yahoo_data = self.get_latest_price(ticker_symbol, "yahoo")
            
            return {
                "ticker_symbol": ticker_symbol,
                "stooq": stooq_data,
                "yahoo": yahoo_data,
                "comparison": {
                    "price_difference": abs(stooq_data.get("close", 0) - yahoo_data.get("close", 0)),
                    "price_difference_percent": abs(stooq_data.get("close", 0) - yahoo_data.get("close", 0)) / max(stooq_data.get("close", 1), 1) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"データソース比較に失敗: {e}")
            return {"error": str(e)}


def main():
    """メイン実行関数"""
    # 株価データ取得システムの初期化
    fetcher = JapaneseStockDataFetcher()
    
    # サンプル銘柄コード（GMOアドパートナーズ: 4784）
    sample_ticker = "4784"
    
    print("=== 日本の株価データ取得システム ===")
    print(f"対象銘柄: {sample_ticker}")
    print()
    
    # 1. stooqから最新データを取得
    print("1. stooqから最新データを取得中...")
    stooq_latest = fetcher.get_latest_price(sample_ticker, "stooq")
    if "error" not in stooq_latest:
        print(f"   最新終値: {stooq_latest['close']}円")
        print(f"   日付: {stooq_latest['date']}")
        print(f"   出来高: {stooq_latest['volume']:,}株")
    else:
        print(f"   エラー: {stooq_latest['error']}")
    
    print()
    
    # 2. Yahoo Financeから最新データを取得
    print("2. Yahoo Financeから最新データを取得中...")
    yahoo_latest = fetcher.get_latest_price(sample_ticker, "yahoo")
    if "error" not in yahoo_latest:
        print(f"   最新終値: {yahoo_latest['close']}円")
        print(f"   日付: {yahoo_latest['date']}")
        print(f"   出来高: {yahoo_latest['volume']:,}株")
    else:
        print(f"   エラー: {yahoo_latest['error']}")
    
    print()
    
    # 3. データソース比較
    print("3. データソース比較...")
    comparison = fetcher.compare_sources(sample_ticker)
    if "error" not in comparison:
        print(f"   価格差: {comparison['comparison']['price_difference']:.2f}円")
        print(f"   価格差率: {comparison['comparison']['price_difference_percent']:.2f}%")
    else:
        print(f"   エラー: {comparison['error']}")
    
    print()
    print("=== 処理完了 ===")


if __name__ == "__main__":
    main() 