#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
エラーハンドリング管理システム
より詳細でユーザーフレンドリーなエラー処理を提供
"""

import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """エラーの重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """エラーのカテゴリ"""
    NETWORK = "network"
    DATA = "data"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    EXTERNAL_API = "external_api"

class ErrorHandler:
    """エラーハンドリング管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.error_callbacks: Dict[ErrorCategory, Callable] = {}
        self.error_count = 0
        self.error_history = []
        self.max_history = 1000
        
        logger.info("エラーハンドリングシステムを初期化しました")
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """
        エラーコールバックを登録
        
        Args:
            category (ErrorCategory): エラーカテゴリ
            callback (Callable): コールバック関数
        """
        self.error_callbacks[category] = callback
        logger.debug(f"エラーコールバックを登録しました: {category.value}")
    
    def handle_error(self, error: Exception, category: ErrorCategory = ErrorCategory.SYSTEM, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        エラーを処理
        
        Args:
            error (Exception): 発生したエラー
            category (ErrorCategory): エラーカテゴリ
            severity (ErrorSeverity): エラーの重要度
            context (Dict[str, Any]): エラーコンテキスト
            
        Returns:
            Dict[str, Any]: エラー情報
        """
        error_info = self._create_error_info(error, category, severity, context)
        
        # エラーをログに記録
        self._log_error(error_info)
        
        # エラー履歴に追加
        self._add_to_history(error_info)
        
        # カテゴリ別コールバックを実行
        if category in self.error_callbacks:
            try:
                self.error_callbacks[category](error_info)
            except Exception as callback_error:
                logger.error(f"エラーコールバック実行中にエラーが発生: {callback_error}")
        
        # 重要度に応じた処理
        self._handle_by_severity(error_info)
        
        return error_info
    
    def _create_error_info(self, error: Exception, category: ErrorCategory, 
                          severity: ErrorSeverity, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """エラー情報を作成"""
        return {
            'timestamp': datetime.utcnow(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'category': category.value,
            'severity': severity.value,
            'context': context or {},
            'traceback': traceback.format_exc(),
            'error_id': f"ERR_{self.error_count:06d}"
        }
    
    def _log_error(self, error_info: Dict[str, Any]):
        """エラーをログに記録"""
        log_message = (
            f"エラー発生: {error_info['error_id']} | "
            f"カテゴリ: {error_info['category']} | "
            f"重要度: {error_info['severity']} | "
            f"メッセージ: {error_info['error_message']}"
        )
        
        if error_info['severity'] == ErrorSeverity.CRITICAL.value:
            logger.critical(log_message)
        elif error_info['severity'] == ErrorSeverity.HIGH.value:
            logger.error(log_message)
        elif error_info['severity'] == ErrorSeverity.MEDIUM.value:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _add_to_history(self, error_info: Dict[str, Any]):
        """エラー履歴に追加"""
        self.error_history.append(error_info)
        self.error_count += 1
        
        # 履歴サイズ制限
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
    
    def _handle_by_severity(self, error_info: Dict[str, Any]):
        """重要度に応じた処理"""
        severity = error_info['severity']
        
        if severity == ErrorSeverity.CRITICAL.value:
            # クリティカルエラー: 管理者に通知
            self._notify_admin(error_info)
        elif severity == ErrorSeverity.HIGH.value:
            # 高重要度エラー: ログに詳細記録
            logger.error(f"詳細エラー情報: {error_info}")
    
    def _notify_admin(self, error_info: Dict[str, Any]):
        """管理者に通知（実装例）"""
        # 実際の実装では、メール送信やSlack通知などを実装
        logger.critical(f"管理者通知が必要なクリティカルエラー: {error_info['error_id']}")
    
    def get_user_friendly_message(self, error_info: Dict[str, Any]) -> str:
        """
        ユーザーフレンドリーなエラーメッセージを生成
        
        Args:
            error_info (Dict[str, Any]): エラー情報
            
        Returns:
            str: ユーザーフレンドリーなメッセージ
        """
        category = error_info['category']
        severity = error_info['severity']
        
        messages = {
            ErrorCategory.NETWORK.value: {
                ErrorSeverity.LOW.value: "ネットワーク接続が不安定です。しばらく待ってから再試行してください。",
                ErrorSeverity.MEDIUM.value: "ネットワークエラーが発生しました。インターネット接続を確認してください。",
                ErrorSeverity.HIGH.value: "ネットワーク接続に問題があります。しばらく時間をおいてから再試行してください。",
                ErrorSeverity.CRITICAL.value: "ネットワーク接続が完全に切断されました。システム管理者に連絡してください。"
            },
            ErrorCategory.DATA.value: {
                ErrorSeverity.LOW.value: "データの一部が取得できませんでした。",
                ErrorSeverity.MEDIUM.value: "データの取得に問題が発生しました。",
                ErrorSeverity.HIGH.value: "重要なデータが取得できませんでした。",
                ErrorSeverity.CRITICAL.value: "データベースエラーが発生しました。システム管理者に連絡してください。"
            },
            ErrorCategory.VALIDATION.value: {
                ErrorSeverity.LOW.value: "入力内容を確認してください。",
                ErrorSeverity.MEDIUM.value: "入力形式が正しくありません。",
                ErrorSeverity.HIGH.value: "入力内容に問題があります。",
                ErrorSeverity.CRITICAL.value: "入力検証エラーが発生しました。"
            },
            ErrorCategory.AUTHENTICATION.value: {
                ErrorSeverity.LOW.value: "認証情報を確認してください。",
                ErrorSeverity.MEDIUM.value: "認証に失敗しました。",
                ErrorSeverity.HIGH.value: "認証エラーが発生しました。",
                ErrorSeverity.CRITICAL.value: "セキュリティエラーが発生しました。"
            },
            ErrorCategory.SYSTEM.value: {
                ErrorSeverity.LOW.value: "システムに軽微な問題が発生しました。",
                ErrorSeverity.MEDIUM.value: "システムエラーが発生しました。",
                ErrorSeverity.HIGH.value: "システムに問題が発生しました。",
                ErrorSeverity.CRITICAL.value: "システムが停止しました。管理者に連絡してください。"
            }
        }
        
        return messages.get(category, {}).get(severity, "エラーが発生しました。")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        エラー統計を取得
        
        Returns:
            Dict[str, Any]: エラー統計情報
        """
        if not self.error_history:
            return {
                'total_errors': 0,
                'errors_by_category': {},
                'errors_by_severity': {},
                'recent_errors': []
            }
        
        # カテゴリ別統計
        errors_by_category = {}
        errors_by_severity = {}
        
        for error in self.error_history:
            category = error['category']
            severity = error['severity']
            
            errors_by_category[category] = errors_by_category.get(category, 0) + 1
            errors_by_severity[severity] = errors_by_severity.get(severity, 0) + 1
        
        return {
            'total_errors': len(self.error_history),
            'errors_by_category': errors_by_category,
            'errors_by_severity': errors_by_severity,
            'recent_errors': self.error_history[-10:]  # 最近10件
        }
    
    def clear_history(self):
        """エラー履歴をクリア"""
        self.error_history.clear()
        logger.info("エラー履歴をクリアしました")

class ValidationError(Exception):
    """バリデーションエラー"""
    pass

class NetworkError(Exception):
    """ネットワークエラー"""
    pass

class DataError(Exception):
    """データエラー"""
    pass

class AuthenticationError(Exception):
    """認証エラー"""
    pass

class AuthorizationError(Exception):
    """認可エラー"""
    pass 