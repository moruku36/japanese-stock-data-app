# 📁 プロジェクト構造

最終的な整理後のプロジェクト構造：

```
japanese-stock-data-app/
├── streamlit_app.py           # メインアプリケーション（v2.0）
├── requirements.txt           # 依存関係（最適化済み）
├── README.md                  # プロジェクト説明
├── README_Streamlit.md        # Streamlit固有の説明
├── STREAMLIT_CLOUD_GUIDE.md   # Streamlit Cloud デプロイガイド
├── packages.txt               # システムパッケージ依存関係
├── 
├── .streamlit/                # Streamlit設定
├── .devcontainer/             # 開発コンテナ設定
├── .venv/                     # 仮想環境
├── 
├── archive/                   # アーカイブフォルダ
│   ├── README.md              # アーカイブ説明
│   ├── development_versions/  # 開発過程のファイル
│   │   ├── streamlit_app_enhanced.py
│   │   ├── streamlit_app_fixed.py
│   │   ├── streamlit_app_minimal.py
│   │   ├── streamlit_app_robust.py
│   │   ├── streamlit_app_simple.py
│   │   ├── streamlit_app_ultra_light.py
│   │   └── streamlit_app_v2.py
│   └── old_files/             # 古いファイル
│       ├── app.py
│       ├── web_app.py
│       ├── test_*.py
│       └── stock_system.log
├── 
├── cache/                     # データキャッシュ
├── config/                    # 設定ファイル
├── docs/                      # ドキュメント
├── src/                       # ソースコード（モジュール）
├── stock_data/                # 株価データ
└── tests/                     # テストコード
```

## 📋 変更点

### ✅ 整理完了項目
1. **メインファイル**: `streamlit_app.py` を最新版（v2.0）に更新
2. **開発版ファイル**: 7つの開発版を `archive/development_versions/` に移動
3. **古いファイル**: 不要な古いファイルを `archive/old_files/` に移動
4. **キャッシュクリーンアップ**: `__pycache__` フォルダを削除

### 🗂️ アーカイブされたファイル
- 開発過程の各種バージョン（enhanced, fixed, minimal, robust, simple, ultra_light, v2）
- 古いメインファイル（main.py, app.py, web_app.py）  
- テストファイル（test_*.py）
- ログファイル（stock_system.log）

### 🔧 依存関係
現在のメインアプリケーションは以下に依存：
- `streamlit` - Webアプリフレームワーク
- `pandas` - データ処理
- `numpy` - 数値計算
- `yfinance` - 株価データ取得
- `plotly` - インタラクティブチャート

全てのモジュール依存関係は正常に保たれています。

## 🚀 使用方法

```bash
# メインアプリケーション実行
streamlit run streamlit_app.py

# 本番環境
https://japanese-stock-data-app.streamlit.app/
```
