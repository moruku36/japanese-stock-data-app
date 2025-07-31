# 🇯🇵 日本の株価データ取得・分析システム - システム構成図

## 📊 システム全体構成図

```mermaid
graph TB
    %% ユーザーインターフェース層
    subgraph "🌐 ユーザーインターフェース層"
        WEB[📱 Webアプリケーション<br/>Streamlit UI]
        CLI[💻 コマンドライン<br/>main.py]
    end

    %% アプリケーション層
    subgraph "🏗️ アプリケーション層"
        WA[web_app.py<br/>Streamlit Web UI]
        SA[stock_analyzer.py<br/>分析・可視化]
        FA[fundamental_analyzer.py<br/>ファンダメンタル分析]
        CS[company_search.py<br/>会社名検索]
    end

    %% データ処理層
    subgraph "⚙️ データ処理層"
        SDF[stock_data_fetcher.py<br/>データ取得]
        UTILS[utils.py<br/>ユーティリティ]
        CONFIG[config.py<br/>設定管理]
    end

    %% データソース層
    subgraph "🌍 データソース層"
        STOOQ[📈 Stooq<br/>株価データ]
        YAHOO[📊 Yahoo Finance<br/>株価データ]
        CDB[company_data.json<br/>企業データベース]
    end

    %% ストレージ層
    subgraph "💾 ストレージ層"
        CSV[📁 CSVファイル<br/>stock_data/]
        CACHE[🗄️ キャッシュ<br/>メモリ/ディスク]
    end

    %% 接続関係
    WEB --> WA
    CLI --> SA
    WA --> SDF
    WA --> FA
    WA --> CS
    SA --> SDF
    FA --> SDF
    CS --> CDB
    SDF --> STOOQ
    SDF --> YAHOO
    SDF --> CSV
    SDF --> CACHE
    UTILS --> SDF
    CONFIG --> SDF
    CONFIG --> SA
    CONFIG --> FA

    %% スタイル
    classDef webClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef appClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef dataClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef sourceClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef storageClass fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class WEB,CLI webClass
    class WA,SA,FA,CS appClass
    class SDF,UTILS,CONFIG dataClass
    class STOOQ,YAHOO,CDB sourceClass
    class CSV,CACHE storageClass
```

## 🔄 データフロー図

```mermaid
flowchart TD
    %% 開始点
    START([ユーザーアクション]) --> CHOICE{アクセス方法}
    
    %% Webアプリケーション
    CHOICE -->|Webブラウザ| WEB[📱 Webアプリケーション<br/>Streamlit UI]
    CHOICE -->|コマンドライン| CLI[💻 CLIインターフェース<br/>main.py]
    
    %% Webアプリケーションのフロー
    WEB --> WEB_CHOICE{機能選択}
    WEB_CHOICE -->|最新株価| LATEST[📊 最新株価取得]
    WEB_CHOICE -->|株価チャート| CHART[📈 株価チャート表示]
    WEB_CHOICE -->|ファンダメンタル| FUND[🏢 ファンダメンタル分析]
    WEB_CHOICE -->|財務比較| COMP[⚖️ 財務指標比較]
    WEB_CHOICE -->|会社検索| SEARCH[🔍 会社名検索]
    WEB_CHOICE -->|複数銘柄| MULTI[📦 複数銘柄分析]
    WEB_CHOICE -->|データエクスポート| EXPORT[💾 データエクスポート]
    
    %% CLIのフロー
    CLI --> CLI_CHOICE{機能選択}
    CLI_CHOICE -->|1| CLI_LATEST[📊 最新株価取得]
    CLI_CHOICE -->|2| CLI_CHART[📈 株価チャート表示]
    CLI_CHOICE -->|3| CLI_TECH[🔧 テクニカル分析]
    CLI_CHOICE -->|4| CLI_REPORT[📋 分析レポート生成]
    CLI_CHOICE -->|5| CLI_COMPARE[🔄 データソース比較]
    CLI_CHOICE -->|6| CLI_BATCH[📦 複数銘柄一括取得]
    CLI_CHOICE -->|7| CLI_SAVE[💾 CSV保存]
    CLI_CHOICE -->|8| CLI_FUND[🏢 ファンダメンタル分析]
    CLI_CHOICE -->|9| CLI_FIN[⚖️ 財務指標比較]
    
    %% データ取得処理
    LATEST --> FETCH[🔄 データ取得処理]
    CHART --> FETCH
    CLI_LATEST --> FETCH
    CLI_CHART --> FETCH
    CLI_TECH --> FETCH
    CLI_REPORT --> FETCH
    CLI_COMPARE --> FETCH
    CLI_BATCH --> FETCH
    CLI_SAVE --> FETCH
    
    %% ファンダメンタル分析
    FUND --> FUND_ANALYSIS[🏢 ファンダメンタル分析処理]
    CLI_FUND --> FUND_ANALYSIS
    
    %% 財務比較
    COMP --> FIN_COMP[⚖️ 財務指標比較処理]
    CLI_FIN --> FIN_COMP
    
    %% 会社検索
    SEARCH --> SEARCH_PROC[🔍 会社名検索処理]
    
    %% データ取得の詳細フロー
    FETCH --> SOURCE_CHOICE{データソース選択}
    SOURCE_CHOICE -->|Stooq| STOOQ_FETCH[📈 Stooqから取得]
    SOURCE_CHOICE -->|Yahoo| YAHOO_FETCH[📊 Yahoo Financeから取得]
    
    %% データ処理
    STOOQ_FETCH --> PROCESS[⚙️ データ処理・変換]
    YAHOO_FETCH --> PROCESS
    PROCESS --> CACHE_CHECK{キャッシュ確認}
    CACHE_CHECK -->|キャッシュあり| CACHE_HIT[🗄️ キャッシュから取得]
    CACHE_CHECK -->|キャッシュなし| CACHE_MISS[🌐 外部APIから取得]
    CACHE_MISS --> CACHE_UPDATE[💾 キャッシュに保存]
    
    %% 結果表示・保存
    CACHE_HIT --> RESULT[📊 結果表示]
    CACHE_UPDATE --> RESULT
    FUND_ANALYSIS --> RESULT
    FIN_COMP --> RESULT
    SEARCH_PROC --> RESULT
    
    %% エンドポイント
    RESULT --> END([処理完了])
    
    %% スタイル
    classDef startEnd fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef data fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef web fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class START,END startEnd
    class FETCH,PROCESS,CACHE_UPDATE,FUND_ANALYSIS,FIN_COMP,SEARCH_PROC process
    class CHOICE,SOURCE_CHOICE,CACHE_CHECK decision
    class STOOQ_FETCH,YAHOO_FETCH,CACHE_HIT,CACHE_MISS data
    class WEB,CLI,LATEST,CHART,FUND,COMP,SEARCH,MULTI,EXPORT web
```

## 🏗️ クラス構成図

```mermaid
classDiagram
    %% メインクラス
    class JapaneseStockDataFetcher {
        +__init__()
        +get_latest_price(ticker, source)
        +fetch_stock_data_stooq(ticker, start_date, end_date)
        +fetch_stock_data_yahoo(ticker, start_date, end_date)
        +save_to_csv(df, ticker, source)
        +compare_data_sources(ticker, start_date, end_date)
    }
    
    class StockAnalyzer {
        +__init__(fetcher)
        +plot_stock_price(ticker, source, days)
        +plot_technical_analysis(ticker, source, days)
        +generate_report(ticker, source, days)
        +batch_analysis(tickers, source, days)
    }
    
    class FundamentalAnalyzer {
        +__init__()
        +get_financial_data(ticker)
        +get_industry_per_comparison(sector)
        +find_undervalued_companies(sector, threshold)
        +find_overvalued_companies(sector, threshold)
        +analyze_target_price(ticker)
        +find_target_price_opportunities(min_upside, max_upside)
        +get_sector_target_price_analysis(sector)
    }
    
    class CompanySearch {
        +__init__()
        +search_by_name(query)
        +search_by_sector(sector)
        +get_popular_companies(limit)
        +get_company_by_code(code)
    }
    
    %% ユーティリティクラス
    class PerformanceMonitor {
        +__call__(func)
        +get_memory_usage()
        +get_execution_time()
    }
    
    class OptimizedCache {
        +__init__(max_size)
        +get(key)
        +set(key, value)
        +clear()
    }
    
    class MemoryOptimizer {
        +get_memory_usage()
        +optimize_memory()
        +cleanup()
    }
    
    class RetryHandler {
        +__init__(max_retries, delay)
        +execute(func, *args, **kwargs)
    }
    
    class DataValidator {
        +validate_ticker(ticker)
        +validate_date_range(start_date, end_date)
        +validate_dataframe(df)
    }
    
    %% 設定クラス
    class Config {
        +DATA_SOURCES
        +CHART_SETTINGS
        +ANALYSIS_SETTINGS
        +UI_SETTINGS
    }
    
    %% 関係性
    StockAnalyzer --> JapaneseStockDataFetcher : uses
    JapaneseStockDataFetcher --> PerformanceMonitor : uses
    JapaneseStockDataFetcher --> OptimizedCache : uses
    JapaneseStockDataFetcher --> MemoryOptimizer : uses
    JapaneseStockDataFetcher --> RetryHandler : uses
    JapaneseStockDataFetcher --> DataValidator : uses
    JapaneseStockDataFetcher --> Config : uses
    FundamentalAnalyzer --> Config : uses
    CompanySearch --> Config : uses
```

## 🔧 技術スタック構成図

```mermaid
graph TB
    %% フロントエンド
    subgraph "🎨 フロントエンド"
        STREAMLIT[Streamlit<br/>Web UI Framework]
        PLOTLY[Plotly<br/>インタラクティブチャート]
        PANDAS_UI[Pandas<br/>データ表示]
    end
    
    %% バックエンド
    subgraph "⚙️ バックエンド"
        PYTHON[Python 3.11<br/>メイン言語]
        ASYNC[Aiohttp<br/>非同期HTTP]
        REQUESTS[Requests<br/>HTTP通信]
    end
    
    %% データ処理
    subgraph "📊 データ処理"
        PANDAS[Pandas<br/>データ分析]
        NUMPY[NumPy<br/>数値計算]
        MATPLOTLIB[Matplotlib<br/>チャート生成]
        SEABORN[Seaborn<br/>統計可視化]
    end
    
    %% データソース
    subgraph "🌍 データソース"
        STOOQ_API[Stooq API<br/>株価データ]
        YAHOO_API[Yahoo Finance API<br/>株価データ]
        JSON_DB[JSON Database<br/>企業情報]
    end
    
    %% ストレージ
    subgraph "💾 ストレージ"
        CSV_FILES[CSV Files<br/>データ保存]
        MEMORY_CACHE[Memory Cache<br/>高速アクセス]
        DISK_CACHE[Disk Cache<br/>永続化]
    end
    
    %% ユーティリティ
    subgraph "🔧 ユーティリティ"
        PSUTIL[psutil<br/>システム監視]
        LRU_DICT[LRU Dict<br/>キャッシュ管理]
        LOGGING[Logging<br/>ログ管理]
    end
    
    %% 接続関係
    STREAMLIT --> PYTHON
    PYTHON --> PANDAS
    PYTHON --> ASYNC
    PYTHON --> REQUESTS
    PANDAS --> NUMPY
    PANDAS --> MATPLOTLIB
    MATPLOTLIB --> SEABORN
    PLOTLY --> PANDAS
    ASYNC --> STOOQ_API
    REQUESTS --> YAHOO_API
    PYTHON --> JSON_DB
    PANDAS --> CSV_FILES
    PYTHON --> MEMORY_CACHE
    PYTHON --> DISK_CACHE
    PYTHON --> PSUTIL
    PYTHON --> LRU_DICT
    PYTHON --> LOGGING
    
    %% スタイル
    classDef frontend fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef backend fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef data fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef source fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef util fill:#f1f8e9,stroke:#33691e,stroke-width:2px
    
    class STREAMLIT,PLOTLY,PANDAS_UI frontend
    class PYTHON,ASYNC,REQUESTS backend
    class PANDAS,NUMPY,MATPLOTLIB,SEABORN data
    class STOOQ_API,YAHOO_API,JSON_DB source
    class CSV_FILES,MEMORY_CACHE,DISK_CACHE storage
    class PSUTIL,LRU_DICT,LOGGING util
```

## 📝 図表の説明

### 1. システム全体構成図
- **4層アーキテクチャ**: ユーザーインターフェース、アプリケーション、データ処理、データソース
- **コンポーネント間の関係**: 依存関係とデータフローを明確化
- **色分け**: 各層を異なる色で分類

### 2. データフロー図
- **ユーザーアクションから結果まで**: 完全な処理フロー
- **分岐処理**: 機能選択とデータソース選択
- **キャッシュ処理**: パフォーマンス最適化の仕組み

### 3. クラス構成図
- **主要クラス**: システムの核となるクラス群
- **依存関係**: クラス間の使用関係
- **メソッド**: 主要な機能メソッド

### 4. 技術スタック構成図
- **使用技術**: Python、Streamlit、Pandas等
- **役割分担**: 各技術の担当領域
- **依存関係**: 技術間の連携

これらの図表により、システムの全体像、データの流れ、技術的な実装詳細を視覚的に理解できます。 