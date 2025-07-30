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
                "beta": 0.9
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
                "beta": 1.1
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
                "beta": 1.3
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
                "beta": 0.7
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
                "beta": 0.6
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
                "current_ratio": 2.2,
                "dividend_yield": 2.8,
                "beta": 1.2
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