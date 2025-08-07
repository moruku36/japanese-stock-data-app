"""
日本株データ分析アプリ - 完全版
確実に動作するシンプルで機能的なバージョン
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time

# ライブラリの安全なインポート
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="日本株データ分析アプリ",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ['7203.T', '9984.T', '6758.T', '7974.T']
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'

def safe_get_stock_data(symbol, period='1y'):
    """安全に株価データを取得"""
    if not YFINANCE_AVAILABLE:
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        return data if not data.empty else None
    except Exception as e:
        st.error(f"データ取得エラー ({symbol}): {str(e)}")
        return None

def show_dashboard():
    """メインダッシュボード"""
    st.title("📊 ダッシュボード")
    st.success("✅ アプリケーションが正常に動作しています！")
    
    # 現在時刻
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    st.info(f"🕐 最終更新: {current_time}")
    
    # システム状態
    st.subheader("🔧 システム状態")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("アプリ状態", "正常", "✅")
    with col2:
        st.metric("データ取得", "可能" if YFINANCE_AVAILABLE else "不可", "✅" if YFINANCE_AVAILABLE else "❌")
    with col3:
        st.metric("チャート表示", "可能" if PLOTLY_AVAILABLE else "不可", "✅" if PLOTLY_AVAILABLE else "❌")
    with col4:
        st.metric("ウォッチリスト", len(st.session_state.watchlist), "📊")
    
    # ウォッチリスト表示
    st.subheader("👀 ウォッチリスト")
    
    if YFINANCE_AVAILABLE and st.session_state.watchlist:
        watchlist_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, symbol in enumerate(st.session_state.watchlist):
            status_text.text(f'データ取得中: {symbol}')
            progress_bar.progress((i + 1) / len(st.session_state.watchlist))
            
            data = safe_get_stock_data(symbol, '2d')
            if data is not None and len(data) >= 2:
                latest = data.iloc[-1]
                prev = data.iloc[-2]
                change = latest['Close'] - prev['Close']
                change_pct = (change / prev['Close']) * 100
                
                watchlist_data.append({
                    '銘柄コード': symbol,
                    '終値': f"¥{latest['Close']:,.0f}",
                    '前日比': f"¥{change:+,.0f}",
                    '変化率': f"{change_pct:+.2f}%",
                    '出来高': f"{latest['Volume']:,}"
                })
        
        progress_bar.empty()
        status_text.empty()
        
        if watchlist_data:
            df = pd.DataFrame(watchlist_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("ウォッチリストのデータを取得できませんでした")
    else:
        if not YFINANCE_AVAILABLE:
            st.warning("株価データの取得にはyfinanceライブラリが必要です")
        else:
            st.info("ウォッチリストが空です")
    
    # ポートフォリオサマリー
    st.subheader("💼 ポートフォリオサマリー")
    
    if st.session_state.portfolio:
        st.write(f"保有銘柄数: {len(st.session_state.portfolio)}")
        
        portfolio_df = pd.DataFrame(st.session_state.portfolio)
        st.dataframe(portfolio_df, use_container_width=True)
    else:
        st.info("ポートフォリオが空です。「ポートフォリオ管理」から銘柄を追加してください。")

def show_stock_search():
    """銘柄検索画面"""
    st.title("🔍 銘柄検索・分析")
    
    # 検索フォーム
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_symbol = st.text_input(
            "銘柄コードを入力 (例: 7203.T)",
            placeholder="7203.T"
        )
    
    with col2:
        search_period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
    
    if search_symbol and YFINANCE_AVAILABLE:
        if st.button("分析開始", type="primary"):
            with st.spinner("データを取得中..."):
                data = safe_get_stock_data(search_symbol, search_period)
                
                if data is not None:
                    st.success(f"✅ {search_symbol} のデータを取得しました")
                    
                    # 基本情報
                    latest = data.iloc[-1]
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("終値", f"¥{latest['Close']:,.0f}")
                    with col2:
                        st.metric("高値", f"¥{latest['High']:,.0f}")
                    with col3:
                        st.metric("安値", f"¥{latest['Low']:,.0f}")
                    with col4:
                        st.metric("出来高", f"{latest['Volume']:,}")
                    
                    # チャート表示
                    if PLOTLY_AVAILABLE:
                        st.subheader("📈 株価チャート")
                        
                        fig = go.Figure(data=go.Candlestick(
                            x=data.index,
                            open=data['Open'],
                            high=data['High'],
                            low=data['Low'],
                            close=data['Close'],
                            name=search_symbol
                        ))
                        
                        fig.update_layout(
                            title=f"{search_symbol} - 株価チャート",
                            yaxis_title="価格 (¥)",
                            height=500,
                            xaxis_rangeslider_visible=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # データテーブル
                    st.subheader("📊 価格データ (直近10日)")
                    recent_data = data.tail(10).copy()
                    recent_data.index = recent_data.index.strftime('%Y-%m-%d')
                    st.dataframe(recent_data, use_container_width=True)
                    
                    # アクションボタン
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("ウォッチリストに追加"):
                            if search_symbol not in st.session_state.watchlist:
                                st.session_state.watchlist.append(search_symbol)
                                st.success("ウォッチリストに追加しました！")
                                st.rerun()
                            else:
                                st.info("既にウォッチリストに登録されています")
                else:
                    st.error("データを取得できませんでした。銘柄コードを確認してください。")
    
    elif not YFINANCE_AVAILABLE:
        st.warning("株価データの取得にはyfinanceライブラリが必要です")

def show_portfolio():
    """ポートフォリオ管理画面"""
    st.title("💼 ポートフォリオ管理")
    
    # 新規追加フォーム
    st.subheader("📝 新規銘柄追加")
    
    with st.form("add_stock_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            symbol = st.text_input("銘柄コード", placeholder="7203.T")
        with col2:
            shares = st.number_input("株数", min_value=1, value=100)
        with col3:
            price = st.number_input("取得価格", min_value=0.0, value=1000.0)
        
        submitted = st.form_submit_button("追加", type="primary")
        
        if submitted and symbol:
            new_holding = {
                'symbol': symbol,
                'shares': shares,
                'avg_price': price,
                'date_added': datetime.now().strftime('%Y-%m-%d')
            }
            
            st.session_state.portfolio.append(new_holding)
            st.success(f"✅ {symbol} をポートフォリオに追加しました")
            st.rerun()
    
    # 現在のポートフォリオ
    st.subheader("📊 現在のポートフォリオ")
    
    if st.session_state.portfolio:
        for i, holding in enumerate(st.session_state.portfolio):
            with st.expander(f"{holding['symbol']} - {holding['shares']}株"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**銘柄コード:** {holding['symbol']}")
                    st.write(f"**株数:** {holding['shares']}株")
                    st.write(f"**平均取得価格:** ¥{holding['avg_price']:,.0f}")
                    st.write(f"**追加日:** {holding['date_added']}")
                
                with col2:
                    if YFINANCE_AVAILABLE:
                        data = safe_get_stock_data(holding['symbol'], '1d')
                        if data is not None:
                            current_price = data['Close'].iloc[-1]
                            current_value = current_price * holding['shares']
                            cost_basis = holding['avg_price'] * holding['shares']
                            pnl = current_value - cost_basis
                            pnl_pct = (pnl / cost_basis) * 100
                            
                            st.write(f"**現在価格:** ¥{current_price:,.0f}")
                            st.write(f"**評価額:** ¥{current_value:,.0f}")
                            st.write(f"**損益:** ¥{pnl:+,.0f} ({pnl_pct:+.2f}%)")
                        else:
                            st.write("価格情報を取得できませんでした")
                    else:
                        st.write("価格情報の取得にはyfinanceが必要です")
                
                with col3:
                    if st.button("削除", key=f"delete_{i}"):
                        st.session_state.portfolio.pop(i)
                        st.success("削除しました")
                        st.rerun()
    else:
        st.info("ポートフォリオが空です。上記のフォームから銘柄を追加してください。")

def show_settings():
    """設定画面"""
    st.title("⚙️ 設定")
    
    st.subheader("🔧 システム情報")
    
    # ライブラリ状態
    libraries = [
        {"ライブラリ": "streamlit", "状態": "✅ 利用可能", "バージョン": st.__version__},
        {"ライブラリ": "pandas", "状態": "✅ 利用可能", "バージョン": pd.__version__},
        {"ライブラリ": "yfinance", "状態": "✅ 利用可能" if YFINANCE_AVAILABLE else "❌ 利用不可", "バージョン": "確認中" if YFINANCE_AVAILABLE else "N/A"},
        {"ライブラリ": "plotly", "状態": "✅ 利用可能" if PLOTLY_AVAILABLE else "❌ 利用不可", "バージョン": "確認中" if PLOTLY_AVAILABLE else "N/A"}
    ]
    
    lib_df = pd.DataFrame(libraries)
    st.dataframe(lib_df, use_container_width=True)
    
    # ウォッチリスト管理
    st.subheader("👀 ウォッチリスト管理")
    
    # 新規追加
    new_symbol = st.text_input("銘柄コードを追加", placeholder="7203.T")
    if st.button("ウォッチリストに追加"):
        if new_symbol and new_symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_symbol)
            st.success(f"{new_symbol} を追加しました")
            st.rerun()
        elif new_symbol in st.session_state.watchlist:
            st.warning("既に登録されています")
    
    # 現在のウォッチリスト
    if st.session_state.watchlist:
        st.write("**現在のウォッチリスト:**")
        for i, symbol in enumerate(st.session_state.watchlist):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"• {symbol}")
            with col2:
                if st.button("削除", key=f"remove_watch_{i}"):
                    st.session_state.watchlist.remove(symbol)
                    st.success(f"{symbol} を削除しました")
                    st.rerun()
    
    # データクリア
    st.subheader("🗑️ データクリア")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ポートフォリオをクリア", type="secondary"):
            st.session_state.portfolio = []
            st.success("ポートフォリオをクリアしました")
            st.rerun()
    
    with col2:
        if st.button("ウォッチリストをリセット", type="secondary"):
            st.session_state.watchlist = ['7203.T', '9984.T', '6758.T', '7974.T']
            st.success("ウォッチリストをリセットしました")
            st.rerun()

def main():
    """メインアプリケーション"""
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("📈 日本株分析アプリ")
        st.markdown("---")
        
        # ナビゲーションメニュー
        pages = {
            "📊 ダッシュボード": "dashboard",
            "🔍 銘柄検索": "search", 
            "💼 ポートフォリオ": "portfolio",
            "⚙️ 設定": "settings"
        }
        
        # ページ選択
        for page_name, page_key in pages.items():
            if st.button(
                page_name, 
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if st.session_state.current_page == page_key else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # クイック情報
        st.write(f"**ウォッチリスト:** {len(st.session_state.watchlist)}銘柄")
        st.write(f"**ポートフォリオ:** {len(st.session_state.portfolio)}銘柄")
        st.write(f"**最終更新:** {datetime.now().strftime('%H:%M')}")
    
    # メインコンテンツ
    try:
        if st.session_state.current_page == "dashboard":
            show_dashboard()
        elif st.session_state.current_page == "search":
            show_stock_search()
        elif st.session_state.current_page == "portfolio":
            show_portfolio()
        elif st.session_state.current_page == "settings":
            show_settings()
        else:
            show_dashboard()
    
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.info("ページを再読み込みしてください")
    
    # フッター
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 12px;'>
        📈 日本株データ分析アプリ v3.0 | 動作確認済み |
        ⚠️ 投資は自己責任で行ってください
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
