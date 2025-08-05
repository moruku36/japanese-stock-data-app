#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ダッシュボード機能
包括的な市場監視とポートフォリオ管理
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class DashboardManager:
    """ダッシュボード管理クラス"""
    
    def __init__(self):
        self.market_indicators = {
            'NIKKEI225': {'value': 33000, 'change': 1.2, 'symbol': '📈'},
            'TOPIX': {'value': 2400, 'change': 0.8, 'symbol': '📊'},
            'JPY/USD': {'value': 150.25, 'change': -0.3, 'symbol': '💱'},
            'VIX': {'value': 18.5, 'change': -2.1, 'symbol': '⚡'}
        }
        
        self.sectors = {
            '自動車': {'performance': 2.1, 'volume': 120000000, 'leaders': ['7203', '7267', '7211']},
            '電気機器': {'performance': 1.8, 'volume': 95000000, 'leaders': ['6758', '6861', '6752']},
            '情報・通信': {'performance': 3.2, 'volume': 150000000, 'leaders': ['9984', '9434', '4751']},
            '銀行': {'performance': -0.5, 'volume': 80000000, 'leaders': ['8306', '8316', '8411']},
            '医薬品': {'performance': 1.2, 'volume': 60000000, 'leaders': ['4502', '4503', '4568']}
        }
    
    def render_market_overview(self):
        """市場概況ウィジェット"""
        st.markdown("### 📊 市場概況")
        
        cols = st.columns(4)
        for i, (indicator, data) in enumerate(self.market_indicators.items()):
            with cols[i]:
                change_color = "🟢" if data['change'] > 0 else "🔴" if data['change'] < 0 else "⚪"
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 1rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                ">
                    <div style="font-size: 1.5rem;">{data['symbol']}</div>
                    <div style="font-weight: bold; font-size: 1.1rem;">{indicator}</div>
                    <div style="font-size: 1.3rem; margin: 0.5rem 0;">{data['value']:,.2f}</div>
                    <div style="font-size: 0.9rem;">{change_color} {data['change']:+.2f}%</div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_sector_heatmap(self):
        """セクター別ヒートマップ"""
        st.markdown("### 🗺️ セクター別パフォーマンス")
        
        # セクターデータを準備
        sectors_df = pd.DataFrame([
            {'sector': sector, 'performance': data['performance'], 'volume': data['volume']}
            for sector, data in self.sectors.items()
        ])
        
        # ヒートマップ作成
        fig = px.treemap(
            sectors_df,
            path=['sector'],
            values='volume',
            color='performance',
            color_continuous_scale='RdYlGn',
            title="セクター別パフォーマンス（面積＝出来高、色＝騰落率）"
        )
        
        fig.update_layout(
            height=400,
            font=dict(size=12),
            coloraxis_colorbar=dict(title="騰落率 (%)")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_top_movers(self):
        """上昇・下落率ランキング"""
        col1, col2 = st.columns(2)
        
        # サンプルデータ
        gainers = pd.DataFrame({
            'ticker': ['6861', '4751', '9984', '7203', '6758'],
            'name': ['キーエンス', 'サイバーエージェント', 'ソフトバンクG', 'トヨタ', 'ソニーG'],
            'price': [45000, 1200, 11500, 2800, 12000],
            'change': [8.5, 6.2, 4.8, 3.1, 2.9]
        })
        
        losers = pd.DataFrame({
            'ticker': ['8306', '8411', '3382', '9433', '4503'],
            'name': ['三菱UFJ', 'みずほ', 'セブン&アイ', 'KDDI', '第一三共'],
            'price': [950, 1800, 5200, 4100, 3800],
            'change': [-3.2, -2.8, -2.1, -1.9, -1.5]
        })
        
        with col1:
            st.markdown("#### 📈 値上がり率ランキング")
            for idx, row in gainers.iterrows():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #10b981, #059669);
                    color: white;
                    padding: 0.8rem;
                    border-radius: 8px;
                    margin: 0.3rem 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <strong>{row['ticker']}</strong><br>
                        <small>{row['name']}</small>
                    </div>
                    <div style="text-align: right;">
                        <div>¥{row['price']:,}</div>
                        <div style="color: #dcfce7;">+{row['change']:.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 📉 値下がり率ランキング")
            for idx, row in losers.iterrows():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #ef4444, #dc2626);
                    color: white;
                    padding: 0.8rem;
                    border-radius: 8px;
                    margin: 0.3rem 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <div>
                        <strong>{row['ticker']}</strong><br>
                        <small>{row['name']}</small>
                    </div>
                    <div style="text-align: right;">
                        <div>¥{row['price']:,}</div>
                        <div style="color: #fecaca;">{row['change']:.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_watchlist(self):
        """ウォッチリスト機能"""
        st.markdown("### 👀 ウォッチリスト")
        
        # セッション状態でウォッチリストを管理
        if 'watchlist' not in st.session_state:
            st.session_state.watchlist = ['7203', '6758', '9984', '6861']
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_ticker = st.text_input("銘柄コードを追加", placeholder="例: 4784")
        
        with col2:
            if st.button("追加", type="primary"):
                if new_ticker and new_ticker not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_ticker)
                    st.rerun()
        
        # ウォッチリスト表示
        if st.session_state.watchlist:
            watchlist_data = []
            for ticker in st.session_state.watchlist:
                # サンプルデータ（実際の実装では株価データを取得）
                price = np.random.uniform(1000, 50000)
                change = np.random.uniform(-5, 5)
                watchlist_data.append({
                    'ticker': ticker,
                    'price': f"¥{price:,.0f}",
                    'change': f"{change:+.2f}%",
                    'change_value': change
                })
            
            df = pd.DataFrame(watchlist_data)
            
            # スタイリング
            def color_change(val):
                if isinstance(val, str) and '%' in val:
                    num_val = float(val.replace('%', '').replace('+', ''))
                    color = 'color: red' if num_val < 0 else 'color: green'
                    return color
                return ''
            
            styled_df = df[['ticker', 'price', 'change']].style.applymap(
                color_change, subset=['change']
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # 削除機能
            if st.session_state.watchlist:
                ticker_to_remove = st.selectbox("削除する銘柄", [""] + st.session_state.watchlist)
                if st.button("削除") and ticker_to_remove:
                    st.session_state.watchlist.remove(ticker_to_remove)
                    st.rerun()
    
    def render_news_feed(self):
        """ニュースフィード"""
        st.markdown("### 📰 市場ニュース")
        
        # サンプルニュース
        news_items = [
            {
                'time': '10:30',
                'title': '日経平均、午前は続伸　半導体関連株が高い',
                'summary': '東京株式市場で日経平均株価は続伸。半導体関連株の上昇が指数を押し上げた。',
                'impact': 'positive'
            },
            {
                'time': '09:15',
                'title': 'トヨタ、電気自動車の新戦略を発表',
                'summary': 'トヨタ自動車が電気自動車の新たな戦略を発表。2030年までの投資計画を明らかにした。',
                'impact': 'positive'
            },
            {
                'time': '08:45',
                'title': '円相場、1ドル＝150円台で推移',
                'summary': '外国為替市場で円相場は1ドル＝150円台で推移。輸出関連株への影響が注目される。',
                'impact': 'neutral'
            }
        ]
        
        for news in news_items:
            impact_color = {
                'positive': '#10b981',
                'negative': '#ef4444',
                'neutral': '#6b7280'
            }[news['impact']]
            
            impact_icon = {
                'positive': '📈',
                'negative': '📉',
                'neutral': '📊'
            }[news['impact']]
            
            st.markdown(f"""
            <div style="
                border-left: 4px solid {impact_color};
                background: rgba(0, 0, 0, 0.02);
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 0 8px 8px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="color: {impact_color}; font-weight: bold;">{impact_icon} {news['time']}</span>
                </div>
                <h4 style="margin: 0.5rem 0; color: #1f2937;">{news['title']}</h4>
                <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">{news['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_portfolio_summary(self):
        """ポートフォリオサマリー"""
        st.markdown("### 💼 ポートフォリオ概要")
        
        # サンプルポートフォリオデータ
        portfolio_data = {
            'total_value': 5000000,
            'day_change': 75000,
            'day_change_pct': 1.52,
            'positions': [
                {'ticker': '7203', 'name': 'トヨタ', 'shares': 100, 'value': 280000, 'weight': 25.2},
                {'ticker': '6758', 'name': 'ソニーG', 'shares': 80, 'value': 960000, 'weight': 19.2},
                {'ticker': '9984', 'name': 'ソフトバンクG', 'shares': 150, 'value': 1725000, 'weight': 34.5},
                {'ticker': '6861', 'name': 'キーエンス', 'shares': 20, 'value': 900000, 'weight': 18.0}
            ]
        }
        
        # 全体サマリー
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "ポートフォリオ評価額",
                f"¥{portfolio_data['total_value']:,}",
                f"¥{portfolio_data['day_change']:,}"
            )
        
        with col2:
            st.metric(
                "当日損益率",
                f"{portfolio_data['day_change_pct']:+.2f}%",
                f"{portfolio_data['day_change_pct']:+.2f}%"
            )
        
        with col3:
            st.metric(
                "保有銘柄数",
                f"{len(portfolio_data['positions'])}銘柄",
                ""
            )
        
        # ポートフォリオ構成円グラフ
        fig = px.pie(
            values=[pos['weight'] for pos in portfolio_data['positions']],
            names=[f"{pos['ticker']}\n{pos['name']}" for pos in portfolio_data['positions']],
            title="ポートフォリオ構成比"
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_alert_system(self):
        """アラートシステム"""
        st.markdown("### 🚨 アラート設定")
        
        # アラート設定フォーム
        with st.expander("新しいアラートを設定"):
            col1, col2 = st.columns(2)
            
            with col1:
                alert_ticker = st.text_input("銘柄コード", placeholder="例: 7203")
                alert_type = st.selectbox("アラートタイプ", 
                    ["価格上昇", "価格下落", "出来高増加", "ニュース"])
            
            with col2:
                if alert_type in ["価格上昇", "価格下落"]:
                    threshold = st.number_input("閾値 (%)", min_value=0.1, max_value=50.0, value=5.0)
                elif alert_type == "出来高増加":
                    threshold = st.number_input("倍率", min_value=1.1, max_value=10.0, value=2.0)
                else:
                    threshold = None
                
                alert_method = st.selectbox("通知方法", ["画面表示", "メール", "LINE"])
            
            if st.button("アラート設定", type="primary"):
                st.success(f"アラートを設定しました: {alert_ticker} - {alert_type}")
        
        # 現在のアラート一覧
        if 'alerts' not in st.session_state:
            st.session_state.alerts = [
                {'ticker': '7203', 'type': '価格上昇', 'threshold': '5%', 'status': 'アクティブ'},
                {'ticker': '6758', 'type': '出来高増加', 'threshold': '2倍', 'status': 'アクティブ'}
            ]
        
        st.markdown("#### 設定済みアラート")
        for i, alert in enumerate(st.session_state.alerts):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**{alert['ticker']}** - {alert['type']}")
            
            with col2:
                st.write(f"閾値: {alert['threshold']} | {alert['status']}")
            
            with col3:
                if st.button("削除", key=f"delete_alert_{i}"):
                    st.session_state.alerts.pop(i)
                    st.rerun()

def render_dashboard():
    """ダッシュボードメイン画面"""
    dashboard = DashboardManager()
    
    st.title("📊 総合ダッシュボード")
    
    # 自動更新設定
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**リアルタイム市場監視ダッシュボード**")
    with col2:
        auto_refresh = st.toggle("自動更新", value=False)
    
    if auto_refresh:
        # 30秒ごとに自動更新
        time.sleep(30)
        st.rerun()
    
    # ダッシュボードコンポーネント
    dashboard.render_market_overview()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        dashboard.render_sector_heatmap()
        dashboard.render_top_movers()
    
    with col2:
        dashboard.render_watchlist()
        dashboard.render_news_feed()
    
    # ポートフォリオとアラート
    col1, col2 = st.columns(2)
    
    with col1:
        dashboard.render_portfolio_summary()
    
    with col2:
        dashboard.render_alert_system()

if __name__ == "__main__":
    render_dashboard()
