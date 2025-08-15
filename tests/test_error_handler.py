#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
エラーハンドリング機能のテスト
エラー処理システムのテストを実行
"""

import sys
import os
import unittest
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, ValidationError, NetworkError, DataError

class TestErrorHandler(unittest.TestCase):
    """エラーハンドリング管理クラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.error_handler = ErrorHandler()
        self.test_error = Exception("テストエラー")
    
    def test_error_creation(self):
        """エラー情報作成のテスト"""
        error_info = self.error_handler.handle_error(
            self.test_error,
            ErrorCategory.SYSTEM,
            ErrorSeverity.MEDIUM,
            {'test_context': 'test_value'}
        )
        
        # エラー情報が正しく作成されることを確認
        self.assertIn('timestamp', error_info)
        self.assertIn('error_type', error_info)
        self.assertIn('error_message', error_info)
        self.assertIn('category', error_info)
        self.assertIn('severity', error_info)
        self.assertIn('context', error_info)
        self.assertIn('error_id', error_info)
        
        self.assertEqual(error_info['error_type'], 'Exception')
        self.assertEqual(error_info['error_message'], 'テストエラー')
        self.assertEqual(error_info['category'], 'system')
        self.assertEqual(error_info['severity'], 'medium')
        self.assertEqual(error_info['context']['test_context'], 'test_value')
    
    def test_error_categories(self):
        """エラーカテゴリのテスト"""
        categories = [
            ErrorCategory.NETWORK,
            ErrorCategory.DATA,
            ErrorCategory.VALIDATION,
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.AUTHORIZATION,
            ErrorCategory.SYSTEM,
            ErrorCategory.USER_INPUT,
            ErrorCategory.EXTERNAL_API
        ]
        
        for category in categories:
            error_info = self.error_handler.handle_error(
                self.test_error,
                category,
                ErrorSeverity.LOW
            )
            self.assertEqual(error_info['category'], category.value)
    
    def test_error_severities(self):
        """エラー重要度のテスト"""
        severities = [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL
        ]
        
        for severity in severities:
            error_info = self.error_handler.handle_error(
                self.test_error,
                ErrorCategory.SYSTEM,
                severity
            )
            self.assertEqual(error_info['severity'], severity.value)
    
    def test_user_friendly_messages(self):
        """ユーザーフレンドリーなメッセージのテスト"""
        # ネットワークエラー
        network_error = NetworkError("接続タイムアウト")
        error_info = self.error_handler.handle_error(
            network_error,
            ErrorCategory.NETWORK,
            ErrorSeverity.MEDIUM
        )
        user_message = self.error_handler.get_user_friendly_message(error_info)
        self.assertIn("ネットワーク", user_message)
        
        # データエラー
        data_error = DataError("データが見つかりません")
        error_info = self.error_handler.handle_error(
            data_error,
            ErrorCategory.DATA,
            ErrorSeverity.HIGH
        )
        user_message = self.error_handler.get_user_friendly_message(error_info)
        self.assertIn("データ", user_message)
        
        # 認証エラー
        auth_error = Exception("認証に失敗しました")
        error_info = self.error_handler.handle_error(
            auth_error,
            ErrorCategory.AUTHENTICATION,
            ErrorSeverity.MEDIUM
        )
        user_message = self.error_handler.get_user_friendly_message(error_info)
        self.assertIn("認証", user_message)
    
    def test_error_statistics(self):
        """エラー統計のテスト"""
        # 複数のエラーを発生させる
        for i in range(5):
            self.error_handler.handle_error(
                Exception(f"エラー{i}"),
                ErrorCategory.SYSTEM,
                ErrorSeverity.MEDIUM
            )
        
        # 統計を取得
        stats = self.error_handler.get_error_statistics()
        
        # 統計情報が正しく取得されることを確認
        self.assertEqual(stats['total_errors'], 5)
        self.assertIn('system', stats['errors_by_category'])
        self.assertEqual(stats['errors_by_category']['system'], 5)
        self.assertIn('medium', stats['errors_by_severity'])
        self.assertEqual(stats['errors_by_severity']['medium'], 5)
        self.assertEqual(len(stats['recent_errors']), 5)
    
    def test_error_history_cleanup(self):
        """エラー履歴のクリーンアップテスト"""
        # 最大履歴数を超えるエラーを発生させる
        for i in range(1100):  # 最大履歴数は1000
            self.error_handler.handle_error(
                Exception(f"エラー{i}"),
                ErrorCategory.SYSTEM,
                ErrorSeverity.LOW
            )
        
        # 履歴が制限されていることを確認
        stats = self.error_handler.get_error_statistics()
        self.assertEqual(stats['total_errors'], 1000)  # 最大履歴数
    
    def test_error_callback_registration(self):
        """エラーコールバック登録のテスト"""
        callback_called = False
        
        def test_callback(error_info):
            nonlocal callback_called
            callback_called = True
        
        # コールバックを登録
        self.error_handler.register_error_callback(ErrorCategory.SYSTEM, test_callback)
        
        # エラーを発生させる
        self.error_handler.handle_error(
            self.test_error,
            ErrorCategory.SYSTEM,
            ErrorSeverity.MEDIUM
        )
        
        # コールバックが呼ばれることを確認
        self.assertTrue(callback_called)

class TestCustomErrors(unittest.TestCase):
    """カスタムエラークラスのテスト"""
    
    def test_validation_error(self):
        """バリデーションエラーのテスト"""
        error = ValidationError("入力値が無効です")
        self.assertEqual(str(error), "入力値が無効です")
        self.assertIsInstance(error, Exception)
    
    def test_network_error(self):
        """ネットワークエラーのテスト"""
        error = NetworkError("接続に失敗しました")
        self.assertEqual(str(error), "接続に失敗しました")
        self.assertIsInstance(error, Exception)
    
    def test_data_error(self):
        """データエラーのテスト"""
        error = DataError("データの取得に失敗しました")
        self.assertEqual(str(error), "データの取得に失敗しました")
        self.assertIsInstance(error, Exception)
    
    def test_authentication_error(self):
        """認証エラーのテスト"""
        error = Exception("認証に失敗しました")
        self.assertEqual(str(error), "認証に失敗しました")
        self.assertIsInstance(error, Exception)
    
    def test_authorization_error(self):
        """認可エラーのテスト"""
        error = Exception("権限がありません")
        self.assertEqual(str(error), "権限がありません")
        self.assertIsInstance(error, Exception)

def run_error_handler_tests():
    """エラーハンドリングテストを実行"""
    try:
        print("⚠️ エラーハンドリング機能テストを開始...")
    except Exception:
        print("[ERROR_HANDLER] エラーハンドリング機能テストを開始...")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # テストケースを追加
    test_suite.addTest(unittest.makeSuite(TestErrorHandler))
    test_suite.addTest(unittest.makeSuite(TestCustomErrors))
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果を表示
    try:
        print(f"\n📊 エラーハンドリングテスト結果:")
    except Exception:
        print("\n[ERROR_HANDLER] テスト結果:")
    print(f"  実行テスト数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  エラー: {len(result.errors)}")
    
    if result.failures:
        try:
            print("\n❌ 失敗したテスト:")
        except Exception:
            print("\n[ERROR_HANDLER] 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        try:
            print("\n⚠️ エラーが発生したテスト:")
        except Exception:
            print("\n[ERROR_HANDLER] エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_error_handler_tests()
    sys.exit(0 if success else 1) 