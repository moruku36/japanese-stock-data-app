#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
stock_data_fetcher のテスト
- 外部依存はモックし、成功/失敗/空データの挙動を検証
- 複数銘柄取得で一部失敗しても成功分が返ることを検証
"""

import os
import sys
import unittest
from datetime import datetime
import pandas as pd

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.stock_data_fetcher import JapaneseStockDataFetcher


def _make_df(code: str) -> pd.DataFrame:
    data = {
        'Date': pd.to_datetime(['2024-07-01', '2024-07-02']),
        'Open': [100.0, 101.0],
        'High': [102.0, 103.0],
        'Low': [99.0, 100.0],
        'Close': [101.0, 102.0],
        'Volume': [1000, 1200],
    }
    df = pd.DataFrame(data).set_index('Date')
    df.insert(0, 'code', code, allow_duplicates=False)
    return df


class TestStockDataFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = JapaneseStockDataFetcher()

    def test_fetch_multiple_stocks_threaded_partial_failure_yahoo(self):
        """yahoo 経路（スレッド並列）で一部失敗しても成功分が返る"""
        def fake_yahoo(ticker, start_date=None, end_date=None):
            if ticker == 'FAIL':
                raise RuntimeError('yahoo error')
            if ticker == 'EMPTY':
                return pd.DataFrame()
            return _make_df(ticker)

        # fetch_stock_data_yahoo をモック
        self.fetcher.fetch_stock_data_yahoo = fake_yahoo  # type: ignore

        res = self.fetcher.fetch_multiple_stocks(
            ['4784', 'FAIL', 'EMPTY'],
            start_date='2024-07-01',
            end_date='2024-07-02',
            source='yahoo',
        )

        # 失敗した銘柄は含まれないが、成功と空DataFrameは含まれる
        self.assertIn('4784', res)
        self.assertIn('EMPTY', res)
        self.assertNotIn('FAIL', res)
        self.assertIsInstance(res['EMPTY'], pd.DataFrame)

    def test_fetch_multiple_stocks_async_stooq_partial_failure(self):
        """stooq 経路（非同期）で一部失敗しても成功分が返る"""
        async def fake_fetch_csv(session, ticker, start_date, end_date):
            if ticker == 'BAD':
                return None
            return _make_df(ticker)

        # _fetch_stooq_csv をモック
        self.fetcher._fetch_stooq_csv = fake_fetch_csv  # type: ignore

        res = self.fetcher.fetch_multiple_stocks(
            ['7203', 'BAD', '6758'],
            start_date='2024-07-01',
            end_date='2024-07-02',
            source='stooq',
        )

        self.assertIn('7203', res)
        self.assertIn('6758', res)
        self.assertNotIn('BAD', res)


if __name__ == '__main__':
    unittest.main()


