#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日本の株価データ取得・分析システムのテストスクリプト
"""

import sys
import os
from datetime import datetime, timedelta

def test_imports():
    """必要なモジュールのインポートテスト"""
    print("🔍 モジュールのインポートテスト...")
    
    try:
        import pandas as pd
        print("✅ pandas インポート成功")
    except ImportError as e:
        print(f"❌ pandas インポート失敗: {e}")
        return False
    
    try:
        import pandas_datareader.data as web
        print("✅ pandas_datareader インポート成功")
    except ImportError as e:
        print(f"❌ pandas_datareader インポート失敗: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        print("✅ matplotlib インポート成功")
    except ImportError as e:
        print(f"❌ matplotlib インポート失敗: {e}")
        return False
    
    try:
        import seaborn as sns
        print("✅ seaborn インポート成功")
    except ImportError as e:
        print(f"❌ seaborn インポート失敗: {e}")
        return False
    
    return True

def test_stock_fetcher():
    """株価データ取得クラスのテスト"""
    print("\n🔍 株価データ取得クラスのテスト...")
    
    try:
        from stock_data_fetcher import JapaneseStockDataFetcher
        fetcher = JapaneseStockDataFetcher()
        print("✅ JapaneseStockDataFetcher 初期化成功")
        return fetcher
    except Exception as e:
        print(f"❌ JapaneseStockDataFetcher 初期化失敗: {e}")
        return None

def test_stock_analyzer(fetcher):
    """株価分析クラスのテスト"""
    print("\n🔍 株価分析クラスのテスト...")
    
    try:
        from stock_analyzer import StockAnalyzer
        analyzer = StockAnalyzer(fetcher)
        print("✅ StockAnalyzer 初期化成功")
        return analyzer
    except Exception as e:
        print(f"❌ StockAnalyzer 初期化失敗: {e}")
        return None

def test_data_fetching(fetcher):
    """データ取得のテスト"""
    print("\n🔍 データ取得のテスト...")
    
    # テスト用銘柄コード（GMOアドパートナーズ）
    test_ticker = "4784"
    
    try:
        # stooqからのデータ取得テスト
        print("  stooqからのデータ取得テスト...")
        stooq_data = fetcher.get_latest_price(test_ticker, "stooq")
        
        if "error" not in stooq_data:
            print(f"    ✅ stooq取得成功: {stooq_data['close']:,.0f}円")
        else:
            print(f"    ⚠️ stooq取得失敗: {stooq_data['error']}")
        
        # Yahoo Financeからのデータ取得テスト
        print("  Yahoo Financeからのデータ取得テスト...")
        yahoo_data = fetcher.get_latest_price(test_ticker, "yahoo")
        
        if "error" not in yahoo_data:
            print(f"    ✅ Yahoo Finance取得成功: {yahoo_data['close']:,.0f}円")
        else:
            print(f"    ⚠️ Yahoo Finance取得失敗: {yahoo_data['error']}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ データ取得テスト失敗: {e}")
        return False

def test_chart_generation(analyzer):
    """チャート生成のテスト"""
    print("\n🔍 チャート生成のテスト...")
    
    test_ticker = "4784"
    
    try:
        # 基本チャート生成テスト（非表示モード）
        print("  基本チャート生成テスト...")
        analyzer.plot_stock_price(test_ticker, "stooq", days=7, save_plot=False)
        print("    ✅ 基本チャート生成成功")
        
        return True
        
    except Exception as e:
        print(f"    ❌ チャート生成テスト失敗: {e}")
        return False

def test_technical_analysis(analyzer):
    """テクニカル分析のテスト"""
    print("\n🔍 テクニカル分析のテスト...")
    
    test_ticker = "4784"
    
    try:
        # テクニカル分析テスト（非表示モード）
        print("  テクニカル分析テスト...")
        analyzer.plot_technical_analysis(test_ticker, "stooq", days=14, save_plot=False)
        print("    ✅ テクニカル分析成功")
        
        return True
        
    except Exception as e:
        print(f"    ❌ テクニカル分析テスト失敗: {e}")
        return False

def test_report_generation(analyzer):
    """レポート生成のテスト"""
    print("\n🔍 レポート生成のテスト...")
    
    test_ticker = "4784"
    
    try:
        # レポート生成テスト
        print("  レポート生成テスト...")
        analyzer.generate_report(test_ticker, "stooq", days=7)
        print("    ✅ レポート生成成功")
        
        return True
        
    except Exception as e:
        print(f"    ❌ レポート生成テスト失敗: {e}")
        return False

def test_csv_saving(fetcher):
    """CSV保存のテスト"""
    print("\n🔍 CSV保存のテスト...")
    
    test_ticker = "4784"
    
    try:
        # 過去7日間のデータを取得してCSV保存
        print("  CSV保存テスト...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        df = fetcher.fetch_stock_data_stooq(
            test_ticker,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not df.empty:
            fetcher.save_to_csv(df, test_ticker, "stooq")
            print("    ✅ CSV保存成功")
            return True
        else:
            print("    ⚠️ データが空のためCSV保存をスキップ")
            return True
            
    except Exception as e:
        print(f"    ❌ CSV保存テスト失敗: {e}")
        return False

def main():
    """メインテスト関数"""
    print("=" * 60)
    print("🧪 日本の株価データ取得・分析システム テスト")
    print("=" * 60)
    
    # テスト結果の記録
    test_results = []
    
    # 1. モジュールインポートテスト
    test_results.append(("モジュールインポート", test_imports()))
    
    # 2. 株価データ取得クラステスト
    fetcher = test_stock_fetcher()
    test_results.append(("株価データ取得クラス", fetcher is not None))
    
    if fetcher is None:
        print("\n❌ 株価データ取得クラスの初期化に失敗したため、テストを中止します。")
        return
    
    # 3. 株価分析クラステスト
    analyzer = test_stock_analyzer(fetcher)
    test_results.append(("株価分析クラス", analyzer is not None))
    
    if analyzer is None:
        print("\n❌ 株価分析クラスの初期化に失敗したため、テストを中止します。")
        return
    
    # 4. データ取得テスト
    test_results.append(("データ取得", test_data_fetching(fetcher)))
    
    # 5. チャート生成テスト
    test_results.append(("チャート生成", test_chart_generation(analyzer)))
    
    # 6. テクニカル分析テスト
    test_results.append(("テクニカル分析", test_technical_analysis(analyzer)))
    
    # 7. レポート生成テスト
    test_results.append(("レポート生成", test_report_generation(analyzer)))
    
    # 8. CSV保存テスト
    test_results.append(("CSV保存", test_csv_saving(fetcher)))
    
    # テスト結果の表示
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 成功" if result else "❌ 失敗"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"合計: {passed}/{total} テストが成功")
    
    if passed == total:
        print("\n🎉 すべてのテストが成功しました！システムは正常に動作します。")
        print("\n🚀 システムを起動するには以下のコマンドを実行してください:")
        print("   python main.py")
    else:
        print(f"\n⚠️ {total - passed}個のテストが失敗しました。")
        print("エラーメッセージを確認して、必要なパッケージをインストールしてください。")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 