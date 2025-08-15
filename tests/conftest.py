import os
import sys
import pytest

# プロジェクトのsrcディレクトリをパスに追加
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, '..', 'src')
if os.path.isdir(SRC_DIR) and SRC_DIR not in sys.path:
    sys.path.insert(0, os.path.normpath(SRC_DIR))

# テスト用フィクスチャ
from core.stock_data_fetcher import JapaneseStockDataFetcher  # noqa: E402
from core.stock_analyzer import StockAnalyzer  # noqa: E402

@pytest.fixture
def fetcher():
    return JapaneseStockDataFetcher()

@pytest.fixture
def analyzer(fetcher):
    return StockAnalyzer(fetcher)


