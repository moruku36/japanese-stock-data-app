#!/usr/bin/env python3
"""
日本株式データアプリケーション - Streamlit Web UI
メインエントリーポイント
"""

import sys
import os

# プロジェクトルートとsrcディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
project_root = current_dir

# パスを設定
sys.path.insert(0, src_dir)
sys.path.insert(0, project_root)

# Streamlitアプリケーションを実行
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    # Streamlitアプリケーションを実行
    sys.argv = ["streamlit", "run", "src/web/web_app.py", "--server.port=8501"]
    sys.exit(stcli.main()) 