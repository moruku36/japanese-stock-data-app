#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日本の株価データ取得・分析システム
参考: https://techblog.gmo-ap.jp/2022/06/07/pythonstockdata/
"""

import sys
import os
from datetime import datetime, timedelta

# プロジェクトのモジュールをインポート
from stock_data_fetcher import JapaneseStockDataFetcher
from stock_analyzer import StockAnalyzer

def print_banner():
    """バナーを表示"""
    print("=" * 60)
    print("🇯🇵 日本の株価データ取得・分析システム 🇯🇵")
    print("=" * 60)
    print("参考: https://techblog.gmo-ap.jp/2022/06/07/pythonstockdata/")
    print("=" * 60)

def print_menu():
    """メニューを表示"""
    print("\n📊 利用可能な機能:")
    print("1. 最新株価を取得")
    print("2. 株価チャートを表示")
    print("3. テクニカル分析を実行")
    print("4. 分析レポートを生成")
    print("5. データソース比較")
    print("6. 複数銘柄の一括取得")
    print("7. データをCSVに保存")
    print("0. 終了")
    print("-" * 60)

def get_ticker_symbol():
    """銘柄コードを入力してもらう"""
    print("\n📈 銘柄コードを入力してください（例: 4784, 7203, 6758）:")
    ticker = input("銘柄コード: ").strip()
    
    # 基本的な入力チェック
    if not ticker.isdigit():
        print("❌ 銘柄コードは数字で入力してください")
        return None
    
    return ticker

def get_data_source():
    """データソースを選択してもらう"""
    print("\n🌐 データソースを選択してください:")
    print("1. stooq（推奨・安定）")
    print("2. Yahoo Finance（現在制限あり）")
    print("3. 両方（Yahoo Financeが失敗した場合はstooqのみ）")
    
    choice = input("選択 (1-3): ").strip()
    
    if choice == "1":
        return "stooq"
    elif choice == "2":
        print("⚠️ Yahoo Financeは現在アクセス制限があります。")
        confirm = input("続行しますか？ (y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            return "yahoo"
        else:
            print("✅ stooqを使用します。")
            return "stooq"
    elif choice == "3":
        return "both"
    else:
        print("❌ 無効な選択です。stooqを使用します。")
        return "stooq"

def get_period():
    """期間を選択してもらう"""
    print("\n📅 期間を選択してください:")
    print("1. 過去7日間")
    print("2. 過去30日間")
    print("3. 過去90日間")
    print("4. 過去1年間")
    print("5. カスタム期間")
    
    choice = input("選択 (1-5): ").strip()
    
    if choice == "1":
        return 7
    elif choice == "2":
        return 30
    elif choice == "3":
        return 90
    elif choice == "4":
        return 365
    elif choice == "5":
        try:
            days = int(input("日数を入力してください: "))
            return max(1, min(days, 3650))  # 1日〜10年間の制限
        except ValueError:
            print("❌ 無効な入力です。30日間を使用します。")
            return 30
    else:
        print("❌ 無効な選択です。30日間を使用します。")
        return 30

def latest_price_menu(fetcher):
    """最新株価取得メニュー"""
    print("\n🔍 最新株価取得")
    
    ticker = get_ticker_symbol()
    if not ticker:
        return
    
    source = get_data_source()
    
    print(f"\n📊 {ticker}の最新株価を取得中...")
    
    try:
        if source == "both":
            stooq_data = fetcher.get_latest_price(ticker, "stooq")
            yahoo_data = fetcher.get_latest_price(ticker, "yahoo")
            
            print("\n📈 stooq データ:")
            if "error" not in stooq_data:
                print(f"   終値: {stooq_data['close']:,.0f}円")
                print(f"   日付: {stooq_data['date']}")
                print(f"   出来高: {stooq_data['volume']:,}株")
            else:
                print(f"   ❌ エラー: {stooq_data['error']}")
            
            print("\n📈 Yahoo Finance データ:")
            if "error" not in yahoo_data:
                print(f"   終値: {yahoo_data['close']:,.0f}円")
                print(f"   日付: {yahoo_data['date']}")
                print(f"   出来高: {yahoo_data['volume']:,}株")
            else:
                print(f"   ⚠️ Yahoo Finance: {yahoo_data['error']}")
                print("   💡 stooqのデータをご利用ください")
        else:
            data = fetcher.get_latest_price(ticker, source)
            if "error" not in data:
                print(f"\n✅ 取得成功!")
                print(f"   銘柄コード: {data['code']}")
                print(f"   終値: {data['close']:,.0f}円")
                print(f"   始値: {data['open']:,.0f}円")
                print(f"   高値: {data['high']:,.0f}円")
                print(f"   安値: {data['low']:,.0f}円")
                print(f"   出来高: {data['volume']:,}株")
                print(f"   日付: {data['date']}")
                print(f"   データソース: {data['source']}")
            else:
                print(f"❌ エラー: {data['error']}")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def chart_menu(fetcher, analyzer):
    """チャート表示メニュー"""
    print("\n📊 株価チャート表示")
    
    ticker = get_ticker_symbol()
    if not ticker:
        return
    
    source = get_data_source()
    if source == "both":
        source = "stooq"  # チャートは1つのソースのみ
    
    period = get_period()
    
    print(f"\n📈 {ticker}のチャートを生成中...")
    
    try:
        analyzer.plot_stock_price(ticker, source, period)
        print("✅ チャートが表示されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def technical_analysis_menu(fetcher, analyzer):
    """テクニカル分析メニュー"""
    print("\n🔬 テクニカル分析")
    
    ticker = get_ticker_symbol()
    if not ticker:
        return
    
    source = get_data_source()
    if source == "both":
        source = "stooq"
    
    period = get_period()
    
    print(f"\n🔬 {ticker}のテクニカル分析を実行中...")
    
    try:
        analyzer.plot_technical_analysis(ticker, source, period)
        print("✅ テクニカル分析チャートが表示されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def report_menu(fetcher, analyzer):
    """レポート生成メニュー"""
    print("\n📋 分析レポート生成")
    
    ticker = get_ticker_symbol()
    if not ticker:
        return
    
    source = get_data_source()
    if source == "both":
        source = "stooq"
    
    period = get_period()
    
    print(f"\n📋 {ticker}の分析レポートを生成中...")
    
    try:
        analyzer.generate_report(ticker, source, period)
        print("✅ レポートが生成されました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def comparison_menu(fetcher):
    """データソース比較メニュー"""
    print("\n⚖️ データソース比較")
    
    ticker = get_ticker_symbol()
    if not ticker:
        return
    
    print(f"\n⚖️ {ticker}のデータソース比較を実行中...")
    
    try:
        comparison = fetcher.compare_sources(ticker)
        if "error" not in comparison:
            print("\n📊 比較結果:")
            print(f"   銘柄コード: {comparison['ticker_symbol']}")
            
            print("\n📈 stooq データ:")
            if "error" not in comparison['stooq']:
                print(f"   終値: {comparison['stooq']['close']:,.0f}円")
                print(f"   日付: {comparison['stooq']['date']}")
            else:
                print(f"   ❌ エラー: {comparison['stooq']['error']}")
            
            print("\n📈 Yahoo Finance データ:")
            if "error" not in comparison['yahoo']:
                print(f"   終値: {comparison['yahoo']['close']:,.0f}円")
                print(f"   日付: {comparison['yahoo']['date']}")
            else:
                print(f"   ❌ エラー: {comparison['yahoo']['error']}")
            
            if "error" not in comparison['stooq'] and "error" not in comparison['yahoo']:
                print(f"\n📊 価格差: {comparison['comparison']['price_difference']:.2f}円")
                print(f"📊 価格差率: {comparison['comparison']['price_difference_percent']:.2f}%")
        else:
            print(f"❌ エラー: {comparison['error']}")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def batch_fetch_menu(fetcher):
    """複数銘柄一括取得メニュー"""
    print("\n📦 複数銘柄一括取得")
    
    print("銘柄コードをカンマ区切りで入力してください（例: 4784,7203,6758）:")
    tickers_input = input("銘柄コード: ").strip()
    
    tickers = [t.strip() for t in tickers_input.split(",") if t.strip().isdigit()]
    
    if not tickers:
        print("❌ 有効な銘柄コードが入力されていません")
        return
    
    source = get_data_source()
    
    print(f"\n📦 {len(tickers)}銘柄のデータを一括取得中...")
    
    results = []
    for i, ticker in enumerate(tickers, 1):
        print(f"\n[{i}/{len(tickers)}] {ticker}を処理中...")
        
        try:
            if source == "both":
                stooq_data = fetcher.get_latest_price(ticker, "stooq")
                yahoo_data = fetcher.get_latest_price(ticker, "yahoo")
                
                result = {
                    "ticker": ticker,
                    "stooq": stooq_data,
                    "yahoo": yahoo_data
                }
            else:
                data = fetcher.get_latest_price(ticker, source)
                result = {
                    "ticker": ticker,
                    "data": data
                }
            
            results.append(result)
            
            if source == "both":
                if "error" not in stooq_data:
                    print(f"   stooq: {stooq_data['close']:,.0f}円")
                if "error" not in yahoo_data:
                    print(f"   yahoo: {yahoo_data['close']:,.0f}円")
            else:
                if "error" not in data:
                    print(f"   {data['close']:,.0f}円")
                else:
                    print(f"   ❌ エラー")
        
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    print(f"\n✅ {len(results)}銘柄の処理が完了しました")

def save_csv_menu(fetcher):
    """CSV保存メニュー"""
    print("\n💾 データをCSVに保存")
    
    ticker = get_ticker_symbol()
    if not ticker:
        return
    
    source = get_data_source()
    if source == "both":
        source = "stooq"
    
    period = get_period()
    
    print(f"\n💾 {ticker}のデータをCSVに保存中...")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period)
        
        if source == "stooq":
            df = fetcher.fetch_stock_data_stooq(
                ticker,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
        else:
            df = fetcher.fetch_stock_data_yahoo(
                ticker,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
        
        if not df.empty:
            fetcher.save_to_csv(df, ticker, source)
            print(f"✅ データが保存されました: stock_data/{source}_stock_data_{ticker}.csv")
        else:
            print("❌ データが見つかりませんでした")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def main():
    """メイン関数"""
    print_banner()
    
    # システムの初期化
    try:
        fetcher = JapaneseStockDataFetcher()
        analyzer = StockAnalyzer(fetcher)
        print("✅ システムが正常に初期化されました")
    except Exception as e:
        print(f"❌ システムの初期化に失敗しました: {e}")
        return
    
    while True:
        print_menu()
        
        try:
            choice = input("選択してください (0-7): ").strip()
            
            if choice == "0":
                print("\n👋 システムを終了します。お疲れ様でした！")
                break
            elif choice == "1":
                latest_price_menu(fetcher)
            elif choice == "2":
                chart_menu(fetcher, analyzer)
            elif choice == "3":
                technical_analysis_menu(fetcher, analyzer)
            elif choice == "4":
                report_menu(fetcher, analyzer)
            elif choice == "5":
                comparison_menu(fetcher)
            elif choice == "6":
                batch_fetch_menu(fetcher)
            elif choice == "7":
                save_csv_menu(fetcher)
            else:
                print("❌ 無効な選択です。0-7の数字を入力してください。")
        
        except KeyboardInterrupt:
            print("\n\n👋 システムを終了します。お疲れ様でした！")
            break
        except Exception as e:
            print(f"❌ 予期しないエラーが発生しました: {e}")

if __name__ == "__main__":
    main() 