#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全テスト実行スクリプト
セキュリティ、エラーハンドリング、統合テストを全て実行
"""

import sys
import os
import subprocess
import time
from datetime import datetime

def run_test_file(test_file):
    """個別のテストファイルを実行"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_file} を実行中...")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(test_file)
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_file} が成功しました (実行時間: {execution_time:.2f}秒)")
            return True, result.stdout
        else:
            print(f"❌ {test_file} が失敗しました (実行時間: {execution_time:.2f}秒)")
            print(f"エラー出力: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        print(f"❌ {test_file} の実行中にエラーが発生: {e}")
        return False, str(e)

def run_all_tests():
    """全てのテストを実行"""
    print("🚀 全テスト実行を開始します")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # テストファイルのリスト
    test_files = [
        "test_security.py",
        "test_error_handler.py", 
        "test_integration.py"
    ]
    
    # 結果を記録
    results = []
    total_start_time = time.time()
    
    # 各テストファイルを実行
    for test_file in test_files:
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        if os.path.exists(test_path):
            success, output = run_test_file(test_path)
            results.append({
                'file': test_file,
                'success': success,
                'output': output
            })
        else:
            print(f"⚠️ テストファイルが見つかりません: {test_file}")
            results.append({
                'file': test_file,
                'success': False,
                'output': f"ファイルが見つかりません: {test_file}"
            })
    
    total_end_time = time.time()
    total_execution_time = total_end_time - total_start_time
    
    # 結果サマリーを表示
    print(f"\n{'='*60}")
    print("📊 テスト結果サマリー")
    print(f"{'='*60}")
    
    successful_tests = sum(1 for result in results if result['success'])
    total_tests = len(results)
    
    print(f"総実行時間: {total_execution_time:.2f}秒")
    print(f"実行テスト数: {total_tests}")
    print(f"成功: {successful_tests}")
    print(f"失敗: {total_tests - successful_tests}")
    
    # 各テストの結果を表示
    print(f"\n詳細結果:")
    for result in results:
        status = "✅ 成功" if result['success'] else "❌ 失敗"
        print(f"  {result['file']}: {status}")
    
    # 成功判定
    all_successful = all(result['success'] for result in results)
    
    if all_successful:
        print(f"\n🎉 全てのテストが成功しました！")
        print(f"システムは正常に動作します。")
    else:
        print(f"\n⚠️ {total_tests - successful_tests}個のテストが失敗しました。")
        print(f"エラーメッセージを確認して、必要な修正を行ってください。")
    
    print(f"\n終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_successful

def main():
    """メイン関数"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ テストが中断されました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ テスト実行中にエラーが発生: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 