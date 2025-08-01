#!/usr/bin/env python3
"""
日本株式データアプリケーション - Streamlit Web UI
Streamlit Cloud用エントリーポイント
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

# web_app.pyのmain関数をインポートして実行
from web.web_app import main

if __name__ == "__main__":
    main() 