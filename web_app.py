#!/usr/bin/env python3
"""
日本株式データアプリケーション - Streamlit Cloud用エントリーポイント
セキュア軽量版を実行
"""

import sys
import os
import streamlit as st

# プロジェクトルートを設定
current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    # セキュア軽量版のstreamlit_app.pyをインポート
    sys.path.insert(0, current_dir)
    from streamlit_app import main
    
    # メイン実行
    main()
    
except ImportError as e1:
    st.error("❌ セキュア版アプリケーションの読み込みでエラーが発生しました")
    st.error(f"インポートエラー: {e1}")
    st.info("📁 streamlit_app.pyが見つからないか、依存関係に問題があります")
    
    # デバッグ情報を表示
    st.markdown("### デバッグ情報")
    st.markdown(f"**現在のディレクトリ**: {current_dir}")
    st.markdown(f"**Pythonパス**: {sys.path[:3]}")
    
    # ファイル存在確認
    streamlit_app_file = os.path.join(current_dir, "streamlit_app.py")
    if os.path.exists(streamlit_app_file):
        st.success("✅ streamlit_app.pyファイルが存在します")
    else:
        st.error("❌ streamlit_app.pyファイルが見つかりません")
    
    st.stop()

except Exception as e:
    st.error("❌ アプリケーション実行中にエラーが発生しました")
    st.error(f"エラー詳細: {e}")
    st.info("セキュア版アプリケーションを確認してください")
    st.stop() 