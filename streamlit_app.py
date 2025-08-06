"""
日本株データ分析アプリ - セキュア版
セキュリティ機能を統合した軽量版
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import secrets
import re
from typing import Optional

class SecurityManager:
    """軽量セキュリティ管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.session_timeout = 3600  # 1時間
        self.max_requests_per_minute = 60
        self.request_history = []
        
        # デフォルトユーザー
        self.users = {
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "role": "admin",
                "permissions": ["read", "write", "admin"]
            },
            "user": {
                "password_hash": self._hash_password("user123"),
                "role": "user", 
                "permissions": ["read", "write"]
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """パスワードをハッシュ化"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """パスワードを検証"""
        try:
            salt, pwd_hash = hashed.split('$')
            verify_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return pwd_hash == verify_hash.hex()
        except:
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """ユーザー認証"""
        if username in self.users:
            user = self.users[username]
            if self.verify_password(password, user["password_hash"]):
                return {
                    "username": username,
                    "role": user["role"],
                    "permissions": user["permissions"]
                }
        return None
    
    def validate_input(self, text: str) -> str:
        """入力検証とサニタイゼーション"""
        if not text:
            return ""
        
        # 危険な文字を除去
        dangerous_chars = ['<', '>', '"', "'", '&', '`', '(', ')', '{', '}', '[', ']']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # 長さ制限
        return text[:100]
    
    def validate_stock_code(self, code: str) -> bool:
        """株式コードの検証"""
        if not code:
            return False
        
        # 日本株コードの基本パターン（4桁.T）
        pattern = r'^\d{4}\.T$'
        return bool(re.match(pattern, code))
    
    def check_rate_limit(self) -> bool:
        """レート制限チェック"""
        current_time = datetime.now()
        
        # 1分前より古い記録を削除
        cutoff_time = current_time - timedelta(minutes=1)
        self.request_history = [t for t in self.request_history if t > cutoff_time]
        
        # 制限チェック
        if len(self.request_history) >= self.max_requests_per_minute:
            return False
        
        # 記録追加
        self.request_history.append(current_time)
        return True

def init_session_state():
    """セッション状態を初期化"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'security_manager' not in st.session_state:
        st.session_state.security_manager = SecurityManager()

def show_login():
    """ログイン画面を表示"""
    st.title("🔐 ログイン")
    
    with st.form("login_form"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        submit = st.form_submit_button("ログイン")
        
        if submit:
            if username and password:
                # 入力検証
                username = st.session_state.security_manager.validate_input(username)
                
                # 認証
                user_info = st.session_state.security_manager.authenticate(username, password)
                
                if user_info:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.success("ログインしました")
                    st.rerun()
                else:
                    st.error("ユーザー名またはパスワードが正しくありません")
            else:
                st.error("ユーザー名とパスワードを入力してください")
    
    # ゲストアクセス
    if st.button("ゲストとしてアクセス"):
        st.session_state.authenticated = True
        st.session_state.user_info = {
            "username": "guest",
            "role": "guest",
            "permissions": ["read"]
        }
        st.rerun()
    
    # 使用可能なアカウント情報
    with st.expander("テスト用アカウント"):
        st.info("""
        **管理者**: admin / admin123
        **ユーザー**: user / user123
        **ゲスト**: ゲストボタンをクリック
        """)

def show_main_app():
    """メインアプリケーションを表示"""
    security_manager = st.session_state.security_manager
    user_info = st.session_state.user_info
    
    # レート制限チェック
    if not security_manager.check_rate_limit():
        st.error("アクセス制限に達しました。しばらくお待ちください。")
        return
    
    # ヘッダー
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📈 日本株データ分析アプリ（セキュア版）")
    with col2:
        st.write(f"ログイン: {user_info['username']} ({user_info['role']})")
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    
    st.markdown("---")
    
    # 権限チェック
    if "read" not in user_info["permissions"]:
        st.error("データ閲覧権限がありません")
        return
    
    # サイドバーで銘柄選択
    st.sidebar.header("銘柄選択")
    
    # よく使われる銘柄コード（検証済み）
    popular_stocks = {
        "トヨタ自動車": "7203.T",
        "ソフトバンクグループ": "9984.T",
        "ファーストリテイリング": "9983.T",
        "キーエンス": "6861.T",
        "信越化学工業": "4063.T"
    }
    
    selected_stock = st.sidebar.selectbox(
        "銘柄を選択",
        options=list(popular_stocks.keys())
    )
    
    stock_code = popular_stocks[selected_stock]
    
    # 株式コードの検証
    if not security_manager.validate_stock_code(stock_code):
        st.error("無効な株式コードです")
        return
    
    # 期間選択
    period_options = {
        "1ヶ月": "1mo",
        "3ヶ月": "3mo", 
        "6ヶ月": "6mo",
        "1年": "1y",
        "2年": "2y"
    }
    
    selected_period = st.sidebar.selectbox(
        "期間を選択",
        options=list(period_options.keys()),
        index=2  # デフォルトは6ヶ月
    )
    
    period = period_options[selected_period]
    
    try:
        # データ取得（エラーハンドリング強化）
        with st.spinner(f"{selected_stock}のデータを取得中..."):
            stock = yf.Ticker(stock_code)
            hist = stock.history(period=period)
            
            # 情報取得は管理者権限のみ
            info = None
            if "admin" in user_info["permissions"]:
                try:
                    info = stock.info
                except:
                    info = None
        
        if len(hist) == 0:
            st.warning("データが取得できませんでした。別の銘柄をお試しください。")
            return
        
        # 基本情報表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = hist['Close'].iloc[-1]
            st.metric("現在価格", f"¥{current_price:,.0f}")
        
        with col2:
            if len(hist) > 1:
                price_change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                change_pct = (price_change / hist['Close'].iloc[-2]) * 100
                st.metric("前日比", f"¥{price_change:+,.0f}", f"{change_pct:+.2f}%")
        
        with col3:
            max_price = hist['High'].max()
            st.metric(f"{selected_period}最高値", f"¥{max_price:,.0f}")
        
        with col4:
            min_price = hist['Low'].min()
            st.metric(f"{selected_period}最安値", f"¥{min_price:,.0f}")
        
        st.markdown("---")
        
        # 株価チャート
        st.subheader("📊 株価チャート")
        
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'], 
            low=hist['Low'],
            close=hist['Close'],
            name=selected_stock
        ))
        
        fig.update_layout(
            title=f"{selected_stock} ({stock_code}) - {selected_period}",
            yaxis_title="価格 (¥)",
            xaxis_title="日付",
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 出来高チャート（書き込み権限が必要）
        if "write" in user_info["permissions"]:
            st.subheader("📊 出来高")
            
            fig_volume = px.bar(
                x=hist.index,
                y=hist['Volume'],
                title="出来高"
            )
            
            fig_volume.update_layout(
                xaxis_title="日付",
                yaxis_title="出来高",
                height=300
            )
            
            st.plotly_chart(fig_volume, use_container_width=True)
        
        # 基本統計
        st.subheader("📈 基本統計")
        
        stats_col1, stats_col2 = st.columns(2)
        
        with stats_col1:
            st.write("**価格統計**")
            price_stats = pd.DataFrame({
                "項目": ["平均価格", "標準偏差", "最高値", "最安値"],
                "値": [
                    f"¥{hist['Close'].mean():,.0f}",
                    f"¥{hist['Close'].std():,.0f}",
                    f"¥{hist['Close'].max():,.0f}",
                    f"¥{hist['Close'].min():,.0f}"
                ]
            })
            st.dataframe(price_stats, hide_index=True)
        
        with stats_col2:
            if "write" in user_info["permissions"]:
                st.write("**出来高統計**")
                volume_stats = pd.DataFrame({
                    "項目": ["平均出来高", "最大出来高", "最小出来高"],
                    "値": [
                        f"{hist['Volume'].mean():,.0f}",
                        f"{hist['Volume'].max():,.0f}",
                        f"{hist['Volume'].min():,.0f}"
                    ]
                })
                st.dataframe(volume_stats, hide_index=True)
        
        # 会社情報（管理者権限のみ）
        if info and "admin" in user_info["permissions"]:
            st.subheader("🏢 会社情報")
            
            info_items = []
            safe_fields = ['longName', 'sector', 'industry']  # 安全なフィールドのみ
            
            for field in safe_fields:
                if field in info:
                    value = security_manager.validate_input(str(info[field]))
                    if value:
                        field_names = {
                            'longName': '会社名',
                            'sector': 'セクター', 
                            'industry': '業界'
                        }
                        info_items.append((field_names[field], value))
            
            if 'marketCap' in info and isinstance(info['marketCap'], (int, float)):
                market_cap = info['marketCap'] / 1e12
                if market_cap > 0:
                    info_items.append(("時価総額", f"約{market_cap:.1f}兆円"))
            
            if info_items:
                info_df = pd.DataFrame(info_items, columns=["項目", "値"])
                st.dataframe(info_df, hide_index=True)
    
    except Exception as e:
        # セキュアなエラーメッセージ
        st.error("データの処理中にエラーが発生しました。")
        
        # 管理者のみ詳細エラーを表示
        if "admin" in user_info["permissions"]:
            with st.expander("詳細エラー情報（管理者のみ）"):
                st.code(str(e))

def main():
    """メインエントリーポイント"""
    st.set_page_config(
        page_title="日本株データ分析",
        page_icon="📈",
        layout="wide"
    )
    
    # セッション状態を初期化
    init_session_state()
    
    # 認証チェック
    if not st.session_state.authenticated:
        show_login()
    else:
        show_main_app()

if __name__ == "__main__":
    main() 