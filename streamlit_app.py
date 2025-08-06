#!/usr/bin/env python3
"""
日本株式データアプリケーション - Streamlit Web UI
Streamlit用エントリーポイント
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

try:
    # web_app.pyのmain関数をインポートして実行
    from src.web.web_app import main
except ImportError:
    # フォールバック: 直接パスを指定
    try:
        from web.web_app import main
    except ImportError:
        # 最後の手段: 相対インポート
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_app", os.path.join(src_dir, "web", "web_app.py"))
        web_app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_app_module)
        main = web_app_module.main

if __name__ == "__main__":
    main() 