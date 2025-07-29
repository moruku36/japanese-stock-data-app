import os
import datetime as dt
import pandas as pd
import pandas_datareader.data as web
from typing import Optional, Dict, Any
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JapaneseStockDataFetcher:
    """日本の株価データを取得するクラス"""
    
    def __init__(self, data_dir: str = "stock_data"):
        """
        初期化
        
        Args:
            data_dir (str): データ保存ディレクトリ
        """
        self.data_dir = data_dir
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """データ保存ディレクトリを作成"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"データディレクトリを作成しました: {self.data_dir}")
    
    def fetch_stock_data_stooq(self, 
                              ticker_symbol: str, 
                              start_date: str = None, 
                              end_date: str = None) -> pd.DataFrame:
        """
        stooqから株価データを取得
        
        Args:
            ticker_symbol (str): 銘柄コード（例: "4784"）
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）
            
        Returns:
            pd.DataFrame: 株価データ
        """
        try:
            # デフォルトの日付設定
            if start_date is None:
                start_date = '2024-01-01'
            if end_date is None:
                end_date = dt.date.today().strftime('%Y-%m-%d')
            
            # stooq用の銘柄コード形式
            ticker_symbol_dr = f"{ticker_symbol}.JP"
            
            logger.info(f"stooqからデータを取得中: {ticker_symbol_dr} ({start_date} から {end_date})")
            
            # データ取得
            df = web.DataReader(ticker_symbol_dr, data_source='stooq', 
                               start=start_date, end=end_date)
            
            # 銘柄コードを追加
            df.insert(0, "code", ticker_symbol, allow_duplicates=False)
            
            # 日付順にソート
            df = df.sort_index()
            
            logger.info(f"stooqからデータ取得成功: {len(df)}件のデータ")
            return df
            
        except Exception as e:
            logger.error(f"stooqからのデータ取得に失敗: {e}")
            raise
    
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
        try:
            # デフォルトの日付設定
            if start_date is None:
                start_date = '2024-01-01'
            if end_date is None:
                end_date = dt.date.today().strftime('%Y-%m-%d')
            
            # Yahoo Finance用の銘柄コード形式
            ticker_symbol_dr = f"{ticker_symbol}.T"
            
            logger.info(f"Yahoo Financeからデータを取得中: {ticker_symbol_dr} ({start_date} から {end_date})")
            
            # データ取得
            df = web.DataReader(ticker_symbol_dr, data_source='yahoo', 
                               start=start_date, end=end_date)
            
            # 銘柄コードを追加
            df.insert(0, "code", ticker_symbol, allow_duplicates=False)
            
            logger.info(f"Yahoo Financeからデータ取得成功: {len(df)}件のデータ")
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
    
    def get_latest_price(self, ticker_symbol: str, source: str = "stooq") -> Dict[str, Any]:
        """
        最新の株価を取得
        
        Args:
            ticker_symbol (str): 銘柄コード
            source (str): データソース（"stooq" または "yahoo"）
            
        Returns:
            Dict[str, Any]: 最新の株価情報
        """
        try:
            # 過去30日間のデータを取得
            end_date = dt.date.today()
            start_date = end_date - dt.timedelta(days=30)
            
            if source.lower() == "stooq":
                df = self.fetch_stock_data_stooq(ticker_symbol, 
                                                start_date.strftime('%Y-%m-%d'),
                                                end_date.strftime('%Y-%m-%d'))
            elif source.lower() == "yahoo":
                df = self.fetch_stock_data_yahoo(ticker_symbol,
                                                start_date.strftime('%Y-%m-%d'),
                                                end_date.strftime('%Y-%m-%d'))
            else:
                raise ValueError("sourceは'stooq'または'yahoo'を指定してください")
            
            if df.empty:
                if source.lower() == "yahoo":
                    return {"error": "Yahoo Financeは現在利用できません。stooqをお試しください。"}
                else:
                    return {"error": "データが見つかりませんでした"}
            
            # 最新のデータを取得
            latest = df.iloc[-1]
            
            result = {
                "code": ticker_symbol,
                "date": latest.name.strftime('%Y-%m-%d'),
                "open": latest['Open'],
                "high": latest['High'],
                "low": latest['Low'],
                "close": latest['Close'],
                "volume": latest['Volume'],
                "source": source
            }
            
            # Yahoo Financeの場合は調整後終値も含める
            if source.lower() == "yahoo" and 'Adj Close' in latest:
                result["adj_close"] = latest['Adj Close']
            
            return result
            
        except Exception as e:
            logger.error(f"最新株価の取得に失敗: {e}")
            return {"error": str(e)}
    
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