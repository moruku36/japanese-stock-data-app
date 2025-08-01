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
from typing import Dict, Any, List

# プロジェクトのモジュールをインポート
try:
    from stock_data_fetcher import JapaneseStockDataFetcher
    from stock_analyzer import StockAnalyzer
    from company_search import CompanySearch
    from fundamental_analyzer import FundamentalAnalyzer
    from advanced_data_sources import AdvancedDataManager
    from async_data_sources import run_async_data_fetch_sync
    from real_time_updater import RealTimeDataManager, start_real_time_services, stop_real_time_services
    from config import config
    from utils import (
        format_currency, format_number, PerformanceMonitor, 
        performance_monitor, MemoryOptimizer, OptimizedCache
    )
except ImportError as e:
    st.error(f"モジュールのインポートエラー: {e}")
    st.info("必要なモジュールがインストールされていない可能性があります。")
    st.stop()

# ページ設定
st.set_page_config(
    page_title="🇯🇵 日本の株価データ分析システム",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# グローバルキャッシュ
@st.cache_resource
def get_global_cache():
    """グローバルキャッシュを取得"""
    return OptimizedCache(max_size=500, ttl_hours=6)

@st.cache_resource
def initialize_system():
    """システムの初期化（キャッシュ付き・最適化版）"""
    try:
        # パフォーマンス監視開始
        monitor = PerformanceMonitor()
        monitor.start()
        
        # システム初期化
        fetcher = JapaneseStockDataFetcher(max_workers=3)
        analyzer = StockAnalyzer(fetcher)
        company_searcher = CompanySearch()
        fundamental_analyzer = FundamentalAnalyzer(fetcher)
        advanced_data_manager = AdvancedDataManager()
        
        # リアルタイムデータ管理を初期化
        real_time_manager = RealTimeDataManager()
        
        # パフォーマンス監視終了
        monitor.end("System Initialization")
        
        return fetcher, analyzer, company_searcher, fundamental_analyzer, advanced_data_manager, real_time_manager
    except ImportError as e:
        st.error(f"モジュールのインポートエラー: {e}")
        st.info("必要なモジュールがインストールされていません。")
        return None, None, None, None, None, None
    except Exception as e:
        st.error(f"システムの初期化に失敗しました: {e}")
        st.info("システムの初期化中にエラーが発生しました。")
        return None, None, None, None, None, None

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

@performance_monitor
def create_stock_price_chart(df, ticker_symbol):
    """株価チャートを作成（最適化版）"""
    if df.empty:
        return None
    
    # データフレームの最適化
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

def main():
    """メイン関数（最適化版）"""
    try:
        # ヘッダー
        st.title("🇯🇵 日本の株価データ分析システム")
        
        # システム初期化
        with st.spinner('システムを初期化中...'):
            fetcher, analyzer, company_searcher, fundamental_analyzer, advanced_data_manager, real_time_manager = initialize_system()
        
        if not all([fetcher, analyzer, company_searcher, fundamental_analyzer, advanced_data_manager, real_time_manager]):
            st.error("システムの初期化に失敗しました。")
            st.info("ページを再読み込みするか、しばらく時間をおいてから再度お試しください。")
            return
    except Exception as e:
        st.error(f"アプリケーションの起動に失敗しました: {e}")
        st.info("エラーが解決しない場合は、管理者にお問い合わせください。")
        return
    
    # パフォーマンス情報は内部で監視（UIには表示しない）
    memory_usage = MemoryOptimizer.get_memory_usage()
    # ログに記録（デバッグ用）
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"メモリ使用量: {memory_usage['rss_mb']:.1f}MB, 使用率: {memory_usage['percent']:.1f}%")
    
    # サイドバー
    st.sidebar.title("📊 機能選択")
    
    # 機能選択（全項目表示）
    page = st.sidebar.radio(
        "機能を選択してください",
        [
            "🏠 ホーム",
            "📈 最新株価",
            "⚡ リアルタイム監視",
            "📊 株価チャート",
            "🏢 ファンダメンタル分析",
            "⚖️ 財務指標比較",
            "📦 複数銘柄分析",
            "🔍 高度なデータ分析",
            "💾 データエクスポート"
        ],
        index=0
    )
    
    # ホームページ
    if page == "🏠 ホーム":
        st.markdown("## 🏠 ホーム")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 登録企業数", len(company_searcher.companies))
        
        with col2:
            st.metric("🏢 ファンダメンタル分析対応", len(fundamental_analyzer.financial_data))
        
        with col3:
            st.metric("🌐 データソース", 6)
        
        # リアルタイム機能の紹介
        st.markdown("---")
        st.markdown("## ⚡ 新機能: リアルタイム監視システム")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🚀 リアルタイム機能:**
            - **即座のデータ更新**: WebSocket通信
            - **プッシュ通知**: 重要な価格変動
            - **自動監視**: 30秒ごとの更新
            - **アラート機能**: カスタマイズ可能な閾値
            """)
        
        with col2:
            st.markdown("""
            **📊 監視対象銘柄:**
            - **9984**: ソフトバンクG
            - **9433**: KDDI
            - **7203**: トヨタ自動車
            - **6758**: ソニーG
            - **6861**: キーエンス
            """)
        
        if st.button("⚡ リアルタイム監視を試す", type="primary"):
            st.session_state.page = "⚡ リアルタイム監視"
            st.rerun()
        
        st.markdown("---")
        
        # 主要企業の一覧（最適化版）
        st.markdown("## ⭐ 主要企業")
        
        # キャッシュ付きで主要企業を取得
        popular_companies = get_cached_data(
            "popular_companies", 
            10,
            _company_searcher=company_searcher
        )
        
        cols = st.columns(2)
        for i, company in enumerate(popular_companies):
            col_idx = i % 2
            with cols[col_idx]:
                with st.expander(f"{company['name']} ({company['code']})"):
                    st.write(f"**業種:** {company['sector']}")
                    st.write(f"**市場:** {company['market']}")
                    
                    # 最新株価を取得（キャッシュ付き）
                    try:
                        price_data = get_cached_data(
                            f"latest_price_stooq_{company['code']}", 
                            company['code'],
                            _fetcher=fetcher
                        )
                        if "error" not in price_data:
                            st.write(f"**現在値:** {format_currency_web(price_data['close'])}")
                            st.write(f"**日付:** {price_data['date']}")
                        else:
                            st.write("**現在値:** データ取得エラー")
                    except:
                        st.write("**現在値:** データ取得エラー")
    
    # 最新株価ページ
    elif page == "📈 最新株価":
        st.markdown("## 📈 最新株価取得")
        
        # 銘柄コード入力
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ticker_input = st.text_input("銘柄コードを入力してください", placeholder="例: 7203, 6758, 9984")
        
        with col2:
            source = st.selectbox("データソース", ["stooq", "yahoo", "both"])
        
        if st.button("📊 株価を取得", type="primary"):
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
        st.markdown("## ⚡ リアルタイム株価監視")
        st.markdown("### 🚀 リアルタイムデータ更新システム")
        
        # リアルタイム機能の説明
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔴 リアルタイム機能:**
            - **WebSocket通信**: 即座のデータ更新
            - **プッシュ通知**: 重要な価格変動の通知
            - **自動更新**: 30秒ごとのデータ更新
            - **主要銘柄監視**: 9984, 9433, 7203, 6758, 6861
            """)
        
        with col2:
            st.markdown("""
            **📊 監視機能:**
            - **価格変動**: リアルタイム価格追跡
            - **ボラティリティ**: 価格変動率の監視
            - **出来高**: 取引量の変化
            - **市場状況**: 取引時間の表示
            """)
        
        st.markdown("---")
        
        # リアルタイム監視の開始/停止
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 リアルタイム監視開始", type="primary"):
                try:
                    # リアルタイムサービスを開始
                    start_real_time_services()
                    st.success("✅ リアルタイム監視を開始しました！")
                    st.session_state.real_time_active = True
                except Exception as e:
                    st.error(f"❌ リアルタイム監視の開始に失敗しました: {e}")
        
        with col2:
            if st.button("⏹️ リアルタイム監視停止"):
                try:
                    # リアルタイムサービスを停止
                    stop_real_time_services()
                    st.success("✅ リアルタイム監視を停止しました！")
                    st.session_state.real_time_active = False
                except Exception as e:
                    st.error(f"❌ リアルタイム監視の停止に失敗しました: {e}")
        
        # リアルタイムデータ表示エリア
        if st.session_state.get('real_time_active', False):
            st.markdown("### 📊 リアルタイム株価データ")
            
            # 主要銘柄のリアルタイムデータを表示
            major_tickers = ["9984", "9433", "7203", "6758", "6861"]
            
            # リアルタイムデータを取得
            real_time_data = {}
            for ticker in major_tickers:
                try:
                    # リアルタイムデータを取得（実際のAPIから）
                    update_data = real_time_manager._get_real_time_data(ticker)
                    if update_data:
                        real_time_data[ticker] = update_data.data
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
                
                # 自動更新
                st.markdown("### 🔄 自動更新")
                st.info("データは30秒ごとに自動更新されます。")
                
                # 手動更新ボタン
                if st.button("🔄 手動更新"):
                    st.rerun()
                
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

if __name__ == "__main__":
    main() 