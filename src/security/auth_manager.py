#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
認証・認可管理システム
セキュリティ強化のための認証機能を提供
"""

import hashlib
import secrets
import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class AuthenticationManager:
    """認証管理クラス"""
    
    def __init__(self, secret_key: str = None):
        """
        初期化
        
        Args:
            secret_key (str): JWT署名用の秘密鍵
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.session_store: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = 100
        self.session_timeout = 3600  # 1時間
        
        logger.info("認証管理システムを初期化しました")
    
    def hash_password(self, password: str) -> str:
        """
        パスワードをハッシュ化
        
        Args:
            password (str): 平文パスワード
            
        Returns:
            str: ハッシュ化されたパスワード
        """
        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        パスワードを検証
        
        Args:
            password (str): 平文パスワード
            hashed (str): ハッシュ化されたパスワード
            
        Returns:
            bool: 検証結果
        """
        try:
            salt, hash_hex = hashed.split('$')
            hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hash_obj.hex() == hash_hex
        except Exception as e:
            logger.error(f"パスワード検証エラー: {e}")
            return False
    
    def create_token(self, user_id: str, username: str, expires_in: int = 3600) -> str:
        """
       JWTトークンを生成
        
        Args:
            user_id (str): ユーザーID
            username (str): ユーザー名
            expires_in (int): 有効期限（秒）
            
        Returns:
            str: JWTトークン
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm='HS256')
            logger.info(f"トークンを生成しました: {user_id}")
            return token
        except Exception as e:
            logger.error(f"トークン生成エラー: {e}")
            raise
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        JWTトークンを検証
        
        Args:
            token (str): JWTトークン
            
        Returns:
            Optional[Dict[str, Any]]: ペイロード（検証成功時）
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            logger.debug(f"トークン検証成功: {payload.get('user_id')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("トークンの有効期限が切れています")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"無効なトークン: {e}")
            return None
        except Exception as e:
            logger.error(f"トークン検証エラー: {e}")
            return None
    
    def create_session(self, user_id: str, username: str) -> str:
        """
        セッションを作成
        
        Args:
            user_id (str): ユーザーID
            username (str): ユーザー名
            
        Returns:
            str: セッションID
        """
        # 古いセッションをクリーンアップ
        self._cleanup_expired_sessions()
        
        # セッション数制限チェック
        if len(self.session_store) >= self.max_sessions:
            self._remove_oldest_session()
        
        session_id = secrets.token_hex(32)
        self.session_store[session_id] = {
            'user_id': user_id,
            'username': username,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        
        logger.info(f"セッションを作成しました: {user_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        セッション情報を取得
        
        Args:
            session_id (str): セッションID
            
        Returns:
            Optional[Dict[str, Any]]: セッション情報
        """
        session = self.session_store.get(session_id)
        if session:
            # 最終アクティビティを更新
            session['last_activity'] = datetime.utcnow()
            return session
        return None
    
    def remove_session(self, session_id: str) -> bool:
        """
        セッションを削除
        
        Args:
            session_id (str): セッションID
            
        Returns:
            bool: 削除成功時True
        """
        if session_id in self.session_store:
            del self.session_store[session_id]
            logger.info(f"セッションを削除しました: {session_id}")
            return True
        return False
    
    def _cleanup_expired_sessions(self):
        """期限切れセッションをクリーンアップ"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session_data in self.session_store.items():
            if (current_time - session_data['last_activity']).total_seconds() > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.session_store[session_id]
        
        if expired_sessions:
            logger.info(f"{len(expired_sessions)}個の期限切れセッションを削除しました")
    
    def _remove_oldest_session(self):
        """最も古いセッションを削除"""
        if not self.session_store:
            return
        
        oldest_session = min(
            self.session_store.items(),
            key=lambda x: x[1]['created_at']
        )
        del self.session_store[oldest_session[0]]
        logger.info("最も古いセッションを削除しました")

class AuthorizationManager:
    """認可管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.permissions = {
            'admin': ['read', 'write', 'delete', 'admin'],
            'user': ['read', 'write'],
            'guest': ['read']
        }
        logger.info("認可管理システムを初期化しました")
    
    def has_permission(self, user_role: str, permission: str) -> bool:
        """
        権限をチェック
        
        Args:
            user_role (str): ユーザーロール
            permission (str): 必要な権限
            
        Returns:
            bool: 権限がある場合True
        """
        user_permissions = self.permissions.get(user_role, [])
        return permission in user_permissions
    
    def get_user_permissions(self, user_role: str) -> list:
        """
        ユーザーの権限一覧を取得
        
        Args:
            user_role (str): ユーザーロール
            
        Returns:
            list: 権限一覧
        """
        return self.permissions.get(user_role, []) 