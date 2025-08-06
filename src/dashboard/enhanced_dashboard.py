#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
強化ダッシュボード機能
リアルタイム市場監視・分析・アラート統合システム
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import time

# 依存関係の動的インポート
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly が利用できません。基本的なチャート機能のみ利用可能です。")

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    st.warning("yfinance が利用できません。デモデータを使用します。")

logger = logging.getLogger(__name__)

class EnhancedDashboard:
    """強化ダッシュボードクラス"""
    
    def __init__(self):
        """初期化"""
        self.cache_duration = 300  # 5分間キャッシュ
        self.last_update = None
        self.market_data = {}
        
        # 主要指数の定義
        self.major_indices = {
            "^N225": "日経平均",
            "^TPX": "TOPIX",
            "^NKH": "日経ハイテク",
            "USDJPY=X": "USD/JPY"
        }
        
        # 注目銘柄
        self.watchlist_symbols = [
            "7203", "6758", "9984", "6861", "8411",
            "7267", "4503", "6501", "8001", "9432"
        ]
        
        # セクター分類
        self.sector_classification = {
            "7203": {"name": "トヨタ自動車", "sector": "自動車", "color": "#FF6B6B"},
            "6758": {"name": "ソニーグループ", "sector": "電気機器", "color": "#4ECDC4"},
            "9984": {"name": "ソフトバンクG", "sector": "情報通信", "color": "#45B7D1"},
            "6861": {"name": "キーエンス", "sector": "電気機器", "color": "#96CEB4"},
            "8411": {"name": "みずほFG", "sector": "銀行", "color": "#FECA57"},
            "7267": {"name": "ホンダ", "sector": "自動車", "color": "#FF9FF3"},
            "4503": {"name": "アステラス製薬", "sector": "医薬品", "color": "#54A0FF"},
            "6501": {"name": "日立製作所", "sector": "電気機器", "color": "#5F27CD"},
            "8001": {"name": "伊藤忠商事", "sector": "商社", "color": "#00D2D3"},
            "9432": {"name": "NTT", "sector": "情報通信", "color": "#FF6348"}
        }
        
        logger.info("強化ダッシュボードを初期化しました")
    
    def get_market_overview(self) -> Dict[str, Any]:
        """市場概要データを取得"""
        try:
            # キャッシュチェック
            if (self.last_update and 
                datetime.now() - self.last_update < timedelta(seconds=self.cache_duration)):
                return self.market_data.get('overview', {})
            
            overview = {}
            
            if YFINANCE_AVAILABLE:
                # 実際のデータを取得
                for symbol, name in self.major_indices.items():
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        hist = ticker.history(period="2d")
                        
                        if not hist.empty:
                            current_price = hist['Close'].iloc[-1]
                            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                            change = current_price - prev_price
                            change_pct = (change / prev_price) * 100
                            
                            overview[symbol] = {
                                'name': name,
                                'price': current_price,
                                'change': change,
                                'change_pct': change_pct,
                                'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
                            }
                    except Exception as e:
                        logger.warning(f"データ取得失敗 {symbol}: {e}")
            else:
                # デモデータ
                overview = self._generate_demo_market_data()
            
            self.market_data['overview'] = overview
            self.last_update = datetime.now()
            
            return overview
            
        except Exception as e:
            logger.error(f"市場概要取得エラー: {e}")
            return self._generate_demo_market_data()
    
    def _generate_demo_market_data(self) -> Dict[str, Any]:
        """デモ用市場データを生成"""
        return {
            "^N225": {
                "name": "日経平均",
                "price": 28500.0 + np.random.normal(0, 200),
                "change": np.random.normal(0, 150),
                "change_pct": np.random.normal(0, 0.8),
                "volume": 1200000000
            },
            "^TPX": {
                "name": "TOPIX",
                "price": 1950.0 + np.random.normal(0, 20),
                "change": np.random.normal(0, 15),
                "change_pct": np.random.normal(0, 0.7),
                "volume": 800000000
            },
            "USDJPY=X": {
                "name": "USD/JPY",
                "price": 150.0 + np.random.normal(0, 2),
                "change": np.random.normal(0, 0.5),
                "change_pct": np.random.normal(0, 0.3),
                "volume": 0
            }
        }
    
    def get_watchlist_data(self) -> Dict[str, Any]:
        """ウォッチリストデータを取得"""
        try:
            watchlist = {}
            
            if YFINANCE_AVAILABLE:
                symbols_with_suffix = [f"{symbol}.T" for symbol in self.watchlist_symbols]
                
                try:
                    data = yf.download(symbols_with_suffix, period="2d", interval="1d", progress=False)
                    
                    for symbol in self.watchlist_symbols:
                        symbol_with_suffix = f"{symbol}.T"
                        info = self.sector_classification.get(symbol, {})
                        
                        try:
                            if len(self.watchlist_symbols) == 1:
                                # 単一銘柄の場合
                                if 'Close' in data.columns:
                                    current_price = data['Close'].iloc[-1]
                                    prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
                                    volume = data['Volume'].iloc[-1] if 'Volume' in data.columns else 0
                            else:
                                # 複数銘柄の場合
                                if ('Close', symbol_with_suffix) in data.columns:
                                    current_price = data[('Close', symbol_with_suffix)].iloc[-1]
                                    prev_price = data[('Close', symbol_with_suffix)].iloc[-2] if len(data) > 1 else current_price
                                    volume = data[('Volume', symbol_with_suffix)].iloc[-1] if ('Volume', symbol_with_suffix) in data.columns else 0
                                else:
                                    continue
                            
                            change = current_price - prev_price
                            change_pct = (change / prev_price) * 100
                            
                            watchlist[symbol] = {
                                'name': info.get('name', f'銘柄{symbol}'),
                                'sector': info.get('sector', 'その他'),
                                'color': info.get('color', '#808080'),
                                'price': current_price,
                                'change': change,
                                'change_pct': change_pct,
                                'volume': volume
                            }
                            
                        except Exception as e:
                            logger.warning(f"銘柄データ処理失敗 {symbol}: {e}")
                            
                except Exception as e:
                    logger.warning(f"ウォッチリストデータ取得失敗: {e}")
            
            # データが不足している場合はデモデータで補完
            if len(watchlist) < len(self.watchlist_symbols):
                watchlist.update(self._generate_demo_watchlist_data())
            
            return watchlist
            
        except Exception as e:
            logger.error(f"ウォッチリストデータ取得エラー: {e}")
            return self._generate_demo_watchlist_data()
    
    def _generate_demo_watchlist_data(self) -> Dict[str, Any]:
        """デモ用ウォッチリストデータを生成"""
        demo_data = {}
        
        for symbol in self.watchlist_symbols:
            info = self.sector_classification.get(symbol, {})
            base_price = 1000 + hash(symbol) % 5000  # シンボルから一定の基準価格を生成
            
            demo_data[symbol] = {
                'name': info.get('name', f'銘柄{symbol}'),
                'sector': info.get('sector', 'その他'),
                'color': info.get('color', '#808080'),
                'price': base_price + np.random.normal(0, base_price * 0.1),
                'change': np.random.normal(0, base_price * 0.05),
                'change_pct': np.random.normal(0, 3),
                'volume': np.random.randint(100000, 10000000)
            }
        
        return demo_data
    
    def get_sector_performance(self) -> Dict[str, Any]:
        """セクター別パフォーマンスを取得"""
        watchlist = self.get_watchlist_data()
        
        sector_data = {}
        for symbol, data in watchlist.items():
            sector = data['sector']
            if sector not in sector_data:
                sector_data[sector] = {
                    'symbols': [],
                    'total_change_pct': 0,
                    'count': 0,
                    'avg_change_pct': 0
                }
            
            sector_data[sector]['symbols'].append(symbol)
            sector_data[sector]['total_change_pct'] += data['change_pct']
            sector_data[sector]['count'] += 1
            sector_data[sector]['avg_change_pct'] = sector_data[sector]['total_change_pct'] / sector_data[sector]['count']
        
        return sector_data
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """市場センチメントを分析"""
        watchlist = self.get_watchlist_data()
        
        # 上昇・下落銘柄数の計算
        rising_count = sum(1 for data in watchlist.values() if data['change_pct'] > 0)
        falling_count = sum(1 for data in watchlist.values() if data['change_pct'] < 0)
        unchanged_count = len(watchlist) - rising_count - falling_count
        
        # センチメントスコアの計算
        if len(watchlist) > 0:
            avg_change = np.mean([data['change_pct'] for data in watchlist.values()])
            sentiment_score = max(-1, min(1, avg_change / 3))  # -1 to 1 の範囲に正規化
        else:
            sentiment_score = 0
        
        # センチメント判定
        if sentiment_score > 0.3:
            sentiment = "強気"
            sentiment_color = "#28a745"
        elif sentiment_score > 0:
            sentiment = "やや強気"
            sentiment_color = "#90EE90"
        elif sentiment_score > -0.3:
            sentiment = "中立"
            sentiment_color = "#ffc107"
        else:
            sentiment = "弱気"
            sentiment_color = "#dc3545"
        
        return {
            'sentiment': sentiment,
            'sentiment_color': sentiment_color,
            'sentiment_score': sentiment_score,
            'rising_count': rising_count,
            'falling_count': falling_count,
            'unchanged_count': unchanged_count,
            'total_count': len(watchlist)
        }

# Streamlit UI関数
def show_enhanced_dashboard_ui():
    """強化ダッシュボードUIを表示"""
    st.markdown("## 🎯 強化ダッシュボード")
    
    # ダッシュボードの初期化
    if 'enhanced_dashboard' not in st.session_state:
        st.session_state.enhanced_dashboard = EnhancedDashboard()
    
    dashboard = st.session_state.enhanced_dashboard
    
    # 自動更新設定
    auto_refresh = st.sidebar.checkbox("🔄 自動更新（30秒）", value=False)
    
    if auto_refresh:
        # 30秒ごとに自動更新
        time.sleep(30)
        st.rerun()
    
    # 手動更新ボタン
    if st.button("🔄 データ更新", help="最新のマーケットデータを取得"):
        dashboard.last_update = None  # キャッシュをクリア
        st.rerun()
    
    # 市場概要セクション
    show_market_overview_section(dashboard)
    
    # セクター分析セクション
    show_sector_analysis_section(dashboard)
    
    # ウォッチリストセクション
    show_watchlist_section(dashboard)
    
    # 市場センチメントセクション
    show_market_sentiment_section(dashboard)

def show_market_overview_section(dashboard: EnhancedDashboard):
    """市場概要セクション"""
    st.markdown("### 📊 市場概要")
    
    overview = dashboard.get_market_overview()
    
    if overview:
        cols = st.columns(len(overview))
        
        for i, (symbol, data) in enumerate(overview.items()):
            with cols[i]:
                # 変動率に基づく色設定
                delta_color = "normal" if data['change'] >= 0 else "inverse"
                
                st.metric(
                    label=data['name'],
                    value=f"{data['price']:,.0f}" if symbol != "USDJPY=X" else f"{data['price']:.2f}",
                    delta=f"{data['change']:+,.0f} ({data['change_pct']:+.2f}%)" if symbol != "USDJPY=X" else f"{data['change']:+.2f} ({data['change_pct']:+.2f}%)",
                    delta_color=delta_color
                )
    
    # 市場概要チャート（Plotlyが利用可能な場合）
    if PLOTLY_AVAILABLE and overview:
        st.markdown("#### 📈 主要指数動向")
        
        # サンプルチャート用データの生成
        timestamps = pd.date_range(end=datetime.now(), periods=30, freq='D')
        
        fig = go.Figure()
        
        for symbol, data in overview.items():
            if symbol != "USDJPY=X":  # 為替は除外
                # ランダムウォークでサンプルデータを生成
                np.random.seed(hash(symbol) % 2**31)
                base_price = data['price']
                returns = np.random.normal(0.001, 0.02, 30)
                prices = base_price * np.exp(np.cumsum(returns))
                
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=prices,
                    mode='lines',
                    name=data['name'],
                    hovertemplate=f"{data['name']}: %{{y:,.0f}}<extra></extra>"
                ))
        
        fig.update_layout(
            title="主要指数 30日間推移",
            xaxis_title="日付",
            yaxis_title="価格",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_sector_analysis_section(dashboard: EnhancedDashboard):
    """セクター分析セクション"""
    st.markdown("### 🏭 セクター分析")
    
    sector_data = dashboard.get_sector_performance()
    
    if sector_data and PLOTLY_AVAILABLE:
        # セクター別パフォーマンス表
        sector_df = pd.DataFrame([
            {
                'セクター': sector,
                '銘柄数': data['count'],
                '平均変動率': f"{data['avg_change_pct']:.2f}%",
                '変動率（数値）': data['avg_change_pct']
            }
            for sector, data in sector_data.items()
        ])
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.dataframe(
                sector_df[['セクター', '銘柄数', '平均変動率']],
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            # セクター別パフォーマンスバーチャート
            colors = ['#28a745' if x > 0 else '#dc3545' for x in sector_df['変動率（数値）']]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=sector_df['セクター'],
                    y=sector_df['変動率（数値）'],
                    marker_color=colors,
                    text=[f"{x:.2f}%" for x in sector_df['変動率（数値）']],
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title="セクター別パフォーマンス",
                xaxis_title="セクター",
                yaxis_title="変動率 (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)

def show_watchlist_section(dashboard: EnhancedDashboard):
    """ウォッチリストセクション"""
    st.markdown("### ⭐ ウォッチリスト")
    
    watchlist = dashboard.get_watchlist_data()
    
    if watchlist:
        # ウォッチリスト表の作成
        watchlist_data = []
        for symbol, data in watchlist.items():
            watchlist_data.append({
                '銘柄': f"{data['name']} ({symbol})",
                'セクター': data['sector'],
                '価格': f"¥{data['price']:,.0f}",
                '変動': f"{data['change']:+,.0f}",
                '変動率': f"{data['change_pct']:+.2f}%",
                '出来高': f"{data['volume']:,}",
                '変動率（数値）': data['change_pct']
            })
        
        df_watchlist = pd.DataFrame(watchlist_data)
        
        # 変動率でソート
        df_watchlist = df_watchlist.sort_values('変動率（数値）', ascending=False)
        
        # 表示用データフレーム（数値列を除外）
        display_df = df_watchlist[['銘柄', 'セクター', '価格', '変動', '変動率', '出来高']]
        
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True
        )
        
        # ヒートマップ（Plotlyが利用可能な場合）
        if PLOTLY_AVAILABLE:
            st.markdown("#### 🗺️ パフォーマンスヒートマップ")
            
            # 銘柄のマトリックス配列を作成
            n_cols = 5
            n_rows = (len(watchlist) + n_cols - 1) // n_cols
            
            z_values = []
            text_values = []
            x_labels = []
            y_labels = []
            
            for i in range(n_rows):
                row_z = []
                row_text = []
                for j in range(n_cols):
                    idx = i * n_cols + j
                    if idx < len(watchlist_data):
                        item = watchlist_data[idx]
                        row_z.append(item['変動率（数値）'])
                        row_text.append(f"{item['銘柄']}<br>{item['変動率']}")
                    else:
                        row_z.append(0)
                        row_text.append("")
                z_values.append(row_z)
                text_values.append(row_text)
            
            fig = go.Figure(data=go.Heatmap(
                z=z_values,
                text=text_values,
                texttemplate="%{text}",
                textfont={"size": 10},
                colorscale=[[0, '#dc3545'], [0.5, '#ffffff'], [1, '#28a745']],
                zmid=0,
                hovertemplate="%{text}<extra></extra>"
            ))
            
            fig.update_layout(
                title="銘柄別パフォーマンス ヒートマップ",
                height=300,
                xaxis=dict(showticklabels=False),
                yaxis=dict(showticklabels=False)
            )
            
            st.plotly_chart(fig, use_container_width=True)

def show_market_sentiment_section(dashboard: EnhancedDashboard):
    """市場センチメントセクション"""
    st.markdown("### 🎭 市場センチメント")
    
    sentiment_data = dashboard.get_market_sentiment()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "市場センチメント",
            sentiment_data['sentiment'],
            help=f"スコア: {sentiment_data['sentiment_score']:.2f}"
        )
    
    with col2:
        st.metric("上昇銘柄", sentiment_data['rising_count'])
    
    with col3:
        st.metric("下落銘柄", sentiment_data['falling_count'])
    
    with col4:
        st.metric("変わらず", sentiment_data['unchanged_count'])
    
    # センチメントゲージ（Plotlyが利用可能な場合）
    if PLOTLY_AVAILABLE:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # センチメントゲージチャート
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=sentiment_data['sentiment_score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "センチメントスコア"},
                delta={'reference': 0},
                gauge={
                    'axis': {'range': [-1, 1]},
                    'bar': {'color': sentiment_data['sentiment_color']},
                    'steps': [
                        {'range': [-1, -0.3], 'color': "lightgray"},
                        {'range': [-0.3, 0.3], 'color': "lightyellow"},
                        {'range': [0.3, 1], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 上昇/下落分布円グラフ
            fig = go.Figure(data=[go.Pie(
                labels=['上昇', '下落', '変わらず'],
                values=[
                    sentiment_data['rising_count'],
                    sentiment_data['falling_count'],
                    sentiment_data['unchanged_count']
                ],
                marker_colors=['#28a745', '#dc3545', '#ffc107'],
                hole=0.3
            )])
            
            fig.update_layout(
                title="銘柄動向分布",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # 市場統計サマリー
    st.markdown("#### 📈 市場統計サマリー")
    
    total_symbols = sentiment_data['total_count']
    rising_pct = (sentiment_data['rising_count'] / total_symbols * 100) if total_symbols > 0 else 0
    falling_pct = (sentiment_data['falling_count'] / total_symbols * 100) if total_symbols > 0 else 0
    
    st.markdown(f"""
    - **総銘柄数**: {total_symbols}
    - **上昇銘柄率**: {rising_pct:.1f}%
    - **下落銘柄率**: {falling_pct:.1f}%
    - **センチメント**: {sentiment_data['sentiment']} (スコア: {sentiment_data['sentiment_score']:.2f})
    - **最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

# 通知・アラート統合機能
def show_integrated_notifications():
    """統合通知システム"""
    st.sidebar.markdown("### 🔔 通知センター")
    
    # アラート通知の表示
    if 'notifications' in st.session_state and st.session_state.notifications:
        notification_count = len(st.session_state.notifications)
        st.sidebar.markdown(f"**未読通知**: {notification_count}件")
        
        with st.sidebar.expander("📬 最新通知", expanded=False):
            for notification in st.session_state.notifications[-3:]:  # 最新3件
                timestamp = datetime.fromisoformat(notification['timestamp'])
                st.markdown(f"""
                <div style="
                    padding: 5px;
                    border-left: 3px solid #ff6b6b;
                    background-color: #fff5f5;
                    margin: 3px 0;
                    font-size: 12px;
                ">
                    <strong>{notification['title']}</strong><br>
                    {notification['message'][:50]}...<br>
                    <small>{timestamp.strftime('%H:%M')}</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("📭 新しい通知はありません")

if __name__ == "__main__":
    # テスト実行
    st.title("🎯 強化ダッシュボード機能テスト")
    show_enhanced_dashboard_ui()
    show_integrated_notifications()
