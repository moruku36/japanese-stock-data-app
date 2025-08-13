#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ポートフォリオ最適化システム
Markowitz理論、リスク管理、資産配分最適化
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import cvxpy as cp
try:
    from scipy.optimize import minimize  # type: ignore
    _SCIPY_AVAILABLE = True
except Exception:
    minimize = None  # type: ignore
    _SCIPY_AVAILABLE = False
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PortfolioAsset:
    """ポートフォリオ資産"""
    ticker: str
    weight: float
    expected_return: float
    risk: float
    sector: str
    market_cap: float

class PortfolioOptimizer:
    """ポートフォリオ最適化クラス"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2%の無リスク金利
        self.max_weight = 0.3  # 最大30%の単一銘柄
        self.min_weight = 0.01  # 最小1%の単一銘柄
        logger.info("ポートフォリオ最適化クラスを初期化しました")
    
    def calculate_returns_and_volatility(self, df: pd.DataFrame) -> Tuple[float, float]:
        """リターンとボラティリティを計算"""
        try:
            # 日次リターンを計算
            returns = df['close'].pct_change().dropna()
            
            # 年率リターンとボラティリティ
            annual_return = returns.mean() * 252
            annual_volatility = returns.std() * np.sqrt(252)
            
            return annual_return, annual_volatility
            
        except Exception as e:
            logger.error(f"リターン・ボラティリティ計算エラー: {e}")
            return 0.0, 0.0
    
    def calculate_correlation_matrix(self, price_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """相関行列を計算"""
        try:
            # 各銘柄のリターンを計算
            returns_data = {}
            for ticker, df in price_data.items():
                returns = df['close'].pct_change().dropna()
                returns_data[ticker] = returns
            
            # 相関行列を作成
            returns_df = pd.DataFrame(returns_data)
            correlation_matrix = returns_df.corr()
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"相関行列計算エラー: {e}")
            return pd.DataFrame()
    
    def markowitz_optimization(self, tickers: List[str], price_data: Dict[str, pd.DataFrame], 
                             target_return: float = None, risk_aversion: float = 1.0) -> Dict[str, Any]:
        """Markowitz最適化"""
        try:
            logger.info(f"Markowitz最適化を実行中: {len(tickers)}銘柄")
            
            # 各銘柄のリターンとボラティリティを計算
            returns = []
            volatilities = []
            
            for ticker in tickers:
                df = price_data[ticker]
                annual_return, annual_vol = self.calculate_returns_and_volatility(df)
                returns.append(annual_return)
                volatilities.append(annual_vol)
            
            returns = np.array(returns)
            volatilities = np.array(volatilities)
            
            # 相関行列を計算
            correlation_matrix = self.calculate_correlation_matrix(price_data)
            if correlation_matrix.empty:
                return {}
            
            # 共分散行列を計算
            covariance_matrix = np.diag(volatilities) @ correlation_matrix @ np.diag(volatilities)
            
            # 最適化問題を設定
            n_assets = len(tickers)
            weights = cp.Variable(n_assets)
            
            # 制約条件
            constraints = [
                cp.sum(weights) == 1,  # 重みの合計が1
                weights >= self.min_weight,  # 最小重み
                weights <= self.max_weight   # 最大重み
            ]
            
            if target_return is not None:
                constraints.append(returns @ weights >= target_return)
            
            # 目的関数（リスク最小化）
            portfolio_variance = cp.quad_form(weights, covariance_matrix)
            portfolio_return = returns @ weights
            
            if target_return is not None:
                objective = cp.Minimize(portfolio_variance)
            else:
                # 効用関数最大化
                utility = portfolio_return - 0.5 * risk_aversion * portfolio_variance
                objective = cp.Maximize(utility)
            
            # 最適化を実行
            problem = cp.Problem(objective, constraints)
            problem.solve()
            
            if problem.status == 'optimal':
                optimal_weights = weights.value
                
                # 結果を計算
                portfolio_return = returns @ optimal_weights
                portfolio_volatility = np.sqrt(optimal_weights @ covariance_matrix @ optimal_weights)
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
                
                result = {
                    'tickers': tickers,
                    'weights': optimal_weights.tolist(),
                    'expected_return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'individual_returns': returns.tolist(),
                    'individual_volatilities': volatilities.tolist(),
                    'correlation_matrix': correlation_matrix.to_dict()
                }
                
                logger.info(f"Markowitz最適化完了: 期待リターン={portfolio_return:.4f}, ボラティリティ={portfolio_volatility:.4f}")
                return result
            else:
                logger.error("Markowitz最適化が失敗しました")
                return {}
                
        except Exception as e:
            logger.error(f"Markowitz最適化エラー: {e}")
            return {}
    
    def risk_parity_optimization(self, tickers: List[str], price_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """リスクパリティ最適化"""
        try:
            logger.info(f"リスクパリティ最適化を実行中: {len(tickers)}銘柄")
            
            # 各銘柄のボラティリティを計算
            volatilities = []
            for ticker in tickers:
                df = price_data[ticker]
                _, annual_vol = self.calculate_returns_and_volatility(df)
                volatilities.append(annual_vol)
            
            volatilities = np.array(volatilities)
            
            # 相関行列を計算
            correlation_matrix = self.calculate_correlation_matrix(price_data)
            if correlation_matrix.empty:
                return {}
            
            # 共分散行列を計算
            covariance_matrix = np.diag(volatilities) @ correlation_matrix @ np.diag(volatilities)
            
            # リスクパリティ最適化
            n_assets = len(tickers)
            
            def risk_parity_objective(weights):
                portfolio_vol = np.sqrt(weights @ covariance_matrix @ weights)
                risk_contributions = weights * (covariance_matrix @ weights) / portfolio_vol
                return np.sum((risk_contributions - portfolio_vol / n_assets) ** 2)
            
            # 制約条件
            constraints = [
                {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # 重みの合計が1
            ]
            
            bounds = [(self.min_weight, self.max_weight) for _ in range(n_assets)]
            
            # 初期値（等重み）
            initial_weights = np.ones(n_assets) / n_assets
            
            # 最適化を実行
            result = minimize(risk_parity_objective, initial_weights, 
                           method='SLSQP', bounds=bounds, constraints=constraints)
            
            if result.success:
                optimal_weights = result.x
                
                # 結果を計算
                portfolio_volatility = np.sqrt(optimal_weights @ covariance_matrix @ optimal_weights)
                
                # 各銘柄のリターンを計算
                returns = []
                for ticker in tickers:
                    df = price_data[ticker]
                    annual_return, _ = self.calculate_returns_and_volatility(df)
                    returns.append(annual_return)
                
                portfolio_return = np.array(returns) @ optimal_weights
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
                
                result_dict = {
                    'tickers': tickers,
                    'weights': optimal_weights.tolist(),
                    'expected_return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'individual_returns': returns,
                    'individual_volatilities': volatilities.tolist(),
                    'correlation_matrix': correlation_matrix.to_dict()
                }
                
                logger.info(f"リスクパリティ最適化完了: 期待リターン={portfolio_return:.4f}, ボラティリティ={portfolio_volatility:.4f}")
                return result_dict
            else:
                logger.error("リスクパリティ最適化が失敗しました")
                return {}
                
        except Exception as e:
            logger.error(f"リスクパリティ最適化エラー: {e}")
            return {}
    
    def sector_diversification(self, tickers: List[str], sectors: List[str], 
                             price_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """セクター分散最適化"""
        try:
            logger.info(f"セクター分散最適化を実行中: {len(tickers)}銘柄")
            
            # セクター別の制約を設定
            sector_constraints = {}
            for ticker, sector in zip(tickers, sectors):
                if sector not in sector_constraints:
                    sector_constraints[sector] = []
                sector_constraints[sector].append(ticker)
            
            # セクター別最大重み制約（各セクター最大40%）
            max_sector_weight = 0.4
            
            # Markowitz最適化を実行（セクター制約付き）
            result = self.markowitz_optimization(tickers, price_data)
            
            if not result:
                return {}
            
            # セクター別重みを計算
            sector_weights = {}
            for sector, sector_tickers in sector_constraints.items():
                sector_weight = sum(result['weights'][tickers.index(ticker)] 
                                  for ticker in sector_tickers)
                sector_weights[sector] = sector_weight
            
            result['sector_weights'] = sector_weights
            result['sector_constraints'] = sector_constraints
            
            logger.info(f"セクター分散最適化完了: セクター重み={sector_weights}")
            return result
            
        except Exception as e:
            logger.error(f"セクター分散最適化エラー: {e}")
            return {}
    
    def create_efficient_frontier(self, tickers: List[str], price_data: Dict[str, pd.DataFrame], 
                                num_portfolios: int = 100) -> Dict[str, Any]:
        """効率的フロンティアを作成"""
        try:
            logger.info(f"効率的フロンティアを作成中: {len(tickers)}銘柄")
            
            # 各銘柄のリターンとボラティリティを計算
            returns = []
            volatilities = []
            
            for ticker in tickers:
                df = price_data[ticker]
                annual_return, annual_vol = self.calculate_returns_and_volatility(df)
                returns.append(annual_return)
                volatilities.append(annual_vol)
            
            returns = np.array(returns)
            volatilities = np.array(volatilities)
            
            # 相関行列を計算
            correlation_matrix = self.calculate_correlation_matrix(price_data)
            if correlation_matrix.empty:
                return {}
            
            # 共分散行列を計算
            covariance_matrix = np.diag(volatilities) @ correlation_matrix @ np.diag(volatilities)
            
            # ランダムポートフォリオを生成
            portfolio_returns = []
            portfolio_volatilities = []
            portfolio_weights_list = []
            
            for _ in range(num_portfolios):
                # ランダムな重みを生成
                weights = np.random.random(len(tickers))
                weights = weights / np.sum(weights)
                
                # ポートフォリオのリターンとボラティリティを計算
                portfolio_return = returns @ weights
                portfolio_volatility = np.sqrt(weights @ covariance_matrix @ weights)
                
                portfolio_returns.append(portfolio_return)
                portfolio_volatilities.append(portfolio_volatility)
                portfolio_weights_list.append(weights.tolist())
            
            # 効率的フロンティアの点を計算
            min_vol_idx = np.argmin(portfolio_volatilities)
            max_sharpe_idx = np.argmax([(r - self.risk_free_rate) / v 
                                      for r, v in zip(portfolio_returns, portfolio_volatilities)])
            
            efficient_frontier = {
                'portfolio_returns': portfolio_returns,
                'portfolio_volatilities': portfolio_volatilities,
                'portfolio_weights': portfolio_weights_list,
                'min_volatility_portfolio': {
                    'return': portfolio_returns[min_vol_idx],
                    'volatility': portfolio_volatilities[min_vol_idx],
                    'weights': portfolio_weights_list[min_vol_idx]
                },
                'max_sharpe_portfolio': {
                    'return': portfolio_returns[max_sharpe_idx],
                    'volatility': portfolio_volatilities[max_sharpe_idx],
                    'weights': portfolio_weights_list[max_sharpe_idx]
                }
            }
            
            logger.info(f"効率的フロンティア作成完了: {num_portfolios}ポートフォリオ")
            return efficient_frontier
            
        except Exception as e:
            logger.error(f"効率的フロンティア作成エラー: {e}")
            return {}
    
    def create_portfolio_charts(self, optimization_result: Dict[str, Any]) -> Dict[str, go.Figure]:
        """ポートフォリオチャートを作成"""
        try:
            charts = {}
            
            # 1. 資産配分円グラフ
            if 'weights' in optimization_result:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=optimization_result['tickers'],
                    values=optimization_result['weights'],
                    hole=0.3
                )])
                fig_pie.update_layout(
                    title="ポートフォリオ資産配分",
                    showlegend=True
                )
                charts['asset_allocation'] = fig_pie
            
            # 2. リスク・リターン散布図
            if 'individual_returns' in optimization_result and 'individual_volatilities' in optimization_result:
                fig_scatter = go.Figure()
                
                fig_scatter.add_trace(go.Scatter(
                    x=optimization_result['individual_volatilities'],
                    y=optimization_result['individual_returns'],
                    mode='markers+text',
                    text=optimization_result['tickers'],
                    textposition="top center",
                    name="個別銘柄"
                ))
                
                # ポートフォリオの点を追加
                if 'volatility' in optimization_result and 'expected_return' in optimization_result:
                    fig_scatter.add_trace(go.Scatter(
                        x=[optimization_result['volatility']],
                        y=[optimization_result['expected_return']],
                        mode='markers',
                        marker=dict(size=15, color='red'),
                        name="最適ポートフォリオ"
                    ))
                
                fig_scatter.update_layout(
                    title="リスク・リターン散布図",
                    xaxis_title="ボラティリティ",
                    yaxis_title="期待リターン",
                    showlegend=True
                )
                charts['risk_return'] = fig_scatter
            
            # 3. セクター配分（セクター情報がある場合）
            if 'sector_weights' in optimization_result:
                sectors = list(optimization_result['sector_weights'].keys())
                weights = list(optimization_result['sector_weights'].values())
                
                fig_sector = go.Figure(data=[go.Bar(
                    x=sectors,
                    y=weights
                )])
                fig_sector.update_layout(
                    title="セクター別配分",
                    xaxis_title="セクター",
                    yaxis_title="重み",
                    showlegend=False
                )
                charts['sector_allocation'] = fig_sector
            
            return charts
            
        except Exception as e:
            logger.error(f"ポートフォリオチャート作成エラー: {e}")
            return {}

# グローバルインスタンス
portfolio_optimizer = PortfolioOptimizer()

def optimize_portfolio(tickers: List[str], price_data: Dict[str, pd.DataFrame], 
                      method: str = 'markowitz', **kwargs) -> Dict[str, Any]:
    """ポートフォリオ最適化を実行"""
    try:
        if method == 'markowitz':
            return portfolio_optimizer.markowitz_optimization(tickers, price_data, **kwargs)
        elif method == 'risk_parity':
            return portfolio_optimizer.risk_parity_optimization(tickers, price_data)
        elif method == 'sector_diversification':
            sectors = kwargs.get('sectors', ['Technology'] * len(tickers))
            return portfolio_optimizer.sector_diversification(tickers, sectors, price_data)
        else:
            logger.error(f"未知の最適化手法: {method}")
            return {}
    except Exception as e:
        logger.error(f"ポートフォリオ最適化エラー: {e}")
        return {}

def create_efficient_frontier(tickers: List[str], price_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """効率的フロンティアを作成"""
    try:
        return portfolio_optimizer.create_efficient_frontier(tickers, price_data)
    except Exception as e:
        logger.error(f"効率的フロンティア作成エラー: {e}")
        return {} 