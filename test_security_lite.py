#!/usr/bin/env python3
"""
セキュリティテスト - 軽量版アプリケーション用
主要なセキュリティ機能のテスト
"""

import unittest
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(__file__))

# streamlit_app.pyからSecurityManagerをインポート
from streamlit_app import SecurityManager

class TestSecurityManager(unittest.TestCase):
    """セキュリティマネージャーのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.security_manager = SecurityManager()
    
    def test_password_hashing(self):
        """パスワードハッシュ化のテスト"""
        password = "test_password_123"
        hashed = self.security_manager._hash_password(password)
        
        # ハッシュ化されたパスワードが元のパスワードと異なることを確認
        self.assertNotEqual(password, hashed)
        self.assertIn('$', hashed)  # ソルトとハッシュが含まれていることを確認
    
    def test_password_verification(self):
        """パスワード検証のテスト"""
        password = "test_password_123"
        hashed = self.security_manager._hash_password(password)
        
        # 正しいパスワードの検証
        self.assertTrue(self.security_manager.verify_password(password, hashed))
        
        # 間違ったパスワードの検証
        self.assertFalse(self.security_manager.verify_password("wrong_password", hashed))
    
    def test_user_authentication(self):
        """ユーザー認証のテスト"""
        # 正しいクレデンシャルでの認証
        user_info = self.security_manager.authenticate("admin", "admin123")
        self.assertIsNotNone(user_info)
        self.assertEqual(user_info["username"], "admin")
        self.assertEqual(user_info["role"], "admin")
        
        # 間違ったパスワードでの認証
        user_info = self.security_manager.authenticate("admin", "wrong_password")
        self.assertIsNone(user_info)
        
        # 存在しないユーザーでの認証
        user_info = self.security_manager.authenticate("nonexistent", "password")
        self.assertIsNone(user_info)
    
    def test_input_validation(self):
        """入力検証のテスト"""
        # 正常な入力
        clean_input = self.security_manager.validate_input("正常なテキスト")
        self.assertEqual(clean_input, "正常なテキスト")
        
        # 危険な文字を含む入力
        dangerous_input = self.security_manager.validate_input("<script>alert('xss')</script>")
        self.assertNotIn("<", dangerous_input)
        self.assertNotIn(">", dangerous_input)
        
        # 長すぎる入力
        long_input = "a" * 200
        validated = self.security_manager.validate_input(long_input)
        self.assertLessEqual(len(validated), 100)
        
        # 空の入力
        empty_input = self.security_manager.validate_input("")
        self.assertEqual(empty_input, "")
        
        # None入力
        none_input = self.security_manager.validate_input(None)
        self.assertEqual(none_input, "")
    
    def test_stock_code_validation(self):
        """株式コード検証のテスト"""
        # 正しい株式コード
        self.assertTrue(self.security_manager.validate_stock_code("7203.T"))
        self.assertTrue(self.security_manager.validate_stock_code("9984.T"))
        
        # 間違った株式コード
        self.assertFalse(self.security_manager.validate_stock_code("AAPL"))
        self.assertFalse(self.security_manager.validate_stock_code("7203"))
        self.assertFalse(self.security_manager.validate_stock_code("7203."))
        self.assertFalse(self.security_manager.validate_stock_code("abc.T"))
        self.assertFalse(self.security_manager.validate_stock_code(""))
        self.assertFalse(self.security_manager.validate_stock_code(None))
    
    def test_rate_limiting(self):
        """レート制限のテスト"""
        # 初回は許可される
        self.assertTrue(self.security_manager.check_rate_limit())
        
        # 連続リクエストテスト
        allowed_count = 0
        for i in range(65):  # 制限を超えるリクエスト
            if self.security_manager.check_rate_limit():
                allowed_count += 1
        
        # 制限内のリクエストのみ許可されることを確認
        self.assertLessEqual(allowed_count, 60)
    
    def test_user_roles_and_permissions(self):
        """ユーザーロールと権限のテスト"""
        # 管理者権限
        admin_info = self.security_manager.authenticate("admin", "admin123")
        self.assertIn("admin", admin_info["permissions"])
        self.assertIn("read", admin_info["permissions"])
        self.assertIn("write", admin_info["permissions"])
        
        # 一般ユーザー権限
        user_info = self.security_manager.authenticate("user", "user123")
        self.assertIn("read", user_info["permissions"])
        self.assertIn("write", user_info["permissions"])
        self.assertNotIn("admin", user_info["permissions"])

class TestSecurityIntegration(unittest.TestCase):
    """セキュリティ統合テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.security_manager = SecurityManager()
    
    def test_end_to_end_security_flow(self):
        """エンドツーエンドセキュリティフローのテスト"""
        # 1. 入力検証
        user_input = self.security_manager.validate_input("admin")
        self.assertEqual(user_input, "admin")
        
        # 2. 認証
        user_info = self.security_manager.authenticate(user_input, "admin123")
        self.assertIsNotNone(user_info)
        
        # 3. 権限チェック
        self.assertIn("admin", user_info["permissions"])
        
        # 4. レート制限チェック
        self.assertTrue(self.security_manager.check_rate_limit())
        
        # 5. 株式コード検証
        self.assertTrue(self.security_manager.validate_stock_code("7203.T"))

def run_security_tests():
    """セキュリティテストを実行"""
    print("🔐 セキュリティテストを開始...")
    
    # テストスイートを作成
    suite = unittest.TestSuite()
    
    # テストケースを追加
    suite.addTest(unittest.makeSuite(TestSecurityManager))
    suite.addTest(unittest.makeSuite(TestSecurityIntegration))
    
    # テストを実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果を表示
    if result.wasSuccessful():
        print("\n✅ 全てのセキュリティテストが成功しました！")
        print(f"実行済みテスト数: {result.testsRun}")
        return True
    else:
        print("\n❌ セキュリティテストに失敗があります")
        print(f"失敗: {len(result.failures)}")
        print(f"エラー: {len(result.errors)}")
        return False

if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)
