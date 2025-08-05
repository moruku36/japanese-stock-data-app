#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新機能テストスクリプト
新機能モジュールが正常にインポートできるかテストします
"""

import sys
import os

# プロジェクトのsrcディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_dir)

def test_new_features():
    """新機能のインポートテスト"""
    results = {}
    
    print("=== 新機能インポートテスト ===\n")
    
    # 1. ダッシュボード機能テスト
    try:
        from web.dashboard import DashboardManager
        dashboard = DashboardManager()
        results['dashboard'] = True
        print("✅ ダッシュボード機能 - インポート成功")
    except ImportError as e:
        results['dashboard'] = False
        print(f"❌ ダッシュボード機能 - インポートエラー: {e}")
    
    # 2. ポートフォリオ最適化機能テスト
    try:
        from web.portfolio_optimization import PortfolioOptimizer
        optimizer = PortfolioOptimizer()
        results['portfolio'] = True
        print("✅ ポートフォリオ最適化機能 - インポート成功")
    except ImportError as e:
        results['portfolio'] = False
        print(f"❌ ポートフォリオ最適化機能 - インポートエラー: {e}")
    
    # 3. API監視機能テスト
    try:
        from web.api_monitoring import APIMonitor
        monitor = APIMonitor()
        results['api_monitoring'] = True
        print("✅ API監視機能 - インポート成功")
    except ImportError as e:
        results['api_monitoring'] = False
        print(f"❌ API監視機能 - インポートエラー: {e}")
    
    print("\n=== 依存関係チェック ===\n")
    
    # 依存関係チェック
    dependencies = {
        'streamlit': 'Streamlitフレームワーク',
        'plotly': 'インタラクティブ可視化',
        'scipy': 'ポートフォリオ最適化',
        'numpy': '数値計算',
        'pandas': 'データ処理',
        'yfinance': '株価データ取得',
        'threading': 'バックグラウンド処理',
        'requests': 'HTTP通信'
    }
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (未インストール)")
    
    print("\n=== 結果サマリー ===\n")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 すべての新機能が正常にインポートされました！")
        print("新機能は利用可能です。")
    else:
        print(f"⚠️  {success_count}/{total_count} の新機能がインポートされました。")
        if not results['dashboard']:
            print("- ダッシュボード機能が利用できません")
        if not results['portfolio']:
            print("- ポートフォリオ最適化機能が利用できません")
        if not results['api_monitoring']:
            print("- API監視機能が利用できません")
    
    return results

if __name__ == "__main__":
    test_new_features()
