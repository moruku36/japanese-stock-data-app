#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改善されたエラーハンドリングとユーザーフィードバックシステム
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
import re
import json

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
    IMPORT_ERROR = "import_error"
    CONFIGURATION = "configuration"

@dataclass
class ErrorSolution:
    """エラー解決策"""
    title: str
    description: str
    steps: List[str]
    code_example: Optional[str] = None
    documentation_link: Optional[str] = None

@dataclass
class UserFriendlyError:
    """ユーザーフレンドリーなエラー情報"""
    error_id: str
    user_message: str
    technical_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    solutions: List[ErrorSolution]
    context: Dict[str, Any]
    timestamp: datetime

class EnhancedErrorHandler:
    """強化されたエラーハンドリングクラス"""
    
    def __init__(self):
        """初期化"""
        self.error_callbacks: Dict[ErrorCategory, Callable] = {}
        self.error_count = 0
        self.error_history: List[UserFriendlyError] = []
        self.max_history = 1000
        
        # エラーメッセージパターンと解決策のマッピング
        self.error_patterns = self._initialize_error_patterns()
        
        # 類似銘柄コードの辞書
        self.similar_codes = self._initialize_similar_codes()
        
        logger.info("強化されたエラーハンドリングシステムを初期化しました")
    
    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """エラーパターンと解決策を初期化"""
        return {
            "import_error": {
                "patterns": [
                    r"ImportError.*(?:yfinance|pandas_datareader|aiohttp|plotly|scipy)",
                    r"ModuleNotFoundError.*(?:yfinance|pandas_datareader|aiohttp|plotly|scipy)"
                ],
                "user_message": "必要なライブラリがインストールされていません。",
                "solutions": [
                    ErrorSolution(
                        title="ライブラリのインストール",
                        description="不足している依存関係をインストールします",
                        steps=[
                            "ターミナルまたはコマンドプロンプトを開く",
                            "以下のコマンドを実行: pip install -r requirements.txt",
                            "または個別にインストール: pip install yfinance pandas_datareader aiohttp plotly scipy"
                        ],
                        code_example="pip install yfinance pandas_datareader aiohttp plotly scipy streamlit",
                        documentation_link="https://github.com/moruku36/japanese-stock-data-app#installation"
                    )
                ]
            },
            "network_error": {
                "patterns": [
                    r"ConnectionError",
                    r"TimeoutError",
                    r"URLError",
                    r"HTTPError",
                    r"requests.*timeout"
                ],
                "user_message": "ネットワーク接続に問題があります。",
                "solutions": [
                    ErrorSolution(
                        title="ネットワーク接続の確認",
                        description="インターネット接続とプロキシ設定を確認します",
                        steps=[
                            "インターネット接続を確認",
                            "プロキシ設定を確認（企業ネットワークの場合）",
                            "ファイアウォールの設定を確認",
                            "時間を置いて再試行"
                        ]
                    )
                ]
            },
            "invalid_symbol": {
                "patterns": [
                    r"No data found.*symbol.*invalid",
                    r"Invalid ticker",
                    r"銘柄.*見つかりません"
                ],
                "user_message": "入力された銘柄コードが無効です。",
                "solutions": [
                    ErrorSolution(
                        title="正しい銘柄コードの確認",
                        description="日本株の銘柄コードは4桁の数字です",
                        steps=[
                            "4桁の数字を入力（例: 7203、9984）",
                            "東証1部上場銘柄を確認",
                            "銘柄コード検索サイトで確認"
                        ],
                        documentation_link="https://quote.jpx.co.jp/jpx/template/quote.cgi?F=tmp/search"
                    )
                ]
            },
            "api_rate_limit": {
                "patterns": [
                    r"rate limit",
                    r"API.*limit.*exceeded",
                    r"429.*Too Many Requests"
                ],
                "user_message": "API呼び出し回数の制限に達しました。",
                "solutions": [
                    ErrorSolution(
                        title="API制限の解除待ち",
                        description="時間を置いてから再試行します",
                        steps=[
                            "しばらく時間を置く（15分〜1時間）",
                            "別のデータソースを試す",
                            "APIキーの制限を確認"
                        ]
                    )
                ]
            },
            "data_validation": {
                "patterns": [
                    r"データ.*不整合",
                    r"invalid.*data",
                    r"validation.*failed"
                ],
                "user_message": "取得したデータに問題があります。",
                "solutions": [
                    ErrorSolution(
                        title="データの再取得",
                        description="別のデータソースから再取得を試みます",
                        steps=[
                            "別の期間を指定して再試行",
                            "別のデータソースを選択",
                            "キャッシュをクリアして再取得"
                        ]
                    )
                ]
            },
            "insufficient_data": {
                "patterns": [
                    r"insufficient.*data",
                    r"データ.*不足",
                    r"too few.*samples"
                ],
                "user_message": "分析に必要なデータが不足しています。",
                "solutions": [
                    ErrorSolution(
                        title="期間またはデータの調整",
                        description="分析期間を調整またはデータ量を増やします",
                        steps=[
                            "分析期間を長くする（例: 3ヶ月→1年）",
                            "銘柄数を増やす（最低3銘柄推奨）",
                            "上場期間の長い銘柄を選択"
                        ]
                    )
                ]
            }
        }
    
    def _initialize_similar_codes(self) -> Dict[str, List[str]]:
        """類似銘柄コードの辞書を初期化"""
        return {
            # 主要企業の類似コード
            "7203": ["7201", "7267", "7211"],  # トヨタ関連
            "9984": ["9983", "4689", "6178"],  # ソフトバンク関連
            "6758": ["6752", "6753", "6754"],  # ソニー関連
            "8031": ["8001", "8002", "8058"],  # 三井物産関連
            "9433": ["9434", "9432", "9613"],  # KDDI関連
            "4689": ["4684", "4751", "4755"],  # Yahoo関連
            "6178": ["6176", "6177", "6179"],  # 日本郵政関連
        }
    
    def handle_error(
        self, 
        error: Exception, 
        category: ErrorCategory, 
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Dict[str, Any] = None,
        user_input: str = None
    ) -> UserFriendlyError:
        """
        エラーを処理してユーザーフレンドリーなメッセージを生成
        
        Args:
            error (Exception): 発生したエラー
            category (ErrorCategory): エラーカテゴリ
            severity (ErrorSeverity): エラーの重要度
            context (Dict[str, Any]): 追加のコンテキスト情報
            user_input (str): ユーザーの入力（該当する場合）
            
        Returns:
            UserFriendlyError: ユーザーフレンドリーなエラー情報
        """
        self.error_count += 1
        error_id = f"ERR_{self.error_count:06d}"
        
        # エラーメッセージの解析
        error_message = str(error)
        technical_message = f"{type(error).__name__}: {error_message}"
        
        # パターンマッチングによる解決策の特定
        matched_pattern = self._match_error_pattern(error_message)
        
        if matched_pattern:
            user_message = matched_pattern["user_message"]
            solutions = matched_pattern["solutions"]
        else:
            user_message = "予期しないエラーが発生しました。"
            solutions = [self._get_generic_solution()]
        
        # ユーザー入力に基づく追加の解決策
        if user_input and category == ErrorCategory.USER_INPUT:
            additional_solutions = self._get_input_specific_solutions(user_input)
            solutions.extend(additional_solutions)
        
        # UserFriendlyErrorオブジェクトを作成
        friendly_error = UserFriendlyError(
            error_id=error_id,
            user_message=user_message,
            technical_message=technical_message,
            category=category,
            severity=severity,
            solutions=solutions,
            context=context or {},
            timestamp=datetime.now()
        )
        
        # 履歴に追加
        self.error_history.append(friendly_error)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # ログに記録
        self._log_friendly_error(friendly_error)
        
        # カテゴリ別コールバックを実行
        if category in self.error_callbacks:
            try:
                self.error_callbacks[category](friendly_error)
            except Exception as callback_error:
                logger.error(f"エラーコールバック実行中にエラーが発生: {callback_error}")
        
        return friendly_error
    
    def _match_error_pattern(self, error_message: str) -> Optional[Dict[str, Any]]:
        """エラーメッセージをパターンマッチング"""
        for pattern_name, pattern_info in self.error_patterns.items():
            for pattern in pattern_info["patterns"]:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return pattern_info
        return None
    
    def _get_generic_solution(self) -> ErrorSolution:
        """汎用的な解決策を取得"""
        return ErrorSolution(
            title="一般的なトラブルシューティング",
            description="基本的な問題解決手順を試します",
            steps=[
                "アプリケーションを再起動",
                "インターネット接続を確認",
                "最新版へのアップデート確認",
                "ログファイルの確認",
                "サポートへの問い合わせ"
            ],
            documentation_link="https://github.com/moruku36/japanese-stock-data-app/issues"
        )
    
    def _get_input_specific_solutions(self, user_input: str) -> List[ErrorSolution]:
        """ユーザー入力に特化した解決策を取得"""
        solutions = []
        
        # 銘柄コード関連
        if re.match(r'^\d{1,4}$', user_input):
            # 数字だが4桁でない場合
            if len(user_input) != 4:
                solutions.append(ErrorSolution(
                    title="銘柄コードの修正",
                    description="4桁の銘柄コードを入力してください",
                    steps=[
                        f"入力: '{user_input}' → 正しい形式: '7203'",
                        "東証一部上場銘柄の4桁コードを確認",
                        "主要銘柄例: 7203(トヨタ), 9984(ソフトバンク), 6758(ソニー)"
                    ]
                ))
            
            # 類似コードの提案
            similar = self.similar_codes.get(user_input, [])
            if similar:
                solutions.append(ErrorSolution(
                    title="類似銘柄の提案",
                    description="関連する銘柄コードを試してみてください",
                    steps=[f"類似銘柄: {', '.join(similar)}"],
                ))
        
        return solutions
    
    def _log_friendly_error(self, error: UserFriendlyError):
        """ユーザーフレンドリーなエラーをログに記録"""
        log_message = (
            f"エラー: {error.error_id} | "
            f"カテゴリ: {error.category.value} | "
            f"重要度: {error.severity.value} | "
            f"ユーザーメッセージ: {error.user_message}"
        )
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """エラーの要約統計を取得"""
        if not self.error_history:
            return {"total": 0, "by_category": {}, "by_severity": {}}
        
        by_category = {}
        by_severity = {}
        
        for error in self.error_history:
            # カテゴリ別集計
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
            
            # 重要度別集計
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": [
                {
                    "error_id": e.error_id,
                    "user_message": e.user_message,
                    "category": e.category.value,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self.error_history[-5:]  # 最新5件
            ]
        }
    
    def get_troubleshooting_guide(self, category: ErrorCategory = None) -> Dict[str, Any]:
        """トラブルシューティングガイドを取得"""
        guide = {
            "general_steps": [
                "1. エラーメッセージを確認",
                "2. インターネット接続を確認", 
                "3. 入力データを確認",
                "4. アプリケーションを再起動",
                "5. 最新版へのアップデート"
            ],
            "common_issues": []
        }
        
        if category:
            # 特定カテゴリのガイド
            for pattern_name, pattern_info in self.error_patterns.items():
                if any(cat.lower() in pattern_name for cat in [category.value]):
                    guide["common_issues"].append({
                        "issue": pattern_info["user_message"],
                        "solutions": [
                            {
                                "title": sol.title,
                                "steps": sol.steps
                            }
                            for sol in pattern_info["solutions"]
                        ]
                    })
        else:
            # 全般的なガイド
            guide["common_issues"] = [
                {
                    "issue": pattern_info["user_message"],
                    "solutions": [
                        {
                            "title": sol.title,
                            "steps": sol.steps
                        }
                        for sol in pattern_info["solutions"]
                    ]
                }
                for pattern_info in self.error_patterns.values()
            ]
        
        return guide
    
    def export_error_log(self, filename: str = None) -> str:
        """エラーログをJSONファイルにエクスポート"""
        if not filename:
            filename = f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_errors": len(self.error_history),
            "summary": self.get_error_summary(),
            "errors": [
                {
                    "error_id": error.error_id,
                    "timestamp": error.timestamp.isoformat(),
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "user_message": error.user_message,
                    "technical_message": error.technical_message,
                    "context": error.context,
                    "solutions": [
                        {
                            "title": sol.title,
                            "description": sol.description,
                            "steps": sol.steps
                        }
                        for sol in error.solutions
                    ]
                }
                for error in self.error_history
            ]
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"エラーログをエクスポートしました: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"エラーログのエクスポートに失敗: {e}")
            raise

# グローバルインスタンス
enhanced_error_handler = EnhancedErrorHandler()

# 互換性のための元のクラスも提供
class ErrorHandler(EnhancedErrorHandler):
    """後方互換性のための元のErrorHandlerクラス"""
    pass

if __name__ == "__main__":
    # テスト実行
    handler = EnhancedErrorHandler()
    
    # テストエラー
    try:
        import non_existent_module
    except ImportError as e:
        error_info = handler.handle_error(
            e, 
            ErrorCategory.IMPORT_ERROR, 
            ErrorSeverity.HIGH,
            context={"module": "non_existent_module"}
        )
        
        print("=== エラー情報 ===")
        print(f"ID: {error_info.error_id}")
        print(f"ユーザーメッセージ: {error_info.user_message}")
        print(f"解決策数: {len(error_info.solutions)}")
        
        for i, solution in enumerate(error_info.solutions, 1):
            print(f"\n解決策 {i}: {solution.title}")
            for step in solution.steps:
                print(f"  - {step}")
    
    # 要約統計
    print("\n=== エラー要約 ===")
    print(json.dumps(handler.get_error_summary(), indent=2, ensure_ascii=False))
