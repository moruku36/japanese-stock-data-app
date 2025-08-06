#!/usr/bin/env python3
"""
日本株式データアプリケーション - Streamlit Cloud対応版
Streamlit用エントリーポイント
"""

import sys
import os
import streamlit as st

# Streamlit Cloud環境対応のパス設定
def setup_paths():
    """環境に応じたパス設定"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Streamlit Cloud環境の判定
    if os.path.exists('/app'):
        # Streamlit Cloud環境
        base_paths = [
            '/app/src',
            '/app',
            os.path.join('/app', 'src')
        ]
    else:
        # ローカル環境
        src_dir = os.path.join(current_dir, 'src')
        base_paths = [
            src_dir,
            current_dir,
            os.path.join(current_dir, 'src')
        ]
    
    # パスを設定
    for path in base_paths:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)

# パス設定を実行
setup_paths()

# アプリケーションの実行
def run_app():
    """アプリケーションを実行"""
    try:
        # メインのweb_appモジュールをインポート
        from src.web.web_app import main
        main()
    except ImportError as e1:
        try:
            # フォールバック1: 直接パス指定
            from web.web_app import main
            main()
        except ImportError as e2:
            # フォールバック2: 動的インポート
            try:
                import importlib.util
                possible_paths = [
                    os.path.join('/app', 'src', 'web', 'web_app.py'),
                    os.path.join(os.getcwd(), 'src', 'web', 'web_app.py'),
                    os.path.join(os.path.dirname(__file__), 'src', 'web', 'web_app.py')
                ]
                
                for app_path in possible_paths:
                    if os.path.exists(app_path):
                        spec = importlib.util.spec_from_file_location("web_app", app_path)
                        web_app_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(web_app_module)
                        web_app_module.main()
                        return
                
                # すべて失敗した場合
                st.error("アプリケーションの起動に失敗しました")
                st.error(f"インポートエラー 1: {e1}")
                st.error(f"インポートエラー 2: {e2}")
                st.info("現在のパス:")
                for path in sys.path:
                    st.info(f"  - {path}")
                
            except Exception as e3:
                st.error(f"動的インポートエラー: {e3}")

if __name__ == "__main__":
    run_app() 