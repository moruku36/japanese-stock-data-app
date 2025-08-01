#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
非同期処理と同期処理の性能比較テスト
"""

import time
import asyncio
from datetime import datetime, timedelta
from advanced_data_sources import AdvancedDataManager
from async_data_sources import run_async_data_fetch_sync

def test_sync_performance():
    """同期処理の性能テスト"""
    print("🔄 同期処理の性能テストを開始...")
    
    # システム初期化
    advanced_data_manager = AdvancedDataManager()
    
    # テスト用銘柄
    test_tickers = ["9984", "9433", "7203"]
    
    total_time = 0
    results = []
    
    for ticker in test_tickers:
        print(f"  📊 {ticker}の同期処理を実行中...")
        start_time = time.time()
        
        try:
            data = advanced_data_manager.get_comprehensive_stock_data(
                ticker,
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d')
            )
            end_time = time.time()
            processing_time = end_time - start_time
            total_time += processing_time
            results.append({
                'ticker': ticker,
                'time': processing_time,
                'success': True,
                'data_count': len(data) if data else 0
            })
            print(f"    ✅ 完了: {processing_time:.2f}秒")
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            total_time += processing_time
            results.append({
                'ticker': ticker,
                'time': processing_time,
                'success': False,
                'error': str(e)
            })
            print(f"    ❌ エラー: {processing_time:.2f}秒 - {e}")
    
    avg_time = total_time / len(test_tickers)
    print(f"\n📈 同期処理結果:")
    print(f"  総処理時間: {total_time:.2f}秒")
    print(f"  平均処理時間: {avg_time:.2f}秒")
    print(f"  成功件数: {sum(1 for r in results if r['success'])}/{len(results)}")
    
    return results, total_time, avg_time

def test_async_performance():
    """非同期処理の性能テスト"""
    print("\n🚀 非同期処理の性能テストを開始...")
    
    # テスト用銘柄
    test_tickers = ["9984", "9433", "7203"]
    
    total_time = 0
    results = []
    
    for ticker in test_tickers:
        print(f"  📊 {ticker}の非同期処理を実行中...")
        start_time = time.time()
        
        try:
            data = run_async_data_fetch_sync(
                ticker,
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d')
            )
            end_time = time.time()
            processing_time = end_time - start_time
            total_time += processing_time
            results.append({
                'ticker': ticker,
                'time': processing_time,
                'success': True,
                'data_count': len(data) if data else 0
            })
            print(f"    ✅ 完了: {processing_time:.2f}秒")
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            total_time += processing_time
            results.append({
                'ticker': ticker,
                'time': processing_time,
                'success': False,
                'error': str(e)
            })
            print(f"    ❌ エラー: {processing_time:.2f}秒 - {e}")
    
    avg_time = total_time / len(test_tickers)
    print(f"\n📈 非同期処理結果:")
    print(f"  総処理時間: {total_time:.2f}秒")
    print(f"  平均処理時間: {avg_time:.2f}秒")
    print(f"  成功件数: {sum(1 for r in results if r['success'])}/{len(results)}")
    
    return results, total_time, avg_time

def compare_performance():
    """性能比較"""
    print("=" * 60)
    print("🏁 非同期処理 vs 同期処理 性能比較テスト")
    print("=" * 60)
    
    # 同期処理テスト
    sync_results, sync_total, sync_avg = test_sync_performance()
    
    # 非同期処理テスト
    async_results, async_total, async_avg = test_async_performance()
    
    # 比較結果
    print("\n" + "=" * 60)
    print("📊 性能比較結果")
    print("=" * 60)
    
    improvement = ((sync_total - async_total) / sync_total) * 100
    
    print(f"同期処理:")
    print(f"  総処理時間: {sync_total:.2f}秒")
    print(f"  平均処理時間: {sync_avg:.2f}秒")
    
    print(f"\n非同期処理:")
    print(f"  総処理時間: {async_total:.2f}秒")
    print(f"  平均処理時間: {async_avg:.2f}秒")
    
    print(f"\n🚀 性能向上:")
    print(f"  処理時間短縮: {sync_total - async_total:.2f}秒")
    print(f"  性能向上率: {improvement:.1f}%")
    
    if improvement > 0:
        print(f"  ✅ 非同期処理が{sync_total/async_total:.1f}倍高速です！")
    else:
        print(f"  ⚠️ 同期処理の方が高速です")
    
    # 詳細結果
    print(f"\n📋 詳細結果:")
    print(f"{'銘柄':<8} {'同期(秒)':<10} {'非同期(秒)':<12} {'改善率':<10}")
    print("-" * 45)
    
    for i, ticker in enumerate(["9984", "9433", "7203"]):
        sync_time = sync_results[i]['time'] if sync_results[i]['success'] else 0
        async_time = async_results[i]['time'] if async_results[i]['success'] else 0
        
        if sync_time > 0 and async_time > 0:
            improvement_rate = ((sync_time - async_time) / sync_time) * 100
            print(f"{ticker:<8} {sync_time:<10.2f} {async_time:<12.2f} {improvement_rate:<10.1f}%")
        else:
            print(f"{ticker:<8} {sync_time:<10.2f} {async_time:<12.2f} {'N/A':<10}")

if __name__ == "__main__":
    compare_performance() 