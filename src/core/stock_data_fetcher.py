import os
import datetime as dt
import pandas as pd
import pandas_datareader.data as web
from typing import Optional, Dict, Any, List
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
from io import StringIO

# 設定とユーティリティをインポート
import sys
import os

# プロジェクトルートとsrcディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..')
project_root = os.path.join(src_dir, '..')

# パスを設定
sys.path.insert(0, src_dir)
sys.path.insert(0, project_root)

from config.config import config
from utils.utils import (
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
        # stooq は非同期CSV取得に対応（高速・低オーバーヘッド）
        if source == "stooq":
            try:
                return asyncio.run(
                    self.fetch_multiple_stocks_async(
                        ticker_symbols=ticker_symbols,
                        start_date=start_date,
                        end_date=end_date,
                        source=source,
                    )
                )
            except RuntimeError:
                # 既存のイベントループがある環境（例: Notebook）では代替手段
                return asyncio.get_event_loop().run_until_complete(
                    self.fetch_multiple_stocks_async(
                        ticker_symbols=ticker_symbols,
                        start_date=start_date,
                        end_date=end_date,
                        source=source,
                    )
                )

        # それ以外のソースは従来のスレッド並列で対応
        results: Dict[str, pd.DataFrame] = {}

        def fetch_single_stock(ticker: str):
            try:
                if source == "yahoo":
                    df = self.fetch_stock_data_yahoo(ticker, start_date, end_date)
                else:
                    raise ValueError(f"サポートされていないデータソース: {source}")
                return ticker, df
            except Exception as e:
                logger.error(f"銘柄 {ticker} のデータ取得に失敗: {e}")
                return ticker, None

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ticker = {executor.submit(fetch_single_stock, t): t for t in ticker_symbols}
            for future in as_completed(future_to_ticker):
                ticker, df = future.result()
                if df is not None:
                    results[ticker] = df

        return results

    async def _fetch_stooq_csv(self, session: aiohttp.ClientSession, ticker_symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """stooq のCSV APIを用いて非同期に1銘柄のデータを取得し DataFrame を返す"""
        try:
            if not DataValidator.validate_ticker_symbol(ticker_symbol):
                return None

            # デフォルトの日付設定を適用
            if start_date is None:
                start_date = '2024-01-01'
            if end_date is None:
                end_date = dt.date.today().strftime('%Y-%m-%d')

            if not DataValidator.validate_date_range(start_date, end_date):
                return None

            # stooq CSV エンドポイント
            # 例: https://stooq.com/q/d/l/?s=4784.JP&d1=20240101&d2=20241231&i=d
            d1 = start_date.replace('-', '')
            d2 = end_date.replace('-', '')
            symbol = f"{ticker_symbol}.JP"
            url = f"https://stooq.com/q/d/l/?s={symbol}&d1={d1}&d2={d2}&i=d"

            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    logger.warning(f"stooq CSV取得失敗: {ticker_symbol} status={resp.status}")
                    return None
                content = await resp.text()

            if not content or 'Date' not in content:
                return None

            df = pd.read_csv(StringIO(content))
            # 必須カラム検証
            required = ['Date', 'Open', 'High', 'Low', 'Close']
            if not all(c in df.columns for c in required):
                return None

            # インデックスとコード付与
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.set_index('Date').sort_index()
            df.insert(0, 'code', ticker_symbol, allow_duplicates=False)

            # メモリ最適化
            df = MemoryOptimizer.optimize_dataframe(df)
            return df
        except Exception as e:
            logger.error(f"stooq CSV 非同期取得失敗: {ticker_symbol}: {e}")
            return None

    async def fetch_multiple_stocks_async(self, ticker_symbols: List[str], start_date: str = None, end_date: str = None, source: str = "stooq") -> Dict[str, pd.DataFrame]:
        """複数銘柄を非同期に取得（stooq対応）。他ソースは従来手段にフォールバック"""
        results: Dict[str, pd.DataFrame] = {}

        if source != "stooq":
            # 非対応ソースは同期版へフォールバック
            return self.fetch_multiple_stocks(ticker_symbols, start_date, end_date, source)

        # セマフォで同時接続数を制限
        semaphore = asyncio.Semaphore(self.max_workers)

        async def _task(ticker: str):
            async with semaphore:
                df = await self._fetch_stooq_csv(session, ticker, start_date, end_date)
                if df is not None:
                    results[ticker] = df

        # SSL検証は標準のまま（stooqは有効な証明書）
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'}) as session:
            tasks = [asyncio.create_task(_task(t)) for t in ticker_symbols]
            await asyncio.gather(*tasks, return_exceptions=True)

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