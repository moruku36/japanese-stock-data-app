# -*- coding: utf-8 -*-
"""
日本株データ分析アプリ - シンプル版
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

# ページ設定
st.set_page_config(
    page_title="日本株データ分析",
    page_icon="📈",
    layout="wide"
)

def fetch_stock_data(symbol, period="1y"):
    """株価データ取得"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        return hist if not hist.empty else None
    except Exception as e:
        st.error(f"データ取得エラー: {str(e)}")
        return None

def show_stock_chart(hist, symbol):
    """株価チャート表示"""
    if hist is None or hist.empty:
        return
    
    fig = go.Figure(data=go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close']
    ))
    
    fig.update_layout(
        title=f"{symbol} - 株価チャート",
        yaxis_title="価格 (¥)",
        height=500,
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    """メイン関数"""
    st.title("📈 日本株データ分析アプリ")
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")
        symbol = st.text_input("銘柄コード", value="7203.T", help="例: 7203.T (トヨタ)")
        period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
        
        if st.button("データ取得", type="primary"):
            if symbol:
                with st.spinner("データを取得中..."):
                    data = fetch_stock_data(symbol, period)
                    if data is not None:
                        st.session_state.stock_data = data
                        st.session_state.selected_stock = symbol
                        st.success("データ取得完了！")
                        st.rerun()
                    else:
                        st.error("データ取得に失敗しました")
            else:
                st.error("銘柄コードを入力してください")
    
    # メインコンテンツ
    if hasattr(st.session_state, 'stock_data') and st.session_state.stock_data is not None:
        hist = st.session_state.stock_data
        symbol = st.session_state.selected_stock
        
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
        
        # チャート表示
        show_stock_chart(hist, symbol)
        
        # データテーブル
        with st.expander("📋 最新データ（10日分）"):
            st.dataframe(hist.tail(10))
    
    else:
        st.info("👈 サイドバーから銘柄を選択してデータを取得してください")
        
        # クイックアクセス
        st.subheader("🚀 クイックアクセス")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🚗 トヨタ\n(7203.T)"):
                with st.spinner("データを取得中..."):
                    data = fetch_stock_data("7203.T", "1y")
                    if data is not None:
                        st.session_state.stock_data = data
                        st.session_state.selected_stock = "7203.T"
                        st.rerun()
        
        with col2:
            if st.button("📱 ソフトバンクG\n(9984.T)"):
                with st.spinner("データを取得中..."):
                    data = fetch_stock_data("9984.T", "1y")
                    if data is not None:
                        st.session_state.stock_data = data
                        st.session_state.selected_stock = "9984.T"
                        st.rerun()
        
        with col3:
            if st.button("🎮 ソニーG\n(6758.T)"):
                with st.spinner("データを取得中..."):
                    data = fetch_stock_data("6758.T", "1y")
                    if data is not None:
                        st.session_state.stock_data = data
                        st.session_state.selected_stock = "6758.T"
                        st.rerun()
        
        with col4:
            if st.button("🎯 任天堂\n(7974.T)"):
                with st.spinner("データを取得中..."):
                    data = fetch_stock_data("7974.T", "1y")
                    if data is not None:
                        st.session_state.stock_data = data
                        st.session_state.selected_stock = "7974.T"
                        st.rerun()

# アプリ実行
if __name__ == "__main__":
    main()
else:
    main()
