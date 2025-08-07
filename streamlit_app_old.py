import streamlit as st
import pandas as pd
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="日本株分析アプリ - 最小版",
    page_icon="📈",
    layout="wide"
)

# メイン画面
st.title("📈 日本株データ分析アプリ")
st.success("✅ 最小軽量版が正常に動作しています！")

# 現在時刻
st.info(f"起動時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# システム状態
st.subheader("🧪 システム状態")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("アプリ状態", "正常", "✅")

with col2:
    st.metric("バージョン", "軽量版", "🚀")

with col3:
    st.metric("更新時刻", datetime.now().strftime("%H:%M"))

# テストデータ
st.subheader("📊 テストデータ")

# 簡単なデータフレーム
test_data = pd.DataFrame({
    '銘柄コード': ['7203.T', '9984.T', '6758.T'],
    '企業名': ['トヨタ自動車', 'ソフトバンクG', 'ソニーG'],
    '株価': [2500, 6000, 12000],
    '前日比': ['+50', '-100', '+200']
})

st.dataframe(test_data, use_container_width=True)

# インタラクション要素
st.subheader("🎮 インタラクション")

# 選択ボックス
selected_stock = st.selectbox(
    "銘柄を選択してください:",
    ['7203.T - トヨタ自動車', '9984.T - ソフトバンクG', '6758.T - ソニーG']
)

st.write(f"選択: {selected_stock}")

# ボタン
if st.button("🎈 テストボタン", type="primary"):
    st.balloons()
    st.success("ボタンが正常に動作しました！")

# 区切り線
st.markdown("---")

# ライブラリ確認
st.subheader("📚 ライブラリ状態")

libraries = []

# pandas確認
try:
    import pandas as pd
    libraries.append({"ライブラリ": "pandas", "状態": "✅ 利用可能", "バージョン": pd.__version__})
except ImportError:
    libraries.append({"ライブラリ": "pandas", "状態": "❌ 利用不可", "バージョン": "N/A"})

# streamlit確認
try:
    import streamlit as st
    libraries.append({"ライブラリ": "streamlit", "状態": "✅ 利用可能", "バージョン": st.__version__})
except:
    libraries.append({"ライブラリ": "streamlit", "状態": "❌ 利用不可", "バージョン": "N/A"})

# yfinance確認
try:
    import yfinance as yf
    libraries.append({"ライブラリ": "yfinance", "状態": "✅ 利用可能", "バージョン": "確認中"})
except ImportError:
    libraries.append({"ライブラリ": "yfinance", "状態": "❌ 利用不可", "バージョン": "N/A"})

# plotly確認
try:
    import plotly
    libraries.append({"ライブラリ": "plotly", "状態": "✅ 利用可能", "バージョン": plotly.__version__})
except ImportError:
    libraries.append({"ライブラリ": "plotly", "状態": "❌ 利用不可", "バージョン": "N/A"})

# ライブラリ状態を表示
lib_df = pd.DataFrame(libraries)
st.dataframe(lib_df, use_container_width=True)

# フッター
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 14px;'>
    📈 日本株データ分析アプリ - 最小軽量版 v1.0<br>
    正常動作確認用テストバージョン
    </div>
    """, 
    unsafe_allow_html=True
)

# 動作確認メッセージ
st.success("🎯 最小軽量版が正常に表示されています！")
