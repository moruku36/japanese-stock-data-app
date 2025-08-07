"""
日本株データ分析アプリ - 超軽量版
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="日本株データ分析",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 日本株データ分析アプリ")
    
    # サイドバーで銘柄選択
    with st.sidebar:
        st.header("銘柄選択")
        symbol = st.text_input("銘柄コード", value="7203.T", help="例: 7203.T (トヨタ)")
        period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y"], index=3)
        
        if st.button("データ取得", type="primary"):
            try:
                with st.spinner("データ取得中..."):
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    
                    if not hist.empty:
                        st.session_state['data'] = hist
                        st.session_state['symbol'] = symbol
                        st.success("✅ データ取得完了")
                    else:
                        st.error("❌ データが見つかりません")
            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")
    
    # メインコンテンツ
    if 'data' in st.session_state and st.session_state['data'] is not None:
        hist = st.session_state['data']
        symbol = st.session_state['symbol']
        
        # 基本情報
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
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
        
        st.markdown("---")
        
        # 価格チャート
        st.subheader(f"📊 {symbol} 価格チャート")
        
        fig = go.Figure(data=go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close']
        ))
        
        fig.update_layout(
            title=f"{symbol} 株価",
            yaxis_title="価格 (¥)",
            height=500,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 簡単な移動平均
        try:
            hist['MA5'] = hist['Close'].rolling(window=5).mean()
            hist['MA25'] = hist['Close'].rolling(window=25).mean()
            
            fig_ma = go.Figure()
            
            fig_ma.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name='終値',
                line=dict(color='black')
            ))
            
            fig_ma.add_trace(go.Scatter(
                x=hist.index,
                y=hist['MA5'],
                mode='lines',
                name='5日移動平均',
                line=dict(color='red')
            ))
            
            fig_ma.add_trace(go.Scatter(
                x=hist.index,
                y=hist['MA25'],
                mode='lines',
                name='25日移動平均',
                line=dict(color='blue')
            ))
            
            fig_ma.update_layout(
                title="移動平均線",
                yaxis_title="価格 (¥)",
                height=400
            )
            
            st.plotly_chart(fig_ma, use_container_width=True)
        except:
            st.info("移動平均の計算でエラーが発生しました")
        
        # データテーブル
        with st.expander("📋 最新データ"):
            st.dataframe(hist.tail(10))
    
    else:
        st.info("👈 サイドバーから銘柄を選択してデータを取得してください")
        
        # クイックアクセス
        st.subheader("🚀 クイックアクセス")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🚗 トヨタ (7203.T)"):
                st.session_state['quick_symbol'] = "7203.T"
        
        with col2:
            if st.button("📱 ソフトバンク (9984.T)"):
                st.session_state['quick_symbol'] = "9984.T"
        
        with col3:
            if st.button("🎮 ソニー (6758.T)"):
                st.session_state['quick_symbol'] = "6758.T"
        
        with col4:
            if st.button("🎯 任天堂 (7974.T)"):
                st.session_state['quick_symbol'] = "7974.T"
        
        # クイックアクセスが選択された場合
        if 'quick_symbol' in st.session_state:
            symbol = st.session_state['quick_symbol']
            try:
                with st.spinner(f"{symbol} のデータを取得中..."):
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="1y")
                    
                    if not hist.empty:
                        st.session_state['data'] = hist
                        st.session_state['symbol'] = symbol
                        del st.session_state['quick_symbol']
                        st.rerun()
            except Exception as e:
                st.error(f"データ取得エラー: {str(e)}")
                del st.session_state['quick_symbol']

if __name__ == "__main__":
    main()
