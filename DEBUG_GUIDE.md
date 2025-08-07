# Streamlit Cloudデバッグガイド

## 問題診断チェックリスト

### 1. Streamlit Cloudでの確認事項
- アプリのURL: https://moruku36-japanese-stock-data-app-streamlit-app-xxxxx.streamlit.app/
- デプロイ状況: GitHubプッシュ後、5分程度で反映
- エラーログ: Streamlit Cloud の "Manage app" から確認可能

### 2. 最も可能性の高い原因
1. **リポジトリ設定の問題**
   - メインファイル名: streamlit_app.py (正しい)
   - requirements.txt: 最小限に設定済み

2. **Streamlit Cloudのキャッシュ問題**
   - "Reboot app" を試す
   - "Clear cache" を実行

3. **ファイルパスの問題**
   - ルートディレクトリにstreamlit_app.pyが存在することを確認

### 3. 緊急対処方法
1. Streamlit Cloudの管理画面で "Reboot app" 実行
2. それでも表示されない場合は "Delete app" → "Deploy" で再作成
3. ブラウザのキャッシュをクリア (Ctrl+Shift+R)

### 4. 確認するべきURL
- GitHub リポジトリ: https://github.com/moruku36/japanese-stock-data-app
- 最新コミット: c533d68

## 今回の修正内容
- 最も基本的な "Hello World" レベルのアプリに変更
- requirements.txtをstreamlitのみに簡素化
- すべての複雑な機能を削除

このバージョンで表示されない場合は、Streamlit Cloud側の設定問題の可能性が高いです。
