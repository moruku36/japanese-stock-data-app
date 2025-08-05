#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
APIパフォーマンス監視システム
リアルタイムでAPIの応答時間、成功率、エラー率を監視
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading
from collections import deque
import requests
import asyncio

logger = logging.getLogger(__name__)

class APIMonitor:
    """API監視クラス"""
    
    def __init__(self):
        self.apis = {
            'stooq': {
                'name': 'Stooq',
                'url': 'https://stooq.com/q/d/?s={ticker}.jp&f=sd2t2ohlcv&h&e=csv',
                'status': 'unknown',
                'response_time': 0,
                'success_rate': 0,
                'error_count': 0,
                'last_check': None
            },
            'yahoo': {
                'name': 'Yahoo Finance',
                'url': 'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}.T',
                'status': 'unknown',
                'response_time': 0,
                'success_rate': 0,
                'error_count': 0,
                'last_check': None
            },
            'alphavantage': {
                'name': 'Alpha Vantage',
                'url': 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey=demo',
                'status': 'unknown',
                'response_time': 0,
                'success_rate': 0,
                'error_count': 0,
                'last_check': None
            },
            'newsapi': {
                'name': 'News API',
                'url': 'https://newsapi.org/v2/everything?q=stock&apiKey=demo',
                'status': 'unknown',
                'response_time': 0,
                'success_rate': 0,
                'error_count': 0,
                'last_check': None
            }
        }
        
        # パフォーマンス履歴（最大1000件）
        self.performance_history = {
            api_name: {
                'timestamps': deque(maxlen=1000),
                'response_times': deque(maxlen=1000),
                'success_rates': deque(maxlen=1000),
                'statuses': deque(maxlen=1000)
            }
            for api_name in self.apis.keys()
        }
        
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def check_api_health(self, api_name: str, ticker: str = "7203") -> Dict[str, Any]:
        """個別APIの健全性チェック"""
        api_info = self.apis[api_name]
        
        try:
            start_time = time.time()
            
            # APIに応じてURLを構築
            if api_name == 'stooq':
                url = api_info['url'].format(ticker=ticker)
            elif api_name == 'yahoo':
                url = api_info['url'].format(ticker=ticker)
            elif api_name == 'alphavantage':
                url = api_info['url'].format(ticker=ticker)
            elif api_name == 'newsapi':
                url = api_info['url']
            
            # HTTP リクエスト実行
            response = requests.get(url, timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ミリ秒
            
            # レスポンス判定
            if response.status_code == 200:
                status = 'healthy'
                success = True
            elif response.status_code == 429:
                status = 'rate_limited'
                success = False
            else:
                status = 'error'
                success = False
            
            return {
                'status': status,
                'response_time': response_time,
                'success': success,
                'status_code': response.status_code,
                'timestamp': datetime.now()
            }
            
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'response_time': 10000,  # タイムアウト値
                'success': False,
                'status_code': 0,
                'timestamp': datetime.now()
            }
        except Exception as e:
            return {
                'status': 'error',
                'response_time': 0,
                'success': False,
                'status_code': 0,
                'timestamp': datetime.now(),
                'error': str(e)
            }
    
    def update_performance_history(self, api_name: str, result: Dict[str, Any]):
        """パフォーマンス履歴を更新"""
        history = self.performance_history[api_name]
        
        history['timestamps'].append(result['timestamp'])
        history['response_times'].append(result['response_time'])
        history['statuses'].append(result['status'])
        
        # 成功率計算（直近100件）
        recent_statuses = list(history['statuses'])[-100:]
        success_count = sum(1 for status in recent_statuses if status == 'healthy')
        success_rate = (success_count / len(recent_statuses)) * 100 if recent_statuses else 0
        history['success_rates'].append(success_rate)
        
        # APIステータス更新
        self.apis[api_name].update({
            'status': result['status'],
            'response_time': result['response_time'],
            'success_rate': success_rate,
            'last_check': result['timestamp']
        })
    
    def start_monitoring(self, interval: int = 30):
        """監視開始"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                for api_name in self.apis.keys():
                    if not self.monitoring_active:
                        break
                    
                    result = self.check_api_health(api_name)
                    self.update_performance_history(api_name, result)
                    
                    time.sleep(1)  # API間の間隔
                
                if self.monitoring_active:
                    time.sleep(interval)
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """監視停止"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def get_system_status(self) -> Dict[str, Any]:
        """システム全体のステータス"""
        healthy_count = sum(1 for api in self.apis.values() if api['status'] == 'healthy')
        total_apis = len(self.apis)
        
        avg_response_time = sum(api['response_time'] for api in self.apis.values()) / total_apis
        avg_success_rate = sum(api['success_rate'] for api in self.apis.values()) / total_apis
        
        overall_status = 'healthy' if healthy_count == total_apis else 'degraded' if healthy_count > 0 else 'down'
        
        return {
            'overall_status': overall_status,
            'healthy_apis': healthy_count,
            'total_apis': total_apis,
            'avg_response_time': avg_response_time,
            'avg_success_rate': avg_success_rate,
            'last_updated': datetime.now()
        }

def render_api_monitoring():
    """API監視画面"""
    st.title("📡 APIパフォーマンス監視")
    
    # セッション状態でモニターを管理
    if 'api_monitor' not in st.session_state:
        st.session_state.api_monitor = APIMonitor()
    
    monitor = st.session_state.api_monitor
    
    # 制御パネル
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        monitoring_interval = st.selectbox(
            "監視間隔",
            [30, 60, 120, 300],
            format_func=lambda x: f"{x}秒"
        )
    
    with col2:
        if st.button("🟢 監視開始", type="primary"):
            monitor.start_monitoring(monitoring_interval)
            st.success("監視を開始しました")
    
    with col3:
        if st.button("🔴 監視停止"):
            monitor.stop_monitoring()
            st.success("監視を停止しました")
    
    # システム概要
    system_status = monitor.get_system_status()
    
    st.markdown("### 🔍 システム概要")
    
    status_color = {
        'healthy': '🟢',
        'degraded': '🟡',
        'down': '🔴',
        'unknown': '⚪'
    }
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "システム状態",
            f"{status_color[system_status['overall_status']]} {system_status['overall_status'].upper()}"
        )
    
    with col2:
        st.metric(
            "稼働API数",
            f"{system_status['healthy_apis']}/{system_status['total_apis']}"
        )
    
    with col3:
        st.metric(
            "平均応答時間",
            f"{system_status['avg_response_time']:.0f}ms"
        )
    
    with col4:
        st.metric(
            "平均成功率",
            f"{system_status['avg_success_rate']:.1f}%"
        )
    
    # API別ステータス
    st.markdown("### 📊 API別ステータス")
    
    cols = st.columns(2)
    
    for i, (api_name, api_info) in enumerate(monitor.apis.items()):
        with cols[i % 2]:
            status_emoji = status_color.get(api_info['status'], '⚪')
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin-bottom: 1rem;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h4 style="margin: 0; color: white;">{status_emoji} {api_info['name']}</h4>
                    <span style="background: rgba(255,255,255,0.2); padding: 0.3rem 0.6rem; border-radius: 5px; font-size: 0.8rem;">
                        {api_info['status'].upper()}
                    </span>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">応答時間</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{api_info['response_time']:.0f}ms</div>
                    </div>
                    <div>
                        <div style="font-size: 0.8rem; opacity: 0.8;">成功率</div>
                        <div style="font-size: 1.2rem; font-weight: bold;">{api_info['success_rate']:.1f}%</div>
                    </div>
                </div>
                
                <div style="margin-top: 1rem; font-size: 0.8rem; opacity: 0.8;">
                    最終チェック: {api_info['last_check'].strftime('%H:%M:%S') if api_info['last_check'] else 'N/A'}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # パフォーマンスチャート
    st.markdown("### 📈 パフォーマンス履歴")
    
    # タブでチャートを分割
    tab1, tab2, tab3 = st.tabs(["応答時間", "成功率", "ステータス履歴"])
    
    with tab1:
        # 応答時間チャート
        fig_response = go.Figure()
        
        for api_name, history in monitor.performance_history.items():
            if history['timestamps']:
                fig_response.add_trace(go.Scatter(
                    x=list(history['timestamps']),
                    y=list(history['response_times']),
                    mode='lines+markers',
                    name=monitor.apis[api_name]['name'],
                    line=dict(width=2)
                ))
        
        fig_response.update_layout(
            title='API応答時間の推移',
            xaxis_title='時刻',
            yaxis_title='応答時間 (ms)',
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_response, use_container_width=True)
    
    with tab2:
        # 成功率チャート
        fig_success = go.Figure()
        
        for api_name, history in monitor.performance_history.items():
            if history['timestamps']:
                fig_success.add_trace(go.Scatter(
                    x=list(history['timestamps']),
                    y=list(history['success_rates']),
                    mode='lines+markers',
                    name=monitor.apis[api_name]['name'],
                    line=dict(width=2)
                ))
        
        fig_success.update_layout(
            title='API成功率の推移',
            xaxis_title='時刻',
            yaxis_title='成功率 (%)',
            height=400,
            yaxis=dict(range=[0, 100]),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_success, use_container_width=True)
    
    with tab3:
        # ステータス履歴テーブル
        st.markdown("#### 📋 最新のAPI チェック結果")
        
        status_data = []
        for api_name, api_info in monitor.apis.items():
            if api_info['last_check']:
                status_data.append({
                    'API': api_info['name'],
                    'ステータス': api_info['status'],
                    '応答時間': f"{api_info['response_time']:.0f}ms",
                    '成功率': f"{api_info['success_rate']:.1f}%",
                    '最終チェック': api_info['last_check'].strftime('%Y-%m-%d %H:%M:%S')
                })
        
        if status_data:
            df = pd.DataFrame(status_data)
            
            # ステータスに応じて色付け
            def highlight_status(val):
                if val == 'healthy':
                    return 'background-color: #dcfce7; color: #166534'
                elif val == 'error':
                    return 'background-color: #fee2e2; color: #dc2626'
                elif val == 'timeout':
                    return 'background-color: #fef3c7; color: #d97706'
                elif val == 'rate_limited':
                    return 'background-color: #f3e8ff; color: #7c3aed'
                return ''
            
            styled_df = df.style.applymap(highlight_status, subset=['ステータス'])
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("まだチェック結果がありません。監視を開始してください。")
    
    # アラート設定
    st.markdown("### 🚨 アラート設定")
    
    with st.expander("アラート設定を変更"):
        col1, col2 = st.columns(2)
        
        with col1:
            response_time_threshold = st.number_input(
                "応答時間閾値 (ms)",
                min_value=100,
                max_value=10000,
                value=3000,
                step=100
            )
            
            success_rate_threshold = st.slider(
                "成功率閾値 (%)",
                min_value=0,
                max_value=100,
                value=95
            )
        
        with col2:
            alert_methods = st.multiselect(
                "通知方法",
                ["画面表示", "メール", "Slack", "Discord"],
                default=["画面表示"]
            )
            
            alert_frequency = st.selectbox(
                "通知頻度",
                ["即座", "5分ごと", "15分ごと", "1時間ごと"]
            )
        
        if st.button("アラート設定を保存"):
            st.success("アラート設定を保存しました")
    
    # 現在のアラート
    current_alerts = []
    for api_name, api_info in monitor.apis.items():
        if api_info['response_time'] > response_time_threshold:
            current_alerts.append(f"🚨 {api_info['name']}: 応答時間が遅い ({api_info['response_time']:.0f}ms)")
        
        if api_info['success_rate'] < success_rate_threshold and api_info['success_rate'] > 0:
            current_alerts.append(f"⚠️ {api_info['name']}: 成功率が低い ({api_info['success_rate']:.1f}%)")
        
        if api_info['status'] == 'error':
            current_alerts.append(f"❌ {api_info['name']}: エラー状態")
        
        if api_info['status'] == 'timeout':
            current_alerts.append(f"⏰ {api_info['name']}: タイムアウト")
    
    if current_alerts:
        st.markdown("### 🚨 現在のアラート")
        for alert in current_alerts:
            st.error(alert)
    else:
        st.success("✅ 現在アラートはありません")
    
    # 自動更新
    if monitor.monitoring_active:
        st.markdown("---")
        st.markdown("**🔄 自動更新中...**")
        
        # 30秒ごとに画面を更新
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    render_api_monitoring()
