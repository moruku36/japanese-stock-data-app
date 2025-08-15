#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
統合テスト
セキュリティ機能とエラーハンドリング機能の統合テストを実行
"""

import sys
import os
import unittest
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from security.auth_manager import AuthenticationManager, AuthorizationManager
from utils.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity

class TestSecurityAndErrorHandlingIntegration(unittest.TestCase):
    """セキュリティとエラーハンドリングの統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.auth_manager = AuthenticationManager()
        self.authz_manager = AuthorizationManager()
        self.error_handler = ErrorHandler()
        self.test_user_id = "integration_test_user"
        self.test_username = "integration_test"
        self.test_password = "integration_password_123"
    
    def test_authentication_with_error_handling(self):
        """認証とエラーハンドリングの統合テスト"""
        # 1. 正常な認証フロー
        try:
            # パスワードハッシュ化
            hashed_password = self.auth_manager.hash_password(self.test_password)
            
            # パスワード検証
            is_valid = self.auth_manager.verify_password(self.test_password, hashed_password)
            self.assertTrue(is_valid)
            
            # トークン生成
            token = self.auth_manager.create_token(self.test_user_id, self.test_username)
            self.assertIsNotNone(token)
            
            # セッション作成
            session_id = self.auth_manager.create_session(self.test_user_id, self.test_username)
            self.assertIsNotNone(session_id)
            
        except Exception as e:
            # エラーハンドリング
            error_info = self.error_handler.handle_error(
                e,
                ErrorCategory.AUTHENTICATION,
                ErrorSeverity.HIGH,
                {'user_id': self.test_user_id, 'operation': 'authentication'}
            )
            user_message = self.error_handler.get_user_friendly_message(error_info)
            self.fail(f"認証エラー: {user_message}")
    
    def test_authorization_with_error_handling(self):
        """認可とエラーハンドリングの統合テスト"""
        # 1. 権限チェック
        try:
            # 管理者権限のチェック
            admin_has_read = self.authz_manager.has_permission('admin', 'read')
            admin_has_write = self.authz_manager.has_permission('admin', 'write')
            admin_has_admin = self.authz_manager.has_permission('admin', 'admin')
            
            self.assertTrue(admin_has_read)
            self.assertTrue(admin_has_write)
            self.assertTrue(admin_has_admin)
            
            # 一般ユーザー権限のチェック
            user_has_read = self.authz_manager.has_permission('user', 'read')
            user_has_write = self.authz_manager.has_permission('user', 'write')
            user_has_admin = self.authz_manager.has_permission('user', 'admin')
            
            self.assertTrue(user_has_read)
            self.assertTrue(user_has_write)
            self.assertFalse(user_has_admin)
            
            # ゲスト権限のチェック
            guest_has_read = self.authz_manager.has_permission('guest', 'read')
            guest_has_write = self.authz_manager.has_permission('guest', 'write')
            
            self.assertTrue(guest_has_read)
            self.assertFalse(guest_has_write)
            
        except Exception as e:
            # エラーハンドリング
            error_info = self.error_handler.handle_error(
                e,
                ErrorCategory.AUTHORIZATION,
                ErrorSeverity.MEDIUM,
                {'operation': 'permission_check'}
            )
            user_message = self.error_handler.get_user_friendly_message(error_info)
            self.fail(f"認可エラー: {user_message}")
    
    def test_session_management_with_error_handling(self):
        """セッション管理とエラーハンドリングの統合テスト"""
        try:
            # セッション作成
            session_id = self.auth_manager.create_session(self.test_user_id, self.test_username)
            
            # セッション情報取得
            session = self.auth_manager.get_session(session_id)
            self.assertIsNotNone(session)
            self.assertEqual(session['user_id'], self.test_user_id)
            self.assertEqual(session['username'], self.test_username)
            
            # セッション削除
            result = self.auth_manager.remove_session(session_id)
            self.assertTrue(result)
            
            # 削除されたセッションが取得できないことを確認
            session = self.auth_manager.get_session(session_id)
            self.assertIsNone(session)
            
        except Exception as e:
            # エラーハンドリング
            error_info = self.error_handler.handle_error(
                e,
                ErrorCategory.SYSTEM,
                ErrorSeverity.MEDIUM,
                {'session_id': session_id if 'session_id' in locals() else None}
            )
            user_message = self.error_handler.get_user_friendly_message(error_info)
            self.fail(f"セッション管理エラー: {user_message}")
    
    def test_error_handling_with_authentication_context(self):
        """認証コンテキストでのエラーハンドリングテスト"""
        # 認証エラーのシミュレーション
        auth_error = Exception("認証に失敗しました")
        error_info = self.error_handler.handle_error(
            auth_error,
            ErrorCategory.AUTHENTICATION,
            ErrorSeverity.MEDIUM,
            {
                'user_id': self.test_user_id,
                'username': self.test_username,
                'attempt_count': 1
            }
        )
        
        # エラー情報の検証
        self.assertEqual(error_info['category'], 'authentication')
        self.assertEqual(error_info['severity'], 'medium')
        self.assertIn('user_id', error_info['context'])
        self.assertIn('username', error_info['context'])
        self.assertIn('attempt_count', error_info['context'])
        
        # ユーザーフレンドリーなメッセージの検証
        user_message = self.error_handler.get_user_friendly_message(error_info)
        self.assertIn("認証", user_message)
    
    def test_error_handling_with_authorization_context(self):
        """認可コンテキストでのエラーハンドリングテスト"""
        # 認可エラーのシミュレーション
        authz_error = Exception("権限がありません")
        error_info = self.error_handler.handle_error(
            authz_error,
            ErrorCategory.AUTHORIZATION,
            ErrorSeverity.HIGH,
            {
                'user_role': 'guest',
                'required_permission': 'write',
                'resource': 'data_export'
            }
        )
        
        # エラー情報の検証
        self.assertEqual(error_info['category'], 'authorization')
        self.assertEqual(error_info['severity'], 'high')
        self.assertIn('user_role', error_info['context'])
        self.assertIn('required_permission', error_info['context'])
        self.assertIn('resource', error_info['context'])
    
    def test_complete_user_flow_with_error_handling(self):
        """完全なユーザーフローの統合テスト"""
        try:
            # 1. ユーザー認証
            hashed_password = self.auth_manager.hash_password(self.test_password)
            is_valid = self.auth_manager.verify_password(self.test_password, hashed_password)
            self.assertTrue(is_valid)
            
            # 2. セッション作成
            session_id = self.auth_manager.create_session(self.test_user_id, self.test_username)
            
            # 3. 権限チェック（ユーザーロールとして）
            has_read_permission = self.authz_manager.has_permission('user', 'read')
            has_write_permission = self.authz_manager.has_permission('user', 'write')
            has_admin_permission = self.authz_manager.has_permission('user', 'admin')
            
            self.assertTrue(has_read_permission)
            self.assertTrue(has_write_permission)
            self.assertFalse(has_admin_permission)
            
            # 4. セッション削除
            result = self.auth_manager.remove_session(session_id)
            self.assertTrue(result)
            
        except Exception as e:
            # エラーハンドリング
            error_info = self.error_handler.handle_error(
                e,
                ErrorCategory.SYSTEM,
                ErrorSeverity.HIGH,
                {'flow': 'complete_user_flow'}
            )
            user_message = self.error_handler.get_user_friendly_message(error_info)
            self.fail(f"ユーザーフローエラー: {user_message}")

class TestErrorRecoveryAndSecurity(unittest.TestCase):
    """エラー復旧とセキュリティの統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.auth_manager = AuthenticationManager()
        self.error_handler = ErrorHandler()
    
    def test_authentication_error_recovery(self):
        """認証エラーの復旧テスト"""
        # 認証エラーを発生させる
        auth_error = Exception("認証に失敗しました")
        error_info = self.error_handler.handle_error(
            auth_error,
            ErrorCategory.AUTHENTICATION,
            ErrorSeverity.MEDIUM
        )
        
        # エラー統計を確認
        stats = self.error_handler.get_error_statistics()
        self.assertGreater(stats['total_errors'], 0)
        self.assertIn('authentication', stats['errors_by_category'])
        
        # エラーハンドリング後も認証機能が正常に動作することを確認
        try:
            token = self.auth_manager.create_token("test_user", "test")
            self.assertIsNotNone(token)
        except Exception as e:
            self.fail(f"認証機能の復旧に失敗: {e}")
    
    def test_session_cleanup_after_errors(self):
        """エラー後のセッションクリーンアップテスト"""
        # 複数のセッションを作成
        session_ids = []
        for i in range(5):
            session_id = self.auth_manager.create_session(f"user_{i}", f"username_{i}")
            session_ids.append(session_id)
        
        # エラーを発生させる
        error = Exception("テストエラー")
        self.error_handler.handle_error(error, ErrorCategory.SYSTEM, ErrorSeverity.LOW)
        
        # セッションが正常に管理されていることを確認
        for session_id in session_ids:
            session = self.auth_manager.get_session(session_id)
            self.assertIsNotNone(session)
        
        # セッションをクリーンアップ
        for session_id in session_ids:
            self.auth_manager.remove_session(session_id)

def run_integration_tests():
    """統合テストを実行"""
    try:
        print("🔗 統合テストを開始...")
    except Exception:
        print("[INTEGRATION] 統合テストを開始...")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # テストケースを追加
    test_suite.addTest(unittest.makeSuite(TestSecurityAndErrorHandlingIntegration))
    test_suite.addTest(unittest.makeSuite(TestErrorRecoveryAndSecurity))
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果を表示
    try:
        print(f"\n📊 統合テスト結果:")
    except Exception:
        print("\n[INTEGRATION] テスト結果:")
    print(f"  実行テスト数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  エラー: {len(result.errors)}")
    
    if result.failures:
        try:
            print("\n❌ 失敗したテスト:")
        except Exception:
            print("\n[INTEGRATION] 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        try:
            print("\n⚠️ エラーが発生したテスト:")
        except Exception:
            print("\n[INTEGRATION] エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1) 