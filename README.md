# 🇯🇵 日本の株価データ取得・分析システム

[GMOアドパートナーズの技術ブログ](https://techblog.gmo-ap.jp/2022/06/07/pythonstockdata/)を参考に作成した、日本の株価データを取得・分析するPythonシステムです。

## 📋 機能一覧

- **最新株価取得**: stooqとYahoo Financeから最新の株価データを取得
- **株価チャート表示**: 美しいチャートで株価の推移を可視化
- **テクニカル分析**: RSI、MACD、移動平均、ボリンジャーバンドなどの技術指標を計算・表示
- **分析レポート生成**: 詳細な分析レポートを自動生成
- **データソース比較**: stooqとYahoo Financeのデータを比較
- **複数銘柄一括取得**: 複数の銘柄を一度に処理
- **CSV保存**: 取得したデータをCSVファイルに保存

## 🚀 セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. システムの実行

```bash
python main.py
```

## 📊 利用可能なデータソース

### stooq
- **URL**: https://stooq.com/
- **銘柄コード形式**: `4784.JP`
- **特徴**: 無料で利用可能、日本の株価データに特化

### Yahoo Finance
- **URL**: https://finance.yahoo.com/
- **銘柄コード形式**: `4784.T`
- **特徴**: 世界的に信頼性の高いデータソース
- **注意**: 現在アクセス制限があり、利用できない場合があります

## 🎯 使用例

### 基本的な使用方法

```python
from stock_data_fetcher import JapaneseStockDataFetcher
from stock_analyzer import StockAnalyzer

# システムの初期化
fetcher = JapaneseStockDataFetcher()
analyzer = StockAnalyzer(fetcher)

# 最新株価を取得
latest_price = fetcher.get_latest_price("4784", "stooq")
print(f"最新終値: {latest_price['close']}円")

# チャートを表示
analyzer.plot_stock_price("4784", "stooq", days=30)

# テクニカル分析を実行
analyzer.plot_technical_analysis("4784", "stooq", days=60)

# 分析レポートを生成
analyzer.generate_report("4784", "stooq", days=30)
```

### データの取得と保存

```python
# 過去30日間のデータを取得
df = fetcher.fetch_stock_data_stooq("4784", "2024-01-01", "2024-01-31")

# CSVファイルに保存
fetcher.save_to_csv(df, "4784", "stooq")
```

## 📈 対応しているテクニカル指標

- **移動平均**: 5日、20日移動平均
- **RSI (相対力指数)**: 14日間のRSI
- **MACD**: 12日、26日、9日のMACD
- **ボリンジャーバンド**: 20日間の標準偏差±2σ

## 📁 ファイル構成

```
japanese-stock-data-app/
├── main.py                 # メインインターフェース
├── stock_data_fetcher.py   # 株価データ取得クラス
├── stock_analyzer.py       # 分析・可視化クラス
├── requirements.txt        # 依存関係
├── README.md              # このファイル
└── stock_data/            # データ保存ディレクトリ（自動作成）
    ├── stooq_stock_data_4784.csv
    └── yahoo_stock_data_4784.csv
```

## 🎨 出力されるチャート

### 基本チャート
- 株価の推移（終値、高値、安値）
- 出来高

### テクニカル分析チャート
- 株価と移動平均、ボリンジャーバンド
- RSI（相対力指数）
- MACD
- 出来高

## 📊 サンプル銘柄コード

| 銘柄コード | 会社名 |
|-----------|--------|
| 4784 | GMOアドパートナーズ |
| 7203 | トヨタ自動車 |
| 6758 | ソニーグループ |
| 9984 | ソフトバンクグループ |
| 6861 | キーエンス |

## ⚠️ 注意事項

1. **データの正確性**: このシステムは教育・研究目的で作成されています。投資判断には必ず公式のデータソースを参照してください。

2. **利用制限**: データソースの利用規約を遵守してください。

3. **エラー処理**: ネットワークエラーやデータ取得エラーが発生する可能性があります。

4. **日本語フォント**: チャートの日本語表示には適切なフォントが必要です。

5. **Yahoo Finance制限**: Yahoo Financeは現在アクセス制限があります。stooqの使用をお勧めします。

## 🔧 トラブルシューティング

### よくある問題

1. **データが取得できない**
   - 銘柄コードが正しいか確認
   - インターネット接続を確認
   - データソースのサービス状況を確認

2. **チャートが表示されない**
   - matplotlibのバックエンドを確認
   - 日本語フォントの設定を確認

3. **パッケージのインストールエラー**
   - Pythonのバージョンを確認（3.7以上推奨）
   - pipを最新版に更新

## 📚 参考資料

- [GMOアドパートナーズ技術ブログ - Pythonで日本の株価を取得する方法](https://techblog.gmo-ap.jp/2022/06/07/pythonstockdata/)
- [pandas-datareader ドキュメント](https://pandas-datareader.readthedocs.io/)
- [matplotlib ドキュメント](https://matplotlib.org/)

## 📄 ライセンス

このプロジェクトは教育・研究目的で作成されています。商用利用の際は、各データソースの利用規約を確認してください。

## 🤝 貢献

バグ報告や機能改善の提案は歓迎します。プルリクエストも受け付けています。

---

**免責事項**: このシステムで取得したデータは参考情報であり、投資判断の責任は利用者にあります。 