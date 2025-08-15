#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
会社名検索機能
日本の上場企業の銘柄コードと会社名のマッピングを管理
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

class CompanySearch:
    """会社名検索クラス"""
    
    def __init__(self, data_file: str = None):
        """
        初期化
        
        Args:
            data_file (str): 会社データファイルのパス
        """
        if data_file is None:
            # 現在のファイルのディレクトリを基準にパスを設定
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_file = os.path.join(current_dir, "company_data.json")
            
            # Streamlit Cloud環境での代替パス
            if not os.path.exists(self.data_file):
                # Streamlit Cloud用の代替パス
                alt_paths = [
                    os.path.join('/app/src/core', "company_data.json"),
                    os.path.join(os.getcwd(), 'src', 'core', "company_data.json"),
                    os.path.join(os.getcwd(), "company_data.json")
                ]
                for alt_path in alt_paths:
                    if os.path.exists(alt_path):
                        self.data_file = alt_path
                        break
        else:
            self.data_file = data_file
        self.companies = self._load_company_data()
    
    def _load_company_data(self) -> List[Dict]:
        """会社データを読み込み"""
        try:
            print(f"🔍 会社データファイルを読み込み中: {self.data_file}")
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    companies = data.get('companies', [])
                    print(f"✅ 会社データを読み込みました: {len(companies)}社")
                    return companies
            else:
                print(f"⚠️ 会社データファイルが見つかりません: {self.data_file}")
                return []
        except Exception as e:
            print(f"❌ 会社データの読み込みに失敗: {e}")
            return []

    def _save_company_data(self) -> None:
        """会社データを保存（動的拡張を永続化）"""
        try:
            data = {"companies": self.companies}
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 保存失敗は致命的ではないため警告のみ
            print(f"⚠️ 会社データの保存に失敗: {e}")

    def _fetch_company_from_remote(self, code: str) -> Optional[Dict]:
        """外部から会社情報を取得（yfinance）し、辞書形式で返す。

        Returns None if not found or on error.
        """
        try:
            import yfinance as yf  # lazy import
        except Exception:
            return None

        try:
            ticker = yf.Ticker(f"{code}.T")
            name = None
            sector = None
            market = "東証"

            # yfinanceの情報取得は環境によって差があるためフォールバック多段
            try:
                info = getattr(ticker, 'info', {}) or {}
                name = info.get('shortName') or info.get('longName')
                sector = info.get('sector')
            except Exception:
                info = {}

            if not name:
                try:
                    fast = getattr(ticker, 'fast_info', None)
                    if fast:
                        name = fast.get('shortName') or name
                except Exception:
                    pass

            if not name:
                # 名前が取れなくてもコードだけで登録可能にする
                name = f"銘柄{code}"
            if not sector:
                sector = "不明"

            return {
                'code': code,
                'name': name,
                'sector': sector,
                'market': market
            }
        except Exception:
            return None

    def _add_or_update_company(self, company: Dict) -> Dict:
        """社内リストへ追加（既存なら更新）し、保存する"""
        # 既存チェック
        for i, c in enumerate(self.companies):
            if c.get('code') == company.get('code'):
                # 既存をアップデート（欠損のみ補完）
                updated = {
                    'code': c.get('code', company.get('code')),
                    'name': c.get('name', company.get('name')),
                    'sector': c.get('sector', company.get('sector', '不明')),
                    'market': c.get('market', company.get('market', '東証')),
                }
                self.companies[i] = updated
                self._save_company_data()
                return updated

        # 新規追加
        self.companies.append(company)
        self._save_company_data()
        return company
    
    def search_by_name(self, query: str, limit: int = 10) -> List[Dict]:
        """
        会社名で検索
        
        Args:
            query (str): 検索クエリ
            limit (int): 結果の最大件数
            
        Returns:
            List[Dict]: 検索結果
        """
        if not query.strip():
            return []
        
        query = query.strip().lower()
        results = []
        
        for company in self.companies:
            name = company['name'].lower()
            code = company['code']
            sector = company['sector']
            
            # 完全一致
            if query == name:
                results.append({
                    'company': company,
                    'score': 1.0,
                    'match_type': '完全一致'
                })
            # 部分一致
            elif query in name:
                score = len(query) / len(name)
                results.append({
                    'company': company,
                    'score': score,
                    'match_type': '部分一致'
                })
            # 類似度検索
            else:
                similarity = SequenceMatcher(None, query, name).ratio()
                if similarity > 0.3:  # 類似度30%以上
                    results.append({
                        'company': company,
                        'score': similarity,
                        'match_type': '類似検索'
                    })
        
        # スコアでソート（降順）
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:limit]
    
    def search_by_code(self, code: str) -> Optional[Dict]:
        """
        銘柄コードで検索
        
        Args:
            code (str): 銘柄コード
            
        Returns:
            Optional[Dict]: 会社情報（見つからない場合はNone）
        """
        code = code.strip()
        for company in self.companies:
            if company['code'] == code:
                return company

        # 未登録の場合でも、4桁の日本株コードは動的に解決を試みる
        if code.isdigit() and len(code) == 4:
            remote = self._fetch_company_from_remote(code)
            if remote:
                return self._add_or_update_company(remote)
            # リモート取得に失敗してもスタブを登録して分析できるようにする
            stub = {
                'code': code,
                'name': f"銘柄{code}",
                'sector': '不明',
                'market': '東証'
            }
            return self._add_or_update_company(stub)

        return None
    
    def search_by_sector(self, sector: str, limit: int = 20) -> List[Dict]:
        """
        業種で検索
        
        Args:
            sector (str): 業種名
            limit (int): 結果の最大件数
            
        Returns:
            List[Dict]: 検索結果
        """
        sector = sector.strip().lower()
        results = []
        
        for company in self.companies:
            if sector in company['sector'].lower():
                results.append(company)
        
        return results[:limit]
    
    def get_all_sectors(self) -> List[str]:
        """
        全業種を取得
        
        Returns:
            List[str]: 業種リスト
        """
        sectors = set()
        for company in self.companies:
            sectors.add(company['sector'])
        return sorted(list(sectors))
    
    def get_popular_companies(self, limit: int = 20) -> List[Dict]:
        """
        人気企業（主要企業）を取得
        
        Args:
            limit (int): 結果の最大件数
            
        Returns:
            List[Dict]: 主要企業リスト
        """
        # 主要企業の銘柄コードリスト
        popular_codes = [
            "7203", "6758", "9984", "6861", "9434", "4784", "7974", "6954",
            "6594", "7733", "4901", "4502", "4519", "3382", "8267", "8306",
            "8316", "8411", "9020", "9021", "9022", "9432", "9433", "9501",
            "9502", "9503", "8031", "8058", "8001", "8002", "2768", "7267",
            "7269", "7270", "4568", "4151", "6952", "6501", "6502", "6503",
            "6752", "6753", "6762", "6988", "7013", "7012", "7004", "7011",
            "3407", "3402", "3401", "3405", "4911", "2501", "2502", "2503",
            "2531", "1332", "1333", "2001", "2002", "1801", "1802", "1803",
            "1812", "1925", "1928", "8801", "8802", "8804", "8830", "9101",
            "9104", "9107", "9201", "9202", "9531", "9532", "9533", "9602",
            "9681", "9735", "9744", "9766", "9769", "9787", "9793", "9843",
            "9850", "9861", "9873", "9889", "9896", "9900", "9902", "9904",
            "9909", "9913", "9914", "9919", "9927", "9928", "9929", "9930",
            "9932", "9934", "9936", "9941", "9942", "9943", "9945", "9946",
            "9948", "9949", "9950", "9955", "9956", "9957", "9959", "9960",
            "9962", "9964", "9966", "9967", "9969", "9972", "9973", "9974",
            "9976", "9977", "9978", "9979", "9980", "9981", "9982", "9983",
            "9986", "9987", "9989", "9990", "9991", "9992", "9993", "9994",
            "9995", "9996", "9997", "9998", "9999"
        ]
        
        popular_companies = []
        for code in popular_codes[:limit]:
            company = self.search_by_code(code)
            if company:
                popular_companies.append(company)
        
        return popular_companies
    
    def display_search_results(self, results: List[Dict]) -> None:
        """
        検索結果を表示
        
        Args:
            results (List[Dict]): 検索結果
        """
        if not results:
            print("❌ 検索結果が見つかりませんでした")
            return
        
        print(f"\n📊 検索結果: {len(results)}件")
        print("-" * 80)
        
        for i, result in enumerate(results, 1):
            company = result['company']
            score = result['score']
            match_type = result['match_type']
            
            print(f"{i:2d}. {company['name']} ({company['code']})")
            print(f"    業種: {company['sector']} | 市場: {company['market']}")
            print(f"    マッチ度: {score:.1%} ({match_type})")
            print()
    
    def display_company_info(self, company: Dict) -> None:
        """
        会社情報を表示
        
        Args:
            company (Dict): 会社情報
        """
        print(f"\n🏢 {company['name']} ({company['code']})")
        print(f"   業種: {company['sector']}")
        print(f"   市場: {company['market']}")
    
    def interactive_search(self) -> Optional[str]:
        """
        対話的な検索
        
        Returns:
            Optional[str]: 選択された銘柄コード（キャンセルの場合はNone）
        """
        print("\n🔍 会社名で検索")
        print("会社名の一部を入力してください（例: トヨタ、ソニー、任天堂）:")
        
        query = input("検索キーワード: ").strip()
        if not query:
            return None
        
        results = self.search_by_name(query, limit=15)
        
        if not results:
            print(f"❌ '{query}' に一致する会社が見つかりませんでした")
            return None
        
        self.display_search_results(results)
        
        if len(results) == 1:
            # 1件のみの場合は自動選択
            selected_company = results[0]['company']
            self.display_company_info(selected_company)
            confirm = input("この会社を選択しますか？ (Y/n): ").strip().lower()
            if confirm in ['', 'y', 'yes']:
                return selected_company['code']
            else:
                return None
        else:
            # 複数件の場合は選択
            while True:
                try:
                    choice = input(f"\n選択してください (1-{len(results)}): ").strip()
                    if choice.lower() in ['q', 'quit', 'cancel', 'キャンセル']:
                        return None
                    
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(results):
                        selected_company = results[choice_num - 1]['company']
                        self.display_company_info(selected_company)
                        return selected_company['code']
                    else:
                        print(f"❌ 1-{len(results)}の数字を入力してください")
                except ValueError:
                    print("❌ 有効な数字を入力してください")
                except KeyboardInterrupt:
                    print("\n❌ 検索をキャンセルしました")
                    return None


def main():
    """テスト用メイン関数"""
    searcher = CompanySearch()
    
    print("=== 会社名検索システム ===")
    print(f"登録企業数: {len(searcher.companies)}社")
    
    # 業種一覧を表示
    sectors = searcher.get_all_sectors()
    print(f"\n📋 対応業種: {len(sectors)}業種")
    for sector in sectors:
        print(f"   - {sector}")
    
    # 人気企業を表示
    popular = searcher.get_popular_companies(10)
    print(f"\n⭐ 主要企業 (上位10社):")
    for i, company in enumerate(popular, 1):
        print(f"   {i:2d}. {company['name']} ({company['code']}) - {company['sector']}")
    
    # 対話的検索
    selected_code = searcher.interactive_search()
    if selected_code:
        print(f"\n✅ 選択された銘柄コード: {selected_code}")
    else:
        print("\n❌ 検索がキャンセルされました")


if __name__ == "__main__":
    main() 