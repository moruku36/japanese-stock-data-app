#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ポートフォリオ最適化機能
Modern Portfolio Theory実装
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any
try:
    from scipy.optimize import minimize  # type: ignore
    _SCIPY_AVAILABLE = True
except Exception:
    minimize = None  # type: ignore
    _SCIPY_AVAILABLE = False
try:
    import yfinance as yf  # type: ignore
    _YF_AVAILABLE = True
except Exception:
    yf = None  # type: ignore
    _YF_AVAILABLE = False

logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    """ポートフォリオ最適化クラス"""
    
    def __init__(self):
        self.risk_free_rate = 0.001  # 無リスク金利（年率0.1%）
        self.trading_days = 252  # 年間取引日数
    
    def fetch_price_data(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        """株価データを取得"""
        try:
            price_data = pd.DataFrame()
            
            for ticker in tickers:
                # 日本株の場合は.Tを追加
                yahoo_ticker = f"{ticker}.T" if ticker.isdigit() else ticker
                
                try:
                    stock = yf.Ticker(yahoo_ticker)
                    hist = stock.history(period=period)
                    if not hist.empty:
                        price_data[ticker] = hist['Close']
                except:
                    # フォールバック：サンプルデータを生成
                    dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
                    np.random.seed(hash(ticker) % 2**32)
                    returns = np.random.normal(0.0005, 0.02, 252)
                    prices = 1000 * np.exp(np.cumsum(returns))
                    price_data[ticker] = pd.Series(prices, index=dates)
            
            return price_data.dropna()
            
        except Exception as e:
            logger.error(f"価格データ取得エラー: {e}")
            # サンプルデータを返す
            return self._generate_sample_data(tickers)
    
    def _generate_sample_data(self, tickers: List[str]) -> pd.DataFrame:
        """サンプル価格データを生成"""
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        price_data = pd.DataFrame(index=dates)
        
        for ticker in tickers:
            np.random.seed(hash(ticker) % 2**32)
            returns = np.random.normal(0.0005, 0.02, 252)
            prices = 1000 * np.exp(np.cumsum(returns))
            price_data[ticker] = prices
        
        return price_data
    
    def calculate_returns(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """リターンを計算"""
        return price_data.pct_change().dropna()
    
    def calculate_portfolio_metrics(self, weights: np.array, returns: pd.DataFrame) -> Dict[str, float]:
        """ポートフォリオの指標を計算"""
        portfolio_return = np.sum(returns.mean() * weights) * self.trading_days
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * self.trading_days, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio
        }
    
    def optimize_portfolio(self, returns: pd.DataFrame, objective: str = 'sharpe') -> Dict[str, Any]:
        """ポートフォリオ最適化"""
        if not _SCIPY_AVAILABLE or minimize is None:
            st.warning("scipyが見つからないため最適化をスキップします。requirements.txtでscipyをインストールしてください。")
            n_assets = len(returns.columns)
            weights = np.array([1/n_assets] * n_assets)
            metrics = self.calculate_portfolio_metrics(weights, returns)
            return {
                'weights': weights,
                'tickers': returns.columns.tolist(),
                'metrics': metrics,
                'success': True,
                'note': 'scipy未インストールのため等重みを返却'
            }
        n_assets = len(returns.columns)
        
        # 制約条件
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # 初期値（等重みポートフォリオ）
        initial_weights = np.array([1/n_assets] * n_assets)
        
        if objective == 'sharpe':
            # シャープレシオ最大化
            def negative_sharpe(weights):
                metrics = self.calculate_portfolio_metrics(weights, returns)
                return -metrics['sharpe_ratio']
            
            result = minimize(
                negative_sharpe,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
        
        elif objective == 'min_variance':
            # 最小分散
            def portfolio_variance(weights):
                return self.calculate_portfolio_metrics(weights, returns)['volatility']**2
            
            result = minimize(
                portfolio_variance,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
        
        elif objective == 'max_return':
            # 最大リターン
            def negative_return(weights):
                return -self.calculate_portfolio_metrics(weights, returns)['return']
            
            result = minimize(
                negative_return,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
        
        if result.success:
            optimal_weights = result.x
            metrics = self.calculate_portfolio_metrics(optimal_weights, returns)
            
            return {
                'weights': optimal_weights,
                'tickers': returns.columns.tolist(),
                'metrics': metrics,
                'success': True
            }
        else:
            return {'success': False, 'message': '最適化に失敗しました'}
    
    def generate_efficient_frontier(self, returns: pd.DataFrame, num_portfolios: int = 100) -> pd.DataFrame:
        """効率的フロンティアを生成"""
        n_assets = len(returns.columns)
        results = []
        
        # リターンの範囲を設定
        min_ret = returns.mean().min() * self.trading_days
        max_ret = returns.mean().max() * self.trading_days
        target_returns = np.linspace(min_ret, max_ret, num_portfolios)
        
        for target in target_returns:
            # 目標リターン制約
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x, target=target: np.sum(returns.mean() * x) * self.trading_days - target}
            ]
            
            bounds = tuple((0, 1) for _ in range(n_assets))
            initial_weights = np.array([1/n_assets] * n_assets)
            
            # 最小分散
            def portfolio_variance(weights):
                return self.calculate_portfolio_metrics(weights, returns)['volatility']**2
            
            result = minimize(
                portfolio_variance,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )
            
            if result.success:
                metrics = self.calculate_portfolio_metrics(result.x, returns)
                results.append({
                    'return': metrics['return'],
                    'volatility': metrics['volatility'],
                    'sharpe_ratio': metrics['sharpe_ratio']
                })
        
        return pd.DataFrame(results)
    
    def monte_carlo_simulation(self, weights: np.array, returns: pd.DataFrame, 
                             time_horizon: int = 252, num_simulations: int = 1000) -> np.array:
        """モンテカルロシミュレーション"""
        portfolio_returns = returns.dot(weights)
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()
        
        # シミュレーション実行
        simulations = []
        for _ in range(num_simulations):
            random_returns = np.random.normal(mean_return, std_return, time_horizon)
            price_path = 100 * np.exp(np.cumsum(random_returns))  # 初期値100
            simulations.append(price_path)
        
        return np.array(simulations)
    
    def calculate_var_cvar(self, simulations: np.array, confidence_level: float = 0.05) -> Dict[str, float]:
        """VaR (Value at Risk) と CVaR (Conditional Value at Risk) を計算"""
        final_values = simulations[:, -1]
        initial_value = 100
        
        losses = initial_value - final_values
        losses_sorted = np.sort(losses)
        
        var_index = int(confidence_level * len(losses_sorted))
        var = losses_sorted[var_index]
        cvar = losses_sorted[:var_index].mean()
        
        return {
            'var': var,
            'cvar': cvar,
            'var_percent': (var / initial_value) * 100,
            'cvar_percent': (cvar / initial_value) * 100
        }

def render_portfolio_optimization():
    """ポートフォリオ最適化メイン画面"""
    st.title("📈 ポートフォリオ最適化")
    
    optimizer = PortfolioOptimizer()
    
    # サイドバー設定
    st.sidebar.markdown("### ⚙️ 設定")
    
    # デフォルト銘柄
    default_tickers = ["7203", "6758", "9984", "6861", "9434"]
    
    # 銘柄選択
    ticker_input = st.sidebar.text_area(
        "銘柄コード（改行区切り）",
        value="\n".join(default_tickers),
        height=150
    )
    
    tickers = [ticker.strip() for ticker in ticker_input.split('\n') if ticker.strip()]
    
    if len(tickers) < 2:
        st.error("最低2銘柄を選択してください")
        return
    
    # 期間選択
    period = st.sidebar.selectbox(
        "データ期間",
        ["1y", "2y", "3y", "5y"],
        format_func=lambda x: {"1y": "1年", "2y": "2年", "3y": "3年", "5y": "5年"}[x]
    )
    
    # 最適化目標
    objective = st.sidebar.selectbox(
        "最適化目標",
        ["sharpe", "min_variance", "max_return"],
        format_func=lambda x: {
            "sharpe": "シャープレシオ最大化",
            "min_variance": "最小分散",
            "max_return": "最大リターン"
        }[x]
    )
    
    # データ取得
    with st.spinner("データを取得中..."):
        price_data = optimizer.fetch_price_data(tickers, period)
        returns = optimizer.calculate_returns(price_data)
    
    if price_data.empty:
        st.error("データを取得できませんでした")
        return
    
    # タブ作成
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 最適化結果", "📈 効率的フロンティア", "🎲 モンテカルロ", "📉 リスク分析", "📋 詳細データ"
    ])
    
    # 最適化実行
    optimization_result = optimizer.optimize_portfolio(returns, objective)
    
    with tab1:
        if optimization_result['success']:
            st.success("✅ ポートフォリオ最適化が完了しました")
            
            # 最適化結果表示
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📊 最適ポートフォリオ構成")
                
                weights_df = pd.DataFrame({
                    '銘柄': optimization_result['tickers'],
                    '構成比': optimization_result['weights'],
                    '構成比(%)': optimization_result['weights'] * 100
                }).round(4)
                
                st.dataframe(weights_df, use_container_width=True)
                
                # 円グラフ
                fig_pie = px.pie(
                    values=optimization_result['weights'],
                    names=optimization_result['tickers'],
                    title="ポートフォリオ構成比"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("#### 📈 ポートフォリオ指標")
                
                metrics = optimization_result['metrics']
                
                st.metric(
                    "期待リターン（年率）",
                    f"{metrics['return']:.2%}",
                    help="年間期待リターン"
                )
                
                st.metric(
                    "ボラティリティ（年率）",
                    f"{metrics['volatility']:.2%}",
                    help="年間標準偏差"
                )
                
                st.metric(
                    "シャープレシオ",
                    f"{metrics['sharpe_ratio']:.2f}",
                    help="リスク調整後リターン"
                )
                
                # 投資額計算
                st.markdown("#### 💰 投資額配分")
                investment_amount = st.number_input(
                    "投資総額（円）",
                    min_value=10000,
                    value=1000000,
                    step=10000
                )
                
                allocation_df = pd.DataFrame({
                    '銘柄': optimization_result['tickers'],
                    '投資額': optimization_result['weights'] * investment_amount,
                    '株数（概算）': (optimization_result['weights'] * investment_amount) // price_data.iloc[-1].values
                })
                
                st.dataframe(allocation_df, use_container_width=True)
        
        else:
            st.error("❌ ポートフォリオ最適化に失敗しました")
    
    with tab2:
        st.markdown("#### 📈 効率的フロンティア")
        
        with st.spinner("効率的フロンティアを計算中..."):
            frontier_data = optimizer.generate_efficient_frontier(returns)
        
        if not frontier_data.empty:
            # 効率的フロンティアのプロット
            fig = go.Figure()
            
            # 効率的フロンティア
            fig.add_trace(go.Scatter(
                x=frontier_data['volatility'],
                y=frontier_data['return'],
                mode='lines',
                name='効率的フロンティア',
                line=dict(color='blue', width=3)
            ))
            
            # 最適ポートフォリオ
            if optimization_result['success']:
                fig.add_trace(go.Scatter(
                    x=[optimization_result['metrics']['volatility']],
                    y=[optimization_result['metrics']['return']],
                    mode='markers',
                    name='最適ポートフォリオ',
                    marker=dict(color='red', size=12, symbol='star')
                ))
            
            # 個別銘柄
            individual_returns = returns.mean() * optimizer.trading_days
            individual_vols = returns.std() * np.sqrt(optimizer.trading_days)
            
            fig.add_trace(go.Scatter(
                x=individual_vols,
                y=individual_returns,
                mode='markers+text',
                name='個別銘柄',
                text=tickers,
                textposition='top center',
                marker=dict(color='green', size=8)
            ))
            
            fig.update_layout(
                title='効率的フロンティア',
                xaxis_title='ボラティリティ（年率）',
                yaxis_title='期待リターン（年率）',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # フロンティアデータ表示
            st.markdown("#### 📊 効率的フロンティアデータ")
            st.dataframe(frontier_data.round(4), use_container_width=True)
    
    with tab3:
        st.markdown("#### 🎲 モンテカルロシミュレーション")
        
        if optimization_result['success']:
            # シミュレーション設定
            col1, col2 = st.columns(2)
            
            with col1:
                time_horizon = st.slider("投資期間（日）", 30, 1000, 252)
            
            with col2:
                num_simulations = st.slider("シミュレーション回数", 100, 5000, 1000)
            
            with st.spinner("モンテカルロシミュレーション実行中..."):
                simulations = optimizer.monte_carlo_simulation(
                    optimization_result['weights'],
                    returns,
                    time_horizon,
                    num_simulations
                )
            
            # シミュレーション結果のプロット
            fig = go.Figure()
            
            # 一部のパスを表示（重すぎないように）
            sample_paths = simulations[:min(100, num_simulations)]
            
            for i, path in enumerate(sample_paths):
                fig.add_trace(go.Scatter(
                    y=path,
                    mode='lines',
                    line=dict(color='lightblue', width=0.5),
                    showlegend=False
                ))
            
            # 平均パス
            mean_path = simulations.mean(axis=0)
            fig.add_trace(go.Scatter(
                y=mean_path,
                mode='lines',
                name='平均パス',
                line=dict(color='red', width=3)
            ))
            
            # 信頼区間
            percentiles = np.percentile(simulations, [5, 95], axis=0)
            
            fig.add_trace(go.Scatter(
                y=percentiles[1],
                mode='lines',
                name='95%信頼区間上限',
                line=dict(color='green', dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                y=percentiles[0],
                mode='lines',
                name='95%信頼区間下限',
                line=dict(color='red', dash='dash')
            ))
            
            fig.update_layout(
                title=f'モンテカルロシミュレーション（{num_simulations}回、{time_horizon}日）',
                xaxis_title='日数',
                yaxis_title='ポートフォリオ価値',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 最終価値の分布
            final_values = simulations[:, -1]
            
            fig_hist = px.histogram(
                x=final_values,
                nbins=50,
                title='最終ポートフォリオ価値の分布'
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # 統計情報
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("平均最終価値", f"¥{final_values.mean():.0f}")
            
            with col2:
                st.metric("中央値", f"¥{np.median(final_values):.0f}")
            
            with col3:
                st.metric("標準偏差", f"¥{final_values.std():.0f}")
    
    with tab4:
        st.markdown("#### 📉 リスク分析")
        
        if optimization_result['success']:
            # VaR/CVaR計算
            simulations = optimizer.monte_carlo_simulation(
                optimization_result['weights'],
                returns,
                252,  # 1年
                1000
            )
            
            risk_metrics = optimizer.calculate_var_cvar(simulations)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📊 VaR (Value at Risk)")
                st.metric(
                    "VaR (5%)",
                    f"¥{risk_metrics['var']:.0f}",
                    f"{risk_metrics['var_percent']:.2f}%"
                )
                st.info("95%の確率で損失がこの金額以下に収まります")
            
            with col2:
                st.markdown("##### 📊 CVaR (Conditional VaR)")
                st.metric(
                    "CVaR (5%)",
                    f"¥{risk_metrics['cvar']:.0f}",
                    f"{risk_metrics['cvar_percent']:.2f}%"
                )
                st.info("最悪5%のシナリオでの平均損失です")
            
            # ドローダウン分析
            portfolio_cumulative_returns = (returns.dot(optimization_result['weights']) + 1).cumprod()
            rolling_max = portfolio_cumulative_returns.expanding().max()
            drawdown = (portfolio_cumulative_returns / rolling_max - 1) * 100
            
            fig_dd = go.Figure()
            
            fig_dd.add_trace(go.Scatter(
                x=drawdown.index,
                y=drawdown,
                mode='lines',
                fill='tonexty',
                name='ドローダウン',
                line=dict(color='red')
            ))
            
            fig_dd.update_layout(
                title='ドローダウン分析',
                xaxis_title='日付',
                yaxis_title='ドローダウン (%)',
                height=400
            )
            
            st.plotly_chart(fig_dd, use_container_width=True)
            
            st.metric("最大ドローダウン", f"{drawdown.min():.2f}%")
    
    with tab5:
        st.markdown("#### 📋 詳細データ")
        
        # 価格データ
        st.markdown("##### 💹 価格データ")
        st.dataframe(price_data.tail(10), use_container_width=True)
        
        # リターンデータ
        st.markdown("##### 📈 リターンデータ")
        st.dataframe(returns.tail(10), use_container_width=True)
        
        # 相関行列
        st.markdown("##### 🔗 相関行列")
        corr_matrix = returns.corr()
        
        fig_corr = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title="銘柄間相関行列"
        )
        
        st.plotly_chart(fig_corr, use_container_width=True)
        
        # 統計サマリー
        st.markdown("##### 📊 統計サマリー")
        stats_df = returns.describe().round(4)
        st.dataframe(stats_df, use_container_width=True)

if __name__ == "__main__":
    render_portfolio_optimization()
