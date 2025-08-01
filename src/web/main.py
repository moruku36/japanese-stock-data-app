#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日本の株価データ取得・分析システム
参考: https://techblog.gmo-ap.jp/2022/06/07/pythonstockdata/
"""

import sys
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import Dict
import platform

# 日本語フォント設定（シンプル版）
plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# プロジェクトのモジュールをインポート
from stock_data_fetcher import JapaneseStockDataFetcher
from stock_analyzer import StockAnalyzer
from company_search import CompanySearch
from fundamental_analyzer import FundamentalAnalyzer
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
from utils.utils import ProgressBar, format_currency, format_number

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
    print("8. ファンダメンタル分析")
    print("9. 財務指標比較")
    print("10. システム設定")
    print("11. キャッシュ管理")
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

def get_ticker_symbol_with_search(company_searcher):
    """会社名検索付きで銘柄コードを取得"""
    print("\n🔍 銘柄コードの入力方法を選択してください:")
    print("1. 銘柄コードを直接入力")
    print("2. 会社名で検索")
    print("3. 主要企業から選択")
    
    choice = input("選択 (1-3): ").strip()
    
    if choice == "1":
        return get_ticker_symbol()
    elif choice == "2":
        return company_searcher.interactive_search()
    elif choice == "3":
        return select_from_popular_companies(company_searcher)
    else:
        print("❌ 無効な選択です。銘柄コードを直接入力します。")
        return get_ticker_symbol()

def select_from_popular_companies(company_searcher):
    """主要企業から選択"""
    print("\n⭐ 主要企業から選択")
    
    popular_companies = company_searcher.get_popular_companies(20)
    
    print("主要企業一覧:")
    print("-" * 60)
    
    for i, company in enumerate(popular_companies, 1):
        print(f"{i:2d}. {company['name']} ({company['code']}) - {company['sector']}")
    
    while True:
        try:
            choice = input(f"\n選択してください (1-{len(popular_companies)}): ").strip()
            if choice.lower() in ['q', 'quit', 'cancel', 'キャンセル']:
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(popular_companies):
                selected_company = popular_companies[choice_num - 1]
                company_searcher.display_company_info(selected_company)
                return selected_company['code']
            else:
                print(f"❌ 1-{len(popular_companies)}の数字を入力してください")
        except ValueError:
            print("❌ 有効な数字を入力してください")
        except KeyboardInterrupt:
            print("\n❌ 選択をキャンセルしました")
            return None

def batch_search_companies(company_searcher):
    """複数銘柄を検索して選択"""
    print("\n🔍 複数銘柄の検索・選択")
    
    selected_tickers = []
    
    while True:
        print(f"\n現在選択済み: {len(selected_tickers)}銘柄")
        if selected_tickers:
            print("選択済み銘柄:", ", ".join(selected_tickers))
        
        print("\n操作を選択してください:")
        print("1. 会社名で検索して追加")
        print("2. 主要企業から追加")
        print("3. 選択完了")
        print("4. 選択をリセット")
        
        choice = input("選択 (1-4): ").strip()
        
        if choice == "1":
            ticker = company_searcher.interactive_search()
            if ticker and ticker not in selected_tickers:
                selected_tickers.append(ticker)
                print(f"✅ {ticker} を追加しました")
            elif ticker in selected_tickers:
                print(f"⚠️ {ticker} は既に選択済みです")
        
        elif choice == "2":
            ticker = select_from_popular_companies(company_searcher)
            if ticker and ticker not in selected_tickers:
                selected_tickers.append(ticker)
                print(f"✅ {ticker} を追加しました")
            elif ticker in selected_tickers:
                print(f"⚠️ {ticker} は既に選択済みです")
        
        elif choice == "3":
            if selected_tickers:
                print(f"\n✅ {len(selected_tickers)}銘柄が選択されました: {', '.join(selected_tickers)}")
                return selected_tickers
            else:
                print("❌ 銘柄が選択されていません")
        
        elif choice == "4":
            selected_tickers.clear()
            print("✅ 選択をリセットしました")
        
        else:
            print("❌ 無効な選択です")

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

def latest_price_menu(fetcher, company_searcher):
    """最新株価取得メニュー"""
    print("\n🔍 最新株価取得")
    
    ticker = get_ticker_symbol_with_search(company_searcher)
    if not ticker:
        return
    
    source = get_data_source()
    
    print(f"\n📊 {ticker}の最新株価を取得中...")
    
    # プログレスバーを表示
    progress = ProgressBar(1, "データ取得中")
    
    try:
        if source == "both":
            stooq_data = fetcher.get_latest_price(ticker, "stooq")
            progress.update()
            yahoo_data = fetcher.get_latest_price(ticker, "yahoo")
            progress.finish()
            
            print("\n📈 stooq データ:")
            if "error" not in stooq_data:
                print(f"   終値: {format_currency(stooq_data['close'])}")
                print(f"   日付: {stooq_data['date']}")
                print(f"   出来高: {format_number(stooq_data['volume'])}株")
            else:
                print(f"   ❌ エラー: {stooq_data['error']}")
            
            print("\n📈 Yahoo Finance データ:")
            if "error" not in yahoo_data:
                print(f"   終値: {format_currency(yahoo_data['close'])}")
                print(f"   日付: {yahoo_data['date']}")
                print(f"   出来高: {format_number(yahoo_data['volume'])}株")
            else:
                print(f"   ⚠️ Yahoo Finance: {yahoo_data['error']}")
                print("   💡 stooqのデータをご利用ください")
        else:
            data = fetcher.get_latest_price(ticker, source)
            progress.finish()
            
            if "error" not in data:
                print(f"\n✅ 取得成功!")
                print(f"   銘柄コード: {data['code']}")
                print(f"   終値: {format_currency(data['close'])}")
                print(f"   始値: {format_currency(data['open'])}")
                print(f"   高値: {format_currency(data['high'])}")
                print(f"   安値: {format_currency(data['low'])}")
                print(f"   出来高: {format_number(data['volume'])}株")
                print(f"   日付: {data['date']}")
                print(f"   データソース: {data['source']}")
            else:
                print(f"❌ エラー: {data['error']}")
    
    except Exception as e:
        progress.finish()
        print(f"❌ エラーが発生しました: {e}")

def chart_menu(fetcher, analyzer, company_searcher):
    """チャート表示メニュー"""
    print("\n📊 株価チャート表示")
    
    ticker = get_ticker_symbol_with_search(company_searcher)
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

def technical_analysis_menu(fetcher, analyzer, company_searcher):
    """テクニカル分析メニュー"""
    print("\n🔬 テクニカル分析")
    
    ticker = get_ticker_symbol_with_search(company_searcher)
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

def report_menu(fetcher, analyzer, company_searcher):
    """レポート生成メニュー"""
    print("\n📋 分析レポート生成")
    
    ticker = get_ticker_symbol_with_search(company_searcher)
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

def comparison_menu(fetcher, company_searcher):
    """データソース比較メニュー"""
    print("\n⚖️ データソース比較")
    
    ticker = get_ticker_symbol_with_search(company_searcher)
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

def batch_fetch_menu(fetcher, company_searcher):
    """複数銘柄一括取得メニュー"""
    print("\n📦 複数銘柄一括取得")
    
    print("銘柄コードをカンマ区切りで入力してください（例: 4784,7203,6758）:")
    print("または、会社名で検索して複数選択することもできます")
    
    method = input("入力方法を選択 (1: 銘柄コード直接入力, 2: 会社名検索): ").strip()
    
    if method == "2":
        tickers = batch_search_companies(company_searcher)
    else:
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

def save_csv_menu(fetcher, company_searcher):
    """CSV保存メニュー"""
    print("\n💾 データをCSVに保存")
    
    ticker = get_ticker_symbol_with_search(company_searcher)
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

def fundamental_analysis_menu(fetcher, fundamental_analyzer, company_searcher):
    """ファンダメンタル分析メニュー"""
    print("\n🏢 ファンダメンタル分析")
    
    ticker = get_ticker_symbol_with_search(company_searcher)
    if not ticker:
        return
    
    print(f"\n🏢 {ticker}のファンダメンタル分析を実行中...")
    
    try:
        # 財務分析チャートを表示
        fundamental_analyzer.plot_financial_analysis(ticker)
        
        # 詳細レポートを生成
        fundamental_analyzer.generate_fundamental_report(ticker)
        
        print("✅ ファンダメンタル分析が完了しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def financial_comparison_menu(fundamental_analyzer, company_searcher):
    """財務指標比較メニュー"""
    print("\n⚖️ 財務指標比較")
    
    # 利用可能な銘柄を表示
    print("📋 現在利用可能な銘柄:")
    available_tickers = ["7203 (トヨタ自動車)", "6758 (ソニーグループ)", "9984 (ソフトバンクグループ)", 
                        "6861 (キーエンス)", "9434 (NTTドコモ)", "4784 (GMOアドパートナーズ)"]
    for ticker in available_tickers:
        print(f"   • {ticker}")
    print()
    
    print("比較したい銘柄を選択してください:")
    tickers = []
    
    for i in range(3):  # 最大3銘柄まで比較
        ticker = get_ticker_symbol_with_search(company_searcher)
        if not ticker:
            break
        
        if ticker in tickers:
            print(f"⚠️ {ticker} は既に選択済みです")
            continue
        
        # 財務データの存在確認
        financial_data = fundamental_analyzer.get_financial_data(ticker)
        if not financial_data:
            print(f"❌ {ticker} の財務データが見つかりません")
            print("📋 上記の利用可能な銘柄から選択してください")
            continue
        
        tickers.append(ticker)
        print(f"✅ {ticker} ({financial_data['company_name']}) を追加しました")
        
        if i < 2:  # 最後の銘柄以外は続行確認
            continue_choice = input("もう1銘柄追加しますか？ (y/N): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                break
    
    if len(tickers) < 2:
        print("❌ 比較には最低2銘柄が必要です")
        return
    
    print(f"\n⚖️ {len(tickers)}銘柄の財務指標を比較中...")
    
    try:
        # 比較用のデータを収集
        comparison_data = {}
        for ticker in tickers:
            financial_data = fundamental_analyzer.get_financial_data(ticker)
            if financial_data:
                comparison_data[ticker] = financial_data
        
        if len(comparison_data) < 2:
            print("❌ 比較可能な財務データが不足しています")
            return
        
        # 比較チャートを表示
        plot_financial_comparison(comparison_data)
        
        # 比較レポートを生成
        generate_comparison_report(comparison_data)
        
        print("✅ 財務指標比較が完了しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

def plot_financial_comparison(comparison_data: Dict):
    """財務指標比較チャートを描画"""
    # 警告を抑制
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
    
    # 日本語フォント設定（シンプル版）
    plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 図のサイズを適切に調整
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 銘柄名のリスト
    tickers = list(comparison_data.keys())
    company_names = [comparison_data[ticker]['company_name'] for ticker in tickers]
    
    # 色の設定
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4749']
    
    # 1. ROE比較
    roe_values = [comparison_data[ticker]['roe'] for ticker in tickers]
    bars1 = axes[0, 0].bar(range(len(company_names)), roe_values, 
                          color=colors[:len(tickers)], alpha=0.8)
    axes[0, 0].set_title('ROE比較 (%)', fontweight='bold', fontsize=12)
    axes[0, 0].set_ylabel('ROE (%)', fontsize=10)
    axes[0, 0].set_xticks(range(len(company_names)))
    axes[0, 0].set_xticklabels(company_names, rotation=15, ha='right', fontsize=9)
    
    # 値のラベルを追加
    for bar, value in zip(bars1, roe_values):
        height = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{value:.1f}%', ha='center', va='bottom', fontsize=9)
    
    # 2. P/E比較
    pe_values = [comparison_data[ticker]['pe_ratio'] for ticker in tickers]
    bars2 = axes[0, 1].bar(range(len(company_names)), pe_values, 
                          color=colors[1:len(tickers)+1], alpha=0.8)
    axes[0, 1].set_title('P/E比較', fontweight='bold', fontsize=12)
    axes[0, 1].set_ylabel('P/E倍率', fontsize=10)
    axes[0, 1].set_xticks(range(len(company_names)))
    axes[0, 1].set_xticklabels(company_names, rotation=15, ha='right', fontsize=9)
    
    # 値のラベルを追加
    for bar, value in zip(bars2, pe_values):
        height = bar.get_height()
        axes[0, 1].text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{value:.1f}', ha='center', va='bottom', fontsize=9)
    
    # 3. 配当利回り比較
    dividend_values = [comparison_data[ticker]['dividend_yield'] for ticker in tickers]
    bars3 = axes[1, 0].bar(range(len(company_names)), dividend_values, 
                          color=colors[2:len(tickers)+2], alpha=0.8)
    axes[1, 0].set_title('配当利回り比較 (%)', fontweight='bold', fontsize=12)
    axes[1, 0].set_ylabel('配当利回り (%)', fontsize=10)
    axes[1, 0].set_xticks(range(len(company_names)))
    axes[1, 0].set_xticklabels(company_names, rotation=15, ha='right', fontsize=9)
    
    # 値のラベルを追加
    for bar, value in zip(bars3, dividend_values):
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.1f}%', ha='center', va='bottom', fontsize=9)
    
    # 4. 負債比率比較
    debt_values = [comparison_data[ticker]['debt_to_equity'] for ticker in tickers]
    bars4 = axes[1, 1].bar(range(len(company_names)), debt_values, 
                          color=colors[3:len(tickers)+3], alpha=0.8)
    axes[1, 1].set_title('負債比率比較', fontweight='bold', fontsize=12)
    axes[1, 1].set_ylabel('負債/自己資本', fontsize=10)
    axes[1, 1].set_xticks(range(len(company_names)))
    axes[1, 1].set_xticklabels(company_names, rotation=15, ha='right', fontsize=9)
    
    # 値のラベルを追加
    for bar, value in zip(bars4, debt_values):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height + 0.01,
                       f'{value:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.suptitle('財務指標比較分析', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(pad=2.0)
    
    # 保存
    filename = f"financial_comparison_{'_'.join(tickers)}.png"
    filepath = f"stock_data/{filename}"
    plt.savefig(filepath, dpi=200, bbox_inches='tight')
    print(f"📊 比較チャートを保存しました: {filepath}")
    
    plt.show()

def generate_comparison_report(comparison_data: Dict):
    """比較レポートを生成"""
    print(f"\n{'='*70}")
    print(f"⚖️ 財務指標比較レポート")
    print(f"{'='*70}")
    print(f"📅 比較日: {datetime.now().strftime('%Y年%m月%d日')}")
    
    tickers = list(comparison_data.keys())
    
    # 基本情報
    print(f"\n📊 基本情報")
    print(f"{'─'*50}")
    for ticker in tickers:
        data = comparison_data[ticker]
        market_cap_trillion = data['market_cap'] / 1000000000000
        print(f"🏢 {data['company_name']} ({ticker})")
        print(f"   業種: {data['sector']}")
        print(f"   時価総額: {market_cap_trillion:.1f}兆円")
        print()
    
    # ROE比較
    print(f"📈 ROE比較 (自己資本利益率)")
    print(f"{'─'*50}")
    roe_data = [(ticker, comparison_data[ticker]['roe']) for ticker in tickers]
    roe_data.sort(key=lambda x: x[1], reverse=True)
    for i, (ticker, roe) in enumerate(roe_data, 1):
        company_name = comparison_data[ticker]['company_name']
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"   {medal} {i}位: {company_name} ({ticker}) - {roe:.1f}%")
    
    # P/E比較
    print(f"\n💰 P/E比較 (株価収益率)")
    print(f"{'─'*50}")
    pe_data = [(ticker, comparison_data[ticker]['pe_ratio']) for ticker in tickers]
    pe_data.sort(key=lambda x: x[1])  # 低い順
    for i, (ticker, pe) in enumerate(pe_data, 1):
        company_name = comparison_data[ticker]['company_name']
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"   {medal} {i}位: {company_name} ({ticker}) - {pe:.1f}倍")
    
    # 配当利回り比較
    print(f"\n💵 配当利回り比較")
    print(f"{'─'*50}")
    dividend_data = [(ticker, comparison_data[ticker]['dividend_yield']) for ticker in tickers]
    dividend_data.sort(key=lambda x: x[1], reverse=True)
    for i, (ticker, dividend) in enumerate(dividend_data, 1):
        company_name = comparison_data[ticker]['company_name']
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"   {medal} {i}位: {company_name} ({ticker}) - {dividend:.1f}%")
    
    # 財務健全性比較
    print(f"\n🏥 財務健全性比較 (負債比率)")
    print(f"{'─'*50}")
    debt_data = [(ticker, comparison_data[ticker]['debt_to_equity']) for ticker in tickers]
    debt_data.sort(key=lambda x: x[1])  # 低い順
    for i, (ticker, debt) in enumerate(debt_data, 1):
        company_name = comparison_data[ticker]['company_name']
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        print(f"   {medal} {i}位: {company_name} ({ticker}) - {debt:.2f}")
    
    # 総合評価
    print(f"\n🎯 総合評価")
    print(f"{'─'*50}")
    print("📊 各指標の1位企業:")
    print(f"   ROE: {roe_data[0][1]:.1f}% ({comparison_data[roe_data[0][0]]['company_name']})")
    print(f"   P/E: {pe_data[0][1]:.1f}倍 ({comparison_data[pe_data[0][0]]['company_name']})")
    print(f"   配当利回り: {dividend_data[0][1]:.1f}% ({comparison_data[dividend_data[0][0]]['company_name']})")
    print(f"   財務健全性: {debt_data[0][1]:.2f} ({comparison_data[debt_data[0][0]]['company_name']})")
    
    print(f"\n{'='*70}")

def settings_menu():
    """システム設定メニュー"""
    print("\n⚙️ システム設定")
    print("1. 現在の設定を表示")
    print("2. 設定を変更")
    print("3. 設定をリセット")
    print("4. 設定を保存")
    print("5. 戻る")
    
    choice = input("選択 (1-5): ").strip()
    
    if choice == "1":
        print("\n📋 現在の設定:")
        print(f"   データディレクトリ: {config.get('data.directory')}")
        print(f"   ログレベル: {config.get('logging.level')}")
        print(f"   チャートDPI: {config.get('charts.dpi')}")
        print(f"   検索結果最大数: {config.get('search.max_results')}")
        print(f"   デフォルト期間: {config.get('analysis.default_period_days')}日")
        print(f"   stooq有効: {config.is_data_source_enabled('stooq')}")
        print(f"   Yahoo Finance有効: {config.is_data_source_enabled('yahoo')}")
    
    elif choice == "2":
        print("\n🔧 設定変更")
        print("変更したい項目を選択してください:")
        print("1. データディレクトリ")
        print("2. ログレベル")
        print("3. チャートDPI")
        print("4. 検索結果最大数")
        print("5. デフォルト期間")
        print("6. データソース設定")
        
        sub_choice = input("選択 (1-6): ").strip()
        
        if sub_choice == "1":
            new_dir = input("新しいデータディレクトリ: ").strip()
            if new_dir:
                config.set("data.directory", new_dir)
                print("✅ データディレクトリを更新しました")
        
        elif sub_choice == "2":
            print("利用可能なログレベル: DEBUG, INFO, WARNING, ERROR")
            new_level = input("新しいログレベル: ").strip().upper()
            if new_level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                config.set("logging.level", new_level)
                print("✅ ログレベルを更新しました")
            else:
                print("❌ 無効なログレベルです")
        
        elif sub_choice == "3":
            try:
                new_dpi = int(input("新しいDPI: ").strip())
                config.set("charts.dpi", new_dpi)
                print("✅ DPIを更新しました")
            except ValueError:
                print("❌ 無効なDPIです")
        
        elif sub_choice == "4":
            try:
                new_max = int(input("新しい最大結果数: ").strip())
                config.set("search.max_results", new_max)
                print("✅ 最大結果数を更新しました")
            except ValueError:
                print("❌ 無効な数値です")
        
        elif sub_choice == "5":
            try:
                new_period = int(input("新しいデフォルト期間（日）: ").strip())
                config.set("analysis.default_period_days", new_period)
                print("✅ デフォルト期間を更新しました")
            except ValueError:
                print("❌ 無効な日数です")
        
        elif sub_choice == "6":
            print("データソース設定:")
            stooq_enabled = input("stooqを有効にするか？ (y/N): ").strip().lower() == 'y'
            yahoo_enabled = input("Yahoo Financeを有効にするか？ (y/N): ").strip().lower() == 'y'
            
            config.set("data_sources.stooq.enabled", stooq_enabled)
            config.set("data_sources.yahoo.enabled", yahoo_enabled)
            print("✅ データソース設定を更新しました")
    
    elif choice == "3":
        confirm = input("設定をリセットしますか？ (y/N): ").strip().lower()
        if confirm == 'y':
            # 設定ファイルを削除してリセット
            import os
            if os.path.exists("config.json"):
                os.remove("config.json")
                print("✅ 設定をリセットしました。システムを再起動してください。")
            else:
                print("✅ 設定は既にデフォルト状態です")
    
    elif choice == "4":
        config.save()
    
    elif choice == "5":
        pass
    else:
        print("❌ 無効な選択です")

def cache_menu(fetcher):
    """キャッシュ管理メニュー"""
    print("\n🗂️ キャッシュ管理")
    print("1. キャッシュ情報を表示")
    print("2. キャッシュをクリア")
    print("3. 期限切れキャッシュを削除")
    print("4. 戻る")
    
    choice = input("選択 (1-4): ").strip()
    
    if choice == "1":
        from pathlib import Path
        cache_dir = Path("cache")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.pkl"))
            print(f"\n📊 キャッシュ情報:")
            print(f"   キャッシュファイル数: {len(cache_files)}")
            
            total_size = sum(f.stat().st_size for f in cache_files)
            print(f"   総サイズ: {total_size / (1024*1024):.2f} MB")
            
            if cache_files:
                print("\n📁 キャッシュファイル一覧:")
                for i, file in enumerate(cache_files[:10], 1):
                    size_mb = file.stat().st_size / (1024*1024)
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    print(f"   {i}. {file.name} ({size_mb:.2f} MB, {mtime.strftime('%Y-%m-%d %H:%M')})")
                
                if len(cache_files) > 10:
                    print(f"   ... 他 {len(cache_files) - 10} ファイル")
        else:
            print("📊 キャッシュディレクトリが存在しません")
    
    elif choice == "2":
        confirm = input("すべてのキャッシュを削除しますか？ (y/N): ").strip().lower()
        if confirm == 'y':
            fetcher.cache.clear()
            print("✅ キャッシュをクリアしました")
    
    elif choice == "3":
        fetcher.cache.cleanup_expired()
        print("✅ 期限切れキャッシュを削除しました")
    
    elif choice == "4":
        pass
    else:
        print("❌ 無効な選択です")

def main():
    """メイン関数"""
    print_banner()
    
    # システムの初期化
    try:
        fetcher = JapaneseStockDataFetcher()
        analyzer = StockAnalyzer(fetcher)
        company_searcher = CompanySearch()
        fundamental_analyzer = FundamentalAnalyzer(fetcher)
        print("✅ システムが正常に初期化されました")
        print(f"📊 登録企業数: {len(company_searcher.companies)}社")
        print(f"🏢 ファンダメンタル分析対応企業数: {len(fundamental_analyzer.financial_data)}社")
    except Exception as e:
        print(f"❌ システムの初期化に失敗しました: {e}")
        return
    
    while True:
        print_menu()
        
        try:
            choice = input("選択してください (0-11): ").strip()
            
            if choice == "0":
                print("\n👋 システムを終了します。お疲れ様でした！")
                break
            elif choice == "1":
                latest_price_menu(fetcher, company_searcher)
            elif choice == "2":
                chart_menu(fetcher, analyzer, company_searcher)
            elif choice == "3":
                technical_analysis_menu(fetcher, analyzer, company_searcher)
            elif choice == "4":
                report_menu(fetcher, analyzer, company_searcher)
            elif choice == "5":
                comparison_menu(fetcher, company_searcher)
            elif choice == "6":
                batch_fetch_menu(fetcher, company_searcher)
            elif choice == "7":
                save_csv_menu(fetcher, company_searcher)
            elif choice == "8":
                fundamental_analysis_menu(fetcher, fundamental_analyzer, company_searcher)
            elif choice == "9":
                financial_comparison_menu(fundamental_analyzer, company_searcher)
            elif choice == "10":
                settings_menu()
            elif choice == "11":
                cache_menu(fetcher)
            else:
                print("❌ 無効な選択です。0-11の数字を入力してください。")
        
        except KeyboardInterrupt:
            print("\n\n👋 システムを終了します。お疲れ様でした！")
            break
        except Exception as e:
            print(f"❌ 予期しないエラーが発生しました: {e}")

if __name__ == "__main__":
    main() 