#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebUI最適化システム
パフォーマンス向上、アクセシビリティ、軽量化を実装
"""

import streamlit as st
import logging
import time
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import threading
from functools import wraps

# オプショナルインポート
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

logger = logging.getLogger(__name__)

class UIMode(Enum):
    """UIモード"""
    FULL = "full"           # フル機能
    LITE = "lite"           # 軽量版
    ACCESSIBLE = "accessible"  # アクセシビリティ重視
    MOBILE = "mobile"       # モバイル最適化

class ThemeMode(Enum):
    """テーマモード"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    page_load_time: float
    render_time: float
    memory_usage: float
    cpu_usage: float
    network_requests: int
    cache_hit_rate: float

@dataclass
class AccessibilityConfig:
    """アクセシビリティ設定"""
    high_contrast: bool = False
    large_text: bool = False
    keyboard_navigation: bool = True
    screen_reader_support: bool = True
    reduced_motion: bool = False
    focus_indicators: bool = True

class UIOptimizer:
    """UI最適化管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.performance_metrics = {}
        self.ui_mode = UIMode.FULL
        self.theme_mode = ThemeMode.LIGHT
        self.accessibility_config = AccessibilityConfig()
        
        # キャッシュ設定
        self.chart_cache = {}
        self.data_cache = {}
        self.component_cache = {}
        
        # パフォーマンス監視
        self.page_start_time = time.time()
        self.render_times = []
        
        logger.info("UI最適化システムを初期化しました")
    
    def set_ui_mode(self, mode: UIMode):
        """UIモードを設定"""
        self.ui_mode = mode
        logger.info(f"UIモードを変更: {mode.value}")
        
        # モード別の設定適用
        if mode == UIMode.LITE:
            self._apply_lite_settings()
        elif mode == UIMode.ACCESSIBLE:
            self._apply_accessible_settings()
        elif mode == UIMode.MOBILE:
            self._apply_mobile_settings()
    
    def _apply_lite_settings(self):
        """軽量版設定を適用"""
        # Streamlit設定
        st.set_page_config(
            page_title="株価分析 (軽量版)",
            layout="centered",  # ワイドレイアウトを無効
            initial_sidebar_state="collapsed"
        )
        
        # CSS適用
        lite_css = """
        <style>
        .main .block-container {
            max-width: 800px;
            padding-top: 1rem;
        }
        .stPlotlyChart {
            height: 300px !important;
        }
        .element-container {
            margin-bottom: 0.5rem;
        }
        </style>
        """
        st.markdown(lite_css, unsafe_allow_html=True)
    
    def _apply_accessible_settings(self):
        """アクセシビリティ設定を適用"""
        self.accessibility_config = AccessibilityConfig(
            high_contrast=True,
            large_text=True,
            keyboard_navigation=True,
            screen_reader_support=True,
            reduced_motion=True,
            focus_indicators=True
        )
        
        # アクセシブルCSS
        accessible_css = """
        <style>
        /* 高コントラスト */
        .main {
            background-color: #ffffff;
            color: #000000;
        }
        
        /* 大きなテキスト */
        .stMarkdown p, .stText {
            font-size: 1.2rem !important;
            line-height: 1.6 !important;
        }
        
        /* フォーカスインジケーター */
        button:focus, input:focus, select:focus {
            outline: 3px solid #005fcc !important;
            outline-offset: 2px !important;
        }
        
        /* 動きを減らす */
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
        
        /* スクリーンリーダー対応 */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        </style>
        """
        st.markdown(accessible_css, unsafe_allow_html=True)
    
    def _apply_mobile_settings(self):
        """モバイル最適化設定を適用"""
        # モバイル専用CSS
        mobile_css = """
        <style>
        /* モバイル最適化 */
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            max-width: 100%;
        }
        
        /* タッチフレンドリーなボタン */
        .stButton button {
            min-height: 44px;
            min-width: 44px;
            padding: 12px 20px;
        }
        
        /* 小さな画面での表示調整 */
        @media (max-width: 768px) {
            .stColumns {
                flex-direction: column;
            }
            
            .stPlotlyChart {
                height: 250px !important;
            }
            
            .stDataFrame {
                font-size: 0.8rem;
            }
        }
        </style>
        """
        st.markdown(mobile_css, unsafe_allow_html=True)
    
    def performance_monitor(self, func_name: str):
        """パフォーマンス監視デコレータ"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # メトリクス記録
                    self.render_times.append(execution_time)
                    if len(self.render_times) > 100:
                        self.render_times.pop(0)
                    
                    logger.debug(f"{func_name} 実行時間: {execution_time:.3f}秒")
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"{func_name} エラー (実行時間: {execution_time:.3f}秒): {e}")
                    raise
                    
            return wrapper
        return decorator
    
    @st.cache_data(ttl=300, show_spinner=False)
    def cached_chart_render(_self, chart_data: Dict[str, Any], chart_type: str) -> Optional[go.Figure]:
        """キャッシュ付きチャート描画"""
        if not PLOTLY_AVAILABLE:
            st.warning("Plotlyライブラリが利用できません。軽量版チャートを表示します。")
            return None
        
        try:
            if chart_type == "candlestick":
                return _self._create_lightweight_candlestick(chart_data)
            elif chart_type == "line":
                return _self._create_lightweight_line(chart_data)
            elif chart_type == "bar":
                return _self._create_lightweight_bar(chart_data)
            else:
                return None
                
        except Exception as e:
            logger.error(f"チャート描画エラー: {e}")
            return None
    
    def _create_lightweight_candlestick(self, data: Dict[str, Any]) -> go.Figure:
        """軽量ローソク足チャート"""
        df = data.get('dataframe')
        if df is None or df.empty:
            return go.Figure()
        
        # 軽量化設定
        config = {
            'displayModeBar': self.ui_mode != UIMode.LITE,
            'responsive': True,
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'stock_chart',
                'height': 400,
                'width': 800,
                'scale': 1
            }
        }
        
        fig = go.Figure(data=[
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Price",
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444'
            )
        ])
        
        # レスポンシブレイアウト
        fig.update_layout(
            title=data.get('title', '株価チャート'),
            xaxis_title="日付",
            yaxis_title="価格 (円)",
            height=300 if self.ui_mode == UIMode.LITE else 500,
            margin=dict(l=50, r=20, t=50, b=50),
            showlegend=False,
            xaxis=dict(
                type='date',
                rangeslider=dict(visible=False)
            ),
            font=dict(
                size=14 if self.accessibility_config.large_text else 12
            )
        )
        
        return fig
    
    def _create_lightweight_line(self, data: Dict[str, Any]) -> go.Figure:
        """軽量ライン チャート"""
        df = data.get('dataframe')
        if df is None or df.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        # 複数系列対応
        columns = data.get('columns', ['Close'])
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        for i, col in enumerate(columns):
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode='lines',
                    name=col,
                    line=dict(color=colors[i % len(colors)], width=2)
                ))
        
        fig.update_layout(
            title=data.get('title', 'ライン チャート'),
            xaxis_title="日付",
            yaxis_title="値",
            height=300 if self.ui_mode == UIMode.LITE else 400,
            margin=dict(l=50, r=20, t=50, b=50),
            hovermode='x unified'
        )
        
        return fig
    
    def _create_lightweight_bar(self, data: Dict[str, Any]) -> go.Figure:
        """軽量バーチャート"""
        df = data.get('dataframe')
        if df is None or df.empty:
            return go.Figure()
        
        fig = go.Figure(data=[
            go.Bar(
                x=df.index if data.get('use_index') else df.iloc[:, 0],
                y=df.iloc[:, -1],  # 最後の列を使用
                marker_color='steelblue'
            )
        ])
        
        fig.update_layout(
            title=data.get('title', 'バーチャート'),
            height=300 if self.ui_mode == UIMode.LITE else 400,
            margin=dict(l=50, r=20, t=50, b=50)
        )
        
        return fig
    
    def create_responsive_layout(self, columns_config: List[int]) -> List:
        """レスポンシブレイアウトを作成"""
        if self.ui_mode == UIMode.MOBILE:
            # モバイルでは1列に強制
            return [st.container() for _ in columns_config]
        else:
            return st.columns(columns_config)
    
    def show_accessibility_controls(self):
        """アクセシビリティコントロールを表示"""
        with st.expander("🔧 アクセシビリティ設定", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                self.accessibility_config.high_contrast = st.checkbox(
                    "高コントラスト", 
                    value=self.accessibility_config.high_contrast,
                    help="背景と文字のコントラストを高くします"
                )
                
                self.accessibility_config.large_text = st.checkbox(
                    "大きなテキスト",
                    value=self.accessibility_config.large_text,
                    help="フォントサイズを大きくします"
                )
                
                self.accessibility_config.reduced_motion = st.checkbox(
                    "動きを減らす",
                    value=self.accessibility_config.reduced_motion,
                    help="アニメーションを最小限にします"
                )
            
            with col2:
                ui_mode = st.selectbox(
                    "表示モード",
                    options=[mode.value for mode in UIMode],
                    index=list(UIMode).index(self.ui_mode),
                    help="用途に応じて表示を最適化します"
                )
                
                if ui_mode != self.ui_mode.value:
                    self.set_ui_mode(UIMode(ui_mode))
                    st.experimental_rerun()
    
    def show_performance_metrics(self):
        """パフォーマンスメトリクスを表示"""
        if not self.render_times:
            return
        
        with st.expander("📊 パフォーマンス情報", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_render_time = sum(self.render_times) / len(self.render_times)
                st.metric(
                    "平均描画時間",
                    f"{avg_render_time:.3f}秒",
                    delta=None
                )
            
            with col2:
                cache_size = len(self.chart_cache) + len(self.data_cache)
                st.metric(
                    "キャッシュサイズ",
                    f"{cache_size}個",
                    delta=None
                )
            
            with col3:
                page_load_time = time.time() - self.page_start_time
                st.metric(
                    "ページ読み込み時間",
                    f"{page_load_time:.1f}秒",
                    delta=None
                )
    
    def lazy_load_component(self, component_key: str, load_func: Callable, *args, **kwargs):
        """遅延読み込みコンポーネント"""
        if component_key not in st.session_state:
            st.session_state[component_key] = False
        
        if not st.session_state[component_key]:
            if st.button(f"📊 {component_key}を読み込む", key=f"load_{component_key}"):
                with st.spinner(f"{component_key}を読み込み中..."):
                    try:
                        result = load_func(*args, **kwargs)
                        self.component_cache[component_key] = result
                        st.session_state[component_key] = True
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"読み込みエラー: {e}")
        else:
            # キャッシュから表示
            if component_key in self.component_cache:
                return self.component_cache[component_key]
    
    def create_error_boundary(self, component_name: str, fallback_content: str = "コンポーネントの読み込みに失敗しました"):
        """エラーバウンダリー"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"{component_name} エラー: {e}")
                    
                    if self.ui_mode == UIMode.ACCESSIBLE:
                        st.error(f"⚠️ {fallback_content}")
                        with st.expander("詳細エラー情報"):
                            st.code(str(e))
                    else:
                        st.warning(fallback_content)
                    
                    return None
                    
            return wrapper
        return decorator
    
    def optimize_dataframe_display(self, df, max_rows: int = None):
        """DataFrameの表示を最適化"""
        if max_rows is None:
            max_rows = 50 if self.ui_mode == UIMode.LITE else 100
        
        if len(df) > max_rows:
            st.info(f"データが多いため、最初の{max_rows}行のみ表示しています")
            
            # ページネーション
            page_size = max_rows
            total_pages = (len(df) - 1) // page_size + 1
            
            if total_pages > 1:
                page_num = st.number_input(
                    "ページ",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    help=f"全{total_pages}ページ"
                )
                
                start_idx = (page_num - 1) * page_size
                end_idx = min(start_idx + page_size, len(df))
                df_display = df.iloc[start_idx:end_idx]
            else:
                df_display = df.head(max_rows)
        else:
            df_display = df
        
        # アクセシビリティ対応
        if self.accessibility_config.large_text:
            st.markdown(f"**データ表示 ({len(df_display)}行)**")
        
        return st.dataframe(
            df_display,
            use_container_width=True,
            height=300 if self.ui_mode == UIMode.LITE else 400
        )
    
    def create_keyboard_shortcuts(self):
        """キーボードショートカットを作成"""
        if not self.accessibility_config.keyboard_navigation:
            return
        
        shortcuts_js = """
        <script>
        document.addEventListener('keydown', function(e) {
            // Alt + 1: メインナビゲーション
            if (e.altKey && e.key === '1') {
                const sidebar = document.querySelector('.css-1d391kg');
                if (sidebar) sidebar.focus();
            }
            
            // Alt + 2: メインコンテンツ
            if (e.altKey && e.key === '2') {
                const main = document.querySelector('.main');
                if (main) main.focus();
            }
            
            // Escape: モーダルを閉じる
            if (e.key === 'Escape') {
                const closeButtons = document.querySelectorAll('[data-testid="modal-close-button"]');
                closeButtons.forEach(btn => btn.click());
            }
        });
        </script>
        """
        
        st.markdown(shortcuts_js, unsafe_allow_html=True)
    
    def show_keyboard_help(self):
        """キーボードヘルプを表示"""
        if self.accessibility_config.keyboard_navigation:
            with st.expander("⌨️ キーボードショートカット"):
                st.markdown("""
                - **Alt + 1**: サイドバーナビゲーション
                - **Alt + 2**: メインコンテンツ
                - **Tab**: 次の要素
                - **Shift + Tab**: 前の要素
                - **Enter**: 選択実行
                - **Escape**: モーダルを閉じる
                """)

# グローバルインスタンス
ui_optimizer = UIOptimizer()

# Streamlit用ヘルパー関数
def init_optimized_ui():
    """最適化されたUIを初期化"""
    # セッション状態の初期化
    if 'ui_optimizer' not in st.session_state:
        st.session_state.ui_optimizer = ui_optimizer
    
    # ページ設定
    if ui_optimizer.ui_mode == UIMode.LITE:
        st.set_page_config(
            page_title="株価分析システム (軽量版)",
            page_icon="📊",
            layout="centered",
            initial_sidebar_state="collapsed"
        )
    else:
        st.set_page_config(
            page_title="株価分析システム",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    # キーボードショートカット
    ui_optimizer.create_keyboard_shortcuts()
    
    return ui_optimizer

def show_optimized_chart(chart_data: Dict[str, Any], chart_type: str = "candlestick"):
    """最適化されたチャートを表示"""
    optimizer = st.session_state.get('ui_optimizer', ui_optimizer)
    
    with optimizer.performance_monitor(f"chart_{chart_type}"):
        fig = optimizer.cached_chart_render(chart_data, chart_type)
        
        if fig:
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    'displayModeBar': optimizer.ui_mode != UIMode.LITE,
                    'responsive': True
                }
            )
        else:
            st.error("チャートの表示に失敗しました")

if __name__ == "__main__":
    # テスト実行
    init_optimized_ui()
    
    st.title("UI最適化システム テスト")
    
    # コントロール表示
    ui_optimizer.show_accessibility_controls()
    ui_optimizer.show_performance_metrics()
    ui_optimizer.show_keyboard_help()
    
    # テストチャート
    import pandas as pd
    import numpy as np
    
    # サンプルデータ
    dates = pd.date_range('2024-01-01', periods=100)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    df = pd.DataFrame({
        'Open': prices + np.random.randn(100) * 0.2,
        'High': prices + np.abs(np.random.randn(100)) * 0.5,
        'Low': prices - np.abs(np.random.randn(100)) * 0.5,
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    chart_data = {
        'dataframe': df,
        'title': 'テスト株価チャート'
    }
    
    show_optimized_chart(chart_data)
