import streamlit as st

st.title("Hello Streamlit!")
st.write("このアプリが表示されていれば、基本的な動作は確認できています。")

# 簡単なテスト
if st.button("テストボタン"):
    st.success("ボタンが正常に動作しています！")

st.info("このメッセージが表示されていれば、Streamlitは正常に動作しています。")
