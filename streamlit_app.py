"""
日本株データ分析アプリ - Streamlit Cloud対応版（軽量版）
必要最小限の機能のみ
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="日本株データ分析",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 日本株データ分析アプリ")
    st.markdown("---")
    
    # サイドバーで銘柄選択
    st.sidebar.header("銘柄選択")
    
    # よく使われる銘柄コード
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
        # データ取得
        with st.spinner(f"{selected_stock}のデータを取得中..."):
            stock = yf.Ticker(stock_code)
            hist = stock.history(period=period)
            info = stock.info
        
        if len(hist) == 0:
            st.error("データが取得できませんでした。")
            return
        
        # 基本情報表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = hist['Close'].iloc[-1]
            st.metric("現在価格", f"¥{current_price:,.0f}")
        
        with col2:
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
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 出来高チャート
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
        
        # 会社情報（可能な場合）
        if info:
            st.subheader("🏢 会社情報")
            
            info_items = []
            if 'longName' in info:
                info_items.append(("会社名", info['longName']))
            if 'sector' in info:
                info_items.append(("セクター", info['sector']))
            if 'industry' in info:
                info_items.append(("業界", info['industry']))
            if 'marketCap' in info:
                market_cap = info['marketCap'] / 1e12
                info_items.append(("時価総額", f"約{market_cap:.1f}兆円"))
            
            if info_items:
                info_df = pd.DataFrame(info_items, columns=["項目", "値"])
                st.dataframe(info_df, hide_index=True)
    
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.info("別の銘柄を選択してお試しください。")

if __name__ == "__main__":
    main() 