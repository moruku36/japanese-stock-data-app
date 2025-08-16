#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
強化されたセキュリティとアクセス制御システム
OAuth/JWT認証、APIキー暗号化、レート制限を実装
"""

import os
import jwt
import hashlib
import secrets
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from functools import wraps
import threading
from collections import defaultdict, deque
import json

# 暗号化ライブラリ（オプション）
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """ユーザーロール"""
    ADMIN = "admin"
    PREMIUM = "premium"
    STANDARD = "standard"
    GUEST = "guest"

class PermissionLevel(Enum):
    """権限レベル"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

@dataclass
class User:
    """ユーザー情報"""
    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

@dataclass
class Session:
    """セッション情報"""
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_active: bool = True

@dataclass
class RateLimitConfig:
    """レート制限設定"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int

class EnhancedSecurityManager:
    """強化されたセキュリティ管理クラス"""
    
    def __init__(self, secret_key: str = None, encryption_key: str = None):
        """
        初期化
        
        Args:
            secret_key (str): JWT署名用の秘密鍵
            encryption_key (str): 暗号化用のキー
        """
        self.secret_key = secret_key or os.environ.get('JWT_SECRET_KEY')
        if not self.secret_key:
            raise ValueError("JWT署名のための環境変数 'JWT_SECRET_KEY' が設定されていません。")
        self.encryption_key = encryption_key
        self.fernet = self._initialize_encryption()
        
        # セッション管理
        self.sessions: Dict[str, Session] = {}
        self.users: Dict[str, User] = {}
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        
        # レート制限
        self.rate_limits: Dict[str, RateLimitConfig] = self._initialize_rate_limits()
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # セキュリティ設定
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
        self.session_timeout = timedelta(hours=24)
        self.password_requirements = {
            'min_length': 8,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special': True
        }
        
        # 権限定義
        self.permissions = self._initialize_permissions()
        
        logger.info("強化されたセキュリティシステムを初期化しました")
    
    def _generate_secret_key(self) -> str:
        """秘密鍵を生成"""
        return secrets.token_hex(32)
    
    def _initialize_encryption(self):
        """暗号化システムを初期化"""
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("暗号化ライブラリ 'cryptography' がインストールされていません。pip install cryptography を実行してください。")
            return None
        
        if not self.encryption_key:
            # パスワードベースのキー生成（デフォルト値は許可しない）
            password_env = os.environ.get('SECURITY_PASSWORD')
            salt_env = os.environ.get('SECURITY_SALT')
            if not password_env or not salt_env:
                raise ValueError("セキュリティキー生成のための環境変数 'SECURITY_PASSWORD' と 'SECURITY_SALT' が設定されていません。")
            password = password_env.encode()
            salt = salt_env.encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            return Fernet(key)
        
        return Fernet(self.encryption_key.encode())
    
    def _initialize_rate_limits(self) -> Dict[str, RateLimitConfig]:
        """レート制限設定を初期化"""
        return {
            UserRole.GUEST.value: RateLimitConfig(
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                burst_limit=5
            ),
            UserRole.STANDARD.value: RateLimitConfig(
                requests_per_minute=30,
                requests_per_hour=500,
                requests_per_day=5000,
                burst_limit=10
            ),
            UserRole.PREMIUM.value: RateLimitConfig(
                requests_per_minute=100,
                requests_per_hour=2000,
                requests_per_day=20000,
                burst_limit=50
            ),
            UserRole.ADMIN.value: RateLimitConfig(
                requests_per_minute=1000,
                requests_per_hour=10000,
                requests_per_day=100000,
                burst_limit=100
            )
        }
    
    def _initialize_permissions(self) -> Dict[UserRole, List[str]]:
        """権限を初期化"""
        return {
            UserRole.GUEST: [
                "stock_data:read",
                "chart:view"
            ],
            UserRole.STANDARD: [
                "stock_data:read",
                "chart:view",
                "analysis:basic",
                "export:basic"
            ],
            UserRole.PREMIUM: [
                "stock_data:read",
                "chart:view",
                "analysis:basic",
                "analysis:advanced",
                "portfolio:manage",
                "alerts:create",
                "export:advanced"
            ],
            UserRole.ADMIN: [
                "stock_data:read",
                "stock_data:write",
                "chart:view",
                "analysis:basic",
                "analysis:advanced",
                "portfolio:manage",
                "alerts:create",
                "export:advanced",
                "system:monitor",
                "user:manage"
            ]
        }
    
    def encrypt_sensitive_data(self, data: str) -> Optional[str]:
        """機密データを暗号化"""
        if not self.fernet:
            logger.warning("暗号化が利用できません")
            return data
        
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"暗号化エラー: {e}")
            return None
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """暗号化されたデータを復号化"""
        if not self.fernet:
            logger.warning("復号化が利用できません")
            return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"復号化エラー: {e}")
            return None
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """パスワードをハッシュ化"""
        if not salt:
            salt = secrets.token_hex(16)
        
        # PBKDF2でハッシュ化
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """パスワードを検証"""
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hash_obj.hex() == hashed
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """パスワード強度を検証"""
        issues = []
        
        if len(password) < self.password_requirements['min_length']:
            issues.append(f"最低{self.password_requirements['min_length']}文字必要です")
        
        if self.password_requirements['require_uppercase'] and not any(c.isupper() for c in password):
            issues.append("大文字を含む必要があります")
        
        if self.password_requirements['require_lowercase'] and not any(c.islower() for c in password):
            issues.append("小文字を含む必要があります")
        
        if self.password_requirements['require_numbers'] and not any(c.isdigit() for c in password):
            issues.append("数字を含む必要があります")
        
        if self.password_requirements['require_special'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            issues.append("特殊文字を含む必要があります")
        
        return len(issues) == 0, issues
    
    def create_user(self, username: str, email: str, password: str, role: UserRole = UserRole.STANDARD) -> Optional[User]:
        """ユーザーを作成"""
        # パスワード強度チェック
        is_valid, issues = self.validate_password_strength(password)
        if not is_valid:
            logger.warning(f"パスワード強度不足: {', '.join(issues)}")
            return None
        
        # ユーザー重複チェック
        if any(user.username == username or user.email == email for user in self.users.values()):
            logger.warning(f"ユーザーまたはメールアドレスが既に存在します: {username}, {email}")
            return None
        
        user_id = secrets.token_hex(16)
        hashed_password, salt = self.hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=self.permissions.get(role, []),
            created_at=datetime.now()
        )
        
        self.users[user_id] = user
        
        # パスワードは別途保存（実際の実装ではデータベース使用）
        self._store_user_credentials(user_id, hashed_password, salt)
        
        logger.info(f"ユーザーを作成しました: {username} ({role.value})")
        return user
    
    def authenticate_user(self, username: str, password: str, ip_address: str = "", user_agent: str = "") -> Optional[str]:
        """ユーザー認証"""
        # アカウントロックアウトチェック
        if self._is_account_locked(username):
            logger.warning(f"アカウントがロックされています: {username}")
            return None
        
        # ユーザー検索
        user = None
        for u in self.users.values():
            if u.username == username:
                user = u
                break
        
        if not user or not user.is_active:
            self._record_failed_attempt(username)
            logger.warning(f"ユーザーが見つからないか無効です: {username}")
            return None
        
        # パスワード検証
        stored_hash, salt = self._get_user_credentials(user.user_id)
        if not stored_hash or not self.verify_password(password, stored_hash, salt):
            self._record_failed_attempt(username)
            logger.warning(f"パスワードが正しくありません: {username}")
            return None
        
        # 認証成功 - セッション作成
        session_id = self._create_session(user.user_id, ip_address, user_agent)
        
        # ログイン時刻更新
        user.last_login = datetime.now()
        
        # 失敗記録をクリア
        self.failed_attempts[username] = []
        
        logger.info(f"ユーザー認証成功: {username}")
        return session_id
    
    def _is_account_locked(self, username: str) -> bool:
        """アカウントロックアウト状態をチェック"""
        failed_list = self.failed_attempts.get(username, [])
        
        # 古い記録を削除
        cutoff_time = datetime.now() - self.lockout_duration
        self.failed_attempts[username] = [
            attempt for attempt in failed_list if attempt > cutoff_time
        ]
        
        return len(self.failed_attempts[username]) >= self.max_failed_attempts
    
    def _record_failed_attempt(self, username: str):
        """失敗試行を記録"""
        self.failed_attempts[username].append(datetime.now())
    
    def _create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """セッションを作成"""
        session_id = secrets.token_hex(32)
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now(),
            expires_at=datetime.now() + self.session_timeout,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """セッションを検証"""
        session = self.sessions.get(session_id)
        
        if not session or not session.is_active:
            return None
        
        if datetime.now() > session.expires_at:
            session.is_active = False
            logger.info(f"セッションが期限切れです: {session_id}")
            return None
        
        user = self.users.get(session.user_id)
        if not user or not user.is_active:
            return None
        
        return user
    
    def create_jwt_token(self, user_id: str, additional_claims: Dict[str, Any] = None) -> str:
        """JWTトークンを作成"""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("ユーザーが見つかりません")
        
        payload = {
            'user_id': user_id,
            'username': user.username,
            'role': user.role.value,
            'permissions': user.permissions,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """JWTトークンを検証"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # ユーザーの有効性を確認
            user = self.users.get(payload.get('user_id'))
            if not user or not user.is_active:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWTトークンが期限切れです")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"無効なJWTトークン: {e}")
            return None
    
    def check_rate_limit(self, user_id: str, endpoint: str = "default") -> Tuple[bool, Dict[str, Any]]:
        """レート制限をチェック"""
        user = self.users.get(user_id)
        if not user:
            # ゲストユーザーとして扱う
            user_role = UserRole.GUEST
        else:
            user_role = user.role
        
        rate_config = self.rate_limits.get(user_role.value, self.rate_limits[UserRole.GUEST.value])
        
        key = f"{user_id}:{endpoint}"
        current_time = time.time()
        
        # 履歴を取得し、古いエントリを削除
        history = self.request_history[key]
        
        # 1分、1時間、1日の制限をチェック
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        day_ago = current_time - 86400
        
        # 古いエントリを削除
        while history and history[0] < day_ago:
            history.popleft()
        
        # 各期間のリクエスト数をカウント
        minute_count = sum(1 for t in history if t > minute_ago)
        hour_count = sum(1 for t in history if t > hour_ago)
        day_count = len(history)
        
        # 制限チェック
        if minute_count >= rate_config.requests_per_minute:
            return False, {"reason": "minute_limit", "retry_after": 60}
        
        if hour_count >= rate_config.requests_per_hour:
            return False, {"reason": "hour_limit", "retry_after": 3600}
        
        if day_count >= rate_config.requests_per_day:
            return False, {"reason": "day_limit", "retry_after": 86400}
        
        # バースト制限チェック（直近10秒間）
        burst_cutoff = current_time - 10
        burst_count = sum(1 for t in history if t > burst_cutoff)
        
        if burst_count >= rate_config.burst_limit:
            return False, {"reason": "burst_limit", "retry_after": 10}
        
        # リクエストを記録
        history.append(current_time)
        
        return True, {
            "remaining": {
                "minute": rate_config.requests_per_minute - minute_count - 1,
                "hour": rate_config.requests_per_hour - hour_count - 1,
                "day": rate_config.requests_per_day - day_count - 1
            }
        }
    
    def require_permission(self, required_permission: str):
        """権限チェックデコレータ"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # セッション情報を取得（実装に応じて調整）
                session_id = kwargs.get('session_id') or getattr(func, '_session_id', None)
                
                if not session_id:
                    raise PermissionError("セッション情報が必要です")
                
                user = self.validate_session(session_id)
                if not user:
                    raise PermissionError("無効なセッションです")
                
                if required_permission not in user.permissions:
                    raise PermissionError(f"権限が不足しています: {required_permission}")
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def _store_user_credentials(self, user_id: str, hashed_password: str, salt: str):
        """ユーザー認証情報を暗号化して保存（環境変数のマスターキー必須）"""
        if not self.fernet:
            raise ValueError("暗号化が利用できないため、認証情報を安全に保存できません。'cryptography' と SECURITY_PASSWORD/SECURITY_SALT を設定してください。")
        try:
            payload = json.dumps({"hashed_password": hashed_password, "salt": salt}, ensure_ascii=False)
            encrypted = self.encrypt_sensitive_data(payload)
            secrets_dir = os.path.join(os.getcwd(), 'secrets')
            os.makedirs(secrets_dir, exist_ok=True)
            credentials_file = os.path.join(secrets_dir, f"credentials_{user_id}.enc")
            with open(credentials_file, 'w', encoding='utf-8') as f:
                f.write(encrypted)
        except Exception as e:
            logger.error(f"認証情報の保存に失敗: {e}")
    
    def _get_user_credentials(self, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """ユーザー認証情報を復号して取得"""
        if not self.fernet:
            logger.error("暗号化が利用できないため、認証情報を取得できません")
            return None, None
        credentials_file = os.path.join(os.getcwd(), 'secrets', f"credentials_{user_id}.enc")
        try:
            with open(credentials_file, 'r', encoding='utf-8') as f:
                encrypted = f.read()
            decrypted = self.decrypt_sensitive_data(encrypted)
            if not decrypted:
                return None, None
            credentials = json.loads(decrypted)
            return credentials.get("hashed_password"), credentials.get("salt")
        except Exception as e:
            logger.error(f"認証情報の取得に失敗: {e}")
            return None, None
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """セキュリティメトリクスを取得"""
        active_sessions = sum(1 for s in self.sessions.values() if s.is_active)
        locked_accounts = sum(1 for attempts in self.failed_attempts.values() if len(attempts) >= self.max_failed_attempts)
        
        return {
            "total_users": len(self.users),
            "active_sessions": active_sessions,
            "locked_accounts": locked_accounts,
            "failed_attempts": sum(len(attempts) for attempts in self.failed_attempts.values()),
            "rate_limit_violations": 0  # 実装により取得
        }
    
    def audit_log(self, user_id: str, action: str, details: Dict[str, Any] = None):
        """監査ログを記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "ip_address": details.get("ip_address", "") if details else ""
        }
        
        logger.info(f"監査ログ: {json.dumps(log_entry, ensure_ascii=False)}")

# グローバルインスタンス
security_manager = None
try:
    if os.environ.get('JWT_SECRET_KEY'):
        security_manager = EnhancedSecurityManager()
    else:
        logger.warning("JWT_SECRET_KEY が未設定のため、security_manager は初期化されていません")
except Exception as e:
    logger.error(f"セキュリティマネージャの初期化に失敗: {e}")

if __name__ == "__main__":
    # テスト実行
    sm = EnhancedSecurityManager()
    
    # テストユーザー作成
    user = sm.create_user("testuser", "test@example.com", "SecurePass123!", UserRole.STANDARD)
    if user:
        print(f"ユーザー作成成功: {user.username}")
        
        # 認証テスト
        session_id = sm.authenticate_user("testuser", "SecurePass123!")
        if session_id:
            print(f"認証成功: {session_id[:16]}...")
            
            # JWT作成
            token = sm.create_jwt_token(user.user_id)
            print(f"JWT作成成功: {token[:50]}...")
            
            # レート制限テスト
            allowed, info = sm.check_rate_limit(user.user_id)
            print(f"レート制限チェック: {allowed}, 残り: {info}")
    
    # セキュリティメトリクス
    print("\nセキュリティメトリクス:")
    print(json.dumps(sm.get_security_metrics(), indent=2, ensure_ascii=False))
