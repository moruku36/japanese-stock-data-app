#!/usr/bin/env python3
"""
日本株式データアプリケーション - Streamlit Cloud用エントリーポイント
"""

import sys
import os

# プロジェクトルートとsrcディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')

# パスを設定
sys.path.insert(0, src_dir)
sys.path.insert(0, current_dir)

try:
    # メイン関数をインポート
    from src.web.web_app import main
except ImportError as e1:
    try:
        # フォールバック: 直接パスを指定
        import importlib.util
        web_app_path = os.path.join(src_dir, "web", "web_app.py")
        spec = importlib.util.spec_from_file_location("web_app", web_app_path)
        web_app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app_module)
        main = web_app_module.main
    except Exception as e2:
        # エラーハンドリング
        import streamlit as st
        st.error("❌ アプリケーションの読み込みでエラーが発生しました")
        st.error(f"インポートエラー1: {e1}")
        st.error(f"インポートエラー2: {e2}")
        st.info("📁 現在のディレクトリ構造を確認してください")
        
        # デバッグ情報を表示
        st.markdown("### デバッグ情報")
        st.markdown(f"**現在のディレクトリ**: {current_dir}")
        st.markdown(f"**srcディレクトリ**: {src_dir}")
        st.markdown(f"**Pythonパス**: {sys.path[:3]}")
        
        if os.path.exists(src_dir):
            st.success("✅ srcディレクトリが存在します")
            web_dir = os.path.join(src_dir, "web")
            if os.path.exists(web_dir):
                st.success("✅ src/webディレクトリが存在します")
                web_app_file = os.path.join(web_dir, "web_app.py")
                if os.path.exists(web_app_file):
                    st.success("✅ src/web/web_app.pyファイルが存在します")
                else:
                    st.error("❌ src/web/web_app.pyファイルが見つかりません")
            else:
                st.error("❌ src/webディレクトリが見つかりません")
        else:
            st.error("❌ srcディレクトリが見つかりません")
        
        st.stop()

# メイン実行
if __name__ == "__main__":
    main()
else:
    # Streamlit Cloudから直接実行される場合
    main() 