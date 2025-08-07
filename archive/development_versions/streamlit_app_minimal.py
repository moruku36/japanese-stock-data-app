"""
日本株データ分析アプリ - 最小版
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib

# 高度なテクニカル分析用ライブラリ（オプション）
ADVANCED_FEATURES_AVAILABLE = False
try:
    import pandas_ta as ta
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    pass

# セキュリティ設定
if 'security_manager' not in st.session_state:
    st.session_state.security_manager = {
        'users': {
            'admin': {'password': hashlib.sha256('admin123'.encode()).hexdigest(), 'permissions': ['read', 'write', 'admin']},
            'user': {'password': hashlib.sha256('user123'.encode()).hexdigest(), 'permissions': ['read', 'write']}
        },
        'current_user': None,
        'authenticated': False
    }

def authenticate_user(username, password):
    """ユーザー認証"""
    users = st.session_state.security_manager['users']
    if username in users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if users[username]['password'] == password_hash:
            st.session_state.security_manager['current_user'] = username
            st.session_state.security_manager['authenticated'] = True
            return users[username]
    return None

def show_login():
    """ログイン画面"""
    st.title("🔐 ログイン")
    
    with st.form("login_form"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")
        
        if submitted:
            if username and password:
                user_info = authenticate_user(username, password)
                if user_info:
                    st.success("ログインに成功しました！")
                    st.rerun()
                else:
                    st.error("ユーザー名またはパスワードが間違っています")
            else:
                st.error("ユーザー名とパスワードを入力してください")
    
    # デモ用の認証情報
    st.info("**デモ用認証情報:**\n- 管理者: admin / admin123\n- 一般: user / user123")

def calculate_basic_indicators(hist):
    """基本的なテクニカル指標を計算"""
    try:
        # 移動平均
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA25'] = hist['Close'].rolling(window=25).mean()
        hist['MA75'] = hist['Close'].rolling(window=75).mean()
        
        # ボリンジャーバンド
        hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
        bb_std = hist['Close'].rolling(window=20).std()
        hist['BB_Upper'] = hist['BB_Middle'] + (bb_std * 2)
        hist['BB_Lower'] = hist['BB_Middle'] - (bb_std * 2)
        
        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        return hist
    except Exception as e:
        st.error(f"指標計算でエラー: {str(e)}")
        return hist

def fetch_stock_data(symbol, period="1y"):
    """株式データを取得"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return None
        return hist
    except Exception as e:
        st.error(f"データ取得エラー: {str(e)}")
        return None

def show_stock_chart(hist, symbol):
    """株価チャートを表示"""
    if hist is None or hist.empty:
        st.error("データがありません")
        return
    
    # 基本チャート
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name=symbol
    ))
    
    fig.update_layout(
        title=f"{symbol} - 株価チャート",
        yaxis_title="価格 (¥)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_basic_analysis(hist, symbol):
    """基本分析を表示"""
    if hist is None or hist.empty:
        return
    
    hist_with_indicators = calculate_basic_indicators(hist.copy())
    
    # 最新データ
    latest = hist_with_indicators.iloc[-1]
    prev = hist_with_indicators.iloc[-2] if len(hist_with_indicators) > 1 else latest
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change = latest['Close'] - prev['Close']
        change_pct = (change / prev['Close']) * 100 if prev['Close'] != 0 else 0
        st.metric("終値", f"¥{latest['Close']:.0f}", f"{change:+.0f} ({change_pct:+.1f}%)")
    
    with col2:
        st.metric("出来高", f"{latest['Volume']:,.0f}")
    
    with col3:
        if not pd.isna(latest['RSI']):
            st.metric("RSI", f"{latest['RSI']:.1f}")
    
    with col4:
        ma5_trend = "↑" if not pd.isna(latest['MA5']) and not pd.isna(prev['MA5']) and latest['MA5'] > prev['MA5'] else "↓"
        if not pd.isna(latest['MA5']):
            st.metric("5日移動平均", f"¥{latest['MA5']:.0f}", ma5_trend)

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="日本株データ分析",
        page_icon="📈",
        layout="wide"
    )
    
    # 認証チェック
    if not st.session_state.security_manager['authenticated']:
        show_login()
        return
    
    # メインアプリ
    st.title("📈 日本株データ分析アプリ")
    
    # サイドバー
    with st.sidebar:
        st.header("設定")
        
        # ログアウト
        if st.button("ログアウト"):
            st.session_state.security_manager['authenticated'] = False
            st.session_state.security_manager['current_user'] = None
            st.rerun()
        
        st.markdown("---")
        
        # 銘柄選択
        symbol_input = st.text_input("銘柄コード", value="7203.T", help="例: 7203.T (トヨタ)")
        period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
        
        if st.button("データ取得"):
            with st.spinner("データを取得中..."):
                hist = fetch_stock_data(symbol_input, period)
                if hist is not None:
                    st.session_state['stock_data'] = hist
                    st.session_state['current_symbol'] = symbol_input
                    st.success("データ取得完了")
                else:
                    st.error("データ取得に失敗しました")
    
    # メインコンテンツ
    if 'stock_data' in st.session_state and st.session_state['stock_data'] is not None:
        hist = st.session_state['stock_data']
        symbol = st.session_state.get('current_symbol', '不明')
        
        # 基本情報
        show_basic_analysis(hist, symbol)
        
        st.markdown("---")
        
        # チャート表示
        show_stock_chart(hist, symbol)
        
        # 詳細データ
        with st.expander("詳細データ"):
            st.dataframe(hist.tail(10))
    
    else:
        st.info("サイドバーから銘柄を選択してデータを取得してください")

if __name__ == "__main__":
    main()
