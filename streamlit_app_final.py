import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="日本株データ分析アプリ",
    page_icon="📈",
    layout="wide"
)

# メイン画面
st.title("📈 日本株データ分析アプリ")
st.success("✅ アプリケーションが正常に動作しています！")

# 現在時刻
st.info(f"現在時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 基本テスト
st.subheader("🧪 システム状態")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("動作状態", "正常", "✅")

with col2:
    st.metric("接続状態", "OK", "🟢")

with col3:
    st.metric("最終更新", datetime.now().strftime("%H:%M"))

# サンプルデータ
st.subheader("📊 サンプルデータ")

data = pd.DataFrame({
    '銘柄': ['7203.T', '9984.T', '6758.T'],
    '企業名': ['トヨタ', 'SBG', 'ソニー'],
    '価格': [2500, 6000, 12000]
})

st.dataframe(data, use_container_width=True)

# ボタンテスト
if st.button("テストボタン"):
    st.balloons()
    st.success("ボタンが動作しました！")

st.markdown("---")
st.markdown("**テスト版が正常に表示されています**")

# ライブラリテスト
try:
    import yfinance as yf
    st.success("✅ yfinance利用可能")
except:
    st.warning("⚠️ yfinance利用不可")

try:
    import plotly
    st.success("✅ plotly利用可能") 
except:
    st.warning("⚠️ plotly利用不可")

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    📈 日本株データ分析アプリ - 簡易版 | 
    正常動作テスト版
    </div>
    """, 
    unsafe_allow_html=True
)
