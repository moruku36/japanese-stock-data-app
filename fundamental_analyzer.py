#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ファンダメンタル分析機能
財務指標、企業価値分析、業界比較などを提供
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Optional, Tuple
import json
import os

warnings.filterwarnings('ignore')

# 日本語フォント設定（シンプル版）
plt.rcParams['font.family'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class FundamentalAnalyzer:
    """ファンダメンタル分析クラス"""
    
    def __init__(self, fetcher):
        """
        初期化
        
        Args:
            fetcher: JapaneseStockDataFetcherのインスタンス
        """
        self.fetcher = fetcher
        self.financial_data = self._load_financial_data()
    
    def _load_financial_data(self) -> Dict:
        """財務データを読み込み（サンプルデータ）"""
        # 実際の実装では、財務データAPIやデータベースから取得
        # ここではサンプルデータを使用
        sample_data = {
            "7203": {  # トヨタ自動車
                "company_name": "トヨタ自動車",
                "sector": "自動車",
                "market_cap": 45000000000000,  # 45兆円
                "revenue": 35000000000000,     # 35兆円
                "net_income": 2800000000000,   # 2.8兆円
                "total_assets": 75000000000000, # 75兆円
                "total_equity": 25000000000000, # 25兆円
                "debt": 20000000000000,        # 20兆円
                "cash": 8000000000000,         # 8兆円
                "pe_ratio": 16.1,
                "pb_ratio": 1.8,
                "roe": 11.2,
                "roa": 3.7,
                "debt_to_equity": 0.8,
                "current_ratio": 1.2,
                "dividend_yield": 2.1,
                "beta": 0.9,
                "pe_ratio_ntm": 15.2,  # NTM PER
                "target_price": 3200,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "6758": {  # ソニーグループ
                "company_name": "ソニーグループ",
                "sector": "電気機器",
                "market_cap": 15000000000000,  # 15兆円
                "revenue": 9000000000000,      # 9兆円
                "net_income": 800000000000,    # 8000億円
                "total_assets": 25000000000000, # 25兆円
                "total_equity": 8000000000000,  # 8兆円
                "debt": 6000000000000,         # 6兆円
                "cash": 3000000000000,         # 3兆円
                "pe_ratio": 18.8,
                "pb_ratio": 1.9,
                "roe": 10.0,
                "roa": 3.2,
                "debt_to_equity": 0.75,
                "current_ratio": 1.4,
                "dividend_yield": 0.8,
                "beta": 1.1,
                "pe_ratio_ntm": 17.5,  # NTM PER
                "target_price": 13500,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9984": {  # ソフトバンクグループ
                "company_name": "ソフトバンクグループ",
                "sector": "情報・通信",
                "market_cap": 12000000000000,  # 12兆円
                "revenue": 6000000000000,      # 6兆円
                "net_income": 500000000000,    # 5000億円
                "total_assets": 40000000000000, # 40兆円
                "total_equity": 15000000000000, # 15兆円
                "debt": 15000000000000,        # 15兆円
                "cash": 5000000000000,         # 5兆円
                "pe_ratio": 24.0,
                "pb_ratio": 0.8,
                "roe": 3.3,
                "roa": 1.3,
                "debt_to_equity": 1.0,
                "current_ratio": 1.1,
                "dividend_yield": 1.2,
                "beta": 1.3,
                "pe_ratio_ntm": 23.5,  # NTM PER
                "target_price": 8500,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "6861": {  # キーエンス
                "company_name": "キーエンス",
                "sector": "電気機器",
                "market_cap": 18000000000000,  # 18兆円
                "revenue": 8000000000000,      # 8兆円
                "net_income": 3000000000000,   # 3兆円
                "total_assets": 12000000000000, # 12兆円
                "total_equity": 10000000000000, # 10兆円
                "debt": 500000000000,          # 5000億円
                "cash": 4000000000000,         # 4兆円
                "pe_ratio": 6.0,
                "pb_ratio": 1.8,
                "roe": 30.0,
                "roa": 25.0,
                "debt_to_equity": 0.05,
                "current_ratio": 3.0,
                "dividend_yield": 0.5,
                "beta": 0.7,
                "pe_ratio_ntm": 5.8,  # NTM PER
                "target_price": 75000,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9434": {  # NTTドコモ
                "company_name": "NTTドコモ",
                "sector": "情報・通信",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 5000000000000,      # 5兆円
                "net_income": 700000000000,    # 7000億円
                "total_assets": 15000000000000, # 15兆円
                "total_equity": 8000000000000,  # 8兆円
                "debt": 3000000000000,         # 3兆円
                "cash": 2000000000000,         # 2兆円
                "pe_ratio": 11.4,
                "pb_ratio": 1.0,
                "roe": 8.8,
                "roa": 4.7,
                "debt_to_equity": 0.38,
                "current_ratio": 1.8,
                "dividend_yield": 3.5,
                "beta": 0.6,
                "pe_ratio_ntm": 10.8,  # NTM PER
                "target_price": 1800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "4784": {  # GMOアドパートナーズ
                "company_name": "GMOアドパートナーズ",
                "sector": "情報・通信",
                "market_cap": 1500000000000,   # 1.5兆円
                "revenue": 800000000000,       # 8000億円
                "net_income": 120000000000,    # 1200億円
                "total_assets": 3000000000000, # 3兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 500000000000,          # 5000億円
                "cash": 800000000000,          # 8000億円
                "pe_ratio": 12.5,
                "pb_ratio": 0.75,
                "roe": 6.0,
                "roa": 4.0,
                "debt_to_equity": 0.25,
                "current_ratio": 2.5,
                "dividend_yield": 1.8,
                "beta": 1.2,
                "pe_ratio_ntm": 11.8,  # NTM PER
                "target_price": 2800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "7974": {  # 任天堂
                "company_name": "任天堂",
                "sector": "情報・通信",
                "market_cap": 9000000000000,   # 9兆円
                "revenue": 1500000000000,      # 1.5兆円
                "net_income": 400000000000,    # 4000億円
                "total_assets": 2000000000000, # 2兆円
                "total_equity": 1500000000000, # 1.5兆円
                "debt": 0,                     # 無借金
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 22.5,
                "pb_ratio": 6.0,
                "roe": 26.7,
                "roa": 20.0,
                "debt_to_equity": 0.0,
                "current_ratio": 4.0,
                "dividend_yield": 1.2,
                "beta": 0.8,
                "pe_ratio_ntm": 21.2,  # NTM PER
                "target_price": 8500,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "6954": {  # ファナック
                "company_name": "ファナック",
                "sector": "電気機器",
                "market_cap": 4000000000000,   # 4兆円
                "revenue": 800000000000,       # 8000億円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 1500000000000, # 1.5兆円
                "total_equity": 1200000000000, # 1.2兆円
                "debt": 0,                     # 無借金
                "cash": 800000000000,          # 8000億円
                "pe_ratio": 20.0,
                "pb_ratio": 3.3,
                "roe": 16.7,
                "roa": 13.3,
                "debt_to_equity": 0.0,
                "current_ratio": 3.5,
                "dividend_yield": 1.5,
                "beta": 0.9,
                "pe_ratio_ntm": 18.5,  # NTM PER
                "target_price": 42000,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "6594": {  # ニデック
                "company_name": "ニデック",
                "sector": "電気機器",
                "market_cap": 3500000000000,   # 3.5兆円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 300000000000,    # 3000億円
                "total_assets": 3000000000000, # 3兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 500000000000,          # 5000億円
                "cash": 600000000000,          # 6000億円
                "pe_ratio": 11.7,
                "pb_ratio": 1.75,
                "roe": 15.0,
                "roa": 10.0,
                "debt_to_equity": 0.25,
                "current_ratio": 2.0,
                "dividend_yield": 1.0,
                "beta": 1.0,
                "pe_ratio_ntm": 11.2,  # NTM PER
                "target_price": 5800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "7733": {  # オリンパス
                "company_name": "オリンパス",
                "sector": "電気機器",
                "market_cap": 3000000000000,   # 3兆円
                "revenue": 800000000000,       # 8000億円
                "net_income": 150000000000,    # 1500億円
                "total_assets": 1200000000000, # 1.2兆円
                "total_equity": 800000000000,  # 8000億円
                "debt": 200000000000,          # 2000億円
                "cash": 300000000000,          # 3000億円
                "pe_ratio": 20.0,
                "pb_ratio": 3.75,
                "roe": 18.8,
                "roa": 12.5,
                "debt_to_equity": 0.25,
                "current_ratio": 2.5,
                "dividend_yield": 1.8,
                "beta": 0.8,
                "pe_ratio_ntm": 19.2,  # NTM PER
                "target_price": 2800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9983": {  # ファーストリテイリング
                "company_name": "ファーストリテイリング",
                "sector": "小売業",
                "market_cap": 10000000000000,  # 10兆円
                "revenue": 3000000000000,      # 3兆円
                "net_income": 300000000000,    # 3000億円
                "total_assets": 4000000000000, # 4兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 1000000000000,         # 1兆円
                "cash": 800000000000,          # 8000億円
                "pe_ratio": 33.3,
                "pb_ratio": 5.0,
                "roe": 15.0,
                "roa": 7.5,
                "debt_to_equity": 0.5,
                "current_ratio": 2.0,
                "dividend_yield": 0.8,
                "beta": 1.1,
                "pe_ratio_ntm": 31.8,  # NTM PER
                "target_price": 45000,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9980": {  # ソフトバンクグループ
                "company_name": "ソフトバンクグループ",
                "sector": "情報・通信",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 4000000000000,      # 4兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 30000000000000, # 30兆円
                "total_equity": 10000000000000, # 10兆円
                "debt": 12000000000000,        # 12兆円
                "cash": 3000000000000,         # 3兆円
                "pe_ratio": 40.0,
                "pb_ratio": 0.8,
                "roe": 2.0,
                "roa": 0.7,
                "debt_to_equity": 1.2,
                "current_ratio": 1.0,
                "dividend_yield": 0.5,
                "beta": 1.4,
                "pe_ratio_ntm": 40.0,  # NTM PER
                "target_price": 6500,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "7269": {  # スズキ
                "company_name": "スズキ",
                "sector": "自動車",
                "market_cap": 2000000000000,   # 2兆円
                "revenue": 4000000000000,      # 4兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 3000000000000, # 3兆円
                "total_equity": 1500000000000, # 1.5兆円
                "debt": 800000000000,          # 8000億円
                "cash": 500000000000,          # 5000億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.33,
                "roe": 13.3,
                "roa": 6.7,
                "debt_to_equity": 0.53,
                "current_ratio": 1.8,
                "dividend_yield": 2.5,
                "beta": 0.9,
                "pe_ratio_ntm": 9.5,  # NTM PER
                "target_price": 1200,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "7267": {  # ホンダ
                "company_name": "ホンダ",
                "sector": "自動車",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 15000000000000,     # 15兆円
                "net_income": 800000000000,    # 8000億円
                "total_assets": 20000000000000, # 20兆円
                "total_equity": 8000000000000,  # 8兆円
                "debt": 6000000000000,         # 6兆円
                "cash": 3000000000000,         # 3兆円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 0.75,
                "current_ratio": 1.5,
                "dividend_yield": 2.8,
                "beta": 0.8,
                "pe_ratio_ntm": 9.8,  # NTM PER
                "target_price": 1800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "8058": {  # 三菱商事
                "company_name": "三菱商事",
                "sector": "商社",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 20000000000000,     # 20兆円
                "net_income": 1000000000000,   # 1兆円
                "total_assets": 25000000000000, # 25兆円
                "total_equity": 8000000000000,  # 8兆円
                "debt": 12000000000000,        # 12兆円
                "cash": 3000000000000,         # 3兆円
                "pe_ratio": 8.0,
                "pb_ratio": 1.0,
                "roe": 12.5,
                "roa": 4.0,
                "debt_to_equity": 1.5,
                "current_ratio": 1.2,
                "dividend_yield": 3.2,
                "beta": 0.7,
                "pe_ratio_ntm": 7.5,  # NTM PER
                "target_price": 8500,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "8001": {  # 伊藤忠商事
                "company_name": "伊藤忠商事",
                "sector": "商社",
                "market_cap": 7000000000000,   # 7兆円
                "revenue": 18000000000000,     # 18兆円
                "net_income": 800000000000,    # 8000億円
                "total_assets": 20000000000000, # 20兆円
                "total_equity": 7000000000000,  # 7兆円
                "debt": 10000000000000,        # 10兆円
                "cash": 2500000000000,         # 2.5兆円
                "pe_ratio": 8.75,
                "pb_ratio": 1.0,
                "roe": 11.4,
                "roa": 4.0,
                "debt_to_equity": 1.43,
                "current_ratio": 1.3,
                "dividend_yield": 3.5,
                "beta": 0.8,
                "pe_ratio_ntm": 8.2,  # NTM PER
                "target_price": 7500,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "8306": {  # 三菱UFJフィナンシャル・グループ
                "company_name": "三菱UFJフィナンシャル・グループ",
                "sector": "銀行業",
                "market_cap": 12000000000000,  # 12兆円
                "revenue": 8000000000000,      # 8兆円
                "net_income": 1200000000000,   # 1.2兆円
                "total_assets": 400000000000000, # 400兆円
                "total_equity": 20000000000000, # 20兆円
                "debt": 300000000000000,       # 300兆円
                "cash": 50000000000000,        # 50兆円
                "pe_ratio": 10.0,
                "pb_ratio": 0.6,
                "roe": 6.0,
                "roa": 0.3,
                "debt_to_equity": 15.0,
                "current_ratio": 1.1,
                "dividend_yield": 4.0,
                "beta": 0.6,
                "pe_ratio_ntm": 9.8,  # NTM PER
                "target_price": 1200,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "8316": {  # 三井住友フィナンシャルグループ
                "company_name": "三井住友フィナンシャルグループ",
                "sector": "銀行業",
                "market_cap": 10000000000000,  # 10兆円
                "revenue": 7000000000000,      # 7兆円
                "net_income": 1000000000000,   # 1兆円
                "total_assets": 300000000000000, # 300兆円
                "total_equity": 18000000000000, # 18兆円
                "debt": 250000000000000,       # 250兆円
                "cash": 40000000000000,        # 40兆円
                "pe_ratio": 10.0,
                "pb_ratio": 0.56,
                "roe": 5.6,
                "roa": 0.33,
                "debt_to_equity": 13.9,
                "current_ratio": 1.0,
                "dividend_yield": 4.2,
                "beta": 0.7,
                "pe_ratio_ntm": 9.5,  # NTM PER
                "target_price": 1100,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "8411": {  # みずほフィナンシャルグループ
                "company_name": "みずほフィナンシャルグループ",
                "sector": "銀行業",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 6000000000000,      # 6兆円
                "net_income": 800000000000,    # 8000億円
                "total_assets": 250000000000000, # 250兆円
                "total_equity": 15000000000000, # 15兆円
                "debt": 200000000000000,       # 200兆円
                "cash": 30000000000000,        # 30兆円
                "pe_ratio": 10.0,
                "pb_ratio": 0.53,
                "roe": 5.3,
                "roa": 0.32,
                "debt_to_equity": 13.3,
                "current_ratio": 1.0,
                "dividend_yield": 4.5,
                "beta": 0.8,
                "pe_ratio_ntm": 9.2,  # NTM PER
                "target_price": 1000,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9432": {  # NTT
                "company_name": "NTT",
                "sector": "情報・通信",
                "market_cap": 12000000000000,  # 12兆円
                "revenue": 12000000000000,     # 12兆円
                "net_income": 1200000000000,   # 1.2兆円
                "total_assets": 25000000000000, # 25兆円
                "total_equity": 10000000000000, # 10兆円
                "debt": 8000000000000,         # 8兆円
                "cash": 3000000000000,         # 3兆円
                "pe_ratio": 10.0,
                "pb_ratio": 1.2,
                "roe": 12.0,
                "roa": 4.8,
                "debt_to_equity": 0.8,
                "current_ratio": 1.5,
                "dividend_yield": 3.8,
                "beta": 0.5,
                "pe_ratio_ntm": 9.8,  # NTM PER
                "target_price": 1800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9433": {  # KDDI
                "company_name": "KDDI",
                "sector": "情報・通信",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 6000000000000,      # 6兆円
                "net_income": 800000000000,    # 8000億円
                "total_assets": 15000000000000, # 15兆円
                "total_equity": 6000000000000,  # 6兆円
                "debt": 5000000000000,         # 5兆円
                "cash": 2000000000000,         # 2兆円
                "pe_ratio": 10.0,
                "pb_ratio": 1.33,
                "roe": 13.3,
                "roa": 5.3,
                "debt_to_equity": 0.83,
                "current_ratio": 1.4,
                "dividend_yield": 4.0,
                "beta": 0.6,
                "pe_ratio_ntm": 10.2,  # NTM PER
                "target_price": 1600,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "4502": {  # 武田薬品工業
                "company_name": "武田薬品工業",
                "sector": "医薬品",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 4000000000000,      # 4兆円
                "net_income": 600000000000,    # 6000億円
                "total_assets": 20000000000000, # 20兆円
                "total_equity": 8000000000000,  # 8兆円
                "debt": 8000000000000,         # 8兆円
                "cash": 2000000000000,         # 2兆円
                "pe_ratio": 13.3,
                "pb_ratio": 1.0,
                "roe": 7.5,
                "roa": 3.0,
                "debt_to_equity": 1.0,
                "current_ratio": 1.2,
                "dividend_yield": 2.5,
                "beta": 0.7,
                "pe_ratio_ntm": 12.8,  # NTM PER
                "target_price": 4500,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "4519": {  # 中外製薬
                "company_name": "中外製薬",
                "sector": "医薬品",
                "market_cap": 6000000000000,   # 6兆円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 400000000000,    # 4000億円
                "total_assets": 8000000000000, # 8兆円
                "total_equity": 5000000000000, # 5兆円
                "debt": 2000000000000,         # 2兆円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 15.0,
                "pb_ratio": 1.2,
                "roe": 8.0,
                "roa": 5.0,
                "debt_to_equity": 0.4,
                "current_ratio": 1.8,
                "dividend_yield": 2.0,
                "beta": 0.6,
                "pe_ratio_ntm": 14.5,  # NTM PER
                "target_price": 3800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "6501": {  # 日立製作所
                "company_name": "日立製作所",
                "sector": "電気機器",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 12000000000000,     # 12兆円
                "net_income": 800000000000,    # 8000億円
                "total_assets": 20000000000000, # 20兆円
                "total_equity": 8000000000000,  # 8兆円
                "debt": 6000000000000,         # 6兆円
                "cash": 3000000000000,         # 3兆円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 0.75,
                "current_ratio": 1.5,
                "dividend_yield": 3.0,
                "beta": 0.8,
                "pe_ratio_ntm": 9.8,  # NTM PER
                "target_price": 2200,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "6502": {  # 東芝
                "company_name": "東芝",
                "sector": "電気機器",
                "market_cap": 2000000000000,   # 2兆円
                "revenue": 4000000000000,      # 4兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 6000000000000, # 6兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 2000000000000,         # 2兆円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 3.3,
                "debt_to_equity": 1.0,
                "current_ratio": 1.5,
                "dividend_yield": 3.5,
                "beta": 1.0,
                "pe_ratio_ntm": 9.5,  # NTM PER
                "target_price": 1800,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "6752": {  # パナソニック
                "company_name": "パナソニック",
                "sector": "電気機器",
                "market_cap": 4000000000000,   # 4兆円
                "revenue": 8000000000000,      # 8兆円
                "net_income": 400000000000,    # 4000億円
                "total_assets": 12000000000000, # 12兆円
                "total_equity": 6000000000000,  # 6兆円
                "debt": 3000000000000,         # 3兆円
                "cash": 2000000000000,         # 2兆円
                "pe_ratio": 10.0,
                "pb_ratio": 0.67,
                "roe": 6.7,
                "roa": 3.3,
                "debt_to_equity": 0.5,
                "current_ratio": 1.8,
                "dividend_yield": 2.8,
                "beta": 0.9,
                "pe_ratio_ntm": 9.8,  # NTM PER
                "target_price": 1600,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9201": {  # 日本航空
                "company_name": "日本航空",
                "sector": "空運業",
                "market_cap": 2000000000000,   # 2兆円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 4000000000000, # 4兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 1000000000000,         # 1兆円
                "cash": 500000000000,          # 5000億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 5.0,
                "debt_to_equity": 0.5,
                "current_ratio": 1.5,
                "dividend_yield": 2.5,
                "beta": 1.2,
                "pe_ratio_ntm": 9.8,  # NTM PER
                "target_price": 1400,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "9202": {  # ANAホールディングス
                "company_name": "ANAホールディングス",
                "sector": "空運業",
                "market_cap": 1500000000000,   # 1.5兆円
                "revenue": 1500000000000,      # 1.5兆円
                "net_income": 150000000000,    # 1500億円
                "total_assets": 3000000000000, # 3兆円
                "total_equity": 1500000000000, # 1.5兆円
                "debt": 800000000000,          # 8000億円
                "cash": 400000000000,          # 4000億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 5.0,
                "debt_to_equity": 0.53,
                "current_ratio": 1.6,
                "dividend_yield": 2.8,
                "beta": 1.3,
                "pe_ratio_ntm": 9.5,  # NTM PER
                "target_price": 1200,  # アナリストターゲットプライス（円）
                "target_price_date": "2024-12-01"  # ターゲットプライス設定日
            },
            "4901": {  # 富士フイルムホールディングス
                "company_name": "富士フイルムホールディングス",
                "sector": "化学",
                "market_cap": 3500000000000,   # 3.5兆円
                "revenue": 2500000000000,      # 2.5兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 4000000000000, # 4兆円
                "total_equity": 2500000000000, # 2.5兆円
                "debt": 800000000000,          # 8000億円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 17.5,
                "pb_ratio": 1.4,
                "roe": 8.0,
                "roa": 5.0,
                "debt_to_equity": 0.32,
                "current_ratio": 1.8,
                "dividend_yield": 1.8,
                "beta": 0.8,
                "pe_ratio_ntm": 16.8,
                "target_price": 8500,
                "target_price_date": "2024-12-01"
            },
            "3382": {  # セブン＆アイ・ホールディングス
                "company_name": "セブン＆アイ・ホールディングス",
                "sector": "小売業",
                "market_cap": 4500000000000,   # 4.5兆円
                "revenue": 10000000000000,     # 10兆円
                "net_income": 300000000000,    # 3000億円
                "total_assets": 8000000000000, # 8兆円
                "total_equity": 3000000000000, # 3兆円
                "debt": 2000000000000,         # 2兆円
                "cash": 1500000000000,         # 1.5兆円
                "pe_ratio": 15.0,
                "pb_ratio": 1.5,
                "roe": 10.0,
                "roa": 3.8,
                "debt_to_equity": 0.67,
                "current_ratio": 1.2,
                "dividend_yield": 2.2,
                "beta": 0.6,
                "pe_ratio_ntm": 14.5,
                "target_price": 4200,
                "target_price_date": "2024-12-01"
            },
            "8267": {  # イオン
                "company_name": "イオン",
                "sector": "小売業",
                "market_cap": 3000000000000,   # 3兆円
                "revenue": 8000000000000,      # 8兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 6000000000000, # 6兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 1500000000000,         # 1.5兆円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 15.0,
                "pb_ratio": 1.5,
                "roe": 10.0,
                "roa": 3.3,
                "debt_to_equity": 0.75,
                "current_ratio": 1.3,
                "dividend_yield": 2.5,
                "beta": 0.7,
                "pe_ratio_ntm": 14.2,
                "target_price": 3800,
                "target_price_date": "2024-12-01"
            },
            "9020": {  # 東日本旅客鉄道
                "company_name": "東日本旅客鉄道",
                "sector": "陸運業",
                "market_cap": 4000000000000,   # 4兆円
                "revenue": 3000000000000,      # 3兆円
                "net_income": 300000000000,    # 3000億円
                "total_assets": 8000000000000, # 8兆円
                "total_equity": 4000000000000, # 4兆円
                "debt": 2000000000000,         # 2兆円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 13.3,
                "pb_ratio": 1.0,
                "roe": 7.5,
                "roa": 3.8,
                "debt_to_equity": 0.5,
                "current_ratio": 1.5,
                "dividend_yield": 2.8,
                "beta": 0.5,
                "pe_ratio_ntm": 12.8,
                "target_price": 8500,
                "target_price_date": "2024-12-01"
            },
            "9021": {  # 西日本旅客鉄道
                "company_name": "西日本旅客鉄道",
                "sector": "陸運業",
                "market_cap": 2000000000000,   # 2兆円
                "revenue": 1500000000000,      # 1.5兆円
                "net_income": 150000000000,    # 1500億円
                "total_assets": 4000000000000, # 4兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 1000000000000,         # 1兆円
                "cash": 500000000000,          # 5000億円
                "pe_ratio": 13.3,
                "pb_ratio": 1.0,
                "roe": 7.5,
                "roa": 3.8,
                "debt_to_equity": 0.5,
                "current_ratio": 1.5,
                "dividend_yield": 2.8,
                "beta": 0.5,
                "pe_ratio_ntm": 12.8,
                "target_price": 4200,
                "target_price_date": "2024-12-01"
            },
            "9022": {  # 東海旅客鉄道
                "company_name": "東海旅客鉄道",
                "sector": "陸運業",
                "market_cap": 3500000000000,   # 3.5兆円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 250000000000,    # 2500億円
                "total_assets": 6000000000000, # 6兆円
                "total_equity": 3500000000000, # 3.5兆円
                "debt": 1500000000000,         # 1.5兆円
                "cash": 800000000000,          # 8000億円
                "pe_ratio": 14.0,
                "pb_ratio": 1.0,
                "roe": 7.1,
                "roa": 4.2,
                "debt_to_equity": 0.43,
                "current_ratio": 1.6,
                "dividend_yield": 2.5,
                "beta": 0.4,
                "pe_ratio_ntm": 13.5,
                "target_price": 7500,
                "target_price_date": "2024-12-01"
            },
            "9501": {  # 東京電力ホールディングス
                "company_name": "東京電力ホールディングス",
                "sector": "電気・ガス業",
                "market_cap": 2500000000000,   # 2.5兆円
                "revenue": 7000000000000,      # 7兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 15000000000000, # 15兆円
                "total_equity": 3000000000000, # 3兆円
                "debt": 8000000000000,         # 8兆円
                "cash": 2000000000000,         # 2兆円
                "pe_ratio": 12.5,
                "pb_ratio": 0.83,
                "roe": 6.7,
                "roa": 1.3,
                "debt_to_equity": 2.67,
                "current_ratio": 1.1,
                "dividend_yield": 3.2,
                "beta": 0.3,
                "pe_ratio_ntm": 12.0,
                "target_price": 1200,
                "target_price_date": "2024-12-01"
            },
            "9502": {  # 中部電力
                "company_name": "中部電力",
                "sector": "電気・ガス業",
                "market_cap": 1500000000000,   # 1.5兆円
                "revenue": 4000000000000,      # 4兆円
                "net_income": 150000000000,    # 1500億円
                "total_assets": 8000000000000, # 8兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 4000000000000,         # 4兆円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 10.0,
                "pb_ratio": 0.75,
                "roe": 7.5,
                "roa": 1.9,
                "debt_to_equity": 2.0,
                "current_ratio": 1.2,
                "dividend_yield": 3.5,
                "beta": 0.3,
                "pe_ratio_ntm": 9.5,
                "target_price": 1800,
                "target_price_date": "2024-12-01"
            },
            "9503": {  # 関西電力
                "company_name": "関西電力",
                "sector": "電気・ガス業",
                "market_cap": 1200000000000,   # 1.2兆円
                "revenue": 3500000000000,      # 3.5兆円
                "net_income": 120000000000,    # 1200億円
                "total_assets": 7000000000000, # 7兆円
                "total_equity": 1500000000000, # 1.5兆円
                "debt": 3500000000000,         # 3.5兆円
                "cash": 800000000000,          # 8000億円
                "pe_ratio": 10.0,
                "pb_ratio": 0.8,
                "roe": 8.0,
                "roa": 1.7,
                "debt_to_equity": 2.33,
                "current_ratio": 1.1,
                "dividend_yield": 3.8,
                "beta": 0.3,
                "pe_ratio_ntm": 9.5,
                "target_price": 1500,
                "target_price_date": "2024-12-01"
            },
            "8031": {  # 三井物産
                "company_name": "三井物産",
                "sector": "商社",
                "market_cap": 6000000000000,   # 6兆円
                "revenue": 15000000000000,     # 15兆円
                "net_income": 800000000000,    # 8000億円
                "total_assets": 20000000000000, # 20兆円
                "total_equity": 8000000000000, # 8兆円
                "debt": 8000000000000,         # 8兆円
                "cash": 3000000000000,         # 3兆円
                "pe_ratio": 7.5,
                "pb_ratio": 0.75,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 1.0,
                "current_ratio": 1.3,
                "dividend_yield": 4.2,
                "beta": 0.8,
                "pe_ratio_ntm": 7.2,
                "target_price": 6500,
                "target_price_date": "2024-12-01"
            },
            "8002": {  # 丸紅
                "company_name": "丸紅",
                "sector": "商社",
                "market_cap": 4000000000000,   # 4兆円
                "revenue": 12000000000000,     # 12兆円
                "net_income": 600000000000,    # 6000億円
                "total_assets": 15000000000000, # 15兆円
                "total_equity": 6000000000000, # 6兆円
                "debt": 6000000000000,         # 6兆円
                "cash": 2000000000000,         # 2兆円
                "pe_ratio": 6.7,
                "pb_ratio": 0.67,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 1.0,
                "current_ratio": 1.3,
                "dividend_yield": 4.5,
                "beta": 0.8,
                "pe_ratio_ntm": 6.5,
                "target_price": 4800,
                "target_price_date": "2024-12-01"
            },
            "2768": {  # 双日
                "company_name": "双日",
                "sector": "商社",
                "market_cap": 1500000000000,   # 1.5兆円
                "revenue": 5000000000000,      # 5兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 6000000000000, # 6兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 2000000000000,         # 2兆円
                "cash": 800000000000,          # 8000億円
                "pe_ratio": 7.5,
                "pb_ratio": 0.75,
                "roe": 10.0,
                "roa": 3.3,
                "debt_to_equity": 1.0,
                "current_ratio": 1.4,
                "dividend_yield": 4.8,
                "beta": 0.9,
                "pe_ratio_ntm": 7.2,
                "target_price": 1800,
                "target_price_date": "2024-12-01"
            },
            "7270": {  # SUBARU
                "company_name": "SUBARU",
                "sector": "自動車",
                "market_cap": 3000000000000,   # 3兆円
                "revenue": 4000000000000,      # 4兆円
                "net_income": 300000000000,    # 3000億円
                "total_assets": 5000000000000, # 5兆円
                "total_equity": 2500000000000, # 2.5兆円
                "debt": 1000000000000,         # 1兆円
                "cash": 800000000000,          # 8000億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.2,
                "roe": 12.0,
                "roa": 6.0,
                "debt_to_equity": 0.4,
                "current_ratio": 1.8,
                "dividend_yield": 2.5,
                "beta": 1.0,
                "pe_ratio_ntm": 9.5,
                "target_price": 4200,
                "target_price_date": "2024-12-01"
            },
            "4568": {  # 第一三共
                "company_name": "第一三共",
                "sector": "医薬品",
                "market_cap": 8000000000000,   # 8兆円
                "revenue": 3000000000000,      # 3兆円
                "net_income": 600000000000,    # 6000億円
                "total_assets": 8000000000000, # 8兆円
                "total_equity": 5000000000000, # 5兆円
                "debt": 1500000000000,         # 1.5兆円
                "cash": 2000000000000,         # 2兆円
                "pe_ratio": 13.3,
                "pb_ratio": 1.6,
                "roe": 12.0,
                "roa": 7.5,
                "debt_to_equity": 0.3,
                "current_ratio": 2.0,
                "dividend_yield": 1.8,
                "beta": 0.6,
                "pe_ratio_ntm": 12.8,
                "target_price": 4800,
                "target_price_date": "2024-12-01"
            },
            "4151": {  # 協和キリン
                "company_name": "協和キリン",
                "sector": "医薬品",
                "market_cap": 4000000000000,   # 4兆円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 300000000000,    # 3000億円
                "total_assets": 4000000000000, # 4兆円
                "total_equity": 2500000000000, # 2.5兆円
                "debt": 800000000000,          # 8000億円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 13.3,
                "pb_ratio": 1.6,
                "roe": 12.0,
                "roa": 7.5,
                "debt_to_equity": 0.32,
                "current_ratio": 1.8,
                "dividend_yield": 2.2,
                "beta": 0.7,
                "pe_ratio_ntm": 12.8,
                "target_price": 2400,
                "target_price_date": "2024-12-01"
            },
            "6952": {  # カシオ計算機
                "company_name": "カシオ計算機",
                "sector": "電気機器",
                "market_cap": 800000000000,    # 8000億円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 100000000000,    # 1000億円
                "total_assets": 1500000000000, # 1.5兆円
                "total_equity": 1000000000000, # 1兆円
                "debt": 200000000000,          # 2000億円
                "cash": 300000000000,          # 3000億円
                "pe_ratio": 8.0,
                "pb_ratio": 0.8,
                "roe": 10.0,
                "roa": 6.7,
                "debt_to_equity": 0.2,
                "current_ratio": 2.0,
                "dividend_yield": 3.2,
                "beta": 0.8,
                "pe_ratio_ntm": 7.8,
                "target_price": 1200,
                "target_price_date": "2024-12-01"
            },
            "6503": {  # 三菱電機
                "company_name": "三菱電機",
                "sector": "電気機器",
                "market_cap": 4000000000000,   # 4兆円
                "revenue": 5000000000000,      # 5兆円
                "net_income": 300000000000,    # 3000億円
                "total_assets": 6000000000000, # 6兆円
                "total_equity": 3000000000000, # 3兆円
                "debt": 1500000000000,         # 1.5兆円
                "cash": 1000000000000,         # 1兆円
                "pe_ratio": 13.3,
                "pb_ratio": 1.33,
                "roe": 10.0,
                "roa": 5.0,
                "debt_to_equity": 0.5,
                "current_ratio": 1.5,
                "dividend_yield": 2.5,
                "beta": 0.9,
                "pe_ratio_ntm": 12.8,
                "target_price": 1800,
                "target_price_date": "2024-12-01"
            },
            "6753": {  # シャープ
                "company_name": "シャープ",
                "sector": "電気機器",
                "market_cap": 2000000000000,   # 2兆円
                "revenue": 3000000000000,      # 3兆円
                "net_income": 150000000000,    # 1500億円
                "total_assets": 4000000000000, # 4兆円
                "total_equity": 1500000000000, # 1.5兆円
                "debt": 1000000000000,         # 1兆円
                "cash": 500000000000,          # 5000億円
                "pe_ratio": 13.3,
                "pb_ratio": 1.33,
                "roe": 10.0,
                "roa": 3.8,
                "debt_to_equity": 0.67,
                "current_ratio": 1.3,
                "dividend_yield": 2.8,
                "beta": 1.1,
                "pe_ratio_ntm": 12.8,
                "target_price": 1200,
                "target_price_date": "2024-12-01"
            },
            "6762": {  # TDK
                "company_name": "TDK",
                "sector": "電気機器",
                "market_cap": 3000000000000,   # 3兆円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 3000000000000, # 3兆円
                "total_equity": 1500000000000, # 1.5兆円
                "debt": 800000000000,          # 8000億円
                "cash": 500000000000,          # 5000億円
                "pe_ratio": 15.0,
                "pb_ratio": 2.0,
                "roe": 13.3,
                "roa": 6.7,
                "debt_to_equity": 0.53,
                "current_ratio": 1.6,
                "dividend_yield": 2.2,
                "beta": 1.0,
                "pe_ratio_ntm": 14.5,
                "target_price": 8500,
                "target_price_date": "2024-12-01"
            },
            "6988": {  # 日東電工
                "company_name": "日東電工",
                "sector": "電気機器",
                "market_cap": 1500000000000,   # 1.5兆円
                "revenue": 1000000000000,      # 1兆円
                "net_income": 100000000000,    # 1000億円
                "total_assets": 1500000000000, # 1.5兆円
                "total_equity": 800000000000,  # 8000億円
                "debt": 400000000000,          # 4000億円
                "cash": 200000000000,          # 2000億円
                "pe_ratio": 15.0,
                "pb_ratio": 1.88,
                "roe": 12.5,
                "roa": 6.7,
                "debt_to_equity": 0.5,
                "current_ratio": 1.8,
                "dividend_yield": 2.5,
                "beta": 0.9,
                "pe_ratio_ntm": 14.5,
                "target_price": 12000,
                "target_price_date": "2024-12-01"
            },
            "7013": {  # IHI
                "company_name": "IHI",
                "sector": "機械",
                "market_cap": 800000000000,    # 8000億円
                "revenue": 1500000000000,      # 1.5兆円
                "net_income": 80000000000,     # 800億円
                "total_assets": 2000000000000, # 2兆円
                "total_equity": 800000000000,  # 8000億円
                "debt": 600000000000,          # 6000億円
                "cash": 200000000000,          # 2000億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 0.75,
                "current_ratio": 1.2,
                "dividend_yield": 3.2,
                "beta": 1.0,
                "pe_ratio_ntm": 9.5,
                "target_price": 4800,
                "target_price_date": "2024-12-01"
            },
            "7012": {  # 川崎重工業
                "company_name": "川崎重工業",
                "sector": "機械",
                "market_cap": 1200000000000,   # 1.2兆円
                "revenue": 2000000000000,      # 2兆円
                "net_income": 120000000000,    # 1200億円
                "total_assets": 3000000000000, # 3兆円
                "total_equity": 1200000000000, # 1.2兆円
                "debt": 800000000000,          # 8000億円
                "cash": 300000000000,          # 3000億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 0.67,
                "current_ratio": 1.3,
                "dividend_yield": 3.0,
                "beta": 1.0,
                "pe_ratio_ntm": 9.5,
                "target_price": 3800,
                "target_price_date": "2024-12-01"
            },
            "7004": {  # 日立造船
                "company_name": "日立造船",
                "sector": "機械",
                "market_cap": 600000000000,    # 6000億円
                "revenue": 1000000000000,      # 1兆円
                "net_income": 60000000000,     # 600億円
                "total_assets": 1500000000000, # 1.5兆円
                "total_equity": 600000000000,  # 6000億円
                "debt": 400000000000,          # 4000億円
                "cash": 150000000000,          # 1500億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 0.67,
                "current_ratio": 1.3,
                "dividend_yield": 3.5,
                "beta": 1.0,
                "pe_ratio_ntm": 9.5,
                "target_price": 2800,
                "target_price_date": "2024-12-01"
            },
            "7011": {  # 三菱重工業
                "company_name": "三菱重工業",
                "sector": "機械",
                "market_cap": 2000000000000,   # 2兆円
                "revenue": 4000000000000,      # 4兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 5000000000000, # 5兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 1500000000000,         # 1.5兆円
                "cash": 500000000000,          # 5000億円
                "pe_ratio": 10.0,
                "pb_ratio": 1.0,
                "roe": 10.0,
                "roa": 4.0,
                "debt_to_equity": 0.75,
                "current_ratio": 1.2,
                "dividend_yield": 3.2,
                "beta": 1.0,
                "pe_ratio_ntm": 9.5,
                "target_price": 6500,
                "target_price_date": "2024-12-01"
            },
            "3407": {  # 旭化成
                "company_name": "旭化成",
                "sector": "化学",
                "market_cap": 2000000000000,   # 2兆円
                "revenue": 2500000000000,      # 2.5兆円
                "net_income": 150000000000,    # 1500億円
                "total_assets": 3000000000000, # 3兆円
                "total_equity": 1500000000000, # 1.5兆円
                "debt": 800000000000,          # 8000億円
                "cash": 500000000000,          # 5000億円
                "pe_ratio": 13.3,
                "pb_ratio": 1.33,
                "roe": 10.0,
                "roa": 5.0,
                "debt_to_equity": 0.53,
                "current_ratio": 1.5,
                "dividend_yield": 2.8,
                "beta": 0.8,
                "pe_ratio_ntm": 12.8,
                "target_price": 3800,
                "target_price_date": "2024-12-01"
            },
            "3402": {  # 東レ
                "company_name": "東レ",
                "sector": "化学",
                "market_cap": 2500000000000,   # 2.5兆円
                "revenue": 3000000000000,      # 3兆円
                "net_income": 200000000000,    # 2000億円
                "total_assets": 4000000000000, # 4兆円
                "total_equity": 2000000000000, # 2兆円
                "debt": 1000000000000,         # 1兆円
                "cash": 600000000000,          # 6000億円
                "pe_ratio": 12.5,
                "pb_ratio": 1.25,
                "roe": 10.0,
                "roa": 5.0,
                "debt_to_equity": 0.5,
                "current_ratio": 1.6,
                "dividend_yield": 2.5,
                "beta": 0.8,
                "pe_ratio_ntm": 12.0,
                "target_price": 4200,
                "target_price_date": "2024-12-01"
            }
        }
        return sample_data
    
    def get_financial_data(self, ticker_symbol: str) -> Optional[Dict]:
        """
        財務データを取得
        
        Args:
            ticker_symbol (str): 銘柄コード
            
        Returns:
            Optional[Dict]: 財務データ（見つからない場合はNone）
        """
        return self.financial_data.get(ticker_symbol)
    
    def calculate_financial_ratios(self, financial_data: Dict) -> Dict:
        """
        財務比率を計算
        
        Args:
            financial_data (Dict): 財務データ
            
        Returns:
            Dict: 計算された財務比率
        """
        ratios = {}
        
        # 収益性指標
        ratios['gross_margin'] = (financial_data['revenue'] - financial_data.get('cost_of_goods_sold', financial_data['revenue'] * 0.7)) / financial_data['revenue'] * 100
        ratios['operating_margin'] = financial_data.get('operating_income', financial_data['net_income'] * 1.2) / financial_data['revenue'] * 100
        ratios['net_margin'] = financial_data['net_income'] / financial_data['revenue'] * 100
        
        # 効率性指標
        ratios['asset_turnover'] = financial_data['revenue'] / financial_data['total_assets']
        ratios['equity_turnover'] = financial_data['revenue'] / financial_data['total_equity']
        
        # 成長性指標（サンプルデータのため固定値）
        ratios['revenue_growth'] = 5.2  # 前年比5.2%成長
        ratios['earnings_growth'] = 8.1  # 前年比8.1%成長
        
        return ratios
    
    def calculate_valuation_metrics(self, financial_data: Dict, current_price: float) -> Dict:
        """
        企業価値指標を計算
        
        Args:
            financial_data (Dict): 財務データ
            current_price (float): 現在の株価
            
        Returns:
            Dict: 企業価値指標
        """
        # 発行済株式数を推定（時価総額 ÷ 株価）
        shares_outstanding = financial_data['market_cap'] / current_price
        
        # EPS（1株当たり利益）
        eps = financial_data['net_income'] / shares_outstanding
        
        # BPS（1株当たり純資産）
        bps = financial_data['total_equity'] / shares_outstanding
        
        # 配当性向
        dividend_payout_ratio = (financial_data.get('dividend', 0) / financial_data['net_income']) * 100
        
        # EV/EBITDA（企業価値倍率）
        ebitda = financial_data.get('ebitda', financial_data['net_income'] * 1.5)
        enterprise_value = financial_data['market_cap'] + financial_data['debt'] - financial_data['cash']
        ev_ebitda = enterprise_value / ebitda
        
        # フリーキャッシュフロー利回り
        fcf = financial_data.get('free_cash_flow', financial_data['net_income'] * 0.8)
        fcf_yield = (fcf / financial_data['market_cap']) * 100
        
        return {
            'eps': eps,
            'bps': bps,
            'dividend_payout_ratio': dividend_payout_ratio,
            'ev_ebitda': ev_ebitda,
            'fcf_yield': fcf_yield,
            'shares_outstanding': shares_outstanding
        }
    
    def analyze_financial_health(self, financial_data: Dict) -> Dict:
        """
        財務健全性を分析
        
        Args:
            financial_data (Dict): 財務データ
            
        Returns:
            Dict: 財務健全性分析結果
        """
        analysis = {}
        
        # 流動性分析
        current_assets = financial_data.get('current_assets', financial_data['total_assets'] * 0.4)
        current_liabilities = financial_data.get('current_liabilities', financial_data['debt'] * 0.6)
        
        analysis['current_ratio'] = current_assets / current_liabilities
        analysis['quick_ratio'] = (current_assets - financial_data.get('inventory', 0)) / current_liabilities
        
        # 財務レバレッジ分析
        analysis['debt_to_equity'] = financial_data['debt'] / financial_data['total_equity']
        analysis['debt_to_assets'] = financial_data['debt'] / financial_data['total_assets']
        analysis['interest_coverage'] = financial_data.get('ebit', financial_data['net_income'] * 1.3) / financial_data.get('interest_expense', financial_data['debt'] * 0.03)
        
        # キャッシュフロー分析
        analysis['operating_cash_flow'] = financial_data.get('operating_cash_flow', financial_data['net_income'] * 1.1)
        analysis['free_cash_flow'] = financial_data.get('free_cash_flow', financial_data['net_income'] * 0.8)
        
        return analysis
    
    def compare_with_industry(self, ticker_symbol: str) -> Dict:
        """
        業界平均との比較
        
        Args:
            ticker_symbol (str): 銘柄コード
            
        Returns:
            Dict: 業界比較結果
        """
        company_data = self.get_financial_data(ticker_symbol)
        if not company_data:
            return {}
        
        # 業界平均データ（サンプル）
        industry_averages = {
            "自動車": {
                "pe_ratio": 12.5,
                "pb_ratio": 1.2,
                "roe": 8.5,
                "roa": 3.2,
                "debt_to_equity": 0.6,
                "current_ratio": 1.3,
                "dividend_yield": 2.8
            },
            "電気機器": {
                "pe_ratio": 18.2,
                "pb_ratio": 2.1,
                "roe": 12.5,
                "roa": 5.8,
                "debt_to_equity": 0.4,
                "current_ratio": 1.6,
                "dividend_yield": 1.5
            },
            "情報・通信": {
                "pe_ratio": 22.5,
                "pb_ratio": 2.8,
                "roe": 15.2,
                "roa": 7.3,
                "debt_to_equity": 0.3,
                "current_ratio": 1.4,
                "dividend_yield": 1.8
            }
        }
        
        sector = company_data['sector']
        industry_avg = industry_averages.get(sector, {})
        
        comparison = {}
        for metric in ['pe_ratio', 'pb_ratio', 'roe', 'roa', 'debt_to_equity', 'current_ratio', 'dividend_yield']:
            if metric in company_data and metric in industry_avg:
                company_value = company_data[metric]
                industry_value = industry_avg[metric]
                comparison[metric] = {
                    'company': company_value,
                    'industry': industry_value,
                    'difference': company_value - industry_value,
                    'percent_diff': ((company_value - industry_value) / industry_value) * 100
                }
        
        return comparison
    
    def get_industry_per_comparison(self, sector: str = None) -> Dict:
        """
        業界別PER比較（NTM PER使用）
        
        Args:
            sector (str): 業界名（Noneの場合は全業界）
            
        Returns:
            Dict: 業界別PER比較結果
        """
        # 業界別の企業をグループ化
        companies_by_sector = {}
        for ticker, data in self.financial_data.items():
            sector_name = data['sector']
            if sector is None or sector_name == sector:
                if sector_name not in companies_by_sector:
                    companies_by_sector[sector_name] = []
                companies_by_sector[sector_name].append({
                    'ticker': ticker,
                    'company_name': data['company_name'],
                    'pe_ratio': data.get('pe_ratio', 0),
                    'pe_ratio_ntm': data.get('pe_ratio_ntm', data.get('pe_ratio', 0)),  # NTM PER
                    'market_cap': data['market_cap'],
                    'roe': data.get('roe', 0),
                    'dividend_yield': data.get('dividend_yield', 0)
                })
        
        # 業界別の統計を計算
        sector_stats = {}
        for sector_name, companies in companies_by_sector.items():
            if companies:
                pe_ratios = [c['pe_ratio'] for c in companies if c['pe_ratio'] > 0]
                pe_ntm_ratios = [c['pe_ratio_ntm'] for c in companies if c['pe_ratio_ntm'] > 0]
                
                sector_stats[sector_name] = {
                    'companies': companies,
                    'avg_pe': sum(pe_ratios) / len(pe_ratios) if pe_ratios else 0,
                    'avg_pe_ntm': sum(pe_ntm_ratios) / len(pe_ntm_ratios) if pe_ntm_ratios else 0,
                    'min_pe_ntm': min(pe_ntm_ratios) if pe_ntm_ratios else 0,
                    'max_pe_ntm': max(pe_ntm_ratios) if pe_ntm_ratios else 0,
                    'company_count': len(companies)
                }
        
        return sector_stats
    
    def find_undervalued_companies(self, sector: str = None, threshold: float = -20.0) -> List[Dict]:
        """
        割安企業を発見（NTM PER基準）
        
        Args:
            sector (str): 業界名（Noneの場合は全業界）
            threshold (float): 割安判定の閾値（%）
            
        Returns:
            List[Dict]: 割安企業のリスト
        """
        sector_stats = self.get_industry_per_comparison(sector)
        undervalued = []
        
        for sector_name, stats in sector_stats.items():
            avg_pe_ntm = stats['avg_pe_ntm']
            if avg_pe_ntm <= 0:
                continue
                
            for company in stats['companies']:
                pe_ntm = company['pe_ratio_ntm']
                if pe_ntm <= 0:
                    continue
                    
                # 業界平均との比較
                percent_diff = ((pe_ntm - avg_pe_ntm) / avg_pe_ntm) * 100
                
                if percent_diff <= threshold:  # 割安判定
                    undervalued.append({
                        'ticker': company['ticker'],
                        'company_name': company['company_name'],
                        'sector': sector_name,
                        'pe_ratio_ntm': pe_ntm,
                        'sector_avg_pe_ntm': avg_pe_ntm,
                        'percent_diff': percent_diff,
                        'market_cap': company['market_cap'],
                        'roe': company['roe'],
                        'dividend_yield': company['dividend_yield']
                    })
        
        # 割安度でソート（最も割安な順）
        undervalued.sort(key=lambda x: x['percent_diff'])
        return undervalued
    
    def find_overvalued_companies(self, sector: str = None, threshold: float = 20.0) -> List[Dict]:
        """
        割高企業を発見（NTM PER基準）
        
        Args:
            sector (str): 業界名（Noneの場合は全業界）
            threshold (float): 割高判定の閾値（%）
            
        Returns:
            List[Dict]: 割高企業のリスト
        """
        sector_stats = self.get_industry_per_comparison(sector)
        overvalued = []
        
        for sector_name, stats in sector_stats.items():
            avg_pe_ntm = stats['avg_pe_ntm']
            if avg_pe_ntm <= 0:
                continue
                
            for company in stats['companies']:
                pe_ntm = company['pe_ratio_ntm']
                if pe_ntm <= 0:
                    continue
                    
                # 業界平均との比較
                percent_diff = ((pe_ntm - avg_pe_ntm) / avg_pe_ntm) * 100
                
                if percent_diff >= threshold:  # 割高判定
                    overvalued.append({
                        'ticker': company['ticker'],
                        'company_name': company['company_name'],
                        'sector': sector_name,
                        'pe_ratio_ntm': pe_ntm,
                        'sector_avg_pe_ntm': avg_pe_ntm,
                        'percent_diff': percent_diff,
                        'market_cap': company['market_cap'],
                        'roe': company['roe'],
                        'dividend_yield': company['dividend_yield']
                    })
        
        # 割高度でソート（最も割高な順）
        overvalued.sort(key=lambda x: x['percent_diff'], reverse=True)
        return overvalued
    
    def analyze_target_price(self, ticker_symbol: str, current_price: float = None) -> Dict:
        """
        ターゲットプライス分析
        
        Args:
            ticker_symbol (str): 銘柄コード
            current_price (float): 現在の株価（Noneの場合は最新価格を取得）
            
        Returns:
            Dict: ターゲットプライス分析結果
        """
        company_data = self.get_financial_data(ticker_symbol)
        if not company_data:
            return {}
        
        # 現在価格を取得
        if current_price is None:
            latest_price = self.fetcher.get_latest_price(ticker_symbol, "stooq")
            if "error" in latest_price:
                return {"error": "現在価格の取得に失敗しました"}
            current_price = latest_price['close']
        
        target_price = company_data.get('target_price', 0)
        if target_price <= 0:
            return {"error": "ターゲットプライスが設定されていません"}
        
        # 分析結果を計算
        price_diff = target_price - current_price
        price_diff_percent = (price_diff / current_price) * 100
        
        # 投資推奨度を判定
        if price_diff_percent >= 20:
            recommendation = "強力買い"
            recommendation_color = "green"
        elif price_diff_percent >= 10:
            recommendation = "買い"
            recommendation_color = "lightgreen"
        elif price_diff_percent >= -10:
            recommendation = "中立"
            recommendation_color = "yellow"
        elif price_diff_percent >= -20:
            recommendation = "売り"
            recommendation_color = "orange"
        else:
            recommendation = "強力売り"
            recommendation_color = "red"
        
        return {
            'ticker': ticker_symbol,
            'company_name': company_data['company_name'],
            'current_price': current_price,
            'target_price': target_price,
            'price_diff': price_diff,
            'price_diff_percent': price_diff_percent,
            'recommendation': recommendation,
            'recommendation_color': recommendation_color,
            'target_price_date': company_data.get('target_price_date', ''),
            'sector': company_data['sector'],
            'pe_ratio_ntm': company_data.get('pe_ratio_ntm', 0),
            'roe': company_data.get('roe', 0),
            'dividend_yield': company_data.get('dividend_yield', 0)
        }
    
    def find_target_price_opportunities(self, min_upside: float = 10.0, max_upside: float = 100.0) -> List[Dict]:
        """
        ターゲットプライス機会を発見
        
        Args:
            min_upside (float): 最小上昇率（%）
            max_upside (float): 最大上昇率（%）
            
        Returns:
            List[Dict]: ターゲットプライス機会のリスト
        """
        opportunities = []
        
        for ticker, company_data in self.financial_data.items():
            target_price = company_data.get('target_price', 0)
            if target_price <= 0:
                continue
            
            # 最新価格を取得
            latest_price = self.fetcher.get_latest_price(ticker, "stooq")
            if "error" in latest_price:
                continue
            
            current_price = latest_price['close']
            upside = ((target_price - current_price) / current_price) * 100
            
            # 条件に合致する場合
            if min_upside <= upside <= max_upside:
                opportunities.append({
                    'ticker': ticker,
                    'company_name': company_data['company_name'],
                    'sector': company_data['sector'],
                    'current_price': current_price,
                    'target_price': target_price,
                    'upside': upside,
                    'pe_ratio_ntm': company_data.get('pe_ratio_ntm', 0),
                    'roe': company_data.get('roe', 0),
                    'dividend_yield': company_data.get('dividend_yield', 0),
                    'target_price_date': company_data.get('target_price_date', '')
                })
        
        # 上昇率でソート（高い順）
        opportunities.sort(key=lambda x: x['upside'], reverse=True)
        return opportunities
    
    def get_sector_target_price_analysis(self, sector: str = None) -> Dict:
        """
        業界別ターゲットプライス分析
        
        Args:
            sector (str): 業界名（Noneの場合は全業界）
            
        Returns:
            Dict: 業界別ターゲットプライス分析結果
        """
        sector_analysis = {}
        
        for ticker, company_data in self.financial_data.items():
            sector_name = company_data['sector']
            if sector is not None and sector_name != sector:
                continue
            
            target_price = company_data.get('target_price', 0)
            if target_price <= 0:
                continue
            
            # 最新価格を取得
            latest_price = self.fetcher.get_latest_price(ticker, "stooq")
            if "error" in latest_price:
                continue
            
            current_price = latest_price['close']
            upside = ((target_price - current_price) / current_price) * 100
            
            if sector_name not in sector_analysis:
                sector_analysis[sector_name] = {
                    'companies': [],
                    'avg_upside': 0,
                    'max_upside': 0,
                    'min_upside': 0,
                    'company_count': 0
                }
            
            sector_analysis[sector_name]['companies'].append({
                'ticker': ticker,
                'company_name': company_data['company_name'],
                'current_price': current_price,
                'target_price': target_price,
                'upside': upside
            })
        
        # 業界別統計を計算
        for sector_name, data in sector_analysis.items():
            upsides = [c['upside'] for c in data['companies']]
            data['avg_upside'] = sum(upsides) / len(upsides) if upsides else 0
            data['max_upside'] = max(upsides) if upsides else 0
            data['min_upside'] = min(upsides) if upsides else 0
            data['company_count'] = len(data['companies'])
        
        return sector_analysis
    
    def plot_financial_analysis(self, ticker_symbol: str, save_plot: bool = True):
        """
        財務分析チャートを描画
        
        Args:
            ticker_symbol (str): 銘柄コード
            save_plot (bool): プロットを保存するかどうか
        """
        financial_data = self.get_financial_data(ticker_symbol)
        if not financial_data:
            print(f"財務データが見つかりません: {ticker_symbol}")
            return
        
        # 最新株価を取得
        latest_price = self.fetcher.get_latest_price(ticker_symbol, "stooq")
        if "error" in latest_price:
            current_price = 10000  # デフォルト値
        else:
            current_price = latest_price['close']
        
        # 各種指標を計算
        ratios = self.calculate_financial_ratios(financial_data)
        valuation = self.calculate_valuation_metrics(financial_data, current_price)
        health = self.analyze_financial_health(financial_data)
        comparison = self.compare_with_industry(ticker_symbol)
        
        # プロット作成
        fig = plt.figure(figsize=(16, 12))
        
        # 1. 収益性指標
        ax1 = plt.subplot(2, 3, 1)
        profitability_metrics = ['ROE', 'ROA', 'Net Margin']
        profitability_values = [financial_data['roe'], financial_data['roa'], ratios['net_margin']]
        bars1 = ax1.bar(profitability_metrics, profitability_values, color=['#2E86AB', '#A23B72', '#F18F01'])
        ax1.set_title('収益性指標 (%)', fontweight='bold')
        ax1.set_ylabel('パーセンテージ')
        for bar, value in zip(bars1, profitability_values):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}%', ha='center', va='bottom')
        
        # 2. 財務健全性
        ax2 = plt.subplot(2, 3, 2)
        health_metrics = ['Current Ratio', 'Debt/Equity', 'Interest Coverage']
        health_values = [health['current_ratio'], health['debt_to_equity'], health['interest_coverage']]
        bars2 = ax2.bar(health_metrics, health_values, color=['#C73E1D', '#F18F01', '#2E86AB'])
        ax2.set_title('財務健全性', fontweight='bold')
        ax2.set_ylabel('比率')
        for bar, value in zip(bars2, health_values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                    f'{value:.2f}', ha='center', va='bottom')
        
        # 3. 企業価値指標
        ax3 = plt.subplot(2, 3, 3)
        valuation_metrics = ['P/E', 'P/B', 'EV/EBITDA']
        valuation_values = [financial_data['pe_ratio'], financial_data['pb_ratio'], valuation['ev_ebitda']]
        bars3 = ax3.bar(valuation_metrics, valuation_values, color=['#A23B72', '#F18F01', '#2E86AB'])
        ax3.set_title('企業価値指標', fontweight='bold')
        ax3.set_ylabel('倍率')
        for bar, value in zip(bars3, valuation_values):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{value:.1f}', ha='center', va='bottom')
        
        # 4. 業界比較（ROE）
        ax4 = plt.subplot(2, 3, 4)
        if 'roe' in comparison:
            comp_data = comparison['roe']
            metrics = ['企業', '業界平均']
            values = [comp_data['company'], comp_data['industry']]
            bars4 = ax4.bar(metrics, values, color=['#2E86AB', '#A23B72'])
            ax4.set_title('ROE 業界比較 (%)', fontweight='bold')
            ax4.set_ylabel('ROE (%)')
            for bar, value in zip(bars4, values):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                        f'{value:.1f}%', ha='center', va='bottom')
        
        # 5. キャッシュフロー分析
        ax5 = plt.subplot(2, 3, 5)
        cf_metrics = ['営業CF', '投資CF', 'フリーCF']
        cf_values = [health['operating_cash_flow'], 
                    -financial_data.get('investing_cash_flow', financial_data['net_income'] * 0.3),
                    health['free_cash_flow']]
        bars5 = ax5.bar(cf_metrics, [v/1000000000000 for v in cf_values], color=['#2E86AB', '#F18F01', '#A23B72'])
        ax5.set_title('キャッシュフロー (兆円)', fontweight='bold')
        ax5.set_ylabel('兆円')
        for bar, value in zip(bars5, cf_values):
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{value/1000000000000:.1f}T', ha='center', va='bottom')
        
        # 6. 成長性指標
        ax6 = plt.subplot(2, 3, 6)
        growth_metrics = ['売上成長率', '利益成長率']
        growth_values = [ratios['revenue_growth'], ratios['earnings_growth']]
        bars6 = ax6.bar(growth_metrics, growth_values, color=['#2E86AB', '#A23B72'])
        ax6.set_title('成長性指標 (%)', fontweight='bold')
        ax6.set_ylabel('成長率 (%)')
        for bar, value in zip(bars6, growth_values):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                    f'{value:.1f}%', ha='center', va='bottom')
        
        plt.suptitle(f'{financial_data["company_name"]} ({ticker_symbol}) ファンダメンタル分析', 
                    fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_plot:
            filename = f"fundamental_analysis_{ticker_symbol}.png"
            filepath = f"stock_data/{filename}"
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"ファンダメンタル分析チャートを保存しました: {filepath}")
        
        plt.show()
    
    def generate_fundamental_report(self, ticker_symbol: str):
        """
        ファンダメンタル分析レポートを生成
        
        Args:
            ticker_symbol (str): 銘柄コード
        """
        financial_data = self.get_financial_data(ticker_symbol)
        if not financial_data:
            print(f"財務データが見つかりません: {ticker_symbol}")
            return
        
        # 最新株価を取得
        latest_price = self.fetcher.get_latest_price(ticker_symbol, "stooq")
        if "error" in latest_price:
            current_price = 10000  # デフォルト値
        else:
            current_price = latest_price['close']
        
        # 各種指標を計算
        ratios = self.calculate_financial_ratios(financial_data)
        valuation = self.calculate_valuation_metrics(financial_data, current_price)
        health = self.analyze_financial_health(financial_data)
        comparison = self.compare_with_industry(ticker_symbol)
        
        print(f"\n{'='*80}")
        print(f"🏢 {financial_data['company_name']} ({ticker_symbol}) ファンダメンタル分析レポート")
        print(f"{'='*80}")
        print(f"📅 分析日: {datetime.now().strftime('%Y年%m月%d日')}")
        print(f"💰 現在株価: {current_price:,.0f}円")
        print(f"🏭 業種: {financial_data['sector']}")
        print(f"📊 時価総額: {financial_data['market_cap']/1000000000000:.1f}兆円")
        
        print(f"\n📈 収益性分析")
        print(f"   ROE (自己資本利益率): {financial_data['roe']:.1f}%")
        print(f"   ROA (総資産利益率): {financial_data['roa']:.1f}%")
        print(f"   純利益率: {ratios['net_margin']:.1f}%")
        print(f"   売上成長率: {ratios['revenue_growth']:.1f}%")
        print(f"   利益成長率: {ratios['earnings_growth']:.1f}%")
        
        print(f"\n💼 企業価値分析")
        print(f"   P/E (株価収益率): {financial_data['pe_ratio']:.1f}倍")
        print(f"   P/B (株価純資産倍率): {financial_data['pb_ratio']:.1f}倍")
        print(f"   EV/EBITDA: {valuation['ev_ebitda']:.1f}倍")
        print(f"   配当利回り: {financial_data['dividend_yield']:.1f}%")
        print(f"   配当性向: {valuation['dividend_payout_ratio']:.1f}%")
        print(f"   フリーキャッシュフロー利回り: {valuation['fcf_yield']:.1f}%")
        
        print(f"\n🏥 財務健全性")
        print(f"   流動比率: {health['current_ratio']:.1f}")
        print(f"   自己資本比率: {(financial_data['total_equity']/financial_data['total_assets'])*100:.1f}%")
        print(f"   負債比率: {health['debt_to_equity']:.1f}")
        print(f"   利息カバレッジ比率: {health['interest_coverage']:.1f}")
        print(f"   営業キャッシュフロー: {health['operating_cash_flow']/1000000000000:.1f}兆円")
        print(f"   フリーキャッシュフロー: {health['free_cash_flow']/1000000000000:.1f}兆円")
        
        print(f"\n⚖️ 業界比較")
        for metric, comp in comparison.items():
            if metric == 'roe':
                print(f"   ROE: 企業 {comp['company']:.1f}% vs 業界平均 {comp['industry']:.1f}% (差: {comp['percent_diff']:+.1f}%)")
            elif metric == 'pe_ratio':
                print(f"   P/E: 企業 {comp['company']:.1f}倍 vs 業界平均 {comp['industry']:.1f}倍 (差: {comp['percent_diff']:+.1f}%)")
            elif metric == 'pb_ratio':
                print(f"   P/B: 企業 {comp['company']:.1f}倍 vs 業界平均 {comp['industry']:.1f}倍 (差: {comp['percent_diff']:+.1f}%)")
        
        print(f"\n🎯 投資判断")
        # 簡易的な投資判断ロジック
        score = 0
        reasons = []
        
        # ROE評価
        if financial_data['roe'] > 15:
            score += 2
            reasons.append("高ROE")
        elif financial_data['roe'] > 10:
            score += 1
            reasons.append("良好なROE")
        
        # P/E評価
        if financial_data['pe_ratio'] < 15:
            score += 2
            reasons.append("割安なP/E")
        elif financial_data['pe_ratio'] < 20:
            score += 1
            reasons.append("適正なP/E")
        
        # 財務健全性評価
        if health['debt_to_equity'] < 0.5:
            score += 2
            reasons.append("低負債")
        elif health['debt_to_equity'] < 1.0:
            score += 1
            reasons.append("適正な負債水準")
        
        # 成長性評価
        if ratios['earnings_growth'] > 10:
            score += 2
            reasons.append("高成長")
        elif ratios['earnings_growth'] > 5:
            score += 1
            reasons.append("安定成長")
        
        print(f"   総合スコア: {score}/8点")
        print(f"   評価理由: {', '.join(reasons)}")
        
        if score >= 6:
            print(f"   💚 推奨: 強力な買い")
        elif score >= 4:
            print(f"   💛 推奨: 買い")
        elif score >= 2:
            print(f"   🟡 推奨: ホールド")
        else:
            print(f"   🔴 推奨: 売り")
        
        print(f"\n{'='*80}")


def main():
    """テスト用メイン関数"""
    from stock_data_fetcher import JapaneseStockDataFetcher
    
    fetcher = JapaneseStockDataFetcher()
    analyzer = FundamentalAnalyzer(fetcher)
    
    print("=== ファンダメンタル分析システム ===")
    
    # テスト用銘柄
    test_tickers = ["7203", "6758", "9984", "6861", "9434"]
    
    for ticker in test_tickers:
        print(f"\n📊 {ticker} のファンダメンタル分析")
        analyzer.plot_financial_analysis(ticker, save_plot=False)
        analyzer.generate_fundamental_report(ticker)


if __name__ == "__main__":
    main() 