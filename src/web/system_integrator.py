#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改善機能統合モジュール
新しい改善機能をメインアプリケーションに統合
"""

import streamlit as st
import logging
import sys
import os
from typing import Dict, Any, Optional

# パス設定
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..')
sys.path.insert(0, src_dir)

logger = logging.getLogger(__name__)

# 改善機能のインポート
try:
    from src.data.data_source_manager import DataSourceManager
    DATA_SOURCE_MANAGER_AVAILABLE = True
except ImportError:
    try:
        from data.data_source_manager import DataSourceManager
        DATA_SOURCE_MANAGER_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"データソース管理機能が利用できません: {e}")
        DATA_SOURCE_MANAGER_AVAILABLE = False

try:
    from src.utils.enhanced_error_handler import EnhancedErrorHandler, ErrorCategory, ErrorSeverity
    ENHANCED_ERROR_HANDLER_AVAILABLE = True
except ImportError:
    try:
        from utils.enhanced_error_handler import EnhancedErrorHandler, ErrorCategory, ErrorSeverity
        ENHANCED_ERROR_HANDLER_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"強化エラーハンドリングが利用できません: {e}")
        ENHANCED_ERROR_HANDLER_AVAILABLE = False

try:
    from src.security.enhanced_security_manager import EnhancedSecurityManager, UserRole
    ENHANCED_SECURITY_AVAILABLE = True
except ImportError:
    try:
        from security.enhanced_security_manager import EnhancedSecurityManager, UserRole
        ENHANCED_SECURITY_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"強化セキュリティが利用できません: {e}")
        ENHANCED_SECURITY_AVAILABLE = False

try:
    from src.web.ui_optimizer import UIOptimizer, UIMode, init_optimized_ui
    UI_OPTIMIZER_AVAILABLE = True
except ImportError:
    try:
        from web.ui_optimizer import UIOptimizer, UIMode, init_optimized_ui
        UI_OPTIMIZER_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"UI最適化機能が利用できません: {e}")
        UI_OPTIMIZER_AVAILABLE = False

try:
    from src.web.enhanced_chart_manager import EnhancedChartManager
    ENHANCED_CHART_AVAILABLE = True
except ImportError:
    try:
        from web.enhanced_chart_manager import EnhancedChartManager
        ENHANCED_CHART_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"強化チャート機能が利用できません: {e}")
        ENHANCED_CHART_AVAILABLE = False

class ImprovedSystemIntegrator:
    """改善システム統合クラス"""
    
    def __init__(self):
        """初期化"""
        self.data_source_manager = None
        self.error_handler = None
        self.security_manager = None
        self.ui_optimizer = None
        self.chart_manager = None
        
        # 利用可能な機能を初期化
        self._initialize_components()
        
        logger.info("改善システム統合を初期化しました")
    
    def _initialize_components(self):
        """コンポーネントを初期化"""
        try:
            # データソース管理
            if DATA_SOURCE_MANAGER_AVAILABLE:
                self.data_source_manager = DataSourceManager()
                logger.info("データソース管理機能を初期化")
            
            # エラーハンドリング
            if ENHANCED_ERROR_HANDLER_AVAILABLE:
                self.error_handler = EnhancedErrorHandler()
                logger.info("強化エラーハンドリングを初期化")
            
            # セキュリティ管理
            if ENHANCED_SECURITY_AVAILABLE:
                self.security_manager = EnhancedSecurityManager()
                logger.info("強化セキュリティを初期化")
            
            # UI最適化
            if UI_OPTIMIZER_AVAILABLE:
                self.ui_optimizer = UIOptimizer()
                logger.info("UI最適化機能を初期化")
            
            # チャート管理
            if ENHANCED_CHART_AVAILABLE:
                self.chart_manager = EnhancedChartManager()
                logger.info("強化チャート機能を初期化")
                
        except Exception as e:
            logger.error(f"コンポーネント初期化エラー: {e}")
    
    def initialize_streamlit_app(self):
        """Streamlit アプリケーションを初期化"""
        try:
            # UI最適化の初期化
            if self.ui_optimizer:
                init_optimized_ui()
            
            # セッション状態の初期化
            if 'system_integrator' not in st.session_state:
                st.session_state.system_integrator = self
            
            # エラーハンドリングコールバックの設定
            if self.error_handler:
                self._setup_error_callbacks()
            
            logger.info("Streamlit アプリケーションを初期化しました")
            
        except Exception as e:
            logger.error(f"Streamlit初期化エラー: {e}")
            st.error("アプリケーションの初期化中にエラーが発生しました")
    
    def _setup_error_callbacks(self):
        """エラーハンドリングコールバックを設定"""
        if not self.error_handler:
            return
        
        def show_user_friendly_error(error_info):
            """ユーザーフレンドリーなエラーを表示"""
            st.error(f"⚠️ {error_info.user_message}")
            
            with st.expander("解決策を見る"):
                for i, solution in enumerate(error_info.solutions, 1):
                    st.markdown(f"**{i}. {solution.title}**")
                    st.markdown(solution.description)
                    
                    if solution.steps:
                        st.markdown("**手順:**")
                        for step in solution.steps:
                            st.markdown(f"- {step}")
                    
                    if solution.code_example:
                        st.code(solution.code_example)
                    
                    if solution.documentation_link:
                        st.markdown(f"[詳細ドキュメント]({solution.documentation_link})")
        
        # コールバック登録
        for category in ErrorCategory:
            self.error_handler.register_error_callback(category, show_user_friendly_error)
    
    async def get_enhanced_stock_data(self, symbol: str, period: str = "1y"):
        """強化されたデータ取得"""
        if not self.data_source_manager:
            # フォールバック: 既存の方法
            st.warning("強化データソース機能が利用できません。標準機能を使用します。")
            return None
        
        try:
            data = await self.data_source_manager.get_stock_data(symbol, period)
            return data
            
        except Exception as e:
            if self.error_handler:
                error_info = self.error_handler.handle_error(
                    e, 
                    ErrorCategory.EXTERNAL_API, 
                    ErrorSeverity.MEDIUM,
                    context={"symbol": symbol, "period": period}
                )
                # エラーは既にコールバックで表示される
            else:
                st.error(f"データ取得エラー: {e}")
            
            return None
    
    def show_data_source_status(self):
        """データソースの状態を表示"""
        if not self.data_source_manager:
            return
        
        with st.expander("📡 データソース状態", expanded=False):
            status = self.data_source_manager.get_source_status()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**データソース一覧**")
                for source_name, source_info in status.items():
                    status_emoji = {
                        "online": "🟢",
                        "offline": "🔴", 
                        "degraded": "🟡",
                        "maintenance": "🟠"
                    }.get(source_info["status"], "⚪")
                    
                    st.markdown(f"{status_emoji} **{source_info['name']}**")
                    st.markdown(f"   成功率: {source_info['success_rate']*100:.1f}%")
                    st.markdown(f"   応答時間: {source_info['response_time']:.2f}秒")
            
            with col2:
                st.markdown("**データ検証要約**")
                validation_summary = self.data_source_manager.get_validation_summary()
                
                st.metric("検証済みデータ", validation_summary.get("total", 0))
                st.metric("有効率", f"{validation_summary.get('validity_rate', 0)*100:.1f}%")
                st.metric("平均信頼度", f"{validation_summary.get('average_confidence', 0)*100:.1f}%")
    
    def show_security_status(self):
        """セキュリティ状態を表示"""
        if not self.security_manager:
            return
        
        with st.expander("🔒 セキュリティ状態", expanded=False):
            metrics = self.security_manager.get_security_metrics()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("登録ユーザー数", metrics.get("total_users", 0))
                st.metric("アクティブセッション", metrics.get("active_sessions", 0))
            
            with col2:
                st.metric("ロックされたアカウント", metrics.get("locked_accounts", 0))
                st.metric("ログイン失敗", metrics.get("failed_attempts", 0))
            
            with col3:
                st.metric("レート制限違反", metrics.get("rate_limit_violations", 0))
    
    def show_performance_metrics(self):
        """パフォーマンスメトリクスを表示"""
        if not self.ui_optimizer:
            return
        
        self.ui_optimizer.show_performance_metrics()
    
    def show_accessibility_controls(self):
        """アクセシビリティコントロールを表示"""
        if not self.ui_optimizer:
            return
        
        self.ui_optimizer.show_accessibility_controls()
    
    def show_enhanced_chart_controls(self):
        """強化チャートコントロールを表示"""
        if not self.chart_manager:
            return None
        
        return self.chart_manager.show_chart_customization_panel()
    
    def create_enhanced_chart(self, data, settings=None, title="株価チャート"):
        """強化チャートを作成"""
        if not self.chart_manager or data is None:
            return None
        
        if settings is None:
            settings = self.chart_manager.default_settings
        
        return self.chart_manager.create_customized_chart(data, settings, title)
    
    def show_error_summary(self):
        """エラー要約を表示"""
        if not self.error_handler:
            return
        
        with st.expander("⚠️ エラー要約", expanded=False):
            summary = self.error_handler.get_error_summary()
            
            if summary["total"] == 0:
                st.success("エラーは発生していません")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**カテゴリ別エラー数**")
                for category, count in summary["by_category"].items():
                    st.markdown(f"- {category}: {count}件")
            
            with col2:
                st.markdown("**重要度別エラー数**")
                for severity, count in summary["by_severity"].items():
                    st.markdown(f"- {severity}: {count}件")
            
            # 最新エラー
            if summary["recent_errors"]:
                st.markdown("**最新のエラー**")
                for error in summary["recent_errors"]:
                    st.markdown(f"- {error['error_id']}: {error['user_message']}")
    
    def show_troubleshooting_guide(self):
        """トラブルシューティングガイドを表示"""
        if not self.error_handler:
            return
        
        with st.expander("🛠️ トラブルシューティングガイド", expanded=False):
            guide = self.error_handler.get_troubleshooting_guide()
            
            st.markdown("**一般的な解決手順**")
            for step in guide["general_steps"]:
                st.markdown(f"- {step}")
            
            st.markdown("**よくある問題と解決策**")
            for issue in guide["common_issues"]:
                with st.expander(issue["issue"]):
                    for solution in issue["solutions"]:
                        st.markdown(f"**{solution['title']}**")
                        for step in solution["steps"]:
                            st.markdown(f"- {step}")
    
    def handle_user_input_error(self, error: Exception, user_input: str = ""):
        """ユーザー入力エラーを処理"""
        if not self.error_handler:
            st.error(f"エラー: {error}")
            return
        
        self.error_handler.handle_error(
            error,
            ErrorCategory.USER_INPUT,
            ErrorSeverity.LOW,
            context={"user_input": user_input},
            user_input=user_input
        )
    
    def is_feature_available(self, feature: str) -> bool:
        """機能の利用可能性をチェック"""
        feature_map = {
            "data_source_manager": DATA_SOURCE_MANAGER_AVAILABLE,
            "error_handler": ENHANCED_ERROR_HANDLER_AVAILABLE,
            "security": ENHANCED_SECURITY_AVAILABLE,
            "ui_optimizer": UI_OPTIMIZER_AVAILABLE,
            "chart_manager": ENHANCED_CHART_AVAILABLE
        }
        
        return feature_map.get(feature, False)
    
    def show_system_status(self):
        """システム全体の状態を表示"""
        st.markdown("## 🎯 システム状態")
        
        # 機能別の状態表示
        features = [
            ("データソース管理", "data_source_manager"),
            ("エラーハンドリング", "error_handler"),
            ("セキュリティ管理", "security"),
            ("UI最適化", "ui_optimizer"),
            ("チャート管理", "chart_manager")
        ]
        
        cols = st.columns(len(features))
        
        for i, (name, key) in enumerate(features):
            with cols[i]:
                available = self.is_feature_available(key)
                status_emoji = "🟢" if available else "🔴"
                status_text = "利用可能" if available else "無効"
                
                st.metric(
                    label=name,
                    value=status_text,
                    delta=None
                )
                st.markdown(f"{status_emoji}")
        
        # 詳細状態
        col1, col2 = st.columns(2)
        
        with col1:
            self.show_data_source_status()
            self.show_error_summary()
        
        with col2:
            self.show_security_status()
            self.show_performance_metrics()
        
        # ガイド
        self.show_troubleshooting_guide()
        self.show_accessibility_controls()

# グローバルインスタンス
system_integrator = ImprovedSystemIntegrator()

def get_system_integrator():
    """システム統合インスタンスを取得"""
    if 'system_integrator' in st.session_state:
        return st.session_state.system_integrator
    return system_integrator

def initialize_improved_app():
    """改善されたアプリケーションを初期化"""
    integrator = get_system_integrator()
    integrator.initialize_streamlit_app()
    return integrator

if __name__ == "__main__":
    # テスト実行
    st.title("改善機能統合システム テスト")
    
    integrator = initialize_improved_app()
    integrator.show_system_status()
    
    # データ取得テスト
    if st.button("データ取得テスト"):
        import asyncio
        
        async def test_data_fetch():
            data = await integrator.get_enhanced_stock_data("7203", "1mo")
            if data is not None:
                st.success(f"データ取得成功: {len(data)}行")
                st.dataframe(data.head())
            else:
                st.error("データ取得失敗")
        
        # 非同期処理の実行
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(test_data_fetch())
        except Exception as e:
            integrator.handle_user_input_error(e, "7203")
        finally:
            loop.close()
