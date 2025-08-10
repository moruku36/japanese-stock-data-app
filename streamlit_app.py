#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit エントリポイント
`src/web/web_app.py` の `main()` を起動します。
"""

import os
import sys

# プロジェクトのsrcディレクトリをパスに追加
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, 'src')
if os.path.isdir(SRC_DIR):
    sys.path.insert(0, SRC_DIR)

from web.web_app import main  # type: ignore

if __name__ == "__main__":
    main()

