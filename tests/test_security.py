#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
セキュリティ機能のテスト
認証・認可システムのテストを実行
"""

import sys
import os
import unittest
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from security.auth_manager import AuthenticationManager, AuthorizationManager

class TestAuthenticationManager(unittest.TestCase):
    """認証管理クラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.auth_manager = AuthenticationManager()
        self.test_user_id = "test_user_123"
        self.test_username = "test_user"
        self.test_password = "secure_password_123"
    
    def test_password_hashing(self):
        """パスワードハッシュ化のテスト"""
        # パスワードをハッシュ化
        hashed_password = self.auth_manager.hash_password(self.test_password)
        
        # ハッシュ化されたパスワードが元のパスワードと異なることを確認
        self.assertNotEqual(self.test_password, hashed_password)
        
        # 同じパスワードでハッシュ化すると異なる結果になることを確認（ソルトのため）
        hashed_password2 = self.auth_manager.hash_password(self.test_password)
        self.assertNotEqual(hashed_password, hashed_password2)
    
    def test_password_verification(self):
        """パスワード検証のテスト"""
        # 正しいパスワードの検証
        hashed_password = self.auth_manager.hash_password(self.test_password)
        self.assertTrue(self.auth_manager.verify_password(self.test_password, hashed_password))
        
        # 間違ったパスワードの検証
        self.assertFalse(self.auth_manager.verify_password("wrong_password", hashed_password))
    
    def test_token_creation_and_verification(self):
        """トークン生成・検証のテスト"""
        # トークンを生成
        token = self.auth_manager.create_token(self.test_user_id, self.test_username)
        
        # トークンが生成されることを確認
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        
        # トークンを検証
        payload = self.auth_manager.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], self.test_user_id)
        self.assertEqual(payload['username'], self.test_username)
    
    def test_token_expiration(self):
        """トークン有効期限のテスト"""
        # 短い有効期限でトークンを生成
        token = self.auth_manager.create_token(self.test_user_id, self.test_username, expires_in=1)
        
        # トークンが有効であることを確認
        payload = self.auth_manager.verify_token(token)
        self.assertIsNotNone(payload)
        
        # 有効期限が切れるまで待機（実際のテストではモックを使用することを推奨）
        import time
        time.sleep(2)
        
        # 有効期限が切れたトークンの検証
        payload = self.auth_manager.verify_token(token)
        self.assertIsNone(payload)
    
    def test_session_management(self):
        """セッション管理のテスト"""
        # セッションを作成
        session_id = self.auth_manager.create_session(self.test_user_id, self.test_username)
        
        # セッションIDが生成されることを確認
        self.assertIsNotNone(session_id)
        self.assertIsInstance(session_id, str)
        
        # セッション情報を取得
        session = self.auth_manager.get_session(session_id)
        self.assertIsNotNone(session)
        self.assertEqual(session['user_id'], self.test_user_id)
        self.assertEqual(session['username'], self.test_username)
        
        # セッションを削除
        result = self.auth_manager.remove_session(session_id)
        self.assertTrue(result)
        
        # 削除されたセッションが取得できないことを確認
        session = self.auth_manager.get_session(session_id)
        self.assertIsNone(session)

class TestAuthorizationManager(unittest.TestCase):
    """認可管理クラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.auth_manager = AuthorizationManager()
    
    def test_permission_checking(self):
        """権限チェックのテスト"""
        # 管理者権限のテスト
        self.assertTrue(self.auth_manager.has_permission('admin', 'read'))
        self.assertTrue(self.auth_manager.has_permission('admin', 'write'))
        self.assertTrue(self.auth_manager.has_permission('admin', 'delete'))
        self.assertTrue(self.auth_manager.has_permission('admin', 'admin'))
        
        # 一般ユーザー権限のテスト
        self.assertTrue(self.auth_manager.has_permission('user', 'read'))
        self.assertTrue(self.auth_manager.has_permission('user', 'write'))
        self.assertFalse(self.auth_manager.has_permission('user', 'delete'))
        self.assertFalse(self.auth_manager.has_permission('user', 'admin'))
        
        # ゲスト権限のテスト
        self.assertTrue(self.auth_manager.has_permission('guest', 'read'))
        self.assertFalse(self.auth_manager.has_permission('guest', 'write'))
        self.assertFalse(self.auth_manager.has_permission('guest', 'delete'))
        self.assertFalse(self.auth_manager.has_permission('guest', 'admin'))
        
        # 存在しないロールのテスト
        self.assertFalse(self.auth_manager.has_permission('unknown_role', 'read'))
    
    def test_get_user_permissions(self):
        """ユーザー権限取得のテスト"""
        # 各ロールの権限一覧を取得
        admin_permissions = self.auth_manager.get_user_permissions('admin')
        user_permissions = self.auth_manager.get_user_permissions('user')
        guest_permissions = self.auth_manager.get_user_permissions('guest')
        
        # 権限一覧が正しく取得されることを確認
        self.assertIn('read', admin_permissions)
        self.assertIn('write', admin_permissions)
        self.assertIn('delete', admin_permissions)
        self.assertIn('admin', admin_permissions)
        
        self.assertIn('read', user_permissions)
        self.assertIn('write', user_permissions)
        self.assertNotIn('delete', user_permissions)
        self.assertNotIn('admin', user_permissions)
        
        self.assertIn('read', guest_permissions)
        self.assertNotIn('write', guest_permissions)
        self.assertNotIn('delete', guest_permissions)
        self.assertNotIn('admin', guest_permissions)
        
        # 存在しないロールのテスト
        unknown_permissions = self.auth_manager.get_user_permissions('unknown_role')
        self.assertEqual(unknown_permissions, [])

class TestSecurityIntegration(unittest.TestCase):
    """セキュリティ統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.auth_manager = AuthenticationManager()
        self.authz_manager = AuthorizationManager()
        self.test_user_id = "integration_test_user"
        self.test_username = "integration_test"
        self.test_password = "integration_password_123"
    
    def test_authentication_and_authorization_flow(self):
        """認証・認可フローの統合テスト"""
        # 1. パスワード検証
        hashed_password = self.auth_manager.hash_password(self.test_password)
        is_valid = self.auth_manager.verify_password(self.test_password, hashed_password)
        self.assertTrue(is_valid)
        
        # 2. トークン生成
        token = self.auth_manager.create_token(self.test_user_id, self.test_username)
        self.assertIsNotNone(token)
        
        # 3. トークン検証
        payload = self.auth_manager.verify_token(token)
        self.assertIsNotNone(payload)
        
        # 4. セッション作成
        session_id = self.auth_manager.create_session(self.test_user_id, self.test_username)
        self.assertIsNotNone(session_id)
        
        # 5. 権限チェック（ユーザーロールとして）
        has_read_permission = self.authz_manager.has_permission('user', 'read')
        has_write_permission = self.authz_manager.has_permission('user', 'write')
        has_admin_permission = self.authz_manager.has_permission('user', 'admin')
        
        self.assertTrue(has_read_permission)
        self.assertTrue(has_write_permission)
        self.assertFalse(has_admin_permission)
        
        # 6. セッション削除
        result = self.auth_manager.remove_session(session_id)
        self.assertTrue(result)

def run_security_tests():
    """セキュリティテストを実行"""
    print("🔒 セキュリティ機能テストを開始...")
    
    # テストスイートを作成
    test_suite = unittest.TestSuite()
    
    # テストケースを追加
    test_suite.addTest(unittest.makeSuite(TestAuthenticationManager))
    test_suite.addTest(unittest.makeSuite(TestAuthorizationManager))
    test_suite.addTest(unittest.makeSuite(TestSecurityIntegration))
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 結果を表示
    print(f"\n📊 セキュリティテスト結果:")
    print(f"  実行テスト数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️ エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1) 