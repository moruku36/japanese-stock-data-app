#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
パフォーマンステストスクリプト
最適化の効果を測定するためのテスト
"""

import time
import psutil
import gc
from datetime import datetime, timedelta
from stock_data_fetcher import JapaneseStockDataFetcher
from stock_analyzer import StockAnalyzer
from fundamental_analyzer import FundamentalAnalyzer
from utils import PerformanceMonitor, MemoryOptimizer

def test_data_fetching_performance():
    """データ取得のパフォーマンステスト"""
    print("🔍 データ取得パフォーマンステスト")
    print("=" * 50)
    
    fetcher = JapaneseStockDataFetcher()
    test_tickers = ["7203", "6758", "9984", "6861", "9434", "4784", "7974", "6954", "6594", "7733"]
    
    # 単一銘柄取得テスト
    print("📊 単一銘柄取得テスト")
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    for ticker in test_tickers[:3]:
        try:
            data = fetcher.get_latest_price(ticker, "stooq")
            if "error" not in data:
                print(f"  ✅ {ticker}: {data['close']:,.0f}円")
            else:
                print(f"  ❌ {ticker}: {data['error']}")
        except Exception as e:
            print(f"  ❌ {ticker}: {e}")
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    print(f"  実行時間: {end_time - start_time:.2f}秒")
    print(f"  メモリ使用量: {end_memory - start_memory:+.1f}MB")
    
    # 複数銘柄一括取得テスト
    print("\n📊 複数銘柄一括取得テスト")
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        batch_data = fetcher.fetch_multiple_stocks(test_tickers[:5], source="stooq")
        print(f"  ✅ {len(batch_data)}銘柄のデータを取得")
    except Exception as e:
        print(f"  ❌ 一括取得失敗: {e}")
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    print(f"  実行時間: {end_time - start_time:.2f}秒")
    print(f"  メモリ使用量: {end_memory - start_memory:+.1f}MB")

def test_analysis_performance():
    """分析機能のパフォーマンステスト"""
    print("\n🔍 分析機能パフォーマンステスト")
    print("=" * 50)
    
    fetcher = JapaneseStockDataFetcher()
    analyzer = StockAnalyzer(fetcher)
    fundamental_analyzer = FundamentalAnalyzer(fetcher)
    
    test_ticker = "4784"
    
    # テクニカル分析テスト
    print("📊 テクニカル分析テスト")
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        analyzer.plot_technical_analysis(test_ticker, save_plot=False)
        print("  ✅ テクニカル分析完了")
    except Exception as e:
        print(f"  ❌ テクニカル分析失敗: {e}")
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    print(f"  実行時間: {end_time - start_time:.2f}秒")
    print(f"  メモリ使用量: {end_memory - start_memory:+.1f}MB")
    
    # ファンダメンタル分析テスト
    print("\n📊 ファンダメンタル分析テスト")
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        fundamental_analyzer.plot_financial_analysis(test_ticker, save_plot=False)
        print("  ✅ ファンダメンタル分析完了")
    except Exception as e:
        print(f"  ❌ ファンダメンタル分析失敗: {e}")
    
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    print(f"  実行時間: {end_time - start_time:.2f}秒")
    print(f"  メモリ使用量: {end_memory - start_memory:+.1f}MB")

def test_memory_optimization():
    """メモリ最適化テスト"""
    print("\n🔍 メモリ最適化テスト")
    print("=" * 50)
    
    # メモリ使用量の監視
    print("📊 メモリ使用量監視")
    memory_info = MemoryOptimizer.get_memory_usage()
    print(f"  現在のメモリ使用量: {memory_info['current_mb']:.1f}MB")
    print(f"  システム全体メモリ: {memory_info['system_mb']:.1f}MB")
    print(f"  メモリ使用率: {memory_info['usage_percent']:.1f}%")
    
    # メモリクリーンアップテスト
    print("\n📊 メモリクリーンアップテスト")
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    # 大量のデータを生成してメモリを消費
    import pandas as pd
    import numpy as np
    
    large_data = []
    for i in range(1000):
        large_data.append({
            'date': datetime.now() - timedelta(days=i),
            'price': np.random.normal(1000, 100),
            'volume': np.random.randint(1000000, 10000000)
        })
    
    df = pd.DataFrame(large_data)
    after_data_memory = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"  データ生成後のメモリ: {after_data_memory - start_memory:+.1f}MB")
    
    # メモリクリーンアップ
    del large_data, df
    MemoryOptimizer.cleanup_memory()
    gc.collect()
    
    after_cleanup_memory = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"  クリーンアップ後のメモリ: {after_cleanup_memory - start_memory:+.1f}MB")
    print(f"  メモリ解放量: {after_data_memory - after_cleanup_memory:.1f}MB")

def test_cache_performance():
    """キャッシュパフォーマンステスト"""
    print("\n🔍 キャッシュパフォーマンステスト")
    print("=" * 50)
    
    fetcher = JapaneseStockDataFetcher()
    test_ticker = "4784"
    
    # 初回取得（キャッシュなし）
    print("📊 初回取得テスト（キャッシュなし）")
    start_time = time.time()
    
    try:
        data1 = fetcher.get_latest_price(test_ticker, "stooq")
        first_fetch_time = time.time() - start_time
        print(f"  初回取得時間: {first_fetch_time:.2f}秒")
    except Exception as e:
        print(f"  ❌ 初回取得失敗: {e}")
        return
    
    # 2回目取得（キャッシュあり）
    print("\n📊 2回目取得テスト（キャッシュあり）")
    start_time = time.time()
    
    try:
        data2 = fetcher.get_latest_price(test_ticker, "stooq")
        second_fetch_time = time.time() - start_time
        print(f"  2回目取得時間: {second_fetch_time:.2f}秒")
        
        if "error" not in data1 and "error" not in data2:
            speedup = first_fetch_time / second_fetch_time if second_fetch_time > 0 else float('inf')
            print(f"  速度向上: {speedup:.1f}倍")
    except Exception as e:
        print(f"  ❌ 2回目取得失敗: {e}")

def test_concurrent_performance():
    """並行処理パフォーマンステスト"""
    print("\n🔍 並行処理パフォーマンステスト")
    print("=" * 50)
    
    fetcher = JapaneseStockDataFetcher()
    test_tickers = ["7203", "6758", "9984", "6861", "9434"]
    
    # 逐次処理
    print("📊 逐次処理テスト")
    start_time = time.time()
    
    sequential_results = []
    for ticker in test_tickers:
        try:
            data = fetcher.get_latest_price(ticker, "stooq")
            if "error" not in data:
                sequential_results.append(data)
        except Exception as e:
            print(f"  ❌ {ticker}: {e}")
    
    sequential_time = time.time() - start_time
    print(f"  逐次処理時間: {sequential_time:.2f}秒")
    print(f"  取得成功数: {len(sequential_results)}/{len(test_tickers)}")
    
    # 並行処理
    print("\n📊 並行処理テスト")
    start_time = time.time()
    
    try:
        concurrent_results = fetcher.fetch_multiple_stocks(test_tickers, source="stooq")
        concurrent_time = time.time() - start_time
        print(f"  並行処理時間: {concurrent_time:.2f}秒")
        print(f"  取得成功数: {len(concurrent_results)}/{len(test_tickers)}")
        
        if sequential_time > 0:
            speedup = sequential_time / concurrent_time
            print(f"  並行処理による速度向上: {speedup:.1f}倍")
    except Exception as e:
        print(f"  ❌ 並行処理失敗: {e}")

def main():
    """メイン関数"""
    print("🚀 パフォーマンステスト開始")
    print("=" * 60)
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # 各テストを実行
        test_data_fetching_performance()
        test_analysis_performance()
        test_memory_optimization()
        test_cache_performance()
        test_concurrent_performance()
        
        print("\n" + "=" * 60)
        print("🎉 パフォーマンステスト完了")
        print(f"終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 最終的なメモリ使用量を表示
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        print(f"最終メモリ使用量: {final_memory:.1f}MB")
        
    except Exception as e:
        print(f"\n❌ テスト実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 