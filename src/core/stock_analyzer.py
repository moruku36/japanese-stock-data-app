import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定（シンプル版）
plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class StockAnalyzer:
    """株価データの分析と可視化を行うクラス"""
    
    def __init__(self, fetcher):
        """
        初期化
        
        Args:
            fetcher: JapaneseStockDataFetcherのインスタンス
        """
        self.fetcher = fetcher
    
    def plot_stock_price(self, ticker_symbol: str, source: str = "stooq", 
                        days: int = 30, save_plot: bool = True):
        """
        株価チャートを描画
        
        Args:
            ticker_symbol (str): 銘柄コード
            source (str): データソース
            days (int): 取得する日数
            save_plot (bool): プロットを保存するかどうか
        """
        try:
            # データ取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if source.lower() == "stooq":
                df = self.fetcher.fetch_stock_data_stooq(
                    ticker_symbol, 
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            else:
                df = self.fetcher.fetch_stock_data_yahoo(
                    ticker_symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            
            if df.empty:
                print(f"データが見つかりませんでした: {ticker_symbol}")
                return
            
            # プロット作成
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # 株価チャート
            ax1.plot(df.index, df['Close'], label='終値', linewidth=2)
            ax1.fill_between(df.index, df['Low'], df['High'], alpha=0.3, label='高値-安値')
            ax1.set_title(f'{ticker_symbol} 株価チャート ({source.upper()})', fontsize=14, fontweight='bold')
            ax1.set_ylabel('株価 (円)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 出来高チャート
            ax2.bar(df.index, df['Volume'], alpha=0.7, color='orange')
            ax2.set_title('出来高', fontsize=12)
            ax2.set_ylabel('出来高 (株)')
            ax2.set_xlabel('日付')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_plot:
                filename = f"{source}_chart_{ticker_symbol}.png"
                filepath = f"stock_data/{filename}"
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                print(f"チャートを保存しました: {filepath}")
            else:
                # 非表示モードでは描画をスキップ
                plt.close()
            
        except Exception as e:
            print(f"チャート作成に失敗: {e}")
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        テクニカル指標を計算
        
        Args:
            df (pd.DataFrame): 株価データ
            
        Returns:
            pd.DataFrame: テクニカル指標を追加したデータ
        """
        try:
            # 移動平均
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # ボリンジャーバンド
            df['BB_middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
            df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
            
            # MACD
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
            
            return df
            
        except Exception as e:
            print(f"テクニカル指標の計算に失敗: {e}")
            return df
    
    def plot_technical_analysis(self, ticker_symbol: str, source: str = "stooq", 
                              days: int = 60, save_plot: bool = True):
        """
        テクニカル分析チャートを描画
        
        Args:
            ticker_symbol (str): 銘柄コード
            source (str): データソース
            days (int): 取得する日数
            save_plot (bool): プロットを保存するかどうか
        """
        try:
            # データ取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if source.lower() == "stooq":
                df = self.fetcher.fetch_stock_data_stooq(
                    ticker_symbol, 
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            else:
                df = self.fetcher.fetch_stock_data_yahoo(
                    ticker_symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            
            if df.empty:
                print(f"データが見つかりませんでした: {ticker_symbol}")
                return
            
            # テクニカル指標を計算
            df = self.calculate_technical_indicators(df)
            
            # プロット作成
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 株価と移動平均
            ax1.plot(df.index, df['Close'], label='終値', linewidth=2)
            ax1.plot(df.index, df['MA5'], label='5日移動平均', alpha=0.7)
            ax1.plot(df.index, df['MA20'], label='20日移動平均', alpha=0.7)
            ax1.fill_between(df.index, df['BB_lower'], df['BB_upper'], alpha=0.2, label='ボリンジャーバンド')
            ax1.set_title(f'{ticker_symbol} テクニカル分析 ({source.upper()})', fontweight='bold')
            ax1.set_ylabel('株価 (円)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # RSI
            ax2.plot(df.index, df['RSI'], label='RSI', color='purple')
            ax2.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='売りシグナル')
            ax2.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='買いシグナル')
            ax2.set_title('RSI (相対力指数)')
            ax2.set_ylabel('RSI')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # MACD
            ax3.plot(df.index, df['MACD'], label='MACD', color='blue')
            ax3.plot(df.index, df['MACD_signal'], label='シグナル', color='red')
            ax3.bar(df.index, df['MACD'] - df['MACD_signal'], alpha=0.3, label='ヒストグラム')
            ax3.set_title('MACD')
            ax3.set_ylabel('MACD')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 出来高
            ax4.bar(df.index, df['Volume'], alpha=0.7, color='orange')
            ax4.set_title('出来高')
            ax4.set_ylabel('出来高 (株)')
            ax4.set_xlabel('日付')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_plot:
                filename = f"{source}_technical_{ticker_symbol}.png"
                filepath = f"stock_data/{filename}"
                plt.savefig(filepath, dpi=300, bbox_inches='tight')
                print(f"テクニカル分析チャートを保存しました: {filepath}")
            else:
                # 非表示モードでは描画をスキップ
                plt.close()
            
        except Exception as e:
            print(f"テクニカル分析チャートの作成に失敗: {e}")
    
    def generate_report(self, ticker_symbol: str, source: str = "stooq", days: int = 30):
        """
        株価分析レポートを生成
        
        Args:
            ticker_symbol (str): 銘柄コード
            source (str): データソース
            days (int): 分析期間
        """
        try:
            # データ取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            if source.lower() == "stooq":
                df = self.fetcher.fetch_stock_data_stooq(
                    ticker_symbol, 
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            else:
                df = self.fetcher.fetch_stock_data_yahoo(
                    ticker_symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            
            if df.empty:
                print(f"データが見つかりませんでした: {ticker_symbol}")
                return
            
            # テクニカル指標を計算
            df = self.calculate_technical_indicators(df)
            
            # 最新データ
            latest = df.iloc[-1]
            
            # レポート生成
            print(f"\n=== {ticker_symbol} 株価分析レポート ({source.upper()}) ===")
            print(f"分析期間: {start_date.strftime('%Y-%m-%d')} から {end_date.strftime('%Y-%m-%d')}")
            print(f"最新日付: {latest.name.strftime('%Y-%m-%d')}")
            print()
            
            print("【基本情報】")
            print(f"最新終値: {latest['Close']:,.0f}円")
            print(f"始値: {latest['Open']:,.0f}円")
            print(f"高値: {latest['High']:,.0f}円")
            print(f"安値: {latest['Low']:,.0f}円")
            print(f"出来高: {latest['Volume']:,}株")
            print()
            
            # 価格変動
            price_change = latest['Close'] - df.iloc[0]['Close']
            price_change_pct = (price_change / df.iloc[0]['Close']) * 100
            
            print("【価格変動】")
            print(f"期間中の価格変動: {price_change:+,.0f}円 ({price_change_pct:+.2f}%)")
            print(f"期間中の最高値: {df['High'].max():,.0f}円")
            print(f"期間中の最安値: {df['Low'].min():,.0f}円")
            print()
            
            # テクニカル指標
            print("【テクニカル指標】")
            if not pd.isna(latest['RSI']):
                print(f"RSI: {latest['RSI']:.1f}")
                if latest['RSI'] > 70:
                    print("  → 売りシグナル（過熱）")
                elif latest['RSI'] < 30:
                    print("  → 買いシグナル（過冷）")
                else:
                    print("  → 中立")
            
            if not pd.isna(latest['MA5']) and not pd.isna(latest['MA20']):
                print(f"5日移動平均: {latest['MA5']:.0f}円")
                print(f"20日移動平均: {latest['MA20']:.0f}円")
                if latest['MA5'] > latest['MA20']:
                    print("  → 短期トレンド上昇")
                else:
                    print("  → 短期トレンド下降")
            
            if not pd.isna(latest['MACD']):
                print(f"MACD: {latest['MACD']:.2f}")
                if latest['MACD'] > latest['MACD_signal']:
                    print("  → 上昇トレンド")
                else:
                    print("  → 下降トレンド")
            
            print("\n=== レポート終了 ===")
            
        except Exception as e:
            print(f"レポート生成に失敗: {e}")


def main():
    """メイン実行関数"""
    from stock_data_fetcher import JapaneseStockDataFetcher
    
    # 株価データ取得システムの初期化
    fetcher = JapaneseStockDataFetcher()
    analyzer = StockAnalyzer(fetcher)
    
    # サンプル銘柄コード
    sample_ticker = "4784"  # GMOアドパートナーズ
    
    print("=== 株価分析システム ===")
    print(f"対象銘柄: {sample_ticker}")
    print()
    
    # 1. 基本チャート
    print("1. 基本チャートを生成中...")
    analyzer.plot_stock_price(sample_ticker, "stooq", days=30)
    
    # 2. テクニカル分析
    print("\n2. テクニカル分析チャートを生成中...")
    analyzer.plot_technical_analysis(sample_ticker, "stooq", days=60)
    
    # 3. 分析レポート
    print("\n3. 分析レポートを生成中...")
    analyzer.generate_report(sample_ticker, "stooq", days=30)
    
    print("\n=== 分析完了 ===")


if __name__ == "__main__":
    main() 