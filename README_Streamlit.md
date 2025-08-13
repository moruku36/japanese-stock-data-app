# 日本株式データ分析システム - Streamlit Cloud版

## 🚀 デプロイ方法

### Streamlit Cloudでの公開

1. **GitHubリポジトリを準備**
   - このリポジトリをGitHubにプッシュ
   - プライベートリポジトリの場合は、Streamlit Cloudでアクセス権限を設定

2. **Streamlit Cloudでデプロイ**
   - [Streamlit Cloud](https://share.streamlit.io/)にアクセス
   - GitHubアカウントでログイン
   - 「New app」をクリック
   - リポジトリを選択
   - **Main file path**: `streamlit_app.py`
   - **Python version**: 3.11以上
   - 「Deploy!」をクリック

3. **環境変数の設定（必要に応じて）**
   - APIキーなどの機密情報は環境変数として設定
   - Streamlit Cloudの管理画面で設定可能

## 📁 ファイル構造

```
japanese-stock-data-app/
├── streamlit_app.py        # エントリーポイント（Cloud/ローカル共通）
├── requirements.txt        # Python依存関係
├── .streamlit/
│   └── config.toml        # Streamlit設定
├── src/
│   ├── web/
│   │   └── web_app.py     # メインアプリケーション
│   ├── core/              # コア機能
│   ├── analysis/          # 分析機能
│   ├── data/              # データ処理
│   ├── ml/                # 機械学習
│   └── utils/             # ユーティリティ
└── config/                # 設定ファイル
```

## 🔧 設定

### Streamlit設定 (.streamlit/config.toml)

```toml
[server]
headless = true
enableCORS = false
port = 8501

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#3b82f6"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

## 📊 機能

- 📈 リアルタイム株価監視
- 📊 テクニカル分析
- 🏢 ファンダメンタル分析
- ⚡ 高度なデータ分析
- 📦 複数銘柄分析
- 💾 データエクスポート

## 🐛 トラブルシューティング

### 「Main module does not exist」エラー

このエラーが発生した場合：

1. **ファイル名の確認**
   - プロジェクトルートに`streamlit_app.py`が存在することを確認
   - ファイル名が正確であることを確認

2. **パスの確認**
   - `streamlit_app.py`がプロジェクトルートにあることを確認
   - サブディレクトリに配置されていないことを確認

3. **インポートエラーの確認**
   - `src/web/web_app.py`が正しくインポートされていることを確認
   - パス設定が正しいことを確認

### モジュールインポートエラー

1. **sys.pathの設定確認**
   - `streamlit_app.py`で`sys.path.insert(0, src_dir)`が設定されていることを確認
   - `sys.path.insert(0, project_root)`が設定されていることを確認

2. **依存関係の確認**
   - `requirements.txt`に必要なパッケージが含まれていることを確認
   - バージョン指定が適切であることを確認

## 🔄 更新方法

1. **ローカルで変更をテスト**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **GitHubにプッシュ**
   ```bash
   git add .
   git commit -m "Update for Streamlit Cloud"
   git push origin main
   ```

3. **Streamlit Cloudで自動デプロイ**
   - GitHubにプッシュすると自動的にデプロイが開始されます
   - デプロイ状況はStreamlit Cloudの管理画面で確認可能

## 📞 サポート

問題が発生した場合は：

1. Streamlit Cloudのログを確認
2. ローカルでの動作確認
3. GitHubのIssuesで報告

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。 