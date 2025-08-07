import streamlit as st
import pandas as pd
import numpy as np

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def main():
    """メイン関数 - Streamlit Cloud対応"""
    # ページ設定
    st.set_page_config(
        page_title="日本株データ分析",
        page_icon="📈",
        layout="wide"
    )
    
    # タイトル
    st.title("📈 日本株データ分析アプリ")
    st.markdown("---")
    
    # システム状態表示
    st.subheader("📋 システム状態")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if YFINANCE_AVAILABLE:
            st.success("✅ yfinance 利用可能")
        else:
            st.error("❌ yfinance 利用不可")
    
    with col2:
        if PLOTLY_AVAILABLE:
            st.success("✅ plotly 利用可能")
        else:
            st.error("❌ plotly 利用不可")
    
    with col3:
        st.success("✅ streamlit 動作中")
    
    st.markdown("---")
    
    # 株価データ取得セクション
    if YFINANCE_AVAILABLE:
        st.subheader("📊 株価データ取得")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbol = st.text_input("銘柄コード", value="7203.T", help="例: 7203.T (トヨタ)")
        
        with col2:
            period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y"])
        
        if st.button("データ取得", type="primary"):
            if symbol:
                with st.spinner("データを取得中..."):
                    try:
                        ticker = yf.Ticker(symbol)
                        data = ticker.history(period=period)
                        
                        if not data.empty:
                            st.success("データ取得完了！")
                            
                            # 基本情報
                            latest = data.iloc[-1]
                            prev = data.iloc[-2] if len(data) > 1 else latest
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                change = latest['Close'] - prev['Close']
                                change_pct = (change / prev['Close']) * 100 if prev['Close'] != 0 else 0
                                st.metric("終値", f"¥{latest['Close']:.0f}", f"{change:+.0f} ({change_pct:+.1f}%)")
                            
                            with col2:
                                st.metric("高値", f"¥{latest['High']:.0f}")
                            
                            with col3:
                                st.metric("安値", f"¥{latest['Low']:.0f}")
                            
                            with col4:
                                st.metric("出来高", f"{latest['Volume']:,.0f}")
                            
                            # チャート表示
                            if PLOTLY_AVAILABLE:
                                fig = go.Figure(data=go.Candlestick(
                                    x=data.index,
                                    open=data['Open'],
                                    high=data['High'],
                                    low=data['Low'],
                                    close=data['Close']
                                ))
                                
                                fig.update_layout(
                                    title=f"{symbol} - 株価チャート",
                                    yaxis_title="価格 (¥)",
                                    height=500,
                                    xaxis_rangeslider_visible=False
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.line_chart(data['Close'])
                            
                            # データテーブル
                            with st.expander("📋 データ詳細"):
                                st.dataframe(data.tail(10))
                        else:
                            st.error("データが見つかりませんでした")
                    except Exception as e:
                        st.error(f"エラー: {str(e)}")
            else:
                st.error("銘柄コードを入力してください")
    
    else:
        st.warning("株価データ機能を利用するには yfinance ライブラリが必要です")
        
        # サンプルデータ表示
        st.subheader("📊 サンプルデータ")
        sample_data = pd.DataFrame({
            '日付': pd.date_range('2024-01-01', periods=10),
            '価格': np.random.randint(1000, 2000, 10),
            '出来高': np.random.randint(10000, 50000, 10)
        })
        st.dataframe(sample_data)
    
    # クイックアクセス
    st.subheader("🚀 クイックアクセス")
    if YFINANCE_AVAILABLE:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🚗 トヨタ\n(7203.T)"):
                st.session_state.quick_symbol = "7203.T"
                st.rerun()
        
        with col2:
            if st.button("📱 ソフトバンクG\n(9984.T)"):
                st.session_state.quick_symbol = "9984.T"
                st.rerun()
        
        with col3:
            if st.button("🎮 ソニーG\n(6758.T)"):
                st.session_state.quick_symbol = "6758.T"
                st.rerun()
        
        with col4:
            if st.button("🎯 任天堂\n(7974.T)"):
                st.session_state.quick_symbol = "7974.T"
                st.rerun()
        
        # クイックアクセス処理
        if hasattr(st.session_state, 'quick_symbol'):
            symbol = st.session_state.quick_symbol
            with st.spinner(f"{symbol} のデータを取得中..."):
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="1y")
                    if not data.empty:
                        st.success(f"{symbol} のデータを取得しました！")
                        # 基本表示のみ
                        latest = data.iloc[-1]
                        st.metric(f"{symbol} 終値", f"¥{latest['Close']:.0f}")
                except Exception as e:
                    st.error(f"データ取得エラー: {str(e)}")
                finally:
                    if hasattr(st.session_state, 'quick_symbol'):
                        del st.session_state.quick_symbol
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")
        st.info("アプリケーション設定")
        
        if st.button("アプリ再起動"):
            st.rerun()
    
    st.markdown("---")
    st.info("画面が正常に表示されていれば、基本機能は動作しています。")

# Streamlit Cloud対応のエントリーポイント
if __name__ == "__main__":
    main()
else:
    # Streamlit Cloudで実行される場合
    main()
