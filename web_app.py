#!/usr/bin/env python3
"""
Streamlit Cloud 互換エントリーポイント
本来は `streamlit_app.py` をメインに使用しますが、
Cloud 設定が `web_app.py` の場合でも起動できるようにする薄いラッパーです。
"""

import os
import sys

# プロジェクトルートをパスに追加（Cloud 環境でも安全）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

if __name__ == "__main__":
    from streamlit_app import main  # type: ignore
    main()

