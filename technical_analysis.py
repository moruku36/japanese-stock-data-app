#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
テクニカル分析チャート機能
移動平均線、ボリンジャーバンド、MACD、RSI、ストキャスティクス等のテクニカル指標
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """テクニカル分析クラス"""
    
    def __init__(self):
        logger.info("テクニカル分析クラスを初期化しました")
    
    def calculate_moving_averages(self, df: pd.DataFrame, periods: List[int] = [5, 20, 50, 200]) -> pd.DataFrame:
        """移動平均線を計算"""
        try:
            df_ma = df.copy()
            
            for period in periods:
                if len(df) >= period:
                    df_ma[f'MA_{period}'] = df['Close'].rolling(window=period).mean()
                else:
                    df_ma[f'MA_{period}'] = np.nan
            
            return df_ma
        except Exception as e:
            logger.error(f"移動平均線計算エラー: {e}")
            return df
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2) -> pd.DataFrame:
        """ボリンジャーバンドを計算"""
        try:
            df_bb = df.copy()
            
            if len(df) >= period:
                # 移動平均
                df_bb['BB_Middle'] = df['Close'].rolling(window=period).mean()
                
                # 標準偏差
                rolling_std = df['Close'].rolling(window=period).std()
                
                # 上下バンド
                df_bb['BB_Upper'] = df_bb['BB_Middle'] + (rolling_std * std_dev)
                df_bb['BB_Lower'] = df_bb['BB_Middle'] - (rolling_std * std_dev)
            else:
                df_bb['BB_Middle'] = np.nan
                df_bb['BB_Upper'] = np.nan
                df_bb['BB_Lower'] = np.nan
            
            return df_bb
        except Exception as e:
            logger.error(f"ボリンジャーバンド計算エラー: {e}")
            return df
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """RSIを計算"""
        try:
            df_rsi = df.copy()
            
            if len(df) >= period + 1:
                # 価格変化
                delta = df['Close'].diff()
                
                # 上昇・下降
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                
                # 平均上昇・下降
                avg_gain = gain.rolling(window=period).mean()
                avg_loss = loss.rolling(window=period).mean()
                
                # RSI計算
                rs = avg_gain / avg_loss
                df_rsi['RSI'] = 100 - (100 / (1 + rs))
            else:
                df_rsi['RSI'] = np.nan
            
            return df_rsi
        except Exception as e:
            logger.error(f"RSI計算エラー: {e}")
            return df
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACDを計算"""
        try:
            df_macd = df.copy()
            
            if len(df) >= slow:
                # EMA計算
                ema_fast = df['Close'].ewm(span=fast).mean()
                ema_slow = df['Close'].ewm(span=slow).mean()
                
                # MACDライン
                df_macd['MACD_Line'] = ema_fast - ema_slow
                
                # シグナルライン
                df_macd['MACD_Signal'] = df_macd['MACD_Line'].ewm(span=signal).mean()
                
                # ヒストグラム
                df_macd['MACD_Histogram'] = df_macd['MACD_Line'] - df_macd['MACD_Signal']
            else:
                df_macd['MACD_Line'] = np.nan
                df_macd['MACD_Signal'] = np.nan
                df_macd['MACD_Histogram'] = np.nan
            
            return df_macd
        except Exception as e:
            logger.error(f"MACD計算エラー: {e}")
            return df
    
    def calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """ストキャスティクスを計算"""
        try:
            df_stoch = df.copy()
            
            if len(df) >= k_period:
                # 期間中の最高値・最安値
                highest_high = df['High'].rolling(window=k_period).max()
                lowest_low = df['Low'].rolling(window=k_period).min()
                
                # %K
                df_stoch['Stoch_K'] = ((df['Close'] - lowest_low) / (highest_high - lowest_low)) * 100
                
                # %D（%Kの移動平均）
                df_stoch['Stoch_D'] = df_stoch['Stoch_K'].rolling(window=d_period).mean()
            else:
                df_stoch['Stoch_K'] = np.nan
                df_stoch['Stoch_D'] = np.nan
            
            return df_stoch
        except Exception as e:
            logger.error(f"ストキャスティクス計算エラー: {e}")
            return df
    
    def create_candlestick_chart(self, df: pd.DataFrame, ticker: str, 
                                show_ma: bool = True, show_bb: bool = False,
                                show_volume: bool = True) -> go.Figure:
        """ローソク足チャートを作成"""
        try:
            # データをコピー
            df_chart = df.copy()
            
            # 技術指標を計算
            if show_ma:
                df_chart = self.calculate_moving_averages(df_chart)
            
            if show_bb:
                df_chart = self.calculate_bollinger_bands(df_chart)
            
            # サブプロットを作成
            if show_volume:
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.03,
                    subplot_titles=(f'{ticker} 株価チャート', '出来高'),
                    row_width=[0.7, 0.3]
                )
            else:
                fig = make_subplots(
                    rows=1, cols=1,
                    subplot_titles=(f'{ticker} 株価チャート',)
                )
            
            # ローソク足チャート
            fig.add_trace(
                go.Candlestick(
                    x=df_chart.index,
                    open=df_chart['Open'],
                    high=df_chart['High'],
                    low=df_chart['Low'],
                    close=df_chart['Close'],
                    name='株価',
                    increasing_line_color='#26a69a',
                    decreasing_line_color='#ef5350'
                ),
                row=1, col=1
            )
            
            # 移動平均線
            if show_ma:
                ma_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                ma_periods = [5, 20, 50, 200]
                
                for i, period in enumerate(ma_periods):
                    if f'MA_{period}' in df_chart.columns and not df_chart[f'MA_{period}'].isna().all():
                        fig.add_trace(
                            go.Scatter(
                                x=df_chart.index,
                                y=df_chart[f'MA_{period}'],
                                mode='lines',
                                name=f'{period}日移動平均',
                                line=dict(color=ma_colors[i], width=1.5),
                                opacity=0.8
                            ),
                            row=1, col=1
                        )
            
            # ボリンジャーバンド
            if show_bb and 'BB_Upper' in df_chart.columns:
                # 上バンド
                fig.add_trace(
                    go.Scatter(
                        x=df_chart.index,
                        y=df_chart['BB_Upper'],
                        mode='lines',
                        name='ボリンジャーバンド上',
                        line=dict(color='rgba(255, 107, 107, 0.5)', width=1),
                        fill=None
                    ),
                    row=1, col=1
                )
                
                # 下バンド
                fig.add_trace(
                    go.Scatter(
                        x=df_chart.index,
                        y=df_chart['BB_Lower'],
                        mode='lines',
                        name='ボリンジャーバンド下',
                        line=dict(color='rgba(255, 107, 107, 0.5)', width=1),
                        fill='tonexty',
                        fillcolor='rgba(255, 107, 107, 0.1)'
                    ),
                    row=1, col=1
                )
                
                # 中バンド
                fig.add_trace(
                    go.Scatter(
                        x=df_chart.index,
                        y=df_chart['BB_Middle'],
                        mode='lines',
                        name='ボリンジャーバンド中',
                        line=dict(color='rgba(255, 107, 107, 0.8)', width=1.5)
                    ),
                    row=1, col=1
                )
            
            # 出来高チャート
            if show_volume:
                colors = ['red' if close < open else 'green' 
                         for close, open in zip(df_chart['Close'], df_chart['Open'])]
                
                fig.add_trace(
                    go.Bar(
                        x=df_chart.index,
                        y=df_chart['Volume'],
                        name='出来高',
                        marker_color=colors,
                        opacity=0.7
                    ),
                    row=2, col=1
                )
            
            # レイアウト設定
            fig.update_layout(
                title=f'{ticker} テクニカル分析チャート',
                xaxis_title='日付',
                yaxis_title='株価 (円)',
                height=600,
                showlegend=True,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"ローソク足チャート作成エラー: {e}")
            return None
    
    def create_technical_indicators_chart(self, df: pd.DataFrame, ticker: str) -> go.Figure:
        """技術指標チャートを作成"""
        try:
            # データをコピー
            df_indicators = df.copy()
            
            # 技術指標を計算
            df_indicators = self.calculate_macd(df_indicators)
            df_indicators = self.calculate_rsi(df_indicators)
            df_indicators = self.calculate_stochastic(df_indicators)
            
            # サブプロットを作成
            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=(
                    f'{ticker} 株価',
                    'MACD',
                    'RSI',
                    'ストキャスティクス'
                ),
                row_width=[0.4, 0.2, 0.2, 0.2]
            )
            
            # 株価チャート
            fig.add_trace(
                go.Scatter(
                    x=df_indicators.index,
                    y=df_indicators['Close'],
                    mode='lines',
                    name='株価',
                    line=dict(color='#1f77b4', width=2)
                ),
                row=1, col=1
            )
            
            # MACD
            if 'MACD_Line' in df_indicators.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_indicators.index,
                        y=df_indicators['MACD_Line'],
                        mode='lines',
                        name='MACD',
                        line=dict(color='blue', width=1.5)
                    ),
                    row=2, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df_indicators.index,
                        y=df_indicators['MACD_Signal'],
                        mode='lines',
                        name='シグナル',
                        line=dict(color='red', width=1.5)
                    ),
                    row=2, col=1
                )
                
                # ヒストグラム
                colors = ['green' if val >= 0 else 'red' for val in df_indicators['MACD_Histogram']]
                fig.add_trace(
                    go.Bar(
                        x=df_indicators.index,
                        y=df_indicators['MACD_Histogram'],
                        name='ヒストグラム',
                        marker_color=colors,
                        opacity=0.7
                    ),
                    row=2, col=1
                )
            
            # RSI
            if 'RSI' in df_indicators.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_indicators.index,
                        y=df_indicators['RSI'],
                        mode='lines',
                        name='RSI',
                        line=dict(color='purple', width=1.5)
                    ),
                    row=3, col=1
                )
                
                # 過買い・過売りライン
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            
            # ストキャスティクス
            if 'Stoch_K' in df_indicators.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_indicators.index,
                        y=df_indicators['Stoch_K'],
                        mode='lines',
                        name='%K',
                        line=dict(color='blue', width=1.5)
                    ),
                    row=4, col=1
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=df_indicators.index,
                        y=df_indicators['Stoch_D'],
                        mode='lines',
                        name='%D',
                        line=dict(color='red', width=1.5)
                    ),
                    row=4, col=1
                )
                
                # 過買い・過売りライン
                fig.add_hline(y=80, line_dash="dash", line_color="red", row=4, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="green", row=4, col=1)
            
            # レイアウト設定
            fig.update_layout(
                title=f'{ticker} テクニカル指標',
                height=800,
                showlegend=True,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"テクニカル指標チャート作成エラー: {e}")
            return None
    
    def get_technical_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """テクニカル分析シグナルを取得"""
        try:
            signals = {}
            
            # データをコピー
            df_signals = df.copy()
            
            # 技術指標を計算
            df_signals = self.calculate_moving_averages(df_signals)
            df_signals = self.calculate_rsi(df_signals)
            df_signals = self.calculate_macd(df_signals)
            df_signals = self.calculate_stochastic(df_signals)
            
            # 最新データ
            latest = df_signals.iloc[-1]
            prev = df_signals.iloc[-2] if len(df_signals) > 1 else latest
            
            # 移動平均シグナル
            if 'MA_5' in df_signals.columns and 'MA_20' in df_signals.columns:
                if not pd.isna(latest['MA_5']) and not pd.isna(latest['MA_20']):
                    if latest['MA_5'] > latest['MA_20'] and prev['MA_5'] <= prev['MA_20']:
                        signals['ma_signal'] = '買い（ゴールデンクロス）'
                    elif latest['MA_5'] < latest['MA_20'] and prev['MA_5'] >= prev['MA_20']:
                        signals['ma_signal'] = '売り（デッドクロス）'
                    else:
                        signals['ma_signal'] = '中立'
            
            # RSIシグナル
            if 'RSI' in df_signals.columns and not pd.isna(latest['RSI']):
                if latest['RSI'] < 30:
                    signals['rsi_signal'] = '買い（過売り）'
                elif latest['RSI'] > 70:
                    signals['rsi_signal'] = '売り（過買い）'
                else:
                    signals['rsi_signal'] = '中立'
            
            # MACDシグナル
            if 'MACD_Line' in df_signals.columns and 'MACD_Signal' in df_signals.columns:
                if not pd.isna(latest['MACD_Line']) and not pd.isna(latest['MACD_Signal']):
                    if latest['MACD_Line'] > latest['MACD_Signal'] and prev['MACD_Line'] <= prev['MACD_Signal']:
                        signals['macd_signal'] = '買い（MACDゴールデンクロス）'
                    elif latest['MACD_Line'] < latest['MACD_Signal'] and prev['MACD_Line'] >= prev['MACD_Signal']:
                        signals['macd_signal'] = '売り（MACDデッドクロス）'
                    else:
                        signals['macd_signal'] = '中立'
            
            # ストキャスティクスシグナル
            if 'Stoch_K' in df_signals.columns and 'Stoch_D' in df_signals.columns:
                if not pd.isna(latest['Stoch_K']) and not pd.isna(latest['Stoch_D']):
                    if latest['Stoch_K'] < 20 and latest['Stoch_D'] < 20:
                        signals['stoch_signal'] = '買い（過売り）'
                    elif latest['Stoch_K'] > 80 and latest['Stoch_D'] > 80:
                        signals['stoch_signal'] = '売り（過買い）'
                    else:
                        signals['stoch_signal'] = '中立'
            
            return signals
            
        except Exception as e:
            logger.error(f"テクニカル分析シグナル取得エラー: {e}")
            return {}

def create_technical_chart(df: pd.DataFrame, ticker: str, chart_type: str = 'candlestick') -> go.Figure:
    """テクニカル分析チャートを作成（簡易関数）"""
    analyzer = TechnicalAnalyzer()
    
    if chart_type == 'candlestick':
        return analyzer.create_candlestick_chart(df, ticker)
    elif chart_type == 'indicators':
        return analyzer.create_technical_indicators_chart(df, ticker)
    else:
        return analyzer.create_candlestick_chart(df, ticker)

def get_technical_signals(df: pd.DataFrame) -> Dict[str, Any]:
    """テクニカル分析シグナルを取得（簡易関数）"""
    analyzer = TechnicalAnalyzer()
    return analyzer.get_technical_signals(df) 