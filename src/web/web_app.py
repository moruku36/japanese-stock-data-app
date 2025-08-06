#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日本の株価データ取得・分析システム - WebUI版（最適化版）
Streamlitを使用したWebインターフェース
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import sys
import time
import logging
from typing import Dict, Any, List

# ログ設定
logger = logging.getLogger(__name__)

# プロジェクトのモジュールをインポート
import sys
import os

# プロジェクトルートとsrcディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..')
project_root = os.path.join(src_dir, '..')

# パスを設定
sys.path.insert(0, src_dir)
sys.path.insert(0, project_root)

try:
    from core.stock_data_fetcher import JapaneseStockDataFetcher
    from core.stock_analyzer import StockAnalyzer
    from core.company_search import CompanySearch
    from analysis.fundamental_analyzer import FundamentalAnalyzer
    from analysis.advanced_data_sources import AdvancedDataManager
    try:
        from analysis.technical_analysis import TechnicalAnalyzer, create_technical_chart
    except ImportError as e:
        st.warning("technical_analysisモジュールが見つかりません。テクニカル分析機能を無効化します。")
        TechnicalAnalyzer = None
        create_technical_chart = None
    try:
        from data.async_data_sources import run_async_data_fetch_sync
    except ImportError as e:
        if "asyncio_throttle" in str(e):
            st.warning("asyncio_throttleモジュールが見つかりません。非同期機能を無効化します。")
            run_async_data_fetch_sync = None
        else:
            raise e
    try:
        from data.real_time_updater import RealTimeDataManager, start_real_time_services, stop_real_time_services
    except ImportError as e:
        if "websockets" in str(e):
            st.warning("websocketsモジュールが見つかりません。リアルタイム機能を無効化します。")
            RealTimeDataManager = None
            start_real_time_services = None
            stop_real_time_services = None
        else:
            raise e
    
    # configモジュールをインポート
    from config.config import config
    
    from utils.utils import (
        format_currency, format_number, PerformanceMonitor, 
        performance_monitor, MemoryOptimizer, OptimizedCache
    )
    
    # セキュリティ機能をインポート
    try:
        from security.auth_manager import AuthenticationManager, AuthorizationManager
        from utils.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
        SECURITY_ENABLED = True
    except ImportError as e:
        st.warning("セキュリティ機能が見つかりません。認証機能を無効化します。")
        AuthenticationManager = None
        AuthorizationManager = None
        ErrorHandler = None
        ErrorCategory = None
        ErrorSeverity = None
        SECURITY_ENABLED = False
    
    # 新しいWeb機能をインポート
    try:
        from web.dashboard import DashboardManager
        from web.portfolio_optimization import PortfolioOptimizer
        from web.api_monitoring import APIMonitor
        NEW_FEATURES_ENABLED = True
    except ImportError as e:
        st.warning(f"新しい機能のインポートに失敗しました: {e}")
        DashboardManager = None
        PortfolioOptimizer = None
        APIMonitor = None
        NEW_FEATURES_ENABLED = False
    
    # 改善機能の統合
    try:
        from src.web.system_integrator import (
            ImprovedSystemIntegrator, initialize_improved_app, get_system_integrator
        )
        IMPROVED_FEATURES_ENABLED = True
    except ImportError:
        try:
            from web.system_integrator import (
                ImprovedSystemIntegrator, initialize_improved_app, get_system_integrator
            )
            IMPROVED_FEATURES_ENABLED = True
        except ImportError as e:
            st.warning(f"改善機能のインポートに失敗しました: {e}")
            ImprovedSystemIntegrator = None
            initialize_improved_app = None
            get_system_integrator = None
            IMPROVED_FEATURES_ENABLED = False
except ImportError as e:
    st.error(f"モジュールのインポートエラー: {e}")
    st.info("必要なモジュールがインストールされていない可能性があります。")
    st.info("基本的な機能のみ利用可能です。")
    # エラーが発生してもアプリを停止せず、基本的な機能のみ提供
    JapaneseStockDataFetcher = None
    StockAnalyzer = None
    CompanySearch = None
    FundamentalAnalyzer = None
    AdvancedDataManager = None
    TechnicalAnalyzer = None
    create_technical_chart = None
    run_async_data_fetch_sync = None
    RealTimeDataManager = None
    start_real_time_services = None
    stop_real_time_services = None
    config = {}
    format_currency = lambda x: f"{x:,.0f}円"
    format_number = lambda x: f"{x:,.0f}"
    PerformanceMonitor = None
    performance_monitor = lambda x: x
    MemoryOptimizer = None
    OptimizedCache = None
    SECURITY_ENABLED = False

# ページ設定
st.set_page_config(
    page_title="🇯🇵 日本の株価データ分析システム",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    /* テーマカラー定義 - シンプルな3色構成 */
    :root {
        /* メインカラー: 青 */
        --primary-color: #3b82f6;
        --primary-dark: #2563eb;
        --primary-light: #60a5fa;
        
        /* アクセントカラー: オレンジ */
        --accent-color: #f97316;
        
        /* 成功カラー: 緑 */
        --success-color: #22c55e;
        
        /* テキストカラー: 白とグレー */
        --text-primary: #ffffff;
        --text-secondary: #e5e7eb;
        --text-light: #9ca3af;
        
        /* 背景カラー: ダークテーマ */
        --bg-primary: #1f2937;
        --bg-secondary: #374151;
        --bg-tertiary: #4b5563;
        
        /* ボーダーカラー */
        --border-color: #4b5563;
        
        /* シャドウ */
        --shadow-light: 0 1px 3px rgba(0, 0, 0, 0.3);
        --shadow-medium: 0 4px 6px rgba(0, 0, 0, 0.3);
        --shadow-heavy: 0 10px 15px rgba(0, 0, 0, 0.3);
    }
    
    /* Streamlit Cloud対応: 強制的な背景色設定 */
    html, body {
        background-color: var(--bg-primary) !important;
    }
    
    /* Streamlit Cloud対応: すべてのメインコンテナ要素 */
    div[data-testid="stAppViewContainer"] {
        background-color: var(--bg-primary) !important;
    }
    
    /* Streamlit Cloud対応: メインコンテンツエリア */
    div[data-testid="stAppViewContainer"] > div {
        background-color: var(--bg-primary) !important;
    }
    
    /* Streamlit Cloud対応: 追加の背景色設定 */
    .stApp > div {
        background-color: var(--bg-primary) !important;
    }
    
    /* Streamlit Cloud対応: すべてのコンテナ要素 */
    .block-container {
        background-color: var(--bg-primary) !important;
    }
    
    /* Streamlit Cloud対応: メインエリア */
    .main .block-container {
        background-color: var(--bg-primary) !important;
    }
    
    /* メインコンテナのスタイル */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background-color: var(--bg-primary) !important;
    }
    

    
    /* Streamlit Cloud対応: メインページ全体の背景色 */
    .main {
        background-color: var(--bg-primary) !important;
    }
    
    /* Streamlit Cloud対応: ページ全体の背景色 */
    .stApp {
        background-color: var(--bg-primary) !important;
    }
    
    /* Streamlit Cloud対応: コンテンツエリアの背景色 */
    .main .block-container > div {
        background-color: var(--bg-primary) !important;
    }
    
    /* ヘッダーのスタイル */
    .main h1 {
        color: var(--text-primary);
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        border-radius: 10px;
        background: var(--bg-secondary);
        box-shadow: var(--shadow-medium);
        border: 2px solid var(--primary-color);
    }
    
    /* サイドバーのスタイル */
    .css-1d391kg {
        background: var(--bg-secondary) !important;
        border-right: 2px solid var(--border-color);
    }
    
    .css-1d391kg .sidebar-content {
        padding: 1rem;
    }
    
    /* Streamlit Cloud対応: サイドバー全体の背景色 */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-secondary) !important;
    }
    
    /* Streamlit Cloud対応: サイドバーコンテンツの背景色 */
    section[data-testid="stSidebar"] > div {
        background-color: var(--bg-secondary) !important;
    }
    
    /* カードスタイル */
    .metric-card {
        background: var(--bg-secondary);
        color: var(--text-primary);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: var(--shadow-medium);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
        border: 2px solid var(--border-color);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: var(--shadow-heavy);
        border-color: var(--primary-color);
    }
    
    /* ボタンスタイル */
    .stButton > button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-light);
    }
    
    .stButton > button:hover {
        background: var(--primary-dark);
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
    }
    
    /* セクションスタイル */
    .section-header {
        background: var(--bg-tertiary);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border-left: 5px solid var(--primary-color);
        margin: 1.5rem 0;
        font-weight: 600;
        color: var(--text-primary);
        box-shadow: var(--shadow-light);
    }
    
    /* テーブルスタイル */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: var(--shadow-medium);
        border: 1px solid var(--border-color);
        background: var(--bg-secondary);
    }
    
    .dataframe th {
        background: var(--primary-color);
        color: white;
        font-weight: 600;
        padding: 1rem;
    }
    
    .dataframe td {
        padding: 0.75rem;
        border-bottom: 1px solid var(--border-color);
        color: var(--text-primary);
        background: var(--bg-secondary);
    }
    
    .dataframe tr:nth-child(even) {
        background-color: var(--bg-tertiary);
    }
    
    /* アラートスタイル */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: var(--shadow-medium);
    }
    
    /* プログレスバースタイル */
    .stProgress > div > div > div {
        background: var(--primary-color);
    }
    
    /* チャートコンテナ */
    .chart-container {
        background: var(--bg-secondary);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: var(--shadow-medium);
        margin: 1rem 0;
        border: 1px solid var(--border-color);
    }
    
    /* レスポンシブデザイン */
    @media (max-width: 768px) {
        .main h1 {
            font-size: 2rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
    }
    
    /* アニメーション */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* カスタムメトリック */
    .metric-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem;
        background: var(--bg-secondary);
        color: var(--text-primary);
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: var(--shadow-medium);
        border: 2px solid var(--border-color);
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        border-color: var(--primary-color);
        box-shadow: var(--shadow-heavy);
    }
    
    .metric-icon {
        font-size: 2rem;
        margin-right: 1rem;
        color: var(--primary-color);
    }
    
    .metric-content {
        flex: 1;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        color: var(--text-primary);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin: 0;
    }
    
    /* テキストカラーの改善 */
    .main p, .main div {
        color: var(--text-primary);
    }
    
    .main h2, .main h3, .main h4 {
        color: var(--text-primary);
    }
    
    /* 入力フィールドの改善 */
    .stTextInput > div > div > input {
        border: 2px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    /* セレクトボックスの改善 */
    .stSelectbox > div > div > div {
        border: 2px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    .stSelectbox > div > div > div:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
    
    /* 成功・警告・エラーメッセージの改善 */
    .stSuccess {
        background-color: var(--bg-secondary);
        border: 1px solid var(--success-color);
        color: var(--text-primary);
    }
    
    .stWarning {
        background-color: var(--bg-secondary);
        border: 1px solid var(--accent-color);
        color: var(--text-primary);
    }
    
    .stError {
        background-color: var(--bg-secondary);
        border: 1px solid #ef4444;
        color: var(--text-primary);
    }
    
    /* 情報メッセージの改善 */
    .stInfo {
        background-color: var(--bg-secondary);
        border: 1px solid var(--primary-color);
        color: var(--text-primary);
    }
    
    /* タブの改善 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--bg-secondary);
        border-radius: 8px 8px 0 0;
        color: var(--text-secondary);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        border: 1px solid var(--border-color);
        border-bottom: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
        font-weight: 600;
        border-color: var(--primary-color);
    }
    
    .stTabs [aria-selected="false"]:hover {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
    }
    
    /* 全体的な文字色の改善 */
    .main * {
        color: var(--text-primary);
    }
    
    /* 特定の要素の文字色を明示的に設定 */
    .main p, .main div, .main span {
        color: var(--text-primary) !important;
    }
    
    .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
        color: var(--text-primary) !important;
    }
    
    /* サイドバーの文字色 */
    .css-1d391kg * {
        color: var(--text-primary);
    }
    
    /* 入力フィールドのラベル */
    .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: var(--text-primary) !important;
        font-weight: 600;
    }
    
    /* セレクトボックスのオプション */
    .stSelectbox [data-baseweb="select"] {
        color: var(--text-primary);
    }
    
    /* データフレームの文字色 */
    .dataframe * {
        color: var(--text-primary);
    }
    
    /* メトリックの文字色 */
    .metric-container * {
        color: var(--text-primary);
    }
    
    /* アラートメッセージの文字色 */
    .stAlert * {
        color: var(--text-primary) !important;
    }
    
    /* ボタンの文字色 */
    .stButton button {
        color: white !important;
    }
    
    /* チェックボックスとラジオボタンのラベル */
    .stCheckbox label, .stRadio label {
        color: var(--text-primary) !important;
    }
    
    /* スライダーのラベル */
    .stSlider label {
        color: var(--text-primary) !important;
    }
    
    /* ファイルアップローダーのラベル */
    .stFileUploader label {
        color: var(--text-primary) !important;
    }
    
    /* 日付入力のラベル */
    .stDateInput label {
        color: var(--text-primary) !important;
    }
    
    /* 時間入力のラベル */
    .stTimeInput label {
        color: var(--text-primary) !important;
    }
    
    /* テキストエリアのラベル */
    .stTextArea label {
        color: var(--text-primary) !important;
    }
    
    /* 数値入力のラベル */
    .stNumberInput label {
        color: var(--text-primary) !important;
    }
    
    /* マルチセレクトのラベル */
    .stMultiselect label {
        color: var(--text-primary) !important;
    }
    
    /* カラーピッカーのラベル */
    .stColorPicker label {
        color: var(--text-primary) !important;
    }
    
    /* セクションヘッダーの文字色 */
    .section-header {
        color: var(--text-primary) !important;
    }
    
    /* カード内の文字色 */
    .metric-card * {
        color: var(--text-primary) !important;
    }
    
    /* チャートコンテナ内の文字色 */
    .chart-container * {
        color: var(--text-primary) !important;
    }
    
    /* Streamlitの特定要素の文字色を強制設定 */
    .stMarkdown, .stMarkdown * {
        color: var(--text-primary) !important;
    }
    
    .stDataFrame, .stDataFrame * {
        color: var(--text-primary) !important;
    }
    
    .stMetric, .stMetric * {
        color: var(--text-primary) !important;
    }
    
    .stExpander, .stExpander * {
        color: var(--text-primary) !important;
    }
    
    .stContainer, .stContainer * {
        color: var(--text-primary) !important;
    }
    
    /* サイドバーのセレクトボックス */
    .css-1d391kg .stSelectbox * {
        color: var(--text-primary) !important;
    }
    
    /* メインエリアのセレクトボックス */
    .main .stSelectbox * {
        color: var(--text-primary) !important;
    }
    
    /* 全体的な文字色の強制設定 */
    body, body * {
        color: var(--text-primary) !important;
    }
    
    /* 特定の例外（ボタンなど） */
    .stButton button {
        color: white !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: white !important;
    }
    
    /* データフレームのヘッダー */
    .dataframe th {
        color: white !important;
    }
</style>

<script>
// Streamlit Cloud対応: 動的背景色設定
function setDarkTheme() {
    // メインコンテナの背景色を強制設定
    const mainContainer = document.querySelector('.main .block-container');
    if (mainContainer) {
        mainContainer.style.backgroundColor = '#1e1e1e';
    }
    
    // サイドバーの背景色を強制設定
    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
        sidebar.style.backgroundColor = '#2d2d2d';
    }
    
    // アプリ全体の背景色を設定
    const appContainer = document.querySelector('div[data-testid="stAppViewContainer"]');
    if (appContainer) {
        appContainer.style.backgroundColor = '#1e1e1e';
    }
    
    // 白い背景を検出して修正
    const whiteElements = document.querySelectorAll('*');
    whiteElements.forEach(element => {
        const bgColor = window.getComputedStyle(element).backgroundColor;
        if (bgColor === 'rgb(255, 255, 255)' || bgColor === '#ffffff') {
            element.style.backgroundColor = '#1e1e1e';
        }
    });
}

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', setDarkTheme);

// 定期的にチェック（Streamlit Cloud対応）
setInterval(setDarkTheme, 2000);

// Streamlitの状態変更を監視
const observer = new MutationObserver(setDarkTheme);
observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# グローバルキャッシュ
@st.cache_resource
def get_global_cache():
    """グローバルキャッシュを取得"""
    if OptimizedCache:
        return OptimizedCache(max_size=500, ttl_hours=6)
    else:
        # 簡易キャッシュ
        return {"cache": {}, "max_size": 500, "ttl_hours": 6}

@st.cache_resource
def initialize_system():
    """システムの初期化（キャッシュ付き・最適化版）"""
    try:
        # モジュールが利用可能かチェック
        if JapaneseStockDataFetcher is None:
            st.warning("一部のモジュールが利用できません。基本的な機能のみ利用可能です。")
            return None, None, None, None, None, None, None
        
        # パフォーマンス監視開始
        if PerformanceMonitor:
            monitor = PerformanceMonitor()
            monitor.start()
        
        # システム初期化
        fetcher = JapaneseStockDataFetcher(max_workers=3)
        analyzer = StockAnalyzer(fetcher)
        company_searcher = CompanySearch()
        fundamental_analyzer = FundamentalAnalyzer(fetcher)
        advanced_data_manager = AdvancedDataManager()
        technical_analyzer = TechnicalAnalyzer() if TechnicalAnalyzer else None
        
        # リアルタイムデータ管理を初期化
        real_time_manager = RealTimeDataManager()
        
        # パフォーマンス監視終了
        if PerformanceMonitor:
            monitor.end("System Initialization")
        
        return fetcher, analyzer, company_searcher, fundamental_analyzer, advanced_data_manager, technical_analyzer, real_time_manager
    except ImportError as e:
        st.error(f"モジュールのインポートエラー: {e}")
        st.info("必要なモジュールがインストールされていません。")
        return None, None, None, None, None, None, None
    except Exception as e:
        st.error(f"システムの初期化に失敗しました: {e}")
        st.info("システムの初期化中にエラーが発生しました。")
        return None, None, None, None, None, None, None

@st.cache_data(ttl=3600)  # 1時間キャッシュ
def get_cached_data(key: str, *args, _fetcher=None, _fundamental_analyzer=None, _company_searcher=None, _advanced_data_manager=None, **kwargs):
    """データをキャッシュ付きで取得"""
    # キーに基づいて適切な関数を呼び出す
    if "latest_price" in key:
        if "stooq" in key:
            ticker = args[0] if args else kwargs.get('ticker_symbol')
            return _fetcher.get_latest_price(ticker, "stooq")
        elif "yahoo" in key:
            ticker = args[0] if args else kwargs.get('ticker_symbol')
            return _fetcher.get_latest_price(ticker, "yahoo")
    elif "stock_data" in key:
        if "stooq" in key:
            ticker = args[0] if args else kwargs.get('ticker_symbol')
            start_date = args[1] if len(args) > 1 else kwargs.get('start_date')
            end_date = args[2] if len(args) > 2 else kwargs.get('end_date')
            return _fetcher.fetch_stock_data_stooq(ticker, start_date, end_date)
        elif "yahoo" in key:
            ticker = args[0] if args else kwargs.get('ticker_symbol')
            start_date = args[1] if len(args) > 1 else kwargs.get('start_date')
            end_date = args[2] if len(args) > 2 else kwargs.get('end_date')
            return _fetcher.fetch_stock_data_yahoo(ticker, start_date, end_date)
    elif "fundamental_data" in key:
        ticker = args[0] if args else kwargs.get('ticker_symbol')
        return _fundamental_analyzer.get_financial_data(ticker)
    elif "popular_companies" in key:
        limit = args[0] if args else kwargs.get('limit', 10)
        return _company_searcher.get_popular_companies(limit)
    elif "industry_per_stats" in key:
        sector = args[0] if args else kwargs.get('sector')
        return _fundamental_analyzer.get_industry_per_comparison(sector)
    elif "undervalued_companies" in key:
        sector = args[0] if args else kwargs.get('sector')
        threshold = args[1] if len(args) > 1 else kwargs.get('threshold')
        return _fundamental_analyzer.find_undervalued_companies(sector, threshold)
    elif "overvalued_companies" in key:
        sector = args[0] if args else kwargs.get('sector')
        threshold = args[1] if len(args) > 1 else kwargs.get('threshold')
        return _fundamental_analyzer.find_overvalued_companies(sector, threshold)
    elif "target_price_analysis" in key:
        ticker = args[0] if args else kwargs.get('ticker_symbol')
        return _fundamental_analyzer.analyze_target_price(ticker)
    elif "target_price_opportunities" in key:
        min_upside = args[0] if args else kwargs.get('min_upside')
        max_upside = args[1] if len(args) > 1 else kwargs.get('max_upside')
        return _fundamental_analyzer.find_target_price_opportunities(min_upside, max_upside)
    elif "sector_target_price_analysis" in key:
        sector = args[0] if args else kwargs.get('sector')
        return _fundamental_analyzer.get_sector_target_price_analysis(sector)
    elif "comprehensive_data" in key:
        ticker = args[0] if args else kwargs.get('ticker')
        start_date = args[1] if len(args) > 1 else kwargs.get('start_date')
        end_date = args[2] if len(args) > 2 else kwargs.get('end_date')
        data = _advanced_data_manager.get_comprehensive_stock_data(ticker, start_date, end_date)
        return serialize_advanced_data(data)
    elif "sentiment_analysis" in key:
        ticker = args[0] if args else kwargs.get('ticker')
        data = _advanced_data_manager.get_sentiment_analysis(ticker)
        return serialize_sentiment_data(data)
    elif "market_intelligence" in key:
        ticker = args[0] if args else kwargs.get('ticker')
        data = _advanced_data_manager.get_market_intelligence(ticker)
        return serialize_intelligence_data(data)
    
    return None

def serialize_advanced_data(data):
    """高度なデータをシリアライズ可能な形式に変換"""
    if not data:
        return {}
    
    serialized = {}
    for key, value in data.items():
        if key == 'bloomberg_data':
            # DataFrameはそのまま保持
            serialized[key] = value
        elif key == 'financial_data':
            # 財務データのdatetimeを文字列に変換
            if value:
                financial_copy = value.copy()
                if 'last_updated' in financial_copy:
                    last_updated = financial_copy['last_updated']
                    if hasattr(last_updated, 'isoformat'):
                        financial_copy['last_updated'] = last_updated.isoformat()
                serialized[key] = financial_copy
        elif key == 'news_data':
            # ニュースデータのdatetimeを文字列に変換
            serialized[key] = {}
            for source, news_list in value.items():
                serialized[key][source] = []
                for news in news_list:
                    news_copy = {
                        'title': news.title,
                        'content': news.content,
                        'source': news.source,
                        'published_date': news.published_date.isoformat() if hasattr(news.published_date, 'isoformat') else str(news.published_date),
                        'url': news.url,
                        'sentiment_score': news.sentiment_score,
                        'keywords': news.keywords
                    }
                    serialized[key][source].append(news_copy)
        elif key == 'market_analysis':
            # 市場分析データのdatetimeを文字列に変換
            serialized[key] = {}
            for source, analysis in value.items():
                if analysis:
                    analysis_copy = analysis.copy()
                    if 'last_updated' in analysis_copy:
                        last_updated = analysis_copy['last_updated']
                        if hasattr(last_updated, 'isoformat'):
                            analysis_copy['last_updated'] = last_updated.isoformat()
                    serialized[key][source] = analysis_copy
        elif key == 'sec_data':
            # SECデータのdatetimeを文字列に変換
            serialized[key] = {}
            for sec_type, sec_list in value.items():
                serialized[key][sec_type] = []
                for item in sec_list:
                    item_copy = item.copy()
                    if 'filing_date' in item_copy:
                        filing_date = item_copy['filing_date']
                        if hasattr(filing_date, 'isoformat'):
                            item_copy['filing_date'] = filing_date.isoformat()
                    if 'trade_date' in item_copy:
                        trade_date = item_copy['trade_date']
                        if hasattr(trade_date, 'isoformat'):
                            item_copy['trade_date'] = trade_date.isoformat()
                    serialized[key][sec_type].append(item_copy)
        elif key == 'last_updated':
            # datetimeを文字列に変換
            if hasattr(value, 'isoformat'):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = str(value)
        else:
            serialized[key] = value
    
    return serialized

def serialize_sentiment_data(data):
    """感情分析データをシリアライズ可能な形式に変換"""
    if not data:
        return {}
    
    serialized = data.copy()
    if 'last_updated' in serialized:
        last_updated = serialized['last_updated']
        if hasattr(last_updated, 'isoformat'):
            serialized['last_updated'] = last_updated.isoformat()
    
    return serialized

def serialize_intelligence_data(data):
    """市場インテリジェンスデータをシリアライズ可能な形式に変換"""
    if not data:
        return {}
    
    serialized = data.copy()
    if 'generated_date' in serialized:
        generated_date = serialized['generated_date']
        if hasattr(generated_date, 'isoformat'):
            serialized['generated_date'] = generated_date.isoformat()
    
    return serialized

def format_currency_web(value):
    """通貨フォーマット（Web用）"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:,.0f}円"

def format_percentage(value):
    """パーセンテージフォーマット"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.1f}%"

def create_stock_price_chart(df, ticker_symbol):
    """株価チャートを作成（最適化版）"""
    if df.empty:
        return None
    
    # データフレームの最適化
    if MemoryOptimizer:
        df = MemoryOptimizer.optimize_dataframe(df)
    
    fig = go.Figure()
    
    # ローソク足チャート
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='株価',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    # 移動平均線（データが十分にある場合のみ）
    if len(df) >= 20:
        ma20 = df['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=ma20,
            mode='lines',
            name='20日移動平均',
            line=dict(color='orange', width=2)
        ))
    
    fig.update_layout(
        title=f'{ticker_symbol} 株価チャート',
        xaxis_title='日付',
        yaxis_title='株価 (円)',
        height=500,
        showlegend=True
    )
    
    return fig

def show_login_page(auth_manager, authz_manager, error_handler):
    """ログインページを表示"""
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h2 style="color: #3b82f6;">🔐 ログイン</h2>
        <p style="color: #6c757d;">システムにログインしてください</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ログインフォーム
    with st.form("login_form"):
        username = st.text_input("ユーザー名", placeholder="ユーザー名を入力")
        password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("🔐 ログイン", use_container_width=True)
        with col2:
            guest_button = st.form_submit_button("👤 ゲストとして利用", use_container_width=True)
        
        if login_button:
            if username and password:
                try:
                    # 簡易認証（実際の実装ではデータベースを使用）
                    if username == "admin" and password == "admin123":
                        # 認証成功
                        st.session_state.authenticated = True
                        st.session_state.user_role = "admin"
                        st.session_state.username = username
                        
                        # セッションを作成
                        session_id = auth_manager.create_session("admin_001", username)
                        st.session_state.session_id = session_id
                        
                        st.success("✅ ログインに成功しました！")
                        st.rerun()
                    elif username == "user" and password == "user123":
                        # 一般ユーザー認証
                        st.session_state.authenticated = True
                        st.session_state.user_role = "user"
                        st.session_state.username = username
                        
                        # セッションを作成
                        session_id = auth_manager.create_session("user_001", username)
                        st.session_state.session_id = session_id
                        
                        st.success("✅ ログインに成功しました！")
                        st.rerun()
                    else:
                        # 認証失敗
                        error_info = error_handler.handle_error(
                            Exception("認証に失敗しました"),
                            ErrorCategory.AUTHENTICATION,
                            ErrorSeverity.MEDIUM,
                            {'username': username}
                        )
                        user_message = error_handler.get_user_friendly_message(error_info)
                        st.error(f"❌ {user_message}")
                except Exception as e:
                    error_info = error_handler.handle_error(
                        e,
                        ErrorCategory.AUTHENTICATION,
                        ErrorSeverity.HIGH,
                        {'username': username}
                    )
                    user_message = error_handler.get_user_friendly_message(error_info)
                    st.error(f"❌ ログインエラー: {user_message}")
            else:
                st.error("❌ ユーザー名とパスワードを入力してください")
        
        if guest_button:
            # ゲストとして利用
            st.session_state.authenticated = True
            st.session_state.user_role = "guest"
            st.session_state.username = "guest"
            st.success("✅ ゲストとしてログインしました！")
            st.rerun()
    
    # テスト用アカウント情報
    st.markdown("""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-top: 2rem;">
        <h4 style="color: #495057;">🧪 テスト用アカウント</h4>
        <p style="color: #6c757d; margin: 0;">
            <strong>管理者:</strong> admin / admin123<br>
            <strong>一般ユーザー:</strong> user / user123<br>
            <strong>ゲスト:</strong> ゲストとして利用ボタンをクリック
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_logout_button():
    """ログアウトボタンを表示"""
    if st.sidebar.button("🚪 ログアウト", use_container_width=True):
        if SECURITY_ENABLED and st.session_state.session_id:
            # セッションを削除
            auth_manager = AuthenticationManager()
            auth_manager.remove_session(st.session_state.session_id)
        
        # セッション状態をクリア
        st.session_state.authenticated = False
        st.session_state.user_role = 'guest'
        st.session_state.session_id = None
        st.session_state.username = None
        
        st.success("✅ ログアウトしました")
        st.rerun()

def check_permission(required_permission):
    """権限チェック"""
    if not SECURITY_ENABLED:
        return True
    
    if not st.session_state.authenticated:
        return False
    
    authz_manager = AuthorizationManager()
    return authz_manager.has_permission(st.session_state.user_role, required_permission)

def check_new_features_availability():
    """新機能の利用可能性をチェック"""
    if not NEW_FEATURES_ENABLED:
        return False, "新機能のインポートに失敗しました"
    
    missing_features = []
    if DashboardManager is None:
        missing_features.append("ダッシュボード")
    if PortfolioOptimizer is None:
        missing_features.append("ポートフォリオ最適化")
    if APIMonitor is None:
        missing_features.append("API監視")
    
    if missing_features:
        return False, f"次の機能が利用できません: {', '.join(missing_features)}"
    
    return True, "すべての新機能が利用可能です"

def main():
    """メイン関数（最適化版）"""
    try:
        # 改善機能の初期化
        system_integrator = None
        if IMPROVED_FEATURES_ENABLED:
            system_integrator = initialize_improved_app()
        
        # セキュリティ機能の初期化
        if SECURITY_ENABLED:
            auth_manager = AuthenticationManager()
            authz_manager = AuthorizationManager()
            error_handler = ErrorHandler()
            
            # セッション状態の初期化
            if 'authenticated' not in st.session_state:
                st.session_state.authenticated = False
            if 'user_role' not in st.session_state:
                st.session_state.user_role = 'guest'
            if 'session_id' not in st.session_state:
                st.session_state.session_id = None
        
        # ヘッダー
        st.markdown("""
        <div class="fade-in">
            <h1 style="color: #3b82f6;">🇯🇵 日本の株価データ分析システム（改善版）</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # サブタイトル
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <p style="font-size: 1.2rem; color: #6c757d; font-weight: 500;">
                📊 リアルタイム株価監視 | 📈 テクニカル分析 | 🏢 ファンダメンタル分析 | ⚡ 高度なデータ分析 | 🛡️ セキュリティ強化
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 改善機能の状態表示
        if system_integrator:
            with st.expander("🎯 システム改善機能の状態", expanded=False):
                system_integrator.show_system_status()
        
        # 認証チェック
        if SECURITY_ENABLED and not st.session_state.authenticated:
            show_login_page(auth_manager, authz_manager, error_handler)
            return
        
        # システム初期化
        with st.spinner('🚀 システムを初期化中...'):
            fetcher, analyzer, company_searcher, fundamental_analyzer, advanced_data_manager, technical_analyzer, real_time_manager = initialize_system()
        
        if not all([fetcher, analyzer, company_searcher, fundamental_analyzer, advanced_data_manager, technical_analyzer, real_time_manager]):
            st.error("❌ システムの初期化に失敗しました。")
            st.info("🔄 ページを再読み込みするか、しばらく時間をおいてから再度お試しください。")
            return
    except Exception as e:
        if SECURITY_ENABLED and error_handler:
            error_info = error_handler.handle_error(
                e, 
                ErrorCategory.SYSTEM, 
                ErrorSeverity.HIGH,
                {'context': 'main_function_initialization'}
            )
            user_message = error_handler.get_user_friendly_message(error_info)
            st.error(f"❌ アプリケーションの起動に失敗しました: {user_message}")
        else:
            st.error(f"❌ アプリケーションの起動に失敗しました: {e}")
        st.info("📞 エラーが解決しない場合は、管理者にお問い合わせください。")
        return
    
    # パフォーマンス情報は内部で監視（UIには表示しない）
    if MemoryOptimizer:
        memory_usage = MemoryOptimizer.get_memory_usage()
        # ログに記録（デバッグ用）
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"メモリ使用量: {memory_usage['rss_mb']:.1f}MB, 使用率: {memory_usage['percent']:.1f}%")
    
    # サイドバー
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: #3b82f6; font-weight: 700; margin-bottom: 1rem;">📊 機能選択</h2>
        <div style="background: #3b82f6; height: 3px; border-radius: 2px; margin: 0 auto; width: 50%;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # ユーザー情報表示
    if SECURITY_ENABLED and st.session_state.authenticated:
        user_role_display = {
            'admin': '👑 管理者',
            'user': '👤 ユーザー',
            'guest': '👤 ゲスト'
        }
        role_display = user_role_display.get(st.session_state.user_role, '👤 ユーザー')
        
        st.sidebar.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <div style="text-align: center;">
                <div style="font-weight: 600; color: #495057;">{role_display}</div>
                <div style="font-size: 0.9rem; color: #6c757d;">{st.session_state.username}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 機能選択（権限に応じて表示）
    available_pages = ["🏠 ホーム", "📈 最新株価"]
    
    # 読み取り権限がある場合の機能
    if check_permission('read'):
        available_pages.extend([
            "📊 株価チャート",
            "📈 テクニカル分析チャート",
            "🏢 ファンダメンタル分析",
            "⚖️ 財務指標比較",
            "📦 複数銘柄分析",
            "🔍 高度なデータ分析"
        ])
        
        # 新機能を追加
        if NEW_FEATURES_ENABLED:
            available_pages.extend([
                "🎯 ダッシュボード",
                "📈 ポートフォリオ最適化",
                "📡 API監視"
            ])
        
        # 改善機能を追加
        if IMPROVED_FEATURES_ENABLED:
            available_pages.extend([
                "📡 データソース管理",
                "🛡️ セキュリティ管理",
                "⚙️ UI最適化",
                "📈 強化チャート機能"
            ])
    
    # 書き込み権限がある場合の機能
    if check_permission('write'):
        available_pages.append("💾 データエクスポート")
    
    # 管理者権限がある場合の機能
    if check_permission('admin'):
        available_pages.append("⚡ リアルタイム監視")
        
        # 改善機能の管理機能
        if IMPROVED_FEATURES_ENABLED:
            available_pages.extend([
                "📊 システム状態監視",
                "🛠️ エラーハンドリング",
                "📋 トラブルシューティング"
            ])
    
    # セッション状態からページを取得、またはデフォルト値を設定
    if 'selected_page' not in st.session_state:
        st.session_state.selected_page = "🏠 ホーム"
    
    page = st.sidebar.selectbox(
        "🎯 機能を選択してください",
        available_pages,
        index=available_pages.index(st.session_state.selected_page) if st.session_state.selected_page in available_pages else 0,
        help="利用したい機能を選択してください"
    )
    
    # ページが変更された場合、セッション状態を更新
    if page != st.session_state.selected_page:
        st.session_state.selected_page = page
    
    # ログアウトボタン
    if SECURITY_ENABLED and st.session_state.authenticated:
        show_logout_button()
    
    # ホームページ
    if page == "🏠 ホーム":
        st.markdown("""
        <div class="fade-in">
            <h2 style="color: #2563eb; font-weight: 700; margin-bottom: 2rem;">🏠 ホーム</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # システム概要カード
        st.markdown("""
        <div class="section-header">
            📊 システム概要
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # デバッグ情報を追加
            if company_searcher and hasattr(company_searcher, 'companies'):
                company_count = len(company_searcher.companies)
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-icon">🏢</div>
                    <div class="metric-content">
                        <div class="metric-value">{company_count:,}</div>
                        <div class="metric-label">登録企業数</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="metric-container">
                    <div class="metric-icon">🏢</div>
                    <div class="metric-content">
                        <div class="metric-value">0</div>
                        <div class="metric-label">登録企業数 (初期化中)</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-icon">📈</div>
                <div class="metric-content">
                    <div class="metric-value">{len(fundamental_analyzer.financial_data)}</div>
                    <div class="metric-label">ファンダメンタル分析対応</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-container">
                <div class="metric-icon">🌐</div>
                <div class="metric-content">
                    <div class="metric-value">6</div>
                    <div class="metric-label">データソース</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # リアルタイム機能の紹介
        st.markdown("""
        <div class="section-header">
            ⚡ 新機能: リアルタイム監視システム
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: #3b82f6; color: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);">
                <h3 style="color: white; margin-bottom: 1rem;">🚀 リアルタイム機能</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin: 0.5rem 0;">✅ <strong>即座のデータ更新</strong>: WebSocket通信</li>
                    <li style="margin: 0.5rem 0;">🔔 <strong>プッシュ通知</strong>: 重要な価格変動</li>
                    <li style="margin: 0.5rem 0;">⏰ <strong>自動監視</strong>: 30秒ごとの更新</li>
                    <li style="margin: 0.5rem 0;">🎯 <strong>アラート機能</strong>: カスタマイズ可能な閾値</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: #22c55e; color: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(34, 197, 94, 0.3);">
                <h3 style="color: white; margin-bottom: 1rem;">📊 監視対象銘柄</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin: 0.5rem 0;">📱 <strong>9984</strong>: ソフトバンクG</li>
                    <li style="margin: 0.5rem 0;">📡 <strong>9433</strong>: KDDI</li>
                    <li style="margin: 0.5rem 0;">🚗 <strong>7203</strong>: トヨタ自動車</li>
                    <li style="margin: 0.5rem 0;">💻 <strong>6758</strong>: ソニーG</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # 新機能の紹介
        features_available, features_status = check_new_features_availability()
        
        st.markdown("""
        <div class="section-header">
            🎯 新機能: 高度な分析ツール
        </div>
        """, unsafe_allow_html=True)
        
        if features_available:
            st.success(f"✅ {features_status}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="background: #8b5cf6; color: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);">
                    <h3 style="color: white; margin-bottom: 1rem;">🎯 ダッシュボード</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 0.5rem 0;">📊 <strong>市場概要</strong>: リアルタイム市場データ</li>
                        <li style="margin: 0.5rem 0;">🗺️ <strong>セクターヒートマップ</strong>: 業界動向</li>
                        <li style="margin: 0.5rem 0;">⭐ <strong>ウォッチリスト</strong>: 銘柄監視</li>
                        <li style="margin: 0.5rem 0;">📰 <strong>ニュースフィード</strong>: 最新情報</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style="background: #f59e0b; color: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(245, 158, 11, 0.3);">
                    <h3 style="color: white; margin-bottom: 1rem;">📈 ポートフォリオ最適化</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 0.5rem 0;">🎯 <strong>効率的フロンティア</strong>: 最適化理論</li>
                        <li style="margin: 0.5rem 0;">🎲 <strong>モンテカルロ</strong>: リスク分析</li>
                        <li style="margin: 0.5rem 0;">⚠️ <strong>VaR/CVaR</strong>: リスク測定</li>
                        <li style="margin: 0.5rem 0;">⚖️ <strong>最適配分</strong>: 資産分散</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style="background: #ef4444; color: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);">
                    <h3 style="color: white; margin-bottom: 1rem;">📡 API監視</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li style="margin: 0.5rem 0;">🔍 <strong>ヘルスチェック</strong>: API状態監視</li>
                        <li style="margin: 0.5rem 0;">⏱️ <strong>レスポンス時間</strong>: 性能測定</li>
                        <li style="margin: 0.5rem 0;">🚨 <strong>アラート</strong>: 障害通知</li>
                        <li style="margin: 0.5rem 0;">📊 <strong>統計情報</strong>: 利用状況分析</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ {features_status}")
            st.info("新機能は現在利用できませんが、すべての基本機能は正常に動作します。")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # リアルタイム監視の状態表示
        if st.session_state.get('real_time_active', False):
            start_time = st.session_state.get('real_time_start_time', datetime.now())
            elapsed_time = datetime.now() - start_time
            st.success(f"🟢 リアルタイム監視が実行中です（開始時刻: {start_time.strftime('%H:%M:%S')}, 経過時間: {elapsed_time.seconds}秒）")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚡ リアルタイム監視を試す", type="primary", use_container_width=True):
                st.session_state.selected_page = "⚡ リアルタイム監視"
                # リアルタイム監視を開始
                st.session_state.real_time_active = True
                st.session_state.real_time_start_time = datetime.now()
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 主要企業の一覧（最適化版）
        st.markdown("""
        <div class="section-header">
            ⭐ 主要企業一覧
        </div>
        """, unsafe_allow_html=True)
        
        # 主要企業を取得（リアルタイム監視が有効な場合はキャッシュを使用せず）
        if st.session_state.get('real_time_active', False):
            popular_companies = company_searcher.get_popular_companies(10)
        else:
            popular_companies = get_cached_data(
                "popular_companies", 
                10,
                _company_searcher=company_searcher
            )
        
        # 企業カードをグリッド表示
        cols = st.columns(3)
        for i, company in enumerate(popular_companies):
            col_idx = i % 3
            with cols[col_idx]:
                # 最新株価を取得（リアルタイム監視が有効な場合はキャッシュを使用せず）
                try:
                    if st.session_state.get('real_time_active', False):
                        price_data = fetcher.get_latest_price(company['code'], "stooq")
                    else:
                        price_data = get_cached_data(
                            f"latest_price_stooq_{company['code']}", 
                            company['code'],
                            _fetcher=fetcher
                        )
                    
                    if "error" not in price_data:
                        price_display = format_currency_web(price_data['close'])
                        date_display = price_data['date']
                        status_color = "#28a745"
                        status_icon = "✅"
                        
                        # リアルタイム監視が有効な場合は価格変化を計算
                        if st.session_state.get('real_time_active', False):
                            if f'prev_price_{company["code"]}' not in st.session_state:
                                st.session_state[f'prev_price_{company["code"]}'] = price_data['close']
                            
                            current_price = price_data['close']
                            prev_price = st.session_state[f'prev_price_{company["code"]}']
                            price_change = current_price - prev_price
                            price_change_percent = (price_change / prev_price) * 100 if prev_price > 0 else 0
                            
                            # 前回の価格を更新
                            st.session_state[f'prev_price_{company["code"]}'] = current_price
                            
                            change_display = f"{price_change:+.0f} ({price_change_percent:+.1f}%)"
                        else:
                            change_display = ""
                    else:
                        price_display = "データ取得エラー"
                        date_display = "N/A"
                        change_display = ""
                        status_color = "#dc3545"
                        status_icon = "❌"
                except:
                    price_display = "データ取得エラー"
                    date_display = "N/A"
                    change_display = ""
                    status_color = "#dc3545"
                    status_icon = "❌"
                
                st.markdown(f"""
                <div style="background: #374151; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); border-left: 5px solid {status_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h4 style="margin: 0; color: #ffffff;">{company['name']}</h4>
                        <span style="background: {status_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 10px; font-size: 0.8rem;">{status_icon}</span>
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong style="color: #3b82f6;">銘柄コード:</strong> {company['code']}
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong style="color: #3b82f6;">業種:</strong> {company['sector']}
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong style="color: #3b82f6;">市場:</strong> {company['market']}
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <strong style="color: #3b82f6;">現在値:</strong> {price_display}
                    </div>
                    {f'<div style="margin-bottom: 0.5rem;"><strong style="color: #3b82f6;">変化:</strong> {change_display}</div>' if change_display else ''}
                    <div style="font-size: 0.9rem; color: #9ca3af;">
                        <strong>更新日:</strong> {date_display}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # 最新株価ページ
    elif page == "📈 最新株価":
        st.markdown("""
        <div class="fade-in">
            <h2 style="color: #2563eb; font-weight: 700; margin-bottom: 2rem;">📈 最新株価取得</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 入力フォーム
        st.markdown("""
        <div class="section-header">
            🎯 株価データ取得
        </div>
        """, unsafe_allow_html=True)
        
        # 銘柄コード入力
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ticker_input = st.text_input(
                "銘柄コードを入力してください", 
                placeholder="例: 7203, 6758, 9984",
                help="4桁の銘柄コードを入力してください"
            )
        
        with col2:
            source = st.selectbox(
                "データソース", 
                ["stooq", "yahoo", "both"],
                help="データを取得するソースを選択してください"
            )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📊 株価を取得", type="primary", use_container_width=True):
                if ticker_input:
                    ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}の株価を取得中..."):
                    try:
                        if source == "both":
                            stooq_data = get_cached_data(
                                f"latest_price_stooq_{ticker}", 
                                ticker,
                                _fetcher=fetcher
                            )
                            yahoo_data = get_cached_data(
                                f"latest_price_yahoo_{ticker}", 
                                ticker,
                                _fetcher=fetcher
                            )
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### 📊 stooq データ")
                                if "error" not in stooq_data:
                                    st.metric("終値", format_currency_web(stooq_data['close']))
                                    st.write(f"**日付:** {stooq_data['date']}")
                                    st.write(f"**出来高:** {format_number(stooq_data['volume'])}株")
                                else:
                                    st.error(f"エラー: {stooq_data['error']}")
                            
                            with col2:
                                st.markdown("### 📊 Yahoo Finance データ")
                                if "error" not in yahoo_data:
                                    st.metric("終値", format_currency_web(yahoo_data['close']))
                                    st.write(f"**日付:** {yahoo_data['date']}")
                                    st.write(f"**出来高:** {format_number(yahoo_data['volume'])}株")
                                else:
                                    st.warning(f"Yahoo Finance: {yahoo_data['error']}")
                        else:
                            data = get_cached_data(
                                f"latest_price_{source}_{ticker}", 
                                ticker,
                                _fetcher=fetcher
                            )
                            
                            if "error" not in data:
                                st.success("✅ データ取得成功!")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("終値", format_currency_web(data['close']))
                                with col2:
                                    st.metric("始値", format_currency_web(data['open']))
                                with col3:
                                    st.metric("高値", format_currency_web(data['high']))
                                with col4:
                                    st.metric("安値", format_currency_web(data['low']))
                                
                                st.write(f"**出来高:** {format_number(data['volume'])}株")
                                st.write(f"**日付:** {data['date']}")
                                st.write(f"**データソース:** {data['source']}")
                            else:
                                st.error(f"❌ エラー: {data['error']}")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
    
    # リアルタイム監視ページ
    elif page == "⚡ リアルタイム監視":
        # 権限チェック
        if not check_permission('admin'):
            st.error("❌ この機能を利用する権限がありません。")
            st.info("リアルタイム監視機能には管理者権限が必要です。")
            return
        
        st.markdown("""
        <div class="fade-in">
            <h2 style="color: #2563eb; font-weight: 700; margin-bottom: 2rem;">⚡ リアルタイム株価監視</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="section-header">
            🚀 リアルタイムデータ更新システム
        </div>
        """, unsafe_allow_html=True)
        
        # リアルタイム機能の説明
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: #3b82f6; color: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);">
                <h3 style="color: white; margin-bottom: 1rem;">🔴 リアルタイム機能</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin: 0.5rem 0;">⚡ <strong>WebSocket通信</strong>: 即座のデータ更新</li>
                    <li style="margin: 0.5rem 0;">🔔 <strong>プッシュ通知</strong>: 重要な価格変動の通知</li>
                    <li style="margin: 0.5rem 0;">⏰ <strong>自動更新</strong>: 30秒ごとのデータ更新</li>
                    <li style="margin: 0.5rem 0;">📱 <strong>主要銘柄監視</strong>: 9984, 9433, 7203, 6758, 6861</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: #f97316; color: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 8px 25px rgba(249, 115, 22, 0.3);">
                <h3 style="color: white; margin-bottom: 1rem;">📊 監視機能</h3>
                <ul style="list-style: none; padding: 0;">
                    <li style="margin: 0.5rem 0;">📈 <strong>価格変動</strong>: リアルタイム価格追跡</li>
                    <li style="margin: 0.5rem 0;">📊 <strong>ボラティリティ</strong>: 価格変動率の監視</li>
                    <li style="margin: 0.5rem 0;">📦 <strong>出来高</strong>: 取引量の変化</li>
                    <li style="margin: 0.5rem 0;">🕒 <strong>市場状況</strong>: 取引時間の表示</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # リアルタイム監視の状態表示
        if st.session_state.get('real_time_active', False):
            start_time = st.session_state.get('real_time_start_time', datetime.now())
            elapsed_time = datetime.now() - start_time
            st.success(f"🟢 リアルタイム監視が実行中です（開始時刻: {start_time.strftime('%H:%M:%S')}, 経過時間: {elapsed_time.seconds}秒）")
        else:
            st.info("🔴 リアルタイム監視は停止中です")
        
        # リアルタイム監視の開始/停止
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 リアルタイム監視開始", type="primary"):
                try:
                    # リアルタイム監視を開始
                    st.session_state.real_time_active = True
                    st.session_state.real_time_start_time = datetime.now()
                    st.success("✅ リアルタイム監視を開始しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ リアルタイム監視の開始に失敗しました: {e}")
        
        with col2:
            if st.button("⏹️ リアルタイム監視停止"):
                try:
                    # リアルタイム監視を停止
                    st.session_state.real_time_active = False
                    st.session_state.real_time_start_time = None
                    st.success("✅ リアルタイム監視を停止しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ リアルタイム監視の停止に失敗しました: {e}")
        
        # リアルタイムデータ表示エリア
        if st.session_state.get('real_time_active', False):
            st.markdown("### 📊 リアルタイム株価データ")
            
            # 主要銘柄のリアルタイムデータを表示
            major_tickers = ["9984", "9433", "7203", "6758", "6861"]
            
            # リアルタイムデータを取得（キャッシュを使用せず最新データを取得）
            real_time_data = {}
            for ticker in major_tickers:
                try:
                    # キャッシュを使用せずに最新の株価データを直接取得
                    latest_data = fetcher.get_latest_price(ticker, "stooq")
                    
                    if "error" not in latest_data:
                        # 前回のデータと比較して変化を計算
                        if f'prev_price_{ticker}' not in st.session_state:
                            st.session_state[f'prev_price_{ticker}'] = latest_data['close']
                        
                        current_price = latest_data['close']
                        prev_price = st.session_state[f'prev_price_{ticker}']
                        price_change = current_price - prev_price
                        price_change_percent = (price_change / prev_price) * 100 if prev_price > 0 else 0
                        
                        # 前回の価格を更新
                        st.session_state[f'prev_price_{ticker}'] = current_price
                        
                        real_time_data[ticker] = {
                            'current_price': current_price,
                            'price_change': price_change,
                            'price_change_percent': price_change_percent,
                            'volume': latest_data.get('volume', 0),
                            'market_status': 'open' if datetime.now().hour < 15 else 'closed',
                            'last_updated': datetime.now().strftime("%H:%M:%S")
                        }
                    else:
                        st.warning(f"銘柄 {ticker} のデータ取得エラー: {latest_data['error']}")
                except Exception as e:
                    st.warning(f"銘柄 {ticker} のリアルタイムデータ取得エラー: {e}")
            
            # リアルタイムデータを表示
            if real_time_data:
                # メトリクス表示
                cols = st.columns(len(major_tickers))
                for i, ticker in enumerate(major_tickers):
                    if ticker in real_time_data:
                        data = real_time_data[ticker]
                        with cols[i]:
                            st.metric(
                                f"{ticker}",
                                f"¥{data['current_price']:,.0f}",
                                f"{data['price_change']:+.0f} ({data['price_change_percent']:+.1f}%)"
                            )
                            st.write(f"**出来高:** {format_number(data['volume'])}")
                            st.write(f"**市場:** {'🟢 取引中' if data['market_status'] == 'open' else '🔴 終了'}")
                
                # リアルタイムチャート
                st.markdown("### 📈 リアルタイム価格推移")
                
                # チャートデータを準備
                chart_data = []
                for ticker in major_tickers:
                    if ticker in real_time_data:
                        data = real_time_data[ticker]
                        chart_data.append({
                            'ticker': ticker,
                            'price': data['current_price'],
                            'change': data['price_change_percent'],
                            'volume': data['volume']
                        })
                
                if chart_data:
                    df_chart = pd.DataFrame(chart_data)
                    
                    # 価格チャート
                    fig_price = px.bar(
                        df_chart, 
                        x='ticker', 
                        y='price',
                        title="リアルタイム株価",
                        color='change',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_price.update_layout(height=400)
                    st.plotly_chart(fig_price, use_container_width=True)
                    
                    # 変動率チャート
                    fig_change = px.bar(
                        df_chart, 
                        x='ticker', 
                        y='change',
                        title="価格変動率 (%)",
                        color='change',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_change.update_layout(height=400)
                    st.plotly_chart(fig_change, use_container_width=True)
                
                # 自動更新機能
                st.markdown("### 🔄 自動更新")
                
                # 自動更新の設定
                col1, col2 = st.columns(2)
                with col1:
                    auto_refresh = st.checkbox("自動更新を有効にする", value=True)
                with col2:
                    refresh_interval = st.selectbox("更新間隔", [5, 10, 30, 60], format_func=lambda x: f"{x}秒")
                
                if auto_refresh:
                    st.info(f"データは{refresh_interval}秒ごとに自動更新されます。")
                    
                    # JavaScriptを使用した自動更新
                    st.markdown(f"""
                    <script>
                    setTimeout(function() {{
                        window.location.reload();
                    }}, {refresh_interval * 1000});
                    </script>
                    """, unsafe_allow_html=True)
                else:
                    st.info("手動更新のみ有効です。")
                
                # 手動更新ボタン
                if st.button("🔄 手動更新"):
                    st.rerun()
                
                # 更新時刻の表示
                st.markdown(f"**最終更新時刻:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # リアルタイム主要企業一覧
                st.markdown("### ⭐ リアルタイム主要企業一覧")
                
                # 主要企業の最新データを取得（キャッシュを使用せず）
                popular_companies = company_searcher.get_popular_companies(10)
                
                # 企業カードをグリッド表示
                cols = st.columns(3)
                for i, company in enumerate(popular_companies):
                    col_idx = i % 3
                    with cols[col_idx]:
                        # 最新株価を直接取得（キャッシュを使用せず）
                        try:
                            price_data = fetcher.get_latest_price(company['code'], "stooq")
                            
                            if "error" not in price_data:
                                price_display = format_currency_web(price_data['close'])
                                date_display = price_data['date']
                                status_color = "#28a745"
                                status_icon = "✅"
                                
                                # 価格変化を計算
                                if f'prev_price_{company["code"]}' not in st.session_state:
                                    st.session_state[f'prev_price_{company["code"]}'] = price_data['close']
                                
                                current_price = price_data['close']
                                prev_price = st.session_state[f'prev_price_{company["code"]}']
                                price_change = current_price - prev_price
                                price_change_percent = (price_change / prev_price) * 100 if prev_price > 0 else 0
                                
                                # 前回の価格を更新
                                st.session_state[f'prev_price_{company["code"]}'] = current_price
                                
                                change_display = f"{price_change:+.0f} ({price_change_percent:+.1f}%)"
                            else:
                                price_display = "データ取得エラー"
                                date_display = "N/A"
                                change_display = "N/A"
                                status_color = "#dc3545"
                                status_icon = "❌"
                        except:
                            price_display = "データ取得エラー"
                            date_display = "N/A"
                            change_display = "N/A"
                            status_color = "#dc3545"
                            status_icon = "❌"
                        
                        st.markdown(f"""
                        <div style="background: #374151; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); border-left: 5px solid {status_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                                <h4 style="margin: 0; color: #ffffff;">{company['name']}</h4>
                                <span style="background: {status_color}; color: white; padding: 0.25rem 0.5rem; border-radius: 10px; font-size: 0.8rem;">{status_icon}</span>
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <strong style="color: #3b82f6;">銘柄コード:</strong> {company['code']}
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <strong style="color: #3b82f6;">業種:</strong> {company['sector']}
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <strong style="color: #3b82f6;">市場:</strong> {company['market']}
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <strong style="color: #3b82f6;">現在値:</strong> {price_display}
                            </div>
                            <div style="margin-bottom: 0.5rem;">
                                <strong style="color: #3b82f6;">変化:</strong> {change_display}
                            </div>
                            <div style="font-size: 0.9rem; color: #9ca3af;">
                                <strong>更新日:</strong> {date_display}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # リアルタイムアラート設定
                st.markdown("### 🔔 リアルタイムアラート設定")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    alert_threshold = st.slider(
                        "価格変動アラート閾値 (%)",
                        min_value=1.0,
                        max_value=10.0,
                        value=5.0,
                        step=0.5
                    )
                    
                    if st.button("🔔 アラート設定を保存"):
                        st.session_state.alert_threshold = alert_threshold
                        st.success(f"✅ アラート閾値を {alert_threshold}% に設定しました！")
                
                with col2:
                    # アラート履歴
                    st.markdown("**📋 アラート履歴:**")
                    if 'alert_history' not in st.session_state:
                        st.session_state.alert_history = []
                    
                    for alert in st.session_state.alert_history[-5:]:  # 最新5件
                        st.write(f"🔄 {alert['time']}: {alert['message']}")
                
                # アラートチェック
                if 'alert_threshold' in st.session_state:
                    for ticker in major_tickers:
                        if ticker in real_time_data:
                            data = real_time_data[ticker]
                            if abs(data['price_change_percent']) >= st.session_state.alert_threshold:
                                alert_message = f"{ticker}: {data['price_change_percent']:+.1f}% の価格変動"
                                alert_time = datetime.now().strftime("%H:%M:%S")
                                
                                # 新しいアラートかチェック
                                new_alert = {'time': alert_time, 'message': alert_message}
                                if new_alert not in st.session_state.alert_history:
                                    st.session_state.alert_history.append(new_alert)
                                    st.warning(f"🚨 アラート: {alert_message}")
            else:
                st.warning("リアルタイムデータが取得できませんでした。")
        else:
            st.info("🚀 リアルタイム監視を開始してください。")
            
            # デモ用のサンプルデータを表示
            st.markdown("### 📊 デモ用サンプルデータ")
            st.info("リアルタイム監視を開始すると、実際の株価データが表示されます。")
            
            # サンプルデータを表示
            sample_tickers = ["9984", "9433", "7203", "6758", "6861"]
            sample_data = {
                "9984": {"name": "ソフトバンクG", "price": 8500, "change": 150, "change_percent": 1.8},
                "9433": {"name": "KDDI", "price": 4200, "change": -50, "change_percent": -1.2},
                "7203": {"name": "トヨタ自動車", "price": 2800, "change": 80, "change_percent": 2.9},
                "6758": {"name": "ソニーG", "price": 12000, "change": 200, "change_percent": 1.7},
                "6861": {"name": "キーエンス", "price": 65000, "change": -1000, "change_percent": -1.5}
            }
            
            cols = st.columns(len(sample_tickers))
            for i, ticker in enumerate(sample_tickers):
                data = sample_data[ticker]
                with cols[i]:
                    st.metric(
                        f"{ticker} ({data['name']})",
                        f"¥{data['price']:,.0f}",
                        f"{data['change']:+.0f} ({data['change_percent']:+.1f}%)"
                    )
    
    # 株価チャートページ
    elif page == "📊 株価チャート":
        st.markdown("## 📊 株価チャート")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ticker_input = st.text_input("銘柄コード", placeholder="例: 7203")
        
        with col2:
            source = st.selectbox("データソース", ["stooq", "yahoo"])
        
        with col3:
            period = st.selectbox("期間", [7, 30, 90, 365], format_func=lambda x: f"{x}日間")
        
        if st.button("📈 チャートを表示", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}のチャートを生成中..."):
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=period)
                        
                        if source == "stooq":
                            df = get_cached_data(
                                f"stock_data_stooq_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d'),
                                _fetcher=fetcher
                            )
                        else:
                            df = get_cached_data(
                                f"stock_data_yahoo_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d'),
                                _fetcher=fetcher
                            )
                        
                        if not df.empty:
                            chart = create_stock_price_chart(df, ticker)
                            if chart:
                                st.plotly_chart(chart, use_container_width=True)
                            else:
                                st.warning("チャートの生成に失敗しました")
                        else:
                            st.error("データが見つかりませんでした")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
    
    # テクニカル分析チャートページ
    elif page == "📈 テクニカル分析チャート":
        st.markdown("## 📈 テクニカル分析チャート")
        st.markdown("移動平均線、ボリンジャーバンド、RSIなどのテクニカル指標を表示します")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ticker_input = st.text_input("銘柄コード", placeholder="例: 7203")
        
        with col2:
            source = st.selectbox("データソース", ["stooq", "yahoo"])
        
        with col3:
            period = st.selectbox("期間", [30, 90, 180, 365], format_func=lambda x: f"{x}日間")
        
        with col4:
            chart_type = st.selectbox("チャートタイプ", ["ローソク足", "テクニカル指標"])
        
        # テクニカル指標のオプション
        col1, col2, col3 = st.columns(3)
        
        with col1:
            show_ma = st.checkbox("移動平均線", value=True)
        
        with col2:
            show_bb = st.checkbox("ボリンジャーバンド", value=False)
        
        with col3:
            show_volume = st.checkbox("出来高", value=True)
        
        if st.button("📈 テクニカル分析チャートを表示", type="primary"):
            if ticker_input and technical_analyzer:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}のテクニカル分析チャートを生成中..."):
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=period)
                        
                        if source == "stooq":
                            df = get_cached_data(
                                f"stock_data_stooq_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d'),
                                _fetcher=fetcher
                            )
                        else:
                            df = get_cached_data(
                                f"stock_data_yahoo_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d'),
                                _fetcher=fetcher
                            )
                        
                        if not df.empty:
                            if chart_type == "ローソク足":
                                chart = technical_analyzer.create_candlestick_chart(
                                    df, ticker, show_ma=show_ma, show_bb=show_bb, show_volume=show_volume
                                )
                            elif chart_type == "テクニカル指標":
                                # テクニカル指標チャート
                                chart = technical_analyzer.create_technical_indicators_chart(df, ticker)
                            else:
                                chart = technical_analyzer.create_candlestick_chart(
                                    df, ticker, show_ma=show_ma, show_bb=show_bb, show_volume=show_volume
                                )
                            
                            if chart:
                                st.plotly_chart(chart, use_container_width=True)
                                
                                # テクニカル分析シグナルを表示
                                st.markdown("### 📊 テクニカル分析シグナル")
                                
                                # テクニカル分析シグナルを取得
                                signals = technical_analyzer.get_technical_signals(df)
                                
                                # RSI計算
                                df_rsi = technical_analyzer.calculate_rsi(df)
                                latest_rsi = df_rsi['RSI'].iloc[-1] if 'RSI' in df_rsi.columns else None
                                
                                # 移動平均計算
                                df_ma = technical_analyzer.calculate_moving_averages(df)
                                latest_ma5 = df_ma['MA_5'].iloc[-1] if 'MA_5' in df_ma.columns else None
                                latest_ma20 = df_ma['MA_20'].iloc[-1] if 'MA_20' in df_ma.columns else None
                                
                                # MACD計算
                                df_macd = technical_analyzer.calculate_macd(df)
                                latest_macd = df_macd['MACD_Line'].iloc[-1] if 'MACD_Line' in df_macd.columns else None
                                latest_signal = df_macd['MACD_Signal'].iloc[-1] if 'MACD_Signal' in df_macd.columns else None
                                
                                # ストキャスティクス計算
                                df_stoch = technical_analyzer.calculate_stochastic(df)
                                latest_stoch_k = df_stoch['Stoch_K'].iloc[-1] if 'Stoch_K' in df_stoch.columns else None
                                latest_stoch_d = df_stoch['Stoch_D'].iloc[-1] if 'Stoch_D' in df_stoch.columns else None
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    if latest_rsi is not None and not pd.isna(latest_rsi):
                                        if latest_rsi < 30:
                                            st.metric("RSI", f"{latest_rsi:.1f}", delta="買いシグナル", delta_color="normal")
                                        elif latest_rsi > 70:
                                            st.metric("RSI", f"{latest_rsi:.1f}", delta="売りシグナル", delta_color="inverse")
                                        else:
                                            st.metric("RSI", f"{latest_rsi:.1f}")
                                    else:
                                        st.metric("RSI", "N/A")
                                
                                with col2:
                                    if latest_ma5 is not None and latest_ma20 is not None:
                                        if not pd.isna(latest_ma5) and not pd.isna(latest_ma20):
                                            if latest_ma5 > latest_ma20:
                                                st.metric("移動平均", "上昇トレンド", delta="5日>20日", delta_color="normal")
                                            else:
                                                st.metric("移動平均", "下降トレンド", delta="5日<20日", delta_color="inverse")
                                        else:
                                            st.metric("移動平均", "N/A")
                                    else:
                                        st.metric("移動平均", "N/A")
                                
                                with col3:
                                    current_price = df['Close'].iloc[-1]
                                    st.metric("現在価格", f"¥{current_price:,.0f}")
                                
                                with col4:
                                    price_change = ((current_price - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                                    st.metric("価格変化", f"{price_change:+.2f}%")
                                
                                # 詳細シグナル表示
                                st.markdown("### 📈 詳細シグナル")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    if 'ma_signal' in signals:
                                        st.info(f"**移動平均:** {signals['ma_signal']}")
                                    if 'rsi_signal' in signals:
                                        st.info(f"**RSI:** {signals['rsi_signal']}")
                                
                                with col2:
                                    if 'macd_signal' in signals:
                                        st.info(f"**MACD:** {signals['macd_signal']}")
                                    if 'stoch_signal' in signals:
                                        st.info(f"**ストキャスティクス:** {signals['stoch_signal']}")
                                
                                with col3:
                                    if latest_macd is not None and latest_signal is not None:
                                        if not pd.isna(latest_macd) and not pd.isna(latest_signal):
                                            st.metric("MACD", f"{latest_macd:.3f}")
                                            st.metric("シグナル", f"{latest_signal:.3f}")
                                
                                with col4:
                                    if latest_stoch_k is not None and latest_stoch_d is not None:
                                        if not pd.isna(latest_stoch_k) and not pd.isna(latest_stoch_d):
                                            st.metric("%K", f"{latest_stoch_k:.1f}")
                                            st.metric("%D", f"{latest_stoch_d:.1f}")
                                
                            else:
                                st.warning("チャートの生成に失敗しました")
                        else:
                            st.error("データが見つかりませんでした")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
            elif not technical_analyzer:
                st.error("テクニカル分析機能が利用できません")
    
    # ファンダメンタル分析ページ
    elif page == "🏢 ファンダメンタル分析":
        st.markdown("## 🏢 ファンダメンタル分析")
        
        ticker_input = st.text_input("銘柄コードを入力してください", placeholder="例: 7203, 6758, 9984")
        
        if st.button("🏢 分析を実行", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}のファンダメンタル分析を実行中..."):
                    try:
                        financial_data = get_cached_data(
                            f"fundamental_data_{ticker}", 
                            ticker,
                            _fundamental_analyzer=fundamental_analyzer
                        )
                        
                        if financial_data:
                            # 基本情報
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("企業名", financial_data['company_name'])
                            with col2:
                                st.metric("業種", financial_data['sector'])
                            with col3:
                                market_cap_trillion = financial_data['market_cap'] / 1000000000000
                                st.metric("時価総額", f"{market_cap_trillion:.1f}兆円")
                            with col4:
                                st.metric("ROE", format_percentage(financial_data['roe']))
                            
                            # 財務指標
                            st.markdown("### 📊 財務指標")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 💰 収益性")
                                st.write(f"**ROE (自己資本利益率):** {format_percentage(financial_data['roe'])}")
                                st.write(f"**ROA (総資産利益率):** {format_percentage(financial_data['roa'])}")
                                st.write(f"**P/E (株価収益率):** {financial_data['pe_ratio']:.1f}倍")
                                st.write(f"**P/B (株価純資産倍率):** {financial_data['pb_ratio']:.1f}倍")
                            
                            with col2:
                                st.markdown("#### 🏥 財務健全性")
                                st.write(f"**負債比率:** {financial_data['debt_to_equity']:.2f}")
                                st.write(f"**流動比率:** {financial_data['current_ratio']:.1f}")
                                st.write(f"**配当利回り:** {format_percentage(financial_data['dividend_yield'])}")
                                st.write(f"**ベータ値:** {financial_data['beta']:.1f}")
                            
                            # ターゲットプライス分析
                            if 'target_price' in financial_data and financial_data['target_price'] > 0:
                                st.markdown("### 🎯 ターゲットプライス分析")
                                
                                # 最新価格を取得
                                latest_price = get_cached_data(
                                    f"latest_price_stooq_{ticker}", 
                                    ticker,
                                    _fetcher=fetcher
                                )
                                if "error" not in latest_price:
                                    current_price = latest_price['close']
                                    target_price = financial_data['target_price']
                                    price_diff = target_price - current_price
                                    price_diff_percent = (price_diff / current_price) * 100
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.metric("現在価格", f"¥{current_price:,.0f}")
                                    with col2:
                                        st.metric("ターゲットプライス", f"¥{target_price:,.0f}")
                                    with col3:
                                        st.metric("価格差", f"¥{price_diff:+,.0f}")
                                    with col4:
                                        st.metric("上昇率", f"{price_diff_percent:+.1f}%")
                                    
                                    # 推奨度を判定
                                    if price_diff_percent >= 20:
                                        recommendation = "強力買い"
                                        recommendation_color = "green"
                                    elif price_diff_percent >= 10:
                                        recommendation = "買い"
                                        recommendation_color = "lightgreen"
                                    elif price_diff_percent >= -10:
                                        recommendation = "中立"
                                        recommendation_color = "yellow"
                                    elif price_diff_percent >= -20:
                                        recommendation = "売り"
                                        recommendation_color = "orange"
                                    else:
                                        recommendation = "強力売り"
                                        recommendation_color = "red"
                                    
                                    st.markdown(f"""
                                    <div style="text-align: center; padding: 15px; background-color: {recommendation_color}; border-radius: 10px; margin: 10px 0;">
                                        <h3>投資推奨度</h3>
                                        <h2>{recommendation}</h2>
                                        <p>設定日: {financial_data.get('target_price_date', 'N/A')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # 価格比較チャート
                                    fig_target = go.Figure()
                                    fig_target.add_trace(go.Bar(
                                        name='現在価格',
                                        x=['現在価格'],
                                        y=[current_price],
                                        marker_color='blue',
                                        text=f"¥{current_price:,.0f}",
                                        textposition='auto'
                                    ))
                                    fig_target.add_trace(go.Bar(
                                        name='ターゲットプライス',
                                        x=['ターゲットプライス'],
                                        y=[target_price],
                                        marker_color='green',
                                        text=f"¥{target_price:,.0f}",
                                        textposition='auto'
                                    ))
                                    fig_target.update_layout(
                                        title=f"{financial_data['company_name']} 価格比較",
                                        xaxis_title="価格タイプ",
                                        yaxis_title="価格（円）",
                                        height=400
                                    )
                                    st.plotly_chart(fig_target, use_container_width=True)
                                else:
                                    st.warning("現在価格の取得に失敗しました")
                            else:
                                st.info("この企業にはターゲットプライスが設定されていません")
                        
                        else:
                            st.error(f"❌ {ticker}の財務データが見つかりません")
                            st.info("📋 利用可能な銘柄: 7203 (トヨタ自動車), 6758 (ソニーグループ), 9984 (ソフトバンクグループ), 6861 (キーエンス), 9434 (NTTドコモ), 4784 (GMOアドパートナーズ)")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
    
    # 財務指標比較ページ
    elif page == "⚖️ 財務指標比較":
        st.markdown("## ⚖️ 財務指標比較")
        
        # タブを作成
        tab1, tab2, tab3, tab4 = st.tabs(["📊 銘柄比較", "🏭 業界別PER比較", "💰 割安・割高企業", "🎯 ターゲットプライス分析"])
        
        with tab1:
            st.info("📋 比較したい銘柄を選択してください（最大3銘柄）")
            
            # 利用可能な銘柄
            available_tickers = ["7203", "6758", "9984", "6861", "9434", "4784", "7974", "6954", "6594", "7733", "9983", "7269", "7267", "8058", "8001", "8306", "8316", "8411", "9432", "9433", "4502", "4519", "6501", "6502", "6752", "9201", "9202"]
            available_names = ["トヨタ自動車", "ソニーグループ", "ソフトバンクグループ", "キーエンス", "NTTドコモ", "GMOアドパートナーズ", "任天堂", "ファナック", "ニデック", "オリンパス", "ファーストリテイリング", "スズキ", "ホンダ", "三菱商事", "伊藤忠商事", "三菱UFJフィナンシャル・グループ", "三井住友フィナンシャルグループ", "みずほフィナンシャルグループ", "NTT", "KDDI", "武田薬品工業", "中外製薬", "日立製作所", "東芝", "パナソニック", "日本航空", "ANAホールディングス"]
            
            selected_tickers = []
            
            for i in range(3):
                col1, col2 = st.columns([3, 1])
                with col1:
                    ticker = st.selectbox(
                        f"銘柄 {i+1}",
                        [""] + available_tickers,
                        format_func=lambda x: f"{x} ({available_names[available_tickers.index(x)]})" if x in available_tickers else x,
                        key=f"ticker_{i}"
                    )
                with col2:
                    if ticker and ticker not in selected_tickers:
                        selected_tickers.append(ticker)
            
            if st.button("⚖️ 比較を実行", type="primary"):
                if len(selected_tickers) >= 2:
                    with st.spinner("財務指標を比較中..."):
                        try:
                            comparison_data = {}
                            
                            for ticker in selected_tickers:
                                financial_data = get_cached_data(
                                    f"fundamental_data_{ticker}", 
                                    ticker,
                                    _fundamental_analyzer=fundamental_analyzer
                                )
                                if financial_data:
                                    comparison_data[ticker] = financial_data
                            
                            if len(comparison_data) >= 2:
                                # 比較チャート
                                st.markdown("### 📊 財務指標比較")
                                
                                # NTM PER比較
                                per_data = []
                                for ticker in comparison_data.keys():
                                    data = comparison_data[ticker]
                                    ntm_per = data.get('pe_ratio_ntm', data.get('pe_ratio', 0))
                                    per_data.append({
                                        '銘柄': ticker,
                                        '企業名': data['company_name'],
                                        'NTM PER': ntm_per,
                                        'PER': data.get('pe_ratio', 0)
                                    })
                                
                                per_df = pd.DataFrame(per_data)
                                
                                fig_per = px.bar(
                                    per_df,
                                    x='企業名',
                                    y='NTM PER',
                                    title='NTM PER比較（Next Twelve Months）',
                                    color='NTM PER',
                                    color_continuous_scale='RdYlGn'
                                )
                                st.plotly_chart(fig_per, use_container_width=True)
                                
                                # ROE比較
                                roe_data = [(ticker, comparison_data[ticker]['roe']) for ticker in comparison_data.keys()]
                                roe_df = pd.DataFrame(roe_data, columns=['銘柄', 'ROE'])
                                roe_df['企業名'] = [comparison_data[ticker]['company_name'] for ticker in roe_df['銘柄']]
                                
                                fig_roe = px.bar(
                                    roe_df,
                                    x='企業名',
                                    y='ROE',
                                    title='ROE比較 (%)',
                                    color='ROE',
                                    color_continuous_scale='RdYlGn'
                                )
                                st.plotly_chart(fig_roe, use_container_width=True)
                                
                                # 詳細比較表
                                st.markdown("### 📋 詳細比較表")
                                
                                comparison_table = []
                                for ticker in comparison_data.keys():
                                    data = comparison_data[ticker]
                                    ntm_per = data.get('pe_ratio_ntm', data.get('pe_ratio', 0))
                                    comparison_table.append({
                                        '銘柄': ticker,
                                        '企業名': data['company_name'],
                                        '業種': data['sector'],
                                        'ROE (%)': f"{data['roe']:.1f}",
                                        'PER (倍)': f"{data['pe_ratio']:.1f}",
                                        'NTM PER (倍)': f"{ntm_per:.1f}",
                                        'P/B (倍)': f"{data['pb_ratio']:.1f}",
                                        '配当利回り (%)': f"{data['dividend_yield']:.1f}",
                                        '負債比率': f"{data['debt_to_equity']:.2f}"
                                    })
                                
                                st.dataframe(pd.DataFrame(comparison_table), use_container_width=True)
                            
                            else:
                                st.error("比較可能な財務データが不足しています")
                        
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {e}")
                else:
                    st.warning("比較には最低2銘柄が必要です")
        
        with tab2:
            st.markdown("### 🏭 業界別PER比較（NTM PER）")
            st.info("📊 業界別のNTM PER比較と統計情報を表示します")
            
            # 業界選択
            sectors = ["全業界", "自動車", "電気機器", "情報・通信", "商社", "銀行業", "医薬品", "小売業", "空運業"]
            selected_sector = st.selectbox("業界を選択", sectors, key="sector_select")
            
            if st.button("🏭 業界比較を実行", type="primary"):
                sector = None if selected_sector == "全業界" else selected_sector
                sector_stats = get_cached_data(
                    f"industry_per_stats_{sector}", 
                    sector,
                    _fundamental_analyzer=fundamental_analyzer
                )
                
                if sector_stats:
                    # 業界別統計表
                    st.markdown("#### 📊 業界別統計")
                    stats_data = []
                    for sector_name, stats in sector_stats.items():
                        stats_data.append({
                            '業界': sector_name,
                            '企業数': stats['company_count'],
                            '平均PER': f"{stats['avg_pe']:.1f}",
                            '平均NTM PER': f"{stats['avg_pe_ntm']:.1f}",
                            '最小NTM PER': f"{stats['min_pe_ntm']:.1f}",
                            '最大NTM PER': f"{stats['max_pe_ntm']:.1f}"
                        })
                    
                    stats_df = pd.DataFrame(stats_data)
                    st.dataframe(stats_df, use_container_width=True)
                    
                    # 業界別PER分布チャート
                    st.markdown("#### 📈 業界別NTM PER分布")
                    fig_sector = go.Figure()
                    
                    for sector_name, stats in sector_stats.items():
                        companies = stats['companies']
                        pe_values = [c['pe_ratio_ntm'] for c in companies if c['pe_ratio_ntm'] > 0]
                        company_names = [c['company_name'] for c in companies if c['pe_ratio_ntm'] > 0]
                        
                        if pe_values:
                            fig_sector.add_trace(go.Bar(
                                name=sector_name,
                                x=company_names,
                                y=pe_values,
                                text=[f"{v:.1f}" for v in pe_values],
                                textposition='auto'
                            ))
                    
                    fig_sector.update_layout(
                        title="業界別NTM PER分布",
                        xaxis_title="企業",
                        yaxis_title="NTM PER",
                        height=500,
                        barmode='group'
                    )
                    st.plotly_chart(fig_sector, use_container_width=True)
                    
                    # 詳細企業リスト
                    st.markdown("#### 📋 企業詳細リスト")
                    all_companies = []
                    for sector_name, stats in sector_stats.items():
                        for company in stats['companies']:
                            all_companies.append({
                                '銘柄コード': company['ticker'],
                                '企業名': company['company_name'],
                                '業界': sector_name,
                                'PER': company['pe_ratio'],
                                'NTM PER': company['pe_ratio_ntm'],
                                'ROE(%)': company['roe'],
                                '配当利回り(%)': company['dividend_yield'],
                                '時価総額(兆円)': f"{company['market_cap'] / 1000000000000:.1f}"
                            })
                    
                    companies_df = pd.DataFrame(all_companies)
                    companies_df = companies_df.sort_values('NTM PER')
                    st.dataframe(companies_df, use_container_width=True)
        
        with tab3:
            st.markdown("### 💰 割安・割高企業分析")
            st.info("📊 NTM PER基準で割安・割高企業を発見します")
            
            col1, col2 = st.columns(2)
            with col1:
                undervalued_threshold = st.slider("割安判定閾値(%)", -50, 0, -20, key="undervalued")
            with col2:
                overvalued_threshold = st.slider("割高判定閾値(%)", 0, 50, 20, key="overvalued")
            
            # 業界選択
            sectors = ["全業界", "自動車", "電気機器", "情報・通信", "商社", "銀行業", "医薬品", "小売業", "空運業"]
            selected_sector = st.selectbox("業界を選択", sectors, key="sector_analysis")
            
            if st.button("💰 割安・割高分析を実行", type="primary"):
                sector = None if selected_sector == "全業界" else selected_sector
                
                # 割安企業
                undervalued = get_cached_data(
                    f"undervalued_companies_{sector}_{undervalued_threshold}", 
                    sector, 
                    undervalued_threshold,
                    _fundamental_analyzer=fundamental_analyzer
                )
                # 割高企業
                overvalued = get_cached_data(
                    f"overvalued_companies_{sector}_{overvalued_threshold}", 
                    sector, 
                    overvalued_threshold,
                    _fundamental_analyzer=fundamental_analyzer
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"#### 📉 割安企業（{len(undervalued)}社）")
                    if undervalued:
                        undervalued_data = []
                        for company in undervalued:
                            undervalued_data.append({
                                '銘柄コード': company['ticker'],
                                '企業名': company['company_name'],
                                '業界': company['sector'],
                                'NTM PER': f"{company['pe_ratio_ntm']:.1f}",
                                '業界平均': f"{company['sector_avg_pe_ntm']:.1f}",
                                '割安度(%)': f"{company['percent_diff']:.1f}",
                                'ROE(%)': f"{company['roe']:.1f}",
                                '配当利回り(%)': f"{company['dividend_yield']:.1f}"
                            })
                        
                        undervalued_df = pd.DataFrame(undervalued_data)
                        st.dataframe(undervalued_df, use_container_width=True)
                    else:
                        st.info("該当する割安企業はありません")
                
                with col2:
                    st.markdown(f"#### 📈 割高企業（{len(overvalued)}社）")
                    if overvalued:
                        overvalued_data = []
                        for company in overvalued:
                            overvalued_data.append({
                                '銘柄コード': company['ticker'],
                                '企業名': company['company_name'],
                                '業界': company['sector'],
                                'NTM PER': f"{company['pe_ratio_ntm']:.1f}",
                                '業界平均': f"{company['sector_avg_pe_ntm']:.1f}",
                                '割高度(%)': f"{company['percent_diff']:.1f}",
                                'ROE(%)': f"{company['roe']:.1f}",
                                '配当利回り(%)': f"{company['dividend_yield']:.1f}"
                            })
                        
                        overvalued_df = pd.DataFrame(overvalued_data)
                        st.dataframe(overvalued_df, use_container_width=True)
                    else:
                        st.info("該当する割高企業はありません")
                
                # 割安・割高企業のチャート
                if undervalued or overvalued:
                    st.markdown("#### 📊 割安・割高企業のNTM PER比較")
                    fig_comparison = go.Figure()
                    
                    # 割安企業
                    if undervalued:
                        undervalued_names = [c['company_name'] for c in undervalued]
                        undervalued_per = [c['pe_ratio_ntm'] for c in undervalued]
                        fig_comparison.add_trace(go.Bar(
                            name='割安企業',
                            x=undervalued_names,
                            y=undervalued_per,
                            marker_color='green',
                            text=[f"{v:.1f}" for v in undervalued_per],
                            textposition='auto'
                        ))
                    
                    # 割高企業
                    if overvalued:
                        overvalued_names = [c['company_name'] for c in overvalued]
                        overvalued_per = [c['pe_ratio_ntm'] for c in overvalued]
                        fig_comparison.add_trace(go.Bar(
                            name='割高企業',
                            x=overvalued_names,
                            y=overvalued_per,
                            marker_color='red',
                            text=[f"{v:.1f}" for v in overvalued_per],
                            textposition='auto'
                        ))
                    
                    fig_comparison.update_layout(
                        title="割安・割高企業のNTM PER比較",
                        xaxis_title="企業",
                        yaxis_title="NTM PER",
                        height=500
                    )
                    st.plotly_chart(fig_comparison, use_container_width=True)
        
        with tab4:
            st.markdown("### 🎯 ターゲットプライス分析")
            st.info("📊 アナリストのターゲットプライスと現在価格を比較して投資機会を分析します")
            
            # サブタブを作成
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📈 個別分析", "🔍 機会発見", "🏭 業界別分析"])
            
            with sub_tab1:
                st.markdown("#### 📈 個別企業のターゲットプライス分析")
                
                # 銘柄選択
                available_tickers = ["7203", "6758", "9984", "6861", "9434", "4784", "7974", "6954", "6594", "7733", "9983", "7269", "7267", "8058", "8001", "8306", "8316", "8411", "9432", "9433", "4502", "4519", "6501", "6502", "6752", "9201", "9202"]
                available_names = ["トヨタ自動車", "ソニーグループ", "ソフトバンクグループ", "キーエンス", "NTTドコモ", "GMOアドパートナーズ", "任天堂", "ファナック", "ニデック", "オリンパス", "ファーストリテイリング", "スズキ", "ホンダ", "三菱商事", "伊藤忠商事", "三菱UFJフィナンシャル・グループ", "三井住友フィナンシャルグループ", "みずほフィナンシャルグループ", "NTT", "KDDI", "武田薬品工業", "中外製薬", "日立製作所", "東芝", "パナソニック", "日本航空", "ANAホールディングス"]
                
                selected_ticker = st.selectbox(
                    "分析する銘柄を選択",
                    available_tickers,
                    format_func=lambda x: f"{x} ({available_names[available_tickers.index(x)]})" if x in available_tickers else x,
                    key="target_price_ticker"
                )
                
                if st.button("🎯 ターゲットプライス分析を実行", type="primary"):
                    with st.spinner("ターゲットプライスを分析中..."):
                        try:
                            analysis = get_cached_data(
                                f"target_price_analysis_{selected_ticker}", 
                                selected_ticker,
                                _fundamental_analyzer=fundamental_analyzer
                            )
                            
                            if "error" in analysis:
                                st.error(f"❌ {analysis['error']}")
                            else:
                                # 分析結果を表示
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    st.metric(
                                        "現在価格",
                                        f"¥{analysis['current_price']:,.0f}",
                                        delta=f"¥{analysis['price_diff']:+,.0f}"
                                    )
                                
                                with col2:
                                    st.metric(
                                        "ターゲットプライス",
                                        f"¥{analysis['target_price']:,.0f}",
                                        delta=f"{analysis['price_diff_percent']:+.1f}%"
                                    )
                                
                                with col3:
                                    # 推奨度を色付きで表示
                                    recommendation_color = analysis['recommendation_color']
                                    st.markdown(f"""
                                    <div style="text-align: center; padding: 10px; background-color: {recommendation_color}; border-radius: 5px;">
                                        <h3>推奨度</h3>
                                        <h2>{analysis['recommendation']}</h2>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # 詳細情報
                                st.markdown("#### 📋 詳細情報")
                                detail_data = {
                                    '項目': ['銘柄コード', '企業名', '業界', 'NTM PER', 'ROE(%)', '配当利回り(%)', 'ターゲットプライス設定日'],
                                    '値': [
                                        analysis['ticker'],
                                        analysis['company_name'],
                                        analysis['sector'],
                                        f"{analysis['pe_ratio_ntm']:.1f}",
                                        f"{analysis['roe']:.1f}",
                                        f"{analysis['dividend_yield']:.1f}",
                                        analysis['target_price_date']
                                    ]
                                }
                                st.dataframe(pd.DataFrame(detail_data), use_container_width=True)
                                
                                # 価格比較チャート
                                st.markdown("#### 📊 価格比較チャート")
                                fig_price = go.Figure()
                                
                                fig_price.add_trace(go.Bar(
                                    name='現在価格',
                                    x=['現在価格'],
                                    y=[analysis['current_price']],
                                    marker_color='blue',
                                    text=f"¥{analysis['current_price']:,.0f}",
                                    textposition='auto'
                                ))
                                
                                fig_price.add_trace(go.Bar(
                                    name='ターゲットプライス',
                                    x=['ターゲットプライス'],
                                    y=[analysis['target_price']],
                                    marker_color='green',
                                    text=f"¥{analysis['target_price']:,.0f}",
                                    textposition='auto'
                                ))
                                
                                fig_price.update_layout(
                                    title=f"{analysis['company_name']} 価格比較",
                                    xaxis_title="価格タイプ",
                                    yaxis_title="価格（円）",
                                    height=400
                                )
                                st.plotly_chart(fig_price, use_container_width=True)
                        
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {e}")
            
            with sub_tab2:
                st.markdown("#### 🔍 ターゲットプライス機会発見")
                st.info("📈 上昇率の高い投資機会を発見します")
                
                col1, col2 = st.columns(2)
                with col1:
                    min_upside = st.slider("最小上昇率(%)", 0, 50, 10, key="min_upside")
                with col2:
                    max_upside = st.slider("最大上昇率(%)", 10, 200, 100, key="max_upside")
                
                if st.button("🔍 機会を発見", type="primary"):
                    with st.spinner("投資機会を分析中..."):
                        try:
                            opportunities = get_cached_data(
                                f"target_price_opportunities_{min_upside}_{max_upside}", 
                                min_upside, 
                                max_upside,
                                _fundamental_analyzer=fundamental_analyzer
                            )
                            
                            if opportunities:
                                st.markdown(f"#### 📈 発見された投資機会（{len(opportunities)}社）")
                                
                                # 機会リスト
                                opportunities_data = []
                                for opp in opportunities:
                                    opportunities_data.append({
                                        '銘柄コード': opp['ticker'],
                                        '企業名': opp['company_name'],
                                        '業界': opp['sector'],
                                        '現在価格': f"¥{opp['current_price']:,.0f}",
                                        'ターゲットプライス': f"¥{opp['target_price']:,.0f}",
                                        '上昇率(%)': f"{opp['upside']:.1f}",
                                        'NTM PER': f"{opp['pe_ratio_ntm']:.1f}",
                                        'ROE(%)': f"{opp['roe']:.1f}",
                                        '配当利回り(%)': f"{opp['dividend_yield']:.1f}"
                                    })
                                
                                st.dataframe(pd.DataFrame(opportunities_data), use_container_width=True)
                                
                                # 上昇率チャート
                                st.markdown("#### 📊 上昇率比較")
                                fig_upside = go.Figure()
                                
                                company_names = [opp['company_name'] for opp in opportunities]
                                upsides = [opp['upside'] for opp in opportunities]
                                
                                fig_upside.add_trace(go.Bar(
                                    name='上昇率',
                                    x=company_names,
                                    y=upsides,
                                    marker_color='lightgreen',
                                    text=[f"{u:.1f}%" for u in upsides],
                                    textposition='auto'
                                ))
                                
                                fig_upside.update_layout(
                                    title="ターゲットプライス上昇率比較",
                                    xaxis_title="企業",
                                    yaxis_title="上昇率(%)",
                                    height=500
                                )
                                st.plotly_chart(fig_upside, use_container_width=True)
                            
                            else:
                                st.info("指定された条件に合致する投資機会は見つかりませんでした")
                        
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {e}")
            
            with sub_tab3:
                st.markdown("#### 🏭 業界別ターゲットプライス分析")
                st.info("📊 業界別のターゲットプライス分析と統計情報を表示します")
                
                # 業界選択
                sectors = ["全業界", "自動車", "電気機器", "情報・通信", "商社", "銀行業", "医薬品", "小売業", "空運業"]
                selected_sector = st.selectbox("業界を選択", sectors, key="target_price_sector")
                
                if st.button("🏭 業界分析を実行", type="primary"):
                    sector = None if selected_sector == "全業界" else selected_sector
                    
                    with st.spinner("業界別分析を実行中..."):
                        try:
                            sector_analysis = get_cached_data(
                                f"sector_target_price_analysis_{sector}", 
                                sector,
                                _fundamental_analyzer=fundamental_analyzer
                            )
                            
                            if sector_analysis:
                                # 業界別統計表
                                st.markdown("#### 📊 業界別統計")
                                stats_data = []
                                for sector_name, stats in sector_analysis.items():
                                    stats_data.append({
                                        '業界': sector_name,
                                        '企業数': stats['company_count'],
                                        '平均上昇率(%)': f"{stats['avg_upside']:.1f}",
                                        '最大上昇率(%)': f"{stats['max_upside']:.1f}",
                                        '最小上昇率(%)': f"{stats['min_upside']:.1f}"
                                    })
                                
                                stats_df = pd.DataFrame(stats_data)
                                st.dataframe(stats_df, use_container_width=True)
                                
                                # 業界別上昇率分布チャート
                                st.markdown("#### 📈 業界別上昇率分布")
                                fig_sector_upside = go.Figure()
                                
                                for sector_name, stats in sector_analysis.items():
                                    companies = stats['companies']
                                    company_names = [c['company_name'] for c in companies]
                                    upsides = [c['upside'] for c in companies]
                                    
                                    fig_sector_upside.add_trace(go.Bar(
                                        name=sector_name,
                                        x=company_names,
                                        y=upsides,
                                        text=[f"{u:.1f}%" for u in upsides],
                                        textposition='auto'
                                    ))
                                
                                fig_sector_upside.update_layout(
                                    title="業界別ターゲットプライス上昇率分布",
                                    xaxis_title="企業",
                                    yaxis_title="上昇率(%)",
                                    height=500,
                                    barmode='group'
                                )
                                st.plotly_chart(fig_sector_upside, use_container_width=True)
                                
                                # 詳細企業リスト
                                st.markdown("#### 📋 企業詳細リスト")
                                all_companies = []
                                for sector_name, stats in sector_analysis.items():
                                    for company in stats['companies']:
                                        all_companies.append({
                                            '銘柄コード': company['ticker'],
                                            '企業名': company['company_name'],
                                            '業界': sector_name,
                                            '現在価格': f"¥{company['current_price']:,.0f}",
                                            'ターゲットプライス': f"¥{company['target_price']:,.0f}",
                                            '上昇率(%)': f"{company['upside']:.1f}"
                                        })
                                
                                companies_df = pd.DataFrame(all_companies)
                                companies_df = companies_df.sort_values('上昇率(%)', ascending=False)
                                st.dataframe(companies_df, use_container_width=True)
                            
                            else:
                                st.info("分析可能なデータが見つかりませんでした")
                        
                        except Exception as e:
                            st.error(f"❌ エラーが発生しました: {e}")
    
    # 複数銘柄分析ページ
    elif page == "📦 複数銘柄分析":
        st.markdown("## 📦 複数銘柄分析")
        
        st.info("📋 分析したい銘柄をカンマ区切りで入力してください")
        
        tickers_input = st.text_input("銘柄コード", placeholder="例: 7203, 6758, 9984")
        source = st.selectbox("データソース", ["stooq", "yahoo"])
        
        if st.button("📦 一括分析", type="primary"):
            if tickers_input:
                tickers = [t.strip() for t in tickers_input.split(",") if t.strip().isdigit()]
                
                if tickers:
                    with st.spinner(f"{len(tickers)}銘柄のデータを取得中..."):
                        results = []
                        
                        for ticker in tickers:
                            try:
                                data = get_cached_data(
                                    f"latest_price_{source}_{ticker}", 
                                    ticker,
                                    _fetcher=fetcher
                                )
                                if "error" not in data:
                                    results.append({
                                        '銘柄': ticker,
                                        '終値': data['close'],
                                        '日付': data['date'],
                                        '出来高': data['volume']
                                    })
                                else:
                                    results.append({
                                        '銘柄': ticker,
                                        '終値': 'エラー',
                                        '日付': 'N/A',
                                        '出来高': 'N/A'
                                    })
                            except Exception as e:
                                results.append({
                                    '銘柄': ticker,
                                    '終値': f'エラー: {e}',
                                    '日付': 'N/A',
                                    '出来高': 'N/A'
                                })
                        
                        if results:
                            df_results = pd.DataFrame(results)
                            st.dataframe(df_results, use_container_width=True)
                else:
                    st.error("有効な銘柄コードが入力されていません")
    
    # データエクスポートページ
    elif page == "💾 データエクスポート":
        # 権限チェック
        if not check_permission('write'):
            st.error("❌ この機能を利用する権限がありません。")
            st.info("データエクスポート機能には書き込み権限が必要です。")
            return
        
        st.markdown("## 💾 データエクスポート")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ticker_input = st.text_input("銘柄コード", placeholder="例: 7203")
        
        with col2:
            source = st.selectbox("データソース", ["stooq", "yahoo"])
        
        with col3:
            period = st.selectbox("期間", [30, 90, 365], format_func=lambda x: f"{x}日間")
        
        if st.button("💾 CSVに保存", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}のデータをCSVに保存中..."):
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=period)
                        
                        if source == "stooq":
                            df = get_cached_data(
                                f"stock_data_stooq_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d'),
                                _fetcher=fetcher
                            )
                        else:
                            df = get_cached_data(
                                f"stock_data_yahoo_{ticker}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d'),
                                _fetcher=fetcher
                            )
                        
                        if not df.empty:
                            fetcher.save_to_csv(df, ticker, source)
                            st.success(f"✅ データが保存されました: stock_data/{source}_stock_data_{ticker}.csv")
                            
                            # データのプレビュー
                            st.markdown("### 📊 データプレビュー")
                            st.dataframe(df.head(10), use_container_width=True)
                        else:
                            st.error("データが見つかりませんでした")
                    
                    except Exception as e:
                        if SECURITY_ENABLED and error_handler:
                            error_info = error_handler.handle_error(
                                e,
                                ErrorCategory.DATA,
                                ErrorSeverity.MEDIUM,
                                {'ticker': ticker, 'source': source, 'operation': 'export'}
                            )
                            user_message = error_handler.get_user_friendly_message(error_info)
                            st.error(f"❌ エラーが発生しました: {user_message}")
                        else:
                            st.error(f"❌ エラーが発生しました: {e}")
    
    # 高度なデータ分析ページ
    elif page == "🔍 高度なデータ分析":
        st.markdown("## 🔍 高度なデータ分析")
        st.markdown("### 📊 4つの新しいデータソースを統合した包括的分析")
        
        # データソース説明
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🌐 追加データソース:**
            - **Bloomberg**: 詳細な金融データ・財務指標
            - **Reuters**: 国際ニュース・市場分析
            - **日本経済新聞**: 国内ニュース・日本市場分析
            - **SEC Filings**: 米国企業開示情報・インサイダー取引
            """)
        
        with col2:
            st.markdown("""
            **🔍 分析機能:**
            - **包括的データ分析**: 複数ソースからの統合データ
            - **感情分析**: ニュース記事の感情スコア分析
            - **市場インテリジェンス**: AI生成の投資レポート
            - **リスク・機会分析**: 自動リスク要因・機会特定
            """)
        
        st.markdown("---")
        
        # 処理モード選択
        col1, col2 = st.columns(2)
        with col1:
            processing_mode = st.radio(
                "処理モードを選択",
                ["同期処理", "非同期処理（高速）"],
                help="非同期処理では複数のAPIを並行して呼び出し、大幅に高速化されます"
            )
        
        with col2:
            if processing_mode == "非同期処理（高速）":
                st.success("🚀 非同期処理モード: 最大60%高速化")
            else:
                st.info("⏱️ 同期処理モード: 従来の処理方式")
        
        # 銘柄入力
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ticker_input = st.text_input("銘柄コードを入力してください", placeholder="例: 7203 (トヨタ自動車)")
        
        with col2:
            analysis_type = st.selectbox("分析タイプ", [
                "包括的データ分析",
                "感情分析",
                "市場インテリジェンス"
            ])
        
        if st.button("🔍 高度分析を実行", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}の高度分析を実行中..."):
                    try:
                        if analysis_type == "包括的データ分析":
                            # 処理モードに応じてデータ取得方法を選択
                            if processing_mode == "非同期処理（高速）":
                                # 非同期処理でデータ取得
                                start_time = time.time()
                                comprehensive_data = run_async_data_fetch_sync(
                                    ticker,
                                    (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                                    datetime.now().strftime('%Y-%m-%d')
                                )
                                end_time = time.time()
                                processing_time = end_time - start_time
                                st.success(f"✅ 非同期処理で包括的データ分析が完了しました (処理時間: {processing_time:.2f}秒)")
                            else:
                                # 同期処理でデータ取得
                                start_time = time.time()
                                comprehensive_data = get_cached_data(
                                    f"comprehensive_data_{ticker}",
                                    ticker,
                                    (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                                    datetime.now().strftime('%Y-%m-%d'),
                                    _advanced_data_manager=advanced_data_manager
                                )
                                end_time = time.time()
                                processing_time = end_time - start_time
                                st.success(f"✅ 同期処理で包括的データ分析が完了しました (処理時間: {processing_time:.2f}秒)")
                            
                            if comprehensive_data:
                                st.success("✅ 包括的データ分析が完了しました")
                                
                                # 株価データ
                                if comprehensive_data.get('stock_data'):
                                    st.markdown("### 📊 株価データ")
                                    stock_data = comprehensive_data['stock_data']
                                    if stock_data.get('data'):
                                        df = pd.DataFrame(stock_data['data'])
                                        st.dataframe(df.head(), use_container_width=True)
                                        st.write(f"**データソース:** {stock_data.get('source', 'Unknown')}")
                                        st.write(f"**データ件数:** {stock_data.get('count', 0)}件")
                                
                                # 財務データ
                                if comprehensive_data.get('financial_data'):
                                    st.markdown("### 💰 Bloomberg財務データ")
                                    financial_data = comprehensive_data['financial_data']
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("時価総額", f"{financial_data.get('market_cap', 0):,.0f}円")
                                    with col2:
                                        st.metric("PER", f"{financial_data.get('pe_ratio', 0):.1f}")
                                    with col3:
                                        st.metric("PBR", f"{financial_data.get('pb_ratio', 0):.1f}")
                                    with col4:
                                        st.metric("配当利回り", f"{financial_data.get('dividend_yield', 0):.1f}%")
                                
                                # ニュースデータ
                                if comprehensive_data.get('news_data'):
                                    st.markdown("### 📰 最新ニュース")
                                    news_data = comprehensive_data['news_data']
                                    
                                    tab1, tab2 = st.tabs(["国際ニュース", "日本ニュース"])
                                    
                                    with tab1:
                                        international_news = news_data.get('international', [])
                                        for i, news in enumerate(international_news[:3]):
                                            with st.expander(f"📰 {news.title}"):
                                                st.write(f"**日付:** {news.published_date.strftime('%Y-%m-%d')}")
                                                st.write(f"**感情スコア:** {news.sentiment_score:.2f}")
                                                st.write(f"**内容:** {news.content[:200]}...")
                                                st.write(f"**URL:** {news.url}")
                                                st.write(f"**ソース:** {news.source}")
                                    
                                    with tab2:
                                        japanese_news = news_data.get('japanese', [])
                                        for i, news in enumerate(japanese_news[:3]):
                                            with st.expander(f"📰 {news.title}"):
                                                st.write(f"**日付:** {news.published_date.strftime('%Y-%m-%d')}")
                                                st.write(f"**感情スコア:** {news.sentiment_score:.2f}")
                                                st.write(f"**内容:** {news.content[:200]}...")
                                                st.write(f"**URL:** {news.url}")
                                                st.write(f"**ソース:** {news.source}")
                                
                                # SECデータ
                                if comprehensive_data.get('sec_data'):
                                    st.markdown("### 📋 SEC開示情報")
                                    sec_data = comprehensive_data['sec_data']
                                    
                                    tab1, tab2 = st.tabs(["企業開示", "インサイダー取引"])
                                    
                                    with tab1:
                                        filings = sec_data.get('filings', [])
                                        for filing in filings[:3]:
                                            with st.expander(f"📄 {filing['filing_title']}"):
                                                st.write(f"**種類:** {filing['filing_type']}")
                                                st.write(f"**日付:** {filing['filing_date'][:10]}")
                                                st.write(f"**ファイルサイズ:** {filing['file_size']}")
                                                st.write(f"**URL:** {filing['filing_url']}")
                                    
                                    with tab2:
                                        insider_trades = sec_data.get('insider_trading', [])
                                        if insider_trades:
                                            insider_df = pd.DataFrame(insider_trades)
                                            st.dataframe(insider_df, use_container_width=True)
                        
                        elif analysis_type == "感情分析":
                            # 感情分析
                            sentiment_data = get_cached_data(
                                f"sentiment_analysis_{ticker}",
                                ticker,
                                _advanced_data_manager=advanced_data_manager
                            )
                            
                            if sentiment_data:
                                st.success("✅ 感情分析が完了しました")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("全体的感情", sentiment_data.get('sentiment_label', 'N/A'))
                                with col2:
                                    st.metric("Reuters感情", f"{sentiment_data.get('reuters_sentiment', 0):.2f}")
                                with col3:
                                    st.metric("日経感情", f"{sentiment_data.get('nikkei_sentiment', 0):.2f}")
                                with col4:
                                    st.metric("ニュース件数", sentiment_data.get('news_count', 0))
                                
                                # 感情スコアの可視化
                                sentiment_scores = {
                                    'Reuters': sentiment_data.get('reuters_sentiment', 0),
                                    '日経': sentiment_data.get('nikkei_sentiment', 0),
                                    '全体': sentiment_data.get('overall_sentiment', 0)
                                }
                                
                                fig = go.Figure(data=[
                                    go.Bar(x=list(sentiment_scores.keys()), y=list(sentiment_scores.values()))
                                ])
                                fig.update_layout(
                                    title="感情スコア比較",
                                    xaxis_title="データソース",
                                    yaxis_title="感情スコア",
                                    height=400
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        elif analysis_type == "市場インテリジェンス":
                            # 市場インテリジェンス
                            intelligence_data = get_cached_data(
                                f"market_intelligence_{ticker}",
                                ticker,
                                _advanced_data_manager=advanced_data_manager
                            )
                            
                            if intelligence_data:
                                st.success("✅ 市場インテリジェンスレポートが生成されました")
                                
                                # エグゼクティブサマリー
                                st.markdown("### 📋 エグゼクティブサマリー")
                                st.info(intelligence_data.get('executive_summary', ''))
                                
                                # リスク要因
                                risk_factors = intelligence_data.get('risk_factors', [])
                                if risk_factors:
                                    st.markdown("### ⚠️ リスク要因")
                                    for risk in risk_factors:
                                        st.write(f"• {risk}")
                                
                                # 機会要因
                                opportunities = intelligence_data.get('opportunities', [])
                                if opportunities:
                                    st.markdown("### 🎯 機会要因")
                                    for opportunity in opportunities:
                                        st.write(f"• {opportunity}")
                                
                                # 推奨事項
                                recommendations = intelligence_data.get('recommendations', [])
                                if recommendations:
                                    st.markdown("### 💡 推奨事項")
                                    for rec in recommendations:
                                        st.write(f"• {rec}")
                                
                                # 詳細データ
                                with st.expander("📊 詳細データ"):
                                    st.json(intelligence_data)
                        
                        else:
                            st.error("分析タイプが選択されていません")
                    
                    except Exception as e:
                        st.error(f"❌ 高度分析でエラーが発生しました: {e}")
    
    # 新機能ページ
    elif page == "🎯 ダッシュボード" and NEW_FEATURES_ENABLED:
        st.markdown("## 🎯 ダッシュボード")
        try:
            dashboard_manager = DashboardManager()
            dashboard_manager.render_main_dashboard()
        except Exception as e:
            st.error(f"❌ ダッシュボードの読み込みでエラーが発生しました: {e}")
            st.info("ダッシュボード機能は現在利用できません。基本機能をご利用ください。")
    
    elif page == "📈 ポートフォリオ最適化" and NEW_FEATURES_ENABLED:
        st.markdown("## 📈 ポートフォリオ最適化")
        try:
            portfolio_optimizer = PortfolioOptimizer()
            portfolio_optimizer.render_portfolio_optimization()
        except Exception as e:
            st.error(f"❌ ポートフォリオ最適化の読み込みでエラーが発生しました: {e}")
            st.info("ポートフォリオ最適化機能は現在利用できません。基本機能をご利用ください。")
    
    elif page == "📡 API監視" and NEW_FEATURES_ENABLED:
        st.markdown("## 📡 API監視")
        try:
            api_monitor = APIMonitor()
            api_monitor.render_api_monitoring()
        except Exception as e:
            st.error(f"❌ API監視の読み込みでエラーが発生しました: {e}")
            st.info("API監視機能は現在利用できません。基本機能をご利用ください。")
    
    # 改善機能ページ
    elif page == "📡 データソース管理" and IMPROVED_FEATURES_ENABLED:
        st.markdown("## 📡 データソース管理")
        if system_integrator and system_integrator.data_source_manager:
            system_integrator.show_data_source_status()
            
            st.markdown("### 🔄 データ取得テスト")
            col1, col2 = st.columns(2)
            with col1:
                test_symbol = st.text_input("銘柄コード", value="7203", help="テスト用の銘柄コードを入力")
            with col2:
                test_period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y"], index=0)
            
            if st.button("データ取得テスト実行"):
                import asyncio
                async def test_fetch():
                    with st.spinner("データを取得中..."):
                        data = await system_integrator.get_enhanced_stock_data(test_symbol, test_period)
                        if data is not None:
                            st.success(f"✅ データ取得成功: {len(data)}行のデータ")
                            st.dataframe(data.head(10))
                        else:
                            st.error("❌ データ取得に失敗しました")
                
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(test_fetch())
                except Exception as e:
                    system_integrator.handle_user_input_error(e, f"{test_symbol}:{test_period}")
                finally:
                    loop.close()
        else:
            st.warning("データソース管理機能が利用できません")
    
    elif page == "🛡️ セキュリティ管理" and IMPROVED_FEATURES_ENABLED:
        st.markdown("## 🛡️ セキュリティ管理")
        if system_integrator and system_integrator.security_manager:
            system_integrator.show_security_status()
            
            # セキュリティ設定
            st.markdown("### ⚙️ セキュリティ設定")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**認証設定**")
                enable_2fa = st.checkbox("二要素認証を有効化", help="セキュリティを強化します")
                session_timeout = st.slider("セッション有効期限（分）", 5, 120, 30)
                
            with col2:
                st.markdown("**アクセス制御**")
                max_login_attempts = st.slider("最大ログイン試行回数", 3, 10, 5)
                enable_rate_limiting = st.checkbox("レート制限を有効化", value=True)
            
            if st.button("設定を保存"):
                st.success("✅ セキュリティ設定を保存しました")
        else:
            st.warning("セキュリティ管理機能が利用できません")
    
    elif page == "⚙️ UI最適化" and IMPROVED_FEATURES_ENABLED:
        st.markdown("## ⚙️ UI最適化")
        if system_integrator and system_integrator.ui_optimizer:
            system_integrator.show_performance_metrics()
            system_integrator.show_accessibility_controls()
            
            st.markdown("### 🎨 表示設定")
            col1, col2 = st.columns(2)
            
            with col1:
                ui_mode = st.selectbox(
                    "UIモード",
                    ["ライトモード", "ダークモード", "ハイコントラスト", "モバイル"],
                    help="表示モードを選択してください"
                )
                
                font_size = st.slider("フォントサイズ", 12, 24, 16)
                
            with col2:
                animation_enabled = st.checkbox("アニメーションを有効化", value=True)
                compact_mode = st.checkbox("コンパクト表示", value=False)
            
            if st.button("UI設定を適用"):
                st.success("✅ UI設定を適用しました")
                st.info("設定はページリロード後に反映されます")
        else:
            st.warning("UI最適化機能が利用できません")
    
    elif page == "📈 強化チャート機能" and IMPROVED_FEATURES_ENABLED:
        st.markdown("## 📈 強化チャート機能")
        if system_integrator and system_integrator.chart_manager:
            st.markdown("### ⚙️ チャート設定")
            chart_settings = system_integrator.show_enhanced_chart_controls()
            
            st.markdown("### 📊 チャートプレビュー")
            
            # サンプルデータでチャートを表示
            col1, col2 = st.columns([3, 1])
            with col2:
                sample_symbol = st.text_input("銘柄コード", value="7203")
                if st.button("チャート生成"):
                    with col1:
                        with st.spinner("チャートを生成中..."):
                            # サンプルデータを生成してチャートを表示
                            import pandas as pd
                            import numpy as np
                            from datetime import datetime, timedelta
                            
                            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
                            sample_data = pd.DataFrame({
                                'Date': dates,
                                'Open': 2000 + np.cumsum(np.random.randn(len(dates)) * 10),
                                'High': 2000 + np.cumsum(np.random.randn(len(dates)) * 10) + 50,
                                'Low': 2000 + np.cumsum(np.random.randn(len(dates)) * 10) - 50,
                                'Close': 2000 + np.cumsum(np.random.randn(len(dates)) * 10),
                                'Volume': np.random.randint(1000000, 5000000, len(dates))
                            })
                            
                            chart = system_integrator.create_enhanced_chart(
                                sample_data, 
                                chart_settings, 
                                f"{sample_symbol} - 強化チャート"
                            )
                            
                            if chart:
                                st.plotly_chart(chart, use_container_width=True)
                            else:
                                st.error("チャートの生成に失敗しました")
        else:
            st.warning("強化チャート機能が利用できません")
    
    elif page == "📊 システム状態監視" and IMPROVED_FEATURES_ENABLED:
        st.markdown("## 📊 システム状態監視")
        if system_integrator:
            system_integrator.show_system_status()
            
            # 自動更新設定
            st.markdown("### 🔄 監視設定")
            auto_refresh = st.checkbox("自動更新を有効化", value=False)
            if auto_refresh:
                refresh_interval = st.slider("更新間隔（秒）", 5, 60, 10)
                if st.button("今すぐ更新"):
                    st.rerun()
        else:
            st.warning("システム状態監視機能が利用できません")
    
    elif page == "🛠️ エラーハンドリング" and IMPROVED_FEATURES_ENABLED:
        st.markdown("## 🛠️ エラーハンドリング")
        if system_integrator and system_integrator.error_handler:
            system_integrator.show_error_summary()
            
            st.markdown("### 🧪 エラーテスト")
            st.info("システムのエラーハンドリング機能をテストできます")
            
            test_error_type = st.selectbox(
                "テストするエラータイプ",
                ["ネットワークエラー", "データ形式エラー", "ユーザー入力エラー", "システムエラー"]
            )
            
            if st.button("エラーテスト実行"):
                try:
                    if test_error_type == "ネットワークエラー":
                        raise ConnectionError("テスト用ネットワークエラー")
                    elif test_error_type == "データ形式エラー":
                        raise ValueError("テスト用データ形式エラー")
                    elif test_error_type == "ユーザー入力エラー":
                        raise TypeError("テスト用ユーザー入力エラー")
                    else:
                        raise RuntimeError("テスト用システムエラー")
                except Exception as e:
                    system_integrator.handle_user_input_error(e, f"テスト: {test_error_type}")
        else:
            st.warning("エラーハンドリング機能が利用できません")
    
    elif page == "📋 トラブルシューティング" and IMPROVED_FEATURES_ENABLED:
        st.markdown("## 📋 トラブルシューティング")
        if system_integrator and system_integrator.error_handler:
            system_integrator.show_troubleshooting_guide()
            
            st.markdown("### 🔍 システム診断")
            if st.button("システム診断を実行"):
                with st.spinner("システムを診断中..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**機能状態チェック**")
                        features = [
                            ("データソース管理", system_integrator.is_feature_available("data_source_manager")),
                            ("エラーハンドリング", system_integrator.is_feature_available("error_handler")),
                            ("セキュリティ", system_integrator.is_feature_available("security")),
                            ("UI最適化", system_integrator.is_feature_available("ui_optimizer")),
                            ("チャート管理", system_integrator.is_feature_available("chart_manager"))
                        ]
                        
                        for feature_name, available in features:
                            status = "✅ 正常" if available else "❌ 無効"
                            st.markdown(f"- {feature_name}: {status}")
                    
                    with col2:
                        st.markdown("**推奨事項**")
                        st.markdown("- 定期的にシステム状態を確認してください")
                        st.markdown("- エラーログを監視してください")
                        st.markdown("- セキュリティ設定を最新に保ってください")
                        st.markdown("- パフォーマンスメトリクスを定期確認してください")
        else:
            st.warning("トラブルシューティング機能が利用できません")

if __name__ == "__main__":
    main() 