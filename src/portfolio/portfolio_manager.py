#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ポートフォリオ管理システム
科学的手法による投資ポートフォリオの作成・管理・追跡機能
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import yfinance as yf

logger = logging.getLogger(__name__)

@dataclass
class Position:
    """ポジション情報"""
    symbol: str
    company_name: str
    shares: float
    avg_price: float
    current_price: float
    total_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    sector: str
    weight: float
    purchase_date: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['purchase_date'] = self.purchase_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        data['purchase_date'] = datetime.fromisoformat(data['purchase_date'])
        return cls(**data)

@dataclass
class PortfolioTransaction:
    """取引記録"""
    transaction_id: str
    symbol: str
    transaction_type: str  # buy, sell
    shares: float
    price: float
    total_amount: float
    fee: float
    timestamp: datetime
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioTransaction':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class PortfolioSnapshot:
    """ポートフォリオのスナップショット"""
    timestamp: datetime
    total_value: float
    total_pnl: float
    total_pnl_pct: float
    positions_count: int
    cash: float
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PortfolioSnapshot':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

class PortfolioManager:
    """ポートフォリオ管理クラス"""
    
    def __init__(self, storage_path: str = "data/portfolio.json"):
        """初期化"""
        self.storage_path = storage_path
        self.positions: Dict[str, Position] = {}
        self.transactions: List[PortfolioTransaction] = []
        self.snapshots: List[PortfolioSnapshot] = []
        self.cash = 0.0
        self.initial_cash = 0.0
        
        # 日本の主要セクター定義
        self.sector_mapping = {
            '1301': '不動産', '1332': '不動産', '1333': '不動産', 
            '1605': '建設', '1721': 'コマース',
            '1801': '建設', '1802': '建設', '1803': '建設',
            '2269': '食品', '2270': '食品', '2282': '食品',
            '4063': '化学', '4183': '化学', '4188': '化学',
            '4502': '医薬品', '4503': '医薬品', '4568': '医薬品',
            '6098': 'サービス', '6178': 'サービス',
            '6301': '機械', '6326': '機械', '6367': '機械',
            '6501': '電気機器', '6502': '電気機器', '6503': '電気機器',
            '6758': 'ソニー', '6861': 'キーエンス', '6954': 'ファナック',
            '7203': '自動車', '7267': '自動車', '7269': '自動車',
            '7733': 'オリンパス', '7741': 'HOYA',
            '8001': '商社', '8031': '商社', '8058': '商社',
            '8267': 'イオン', '8411': 'みずほ', '8604': '野村',
            '9432': 'NTT', '9433': 'KDDI', '9984': 'ソフトバンク'
        }
        
        # ストレージディレクトリの作成
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # データの読み込み
        self.load_portfolio()
        
        logger.info("ポートフォリオ管理システムを初期化しました")
    
    def set_initial_cash(self, amount: float):
        """初期資金を設定"""
        self.initial_cash = amount
        self.cash = amount
        self.save_portfolio()
        logger.info(f"初期資金を設定しました: ¥{amount:,.0f}")
    
    def add_transaction(self, symbol: str, transaction_type: str, shares: float, 
                       price: float, fee: float = 0.0, notes: str = "") -> str:
        """取引を追加"""
        
        # 取引IDの生成
        transaction_id = f"{symbol}_{transaction_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 取引金額の計算
        total_amount = shares * price + fee
        
        # 資金チェック（買いの場合）
        if transaction_type == "buy" and total_amount > self.cash:
            raise ValueError(f"資金不足です。必要: ¥{total_amount:,.0f}, 利用可能: ¥{self.cash:,.0f}")
        
        # 株数チェック（売りの場合）
        if transaction_type == "sell":
            if symbol not in self.positions:
                raise ValueError(f"銘柄 {symbol} のポジションがありません")
            if shares > self.positions[symbol].shares:
                raise ValueError(f"保有株数が不足です。保有: {self.positions[symbol].shares}, 売却予定: {shares}")
        
        # 取引記録の作成
        transaction = PortfolioTransaction(
            transaction_id=transaction_id,
            symbol=symbol,
            transaction_type=transaction_type,
            shares=shares,
            price=price,
            total_amount=total_amount,
            fee=fee,
            timestamp=datetime.now(),
            notes=notes
        )
        
        self.transactions.append(transaction)
        
        # ポジションの更新
        self._update_position(symbol, transaction_type, shares, price, total_amount)
        
        # キャッシュの更新
        if transaction_type == "buy":
            self.cash -= total_amount
        else:  # sell
            self.cash += (shares * price - fee)
        
        # 保存
        self.save_portfolio()
        
        logger.info(f"取引を追加しました: {transaction_id}")
        return transaction_id
    
    def _update_position(self, symbol: str, transaction_type: str, shares: float, 
                        price: float, total_amount: float):
        """ポジションを更新"""
        
        if transaction_type == "buy":
            if symbol in self.positions:
                # 既存ポジションの平均価格を更新
                position = self.positions[symbol]
                total_shares = position.shares + shares
                total_cost = (position.shares * position.avg_price) + total_amount
                new_avg_price = total_cost / total_shares
                
                position.shares = total_shares
                position.avg_price = new_avg_price
            else:
                # 新規ポジション作成
                # 会社名を取得（簡易版）
                company_name = self._get_company_name(symbol)
                sector = self.sector_mapping.get(symbol, "その他")
                
                self.positions[symbol] = Position(
                    symbol=symbol,
                    company_name=company_name,
                    shares=shares,
                    avg_price=price,
                    current_price=price,
                    total_value=shares * price,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0,
                    sector=sector,
                    weight=0.0,
                    purchase_date=datetime.now()
                )
        
        elif transaction_type == "sell":
            if symbol in self.positions:
                position = self.positions[symbol]
                position.shares -= shares
                
                # ポジションが0になった場合は削除
                if position.shares <= 0:
                    del self.positions[symbol]
    
    def _get_company_name(self, symbol: str) -> str:
        """銘柄コードから会社名を取得"""
        company_names = {
            '7203': 'トヨタ自動車',
            '6758': 'ソニーグループ',
            '9984': 'ソフトバンクグループ',
            '6861': 'キーエンス',
            '8411': 'みずほフィナンシャルグループ',
            '7267': '本田技研工業',
            '4503': 'アステラス製薬',
            '6501': '日立製作所',
            '8001': '伊藤忠商事',
            '9432': 'NTT'
        }
        
        return company_names.get(symbol, f"銘柄{symbol}")
    
    def update_market_prices(self):
        """市場価格を更新"""
        try:
            if not self.positions:
                return
            
            symbols = [f"{symbol}.T" for symbol in self.positions.keys()]
            
            # Yahoo Financeから価格を取得
            data = yf.download(symbols, period="1d", interval="1d", progress=False)
            
            if len(symbols) == 1:
                # 単一銘柄の場合
                symbol = list(self.positions.keys())[0]
                if 'Close' in data.columns:
                    current_price = data['Close'].iloc[-1]
                    self._update_position_price(symbol, current_price)
            else:
                # 複数銘柄の場合
                for symbol in self.positions.keys():
                    try:
                        symbol_with_suffix = f"{symbol}.T"
                        if ('Close', symbol_with_suffix) in data.columns:
                            current_price = data[('Close', symbol_with_suffix)].iloc[-1]
                            self._update_position_price(symbol, current_price)
                    except Exception as e:
                        logger.warning(f"価格更新失敗 {symbol}: {e}")
            
            # ポートフォリオ重み付けを再計算
            self._recalculate_weights()
            
            logger.info("市場価格を更新しました")
            
        except Exception as e:
            logger.error(f"市場価格更新エラー: {e}")
    
    def _update_position_price(self, symbol: str, current_price: float):
        """個別ポジションの価格を更新"""
        if symbol in self.positions:
            position = self.positions[symbol]
            position.current_price = current_price
            position.total_value = position.shares * current_price
            position.unrealized_pnl = position.total_value - (position.shares * position.avg_price)
            position.unrealized_pnl_pct = (position.unrealized_pnl / (position.shares * position.avg_price)) * 100
    
    def _recalculate_weights(self):
        """ポートフォリオの重み付けを再計算"""
        total_value = sum(position.total_value for position in self.positions.values())
        
        if total_value > 0:
            for position in self.positions.values():
                position.weight = (position.total_value / total_value) * 100
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """ポートフォリオサマリーを取得"""
        if not self.positions:
            return {
                'total_value': self.cash,
                'total_invested': 0.0,
                'total_pnl': 0.0,
                'total_pnl_pct': 0.0,
                'cash': self.cash,
                'positions_count': 0,
                'largest_position': None,
                'best_performer': None,
                'worst_performer': None
            }
        
        total_value = sum(position.total_value for position in self.positions.values()) + self.cash
        total_invested = sum(position.shares * position.avg_price for position in self.positions.values())
        total_pnl = sum(position.unrealized_pnl for position in self.positions.values())
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
        
        # 最大ポジション
        largest_position = max(self.positions.values(), key=lambda p: p.total_value)
        
        # パフォーマンス
        best_performer = max(self.positions.values(), key=lambda p: p.unrealized_pnl_pct)
        worst_performer = min(self.positions.values(), key=lambda p: p.unrealized_pnl_pct)
        
        return {
            'total_value': total_value,
            'total_invested': total_invested,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'cash': self.cash,
            'positions_count': len(self.positions),
            'largest_position': largest_position,
            'best_performer': best_performer,
            'worst_performer': worst_performer
        }
    
    def get_sector_allocation(self) -> pd.DataFrame:
        """セクター配分を取得"""
        if not self.positions:
            return pd.DataFrame()
        
        sector_data = {}
        for position in self.positions.values():
            sector = position.sector
            if sector not in sector_data:
                sector_data[sector] = {
                    'value': 0.0,
                    'weight': 0.0,
                    'pnl': 0.0
                }
            
            sector_data[sector]['value'] += position.total_value
            sector_data[sector]['weight'] += position.weight
            sector_data[sector]['pnl'] += position.unrealized_pnl
        
        return pd.DataFrame(sector_data).T
    
    def create_snapshot(self):
        """現在のポートフォリオ状況のスナップショットを作成"""
        summary = self.get_portfolio_summary()
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            total_value=summary['total_value'],
            total_pnl=summary['total_pnl'],
            total_pnl_pct=summary['total_pnl_pct'],
            positions_count=summary['positions_count'],
            cash=summary['cash']
        )
        
        self.snapshots.append(snapshot)
        
        # 古いスナップショット（30日以上前）を削除
        cutoff_date = datetime.now() - timedelta(days=30)
        self.snapshots = [s for s in self.snapshots if s.timestamp > cutoff_date]
        
        self.save_portfolio()
        logger.info("ポートフォリオスナップショットを作成しました")
    
    def get_performance_history(self) -> pd.DataFrame:
        """パフォーマンス履歴を取得"""
        if not self.snapshots:
            return pd.DataFrame()
        
        data = []
        for snapshot in self.snapshots:
            data.append({
                'timestamp': snapshot.timestamp,
                'total_value': snapshot.total_value,
                'total_pnl': snapshot.total_pnl,
                'total_pnl_pct': snapshot.total_pnl_pct,
                'cash': snapshot.cash
            })
        
        return pd.DataFrame(data)
    
    def save_portfolio(self):
        """ポートフォリオをファイルに保存"""
        try:
            data = {
                'positions': {symbol: position.to_dict() for symbol, position in self.positions.items()},
                'transactions': [t.to_dict() for t in self.transactions],
                'snapshots': [s.to_dict() for s in self.snapshots],
                'cash': self.cash,
                'initial_cash': self.initial_cash
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"ポートフォリオ保存エラー: {e}")
    
    def load_portfolio(self):
        """ファイルからポートフォリオを読み込み"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # ポジションの復元
                if 'positions' in data:
                    for symbol, position_data in data['positions'].items():
                        self.positions[symbol] = Position.from_dict(position_data)
                
                # 取引履歴の復元
                if 'transactions' in data:
                    self.transactions = [PortfolioTransaction.from_dict(t) for t in data['transactions']]
                
                # スナップショットの復元
                if 'snapshots' in data:
                    self.snapshots = [PortfolioSnapshot.from_dict(s) for s in data['snapshots']]
                
                # キャッシュの復元
                self.cash = data.get('cash', 0.0)
                self.initial_cash = data.get('initial_cash', 0.0)
                
                logger.info(f"ポートフォリオを読み込みました: {len(self.positions)}ポジション")
                
        except Exception as e:
            logger.error(f"ポートフォリオ読み込みエラー: {e}")

# Streamlit UI関数
def show_portfolio_management_ui():
    """ポートフォリオ管理UIを表示"""
    st.markdown("## 💼 ポートフォリオ管理")
    
    # ポートフォリオマネージャーの初期化
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = PortfolioManager()
    
    portfolio_manager = st.session_state.portfolio_manager
    
    # 自動価格更新
    if st.button("📈 価格を更新", help="最新の市場価格を取得"):
        with st.spinner("価格を更新中..."):
            portfolio_manager.update_market_prices()
            portfolio_manager.create_snapshot()
        st.success("価格を更新しました")
        st.rerun()
    
    # タブの作成
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["概要", "取引", "ポジション", "履歴", "分析"])
    
    with tab1:
        show_portfolio_overview_ui(portfolio_manager)
    
    with tab2:
        show_transaction_ui(portfolio_manager)
    
    with tab3:
        show_positions_ui(portfolio_manager)
    
    with tab4:
        show_transaction_history_ui(portfolio_manager)
    
    with tab5:
        show_portfolio_analysis_ui(portfolio_manager)

def show_portfolio_overview_ui(portfolio_manager: PortfolioManager):
    """ポートフォリオ概要UI"""
    st.markdown("### 📊 ポートフォリオ概要")
    
    # 初期資金設定
    if portfolio_manager.initial_cash == 0:
        st.warning("⚠️ 初期資金を設定してください")
        initial_cash = st.number_input("初期資金（円）", min_value=10000, value=1000000, step=10000)
        if st.button("初期資金を設定"):
            portfolio_manager.set_initial_cash(initial_cash)
            st.success("初期資金を設定しました")
            st.rerun()
        return
    
    summary = portfolio_manager.get_portfolio_summary()
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "総資産",
            f"¥{summary['total_value']:,.0f}",
            f"¥{summary['total_pnl']:,.0f}"
        )
    
    with col2:
        pnl_color = "normal" if summary['total_pnl'] >= 0 else "inverse"
        st.metric(
            "損益率",
            f"{summary['total_pnl_pct']:.2f}%",
            delta_color=pnl_color
        )
    
    with col3:
        st.metric("現金", f"¥{summary['cash']:,.0f}")
    
    with col4:
        st.metric("ポジション数", summary['positions_count'])
    
    # チャート表示
    if summary['positions_count'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # ポートフォリオ構成円グラフ
            positions_data = []
            for position in portfolio_manager.positions.values():
                positions_data.append({
                    'symbol': position.symbol,
                    'company_name': position.company_name,
                    'value': position.total_value,
                    'weight': position.weight
                })
            
            df_positions = pd.DataFrame(positions_data)
            
            fig_pie = px.pie(
                df_positions,
                values='value',
                names='company_name',
                title="ポートフォリオ構成"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # セクター配分
            sector_df = portfolio_manager.get_sector_allocation()
            if not sector_df.empty:
                fig_sector = px.pie(
                    values=sector_df['value'],
                    names=sector_df.index,
                    title="セクター配分"
                )
                st.plotly_chart(fig_sector, use_container_width=True)
        
        # パフォーマンス情報
        st.markdown("#### 📈 パフォーマンス情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if summary['best_performer']:
                best = summary['best_performer']
                st.markdown(f"""
                **🏆 最高パフォーマンス**
                - {best.company_name} ({best.symbol})
                - 損益: ¥{best.unrealized_pnl:,.0f}
                - 損益率: {best.unrealized_pnl_pct:.2f}%
                """)
        
        with col2:
            if summary['worst_performer']:
                worst = summary['worst_performer']
                st.markdown(f"""
                **📉 最低パフォーマンス**
                - {worst.company_name} ({worst.symbol})
                - 損益: ¥{worst.unrealized_pnl:,.0f}
                - 損益率: {worst.unrealized_pnl_pct:.2f}%
                """)

def show_transaction_ui(portfolio_manager: PortfolioManager):
    """取引UIを表示"""
    st.markdown("### 💱 新規取引")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("銘柄コード", placeholder="7203")
            transaction_type = st.selectbox("取引種別", ["buy", "sell"], 
                                          format_func=lambda x: "買い" if x == "buy" else "売り")
            shares = st.number_input("株数", min_value=1, value=100)
        
        with col2:
            price = st.number_input("価格（円）", min_value=0.1, value=1000.0, step=0.1)
            fee = st.number_input("手数料（円）", min_value=0.0, value=0.0, step=1.0)
            notes = st.text_input("メモ", placeholder="取引の詳細...")
        
        # 取引見積もり
        if symbol and shares and price:
            total_amount = shares * price + fee
            st.markdown(f"**取引金額**: ¥{total_amount:,.0f}")
            
            if transaction_type == "buy":
                st.markdown(f"**利用可能資金**: ¥{portfolio_manager.cash:,.0f}")
                if total_amount > portfolio_manager.cash:
                    st.error("❌ 資金不足です")
            else:
                if symbol in portfolio_manager.positions:
                    available_shares = portfolio_manager.positions[symbol].shares
                    st.markdown(f"**保有株数**: {available_shares}")
                    if shares > available_shares:
                        st.error("❌ 保有株数が不足です")
                else:
                    st.error("❌ 該当銘柄のポジションがありません")
        
        if st.form_submit_button("🔄 取引実行", type="primary"):
            if symbol and shares and price:
                try:
                    transaction_id = portfolio_manager.add_transaction(
                        symbol=symbol.upper(),
                        transaction_type=transaction_type,
                        shares=shares,
                        price=price,
                        fee=fee,
                        notes=notes
                    )
                    
                    action = "買付" if transaction_type == "buy" else "売却"
                    st.success(f"✅ {action}を実行しました！ 取引ID: {transaction_id}")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ 取引エラー: {e}")
            else:
                st.warning("⚠️ すべての項目を入力してください")

def show_positions_ui(portfolio_manager: PortfolioManager):
    """ポジション一覧UI"""
    st.markdown("### 📈 保有ポジション")
    
    if not portfolio_manager.positions:
        st.info("📭 保有ポジションはありません")
        return
    
    # ポジション一覧の表示
    positions_data = []
    for position in portfolio_manager.positions.values():
        positions_data.append({
            '銘柄': f"{position.company_name} ({position.symbol})",
            '株数': f"{position.shares:,.0f}",
            '平均価格': f"¥{position.avg_price:,.0f}",
            '現在価格': f"¥{position.current_price:,.0f}",
            '評価額': f"¥{position.total_value:,.0f}",
            '損益': f"¥{position.unrealized_pnl:,.0f}",
            '損益率': f"{position.unrealized_pnl_pct:.2f}%",
            '比重': f"{position.weight:.1f}%",
            'セクター': position.sector
        })
    
    df_positions = pd.DataFrame(positions_data)
    
    # カラム設定でスタイリング
    st.dataframe(
        df_positions,
        use_container_width=True,
        hide_index=True
    )
    
    # 個別ポジション詳細
    st.markdown("#### 📊 個別ポジション詳細")
    
    selected_symbol = st.selectbox(
        "詳細表示する銘柄を選択",
        options=list(portfolio_manager.positions.keys()),
        format_func=lambda x: f"{portfolio_manager.positions[x].company_name} ({x})"
    )
    
    if selected_symbol:
        position = portfolio_manager.positions[selected_symbol]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("投資額", f"¥{position.shares * position.avg_price:,.0f}")
            st.metric("現在価値", f"¥{position.total_value:,.0f}")
        
        with col2:
            st.metric("未実現損益", f"¥{position.unrealized_pnl:,.0f}")
            st.metric("損益率", f"{position.unrealized_pnl_pct:.2f}%")
        
        with col3:
            st.metric("ポートフォリオ比重", f"{position.weight:.2f}%")
            st.metric("購入日", position.purchase_date.strftime('%Y-%m-%d'))

def show_transaction_history_ui(portfolio_manager: PortfolioManager):
    """取引履歴UI"""
    st.markdown("### 📋 取引履歴")
    
    if not portfolio_manager.transactions:
        st.info("📭 取引履歴はありません")
        return
    
    # 取引履歴の表示
    transactions_data = []
    for transaction in reversed(portfolio_manager.transactions[-50:]):  # 最新50件
        action = "買付" if transaction.transaction_type == "buy" else "売却"
        transactions_data.append({
            '日時': transaction.timestamp.strftime('%Y-%m-%d %H:%M'),
            '銘柄': transaction.symbol,
            '取引': action,
            '株数': f"{transaction.shares:,.0f}",
            '価格': f"¥{transaction.price:,.0f}",
            '取引金額': f"¥{transaction.total_amount:,.0f}",
            '手数料': f"¥{transaction.fee:,.0f}",
            'メモ': transaction.notes
        })
    
    df_transactions = pd.DataFrame(transactions_data)
    
    st.dataframe(
        df_transactions,
        use_container_width=True,
        hide_index=True
    )
    
    # 取引統計
    st.markdown("#### 📊 取引統計")
    
    buy_transactions = [t for t in portfolio_manager.transactions if t.transaction_type == "buy"]
    sell_transactions = [t for t in portfolio_manager.transactions if t.transaction_type == "sell"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総取引数", len(portfolio_manager.transactions))
    
    with col2:
        st.metric("買付回数", len(buy_transactions))
    
    with col3:
        st.metric("売却回数", len(sell_transactions))
    
    with col4:
        total_fees = sum(t.fee for t in portfolio_manager.transactions)
        st.metric("総手数料", f"¥{total_fees:,.0f}")

def show_portfolio_analysis_ui(portfolio_manager: PortfolioManager):
    """ポートフォリオ分析UI"""
    st.markdown("### 📊 ポートフォリオ分析")
    
    # パフォーマンス履歴
    performance_df = portfolio_manager.get_performance_history()
    
    if not performance_df.empty:
        st.markdown("#### 📈 パフォーマンス推移")
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('総資産価値', '損益率'),
            vertical_spacing=0.1
        )
        
        fig.add_trace(
            go.Scatter(
                x=performance_df['timestamp'],
                y=performance_df['total_value'],
                mode='lines',
                name='総資産',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=performance_df['timestamp'],
                y=performance_df['total_pnl_pct'],
                mode='lines',
                name='損益率',
                line=dict(color='green')
            ),
            row=2, col=1
        )
        
        fig.update_layout(height=600, showlegend=False)
        fig.update_yaxis(title_text="金額（円）", row=1, col=1)
        fig.update_yaxis(title_text="損益率（%）", row=2, col=1)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # リスク分析
    if portfolio_manager.positions:
        st.markdown("#### ⚠️ リスク分析")
        
        summary = portfolio_manager.get_portfolio_summary()
        
        # 集中度リスク
        largest_weight = max(p.weight for p in portfolio_manager.positions.values())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**集中度リスク**")
            if largest_weight > 30:
                st.error(f"🔴 高リスク: 最大ポジション {largest_weight:.1f}%")
            elif largest_weight > 20:
                st.warning(f"🟡 中リスク: 最大ポジション {largest_weight:.1f}%")
            else:
                st.success(f"🟢 低リスク: 最大ポジション {largest_weight:.1f}%")
        
        with col2:
            # セクター集中度
            sector_df = portfolio_manager.get_sector_allocation()
            if not sector_df.empty:
                max_sector_weight = sector_df['weight'].max()
                st.markdown("**セクター集中度**")
                if max_sector_weight > 40:
                    st.error(f"🔴 高リスク: 最大セクター {max_sector_weight:.1f}%")
                elif max_sector_weight > 30:
                    st.warning(f"🟡 中リスク: 最大セクター {max_sector_weight:.1f}%")
                else:
                    st.success(f"🟢 低リスク: 最大セクター {max_sector_weight:.1f}%")

if __name__ == "__main__":
    # テスト実行
    st.title("💼 ポートフォリオ管理機能テスト")
    show_portfolio_management_ui()
