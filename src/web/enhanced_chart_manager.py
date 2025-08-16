#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
強化されたチャートカスタマイズシステム
パラメータ変更、追加チャートタイプ、注釈機能、テーマ切り替えを実装
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta

# オプショナルインポート
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

class ChartType(Enum):
    """チャートタイプ"""
    CANDLESTICK = "candlestick"
    LINE = "line"
    AREA = "area"
    BAR = "bar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    RENKO = "renko"
    POINT_FIGURE = "point_figure"
    HEIKEN_ASHI = "heiken_ashi"
    VOLUME = "volume"
    CORRELATION = "correlation"

class ChartTheme(Enum):
    """チャートテーマ"""
    LIGHT = "plotly_white"
    DARK = "plotly_dark"
    BUSINESS = "simple_white"
    COLORFUL = "plotly"
    MINIMAL = "none"

@dataclass
class TechnicalIndicator:
    """テクニカル指標設定"""
    name: str
    enabled: bool
    parameters: Dict[str, Any]
    color: str
    style: str = "solid"

@dataclass
class ChartAnnotation:
    """チャート注釈"""
    x: Any  # 日付または値
    y: float
    text: str
    color: str = "#000000"
    arrow: bool = True
    background: bool = False

@dataclass
class ChartSettings:
    """チャート設定"""
    chart_type: ChartType
    theme: ChartTheme
    width: int
    height: int
    show_volume: bool
    show_grid: bool
    show_rangeslider: bool
    technical_indicators: List[TechnicalIndicator]
    annotations: List[ChartAnnotation]
    time_range: str
    color_scheme: Dict[str, str]

class EnhancedChartManager:
    """強化されたチャート管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.default_settings = self._create_default_settings()
        self.user_settings = {}
        self.chart_presets = self._create_chart_presets()
        self.technical_indicators = self._initialize_indicators()
        
        logger.info("強化されたチャートシステムを初期化しました")
    
    def _create_default_settings(self) -> ChartSettings:
        """デフォルト設定を作成"""
        return ChartSettings(
            chart_type=ChartType.CANDLESTICK,
            theme=ChartTheme.LIGHT,
            width=800,
            height=500,
            show_volume=True,
            show_grid=True,
            show_rangeslider=False,
            technical_indicators=[],
            annotations=[],
            time_range="1y",
            color_scheme={
                "bullish": "#00ff88",
                "bearish": "#ff4444",
                "volume": "#1f77b4",
                "ma": "#ff7f0e",
                "grid": "#f0f0f0"
            }
        )
    
    def _create_chart_presets(self) -> Dict[str, ChartSettings]:
        """チャートプリセットを作成"""
        presets = {}
        
        # トレーダー向け
        presets["trader"] = ChartSettings(
            chart_type=ChartType.CANDLESTICK,
            theme=ChartTheme.DARK,
            width=1200,
            height=600,
            show_volume=True,
            show_grid=True,
            show_rangeslider=False,
            technical_indicators=[
                TechnicalIndicator("SMA_20", True, {"period": 20}, "#ff7f0e"),
                TechnicalIndicator("SMA_50", True, {"period": 50}, "#2ca02c"),
                TechnicalIndicator("RSI", True, {"period": 14}, "#d62728"),
                TechnicalIndicator("MACD", True, {"fast": 12, "slow": 26, "signal": 9}, "#9467bd")
            ],
            annotations=[],
            time_range="3mo",
            color_scheme={
                "bullish": "#00ff88",
                "bearish": "#ff4444",
                "volume": "#5d5d5d",
                "ma": "#ffffff",
                "grid": "#2a2a2a"
            }
        )
        
        # 投資家向け
        presets["investor"] = ChartSettings(
            chart_type=ChartType.LINE,
            theme=ChartTheme.BUSINESS,
            width=900,
            height=400,
            show_volume=False,
            show_grid=True,
            show_rangeslider=True,
            technical_indicators=[
                TechnicalIndicator("SMA_200", True, {"period": 200}, "#2ca02c")
            ],
            annotations=[],
            time_range="2y",
            color_scheme={
                "bullish": "#28a745",
                "bearish": "#dc3545",
                "volume": "#6c757d",
                "ma": "#007bff",
                "grid": "#e9ecef"
            }
        )
        
        # アナリスト向け
        presets["analyst"] = ChartSettings(
            chart_type=ChartType.CANDLESTICK,
            theme=ChartTheme.LIGHT,
            width=1000,
            height=700,
            show_volume=True,
            show_grid=True,
            show_rangeslider=True,
            technical_indicators=[
                TechnicalIndicator("SMA_20", True, {"period": 20}, "#ff7f0e"),
                TechnicalIndicator("BB", True, {"period": 20, "std": 2}, "#17becf"),
                TechnicalIndicator("Volume_SMA", True, {"period": 20}, "#bcbd22")
            ],
            annotations=[],
            time_range="1y",
            color_scheme={
                "bullish": "#2ca02c",
                "bearish": "#d62728",
                "volume": "#1f77b4",
                "ma": "#ff7f0e",
                "grid": "#f8f9fa"
            }
        )
        
        return presets
    
    def _initialize_indicators(self) -> Dict[str, Dict[str, Any]]:
        """テクニカル指標を初期化"""
        return {
            "SMA": {
                "name": "単純移動平均",
                "parameters": {"period": 20},
                "calculation": self._calculate_sma
            },
            "EMA": {
                "name": "指数移動平均",
                "parameters": {"period": 12},
                "calculation": self._calculate_ema
            },
            "BB": {
                "name": "ボリンジャーバンド",
                "parameters": {"period": 20, "std": 2},
                "calculation": self._calculate_bollinger_bands
            },
            "RSI": {
                "name": "RSI",
                "parameters": {"period": 14},
                "calculation": self._calculate_rsi
            },
            "MACD": {
                "name": "MACD",
                "parameters": {"fast": 12, "slow": 26, "signal": 9},
                "calculation": self._calculate_macd
            },
            "Volume_SMA": {
                "name": "出来高移動平均",
                "parameters": {"period": 20},
                "calculation": self._calculate_volume_sma
            }
        }
    
    def show_chart_customization_panel(self) -> ChartSettings:
        """チャートカスタマイズパネルを表示"""
        st.sidebar.markdown("## 📊 チャート設定")
        
        # プリセット選択
        preset_names = ["カスタム"] + list(self.chart_presets.keys())
        selected_preset = st.sidebar.selectbox(
            "プリセット",
            preset_names,
            help="用途に応じたプリセット設定を選択"
        )
        
        if selected_preset != "カスタム":
            current_settings = self.chart_presets[selected_preset]
        else:
            current_settings = st.session_state.get('chart_settings', self.default_settings)
        
        # 基本設定
        st.sidebar.markdown("### 基本設定")
        
        chart_type = st.sidebar.selectbox(
            "チャートタイプ",
            [ct.value for ct in ChartType],
            index=list(ChartType).index(current_settings.chart_type),
            help="表示するチャートの種類を選択"
        )
        
        theme = st.sidebar.selectbox(
            "テーマ",
            [theme.value for theme in ChartTheme],
            index=list(ChartTheme).index(current_settings.theme),
            help="チャートの外観テーマを選択"
        )
        
        # サイズ設定
        col1, col2 = st.sidebar.columns(2)
        with col1:
            width = st.number_input(
                "幅",
                min_value=400,
                max_value=1600,
                value=current_settings.width,
                step=50
            )
        
        with col2:
            height = st.number_input(
                "高さ",
                min_value=200,
                max_value=1000,
                value=current_settings.height,
                step=50
            )
        
        # 表示オプション
        st.sidebar.markdown("### 表示オプション")
        
        show_volume = st.sidebar.checkbox(
            "出来高表示",
            value=current_settings.show_volume,
            help="出来高チャートを表示"
        )
        
        show_grid = st.sidebar.checkbox(
            "グリッド表示",
            value=current_settings.show_grid,
            help="グリッド線を表示"
        )
        
        show_rangeslider = st.sidebar.checkbox(
            "レンジスライダー",
            value=current_settings.show_rangeslider,
            help="時間範囲選択スライダーを表示"
        )
        
        # 時間範囲
        time_range = st.sidebar.selectbox(
            "時間範囲",
            ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"].index(current_settings.time_range)
        )
        
        # テクニカル指標
        st.sidebar.markdown("### テクニカル指標")
        
        selected_indicators = []
        for indicator_key, indicator_info in self.technical_indicators.items():
            enabled = st.sidebar.checkbox(
                indicator_info["name"],
                value=any(ti.name == indicator_key for ti in current_settings.technical_indicators),
                key=f"indicator_{indicator_key}"
            )
            
            if enabled:
                # パラメータ設定
                with st.sidebar.expander(f"{indicator_info['name']} 設定"):
                    parameters = {}
                    for param_name, default_value in indicator_info["parameters"].items():
                        if param_name == "period":
                            parameters[param_name] = st.number_input(
                                "期間",
                                min_value=1,
                                max_value=200,
                                value=default_value,
                                key=f"{indicator_key}_{param_name}"
                            )
                        elif param_name == "std":
                            parameters[param_name] = st.number_input(
                                "標準偏差",
                                min_value=0.5,
                                max_value=5.0,
                                value=default_value,
                                step=0.1,
                                key=f"{indicator_key}_{param_name}"
                            )
                        else:
                            parameters[param_name] = st.number_input(
                                param_name,
                                value=default_value,
                                key=f"{indicator_key}_{param_name}"
                            )
                    
                    color = st.color_picker(
                        "カラー",
                        value="#ff7f0e",
                        key=f"{indicator_key}_color"
                    )
                
                selected_indicators.append(
                    TechnicalIndicator(indicator_key, True, parameters, color)
                )
        
        # カラー設定
        st.sidebar.markdown("### カラー設定")
        
        with st.sidebar.expander("カラーカスタマイズ"):
            bullish_color = st.color_picker(
                "上昇カラー",
                value=current_settings.color_scheme.get("bullish", "#00ff88"),
                key="bullish_color"
            )
            
            bearish_color = st.color_picker(
                "下降カラー",
                value=current_settings.color_scheme.get("bearish", "#ff4444"),
                key="bearish_color"
            )
            
            volume_color = st.color_picker(
                "出来高カラー",
                value=current_settings.color_scheme.get("volume", "#1f77b4"),
                key="volume_color"
            )
        
        color_scheme = {
            "bullish": bullish_color,
            "bearish": bearish_color,
            "volume": volume_color,
            "ma": "#ff7f0e",
            "grid": "#f0f0f0"
        }
        
        # 設定を更新
        updated_settings = ChartSettings(
            chart_type=ChartType(chart_type),
            theme=ChartTheme(theme),
            width=width,
            height=height,
            show_volume=show_volume,
            show_grid=show_grid,
            show_rangeslider=show_rangeslider,
            technical_indicators=selected_indicators,
            annotations=current_settings.annotations,  # 注釈は別途管理
            time_range=time_range,
            color_scheme=color_scheme
        )
        
        # セッション状態に保存
        st.session_state['chart_settings'] = updated_settings
        
        return updated_settings
    
    def create_customized_chart(self, data: pd.DataFrame, settings: ChartSettings, title: str = "株価チャート") -> Optional[go.Figure]:
        """カスタマイズされたチャートを作成"""
        if not PLOTLY_AVAILABLE:
            st.error("Plotlyライブラリが必要です")
            return None
        
        try:
            if settings.chart_type == ChartType.CANDLESTICK:
                return self._create_candlestick_chart(data, settings, title)
            elif settings.chart_type == ChartType.LINE:
                return self._create_line_chart(data, settings, title)
            elif settings.chart_type == ChartType.AREA:
                return self._create_area_chart(data, settings, title)
            elif settings.chart_type == ChartType.HEIKEN_ASHI:
                return self._create_heiken_ashi_chart(data, settings, title)
            elif settings.chart_type == ChartType.RENKO:
                return self._create_renko_chart(data, settings, title)
            else:
                return self._create_candlestick_chart(data, settings, title)
                
        except Exception as e:
            logger.error(f"チャート作成エラー: {e}")
            return None
    
    def _create_candlestick_chart(self, data: pd.DataFrame, settings: ChartSettings, title: str) -> go.Figure:
        """ローソク足チャートを作成"""
        # サブプロット設定
        if settings.show_volume:
            fig = make_subplots(
                rows=2, cols=1,
                row_heights=[0.7, 0.3],
                vertical_spacing=0.05,
                subplot_titles=[title, "出来高"]
            )
        else:
            fig = go.Figure()
        
        # ローソク足
        candlestick = go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name="Price",
            increasing_line_color=settings.color_scheme["bullish"],
            decreasing_line_color=settings.color_scheme["bearish"],
            increasing_fillcolor=settings.color_scheme["bullish"],
            decreasing_fillcolor=settings.color_scheme["bearish"]
        )
        
        if settings.show_volume:
            fig.add_trace(candlestick, row=1, col=1)
        else:
            fig.add_trace(candlestick)
        
        # テクニカル指標を追加
        for indicator in settings.technical_indicators:
            self._add_technical_indicator(fig, data, indicator, settings)
        
        # 出来高
        if settings.show_volume and 'Volume' in data.columns:
            colors = [
                settings.color_scheme["bullish"] if close >= open
                else settings.color_scheme["bearish"]
                for close, open in zip(data['Close'], data['Open'])
            ]
            
            volume_bar = go.Bar(
                x=data.index,
                y=data['Volume'],
                name="Volume",
                marker_color=colors,
                opacity=0.7
            )
            
            fig.add_trace(volume_bar, row=2, col=1)
        
        # レイアウト設定
        self._apply_chart_layout(fig, settings, title)
        
        return fig
    
    def _create_line_chart(self, data: pd.DataFrame, settings: ChartSettings, title: str) -> go.Figure:
        """ラインチャートを作成"""
        fig = go.Figure()
        
        # メインライン
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='終値',
            line=dict(color=settings.color_scheme["bullish"], width=2)
        ))
        
        # テクニカル指標を追加
        for indicator in settings.technical_indicators:
            self._add_technical_indicator(fig, data, indicator, settings)
        
        self._apply_chart_layout(fig, settings, title)
        
        return fig
    
    def _create_area_chart(self, data: pd.DataFrame, settings: ChartSettings, title: str) -> go.Figure:
        """エリアチャートを作成"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='終値',
            fill='tonexty',
            fillcolor=f"rgba{tuple(list(plt.colors.to_rgba(settings.color_scheme['bullish'])) + [0.3])}",
            line=dict(color=settings.color_scheme["bullish"])
        ))
        
        self._apply_chart_layout(fig, settings, title)
        
        return fig
    
    def _create_heiken_ashi_chart(self, data: pd.DataFrame, settings: ChartSettings, title: str) -> go.Figure:
        """平均足チャートを作成"""
        # 平均足の計算
        ha_data = self._calculate_heiken_ashi(data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=ha_data.index,
            open=ha_data['HA_Open'],
            high=ha_data['HA_High'],
            low=ha_data['HA_Low'],
            close=ha_data['HA_Close'],
            name="平均足",
            increasing_line_color=settings.color_scheme["bullish"],
            decreasing_line_color=settings.color_scheme["bearish"]
        ))
        
        self._apply_chart_layout(fig, settings, f"{title} (平均足)")
        
        return fig
    
    def _create_renko_chart(self, data: pd.DataFrame, settings: ChartSettings, title: str) -> go.Figure:
        """レンコーチャートを作成"""
        # レンコーブロックの計算（簡易版）
        renko_data = self._calculate_renko_blocks(data)
        
        fig = go.Figure()
        
        for i, block in renko_data.iterrows():
            color = settings.color_scheme["bullish"] if block['Direction'] == 1 else settings.color_scheme["bearish"]
            
            fig.add_trace(go.Scatter(
                x=[block['Time'], block['Time'], block['Time'], block['Time'], block['Time']],
                y=[block['Low'], block['High'], block['High'], block['Low'], block['Low']],
                mode='lines',
                fill='toself',
                fillcolor=color,
                line=dict(color=color),
                showlegend=False
            ))
        
        self._apply_chart_layout(fig, settings, f"{title} (レンコー)")
        
        return fig
    
    def _add_technical_indicator(self, fig: go.Figure, data: pd.DataFrame, indicator: TechnicalIndicator, settings: ChartSettings):
        """テクニカル指標をチャートに追加"""
        if indicator.name not in self.technical_indicators:
            return
        
        calc_func = self.technical_indicators[indicator.name]["calculation"]
        result = calc_func(data, **indicator.parameters)
        
        if result is None:
            return
        
        # 結果の種類に応じて表示
        if isinstance(result, pd.Series):
            # 単一ライン（SMA、EMAなど）
            fig.add_trace(go.Scatter(
                x=data.index,
                y=result,
                mode='lines',
                name=f"{indicator.name}({','.join(map(str, indicator.parameters.values()))})",
                line=dict(color=indicator.color, width=1.5),
                opacity=0.8
            ))
        
        elif isinstance(result, pd.DataFrame):
            # 複数ライン（ボリンジャーバンド、MACDなど）
            for col in result.columns:
                line_style = dict(color=indicator.color, width=1)
                if 'upper' in col.lower() or 'lower' in col.lower():
                    line_style['dash'] = 'dash'
                
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=result[col],
                    mode='lines',
                    name=f"{indicator.name}_{col}",
                    line=line_style,
                    opacity=0.6
                ))
    
    def _apply_chart_layout(self, fig: go.Figure, settings: ChartSettings, title: str):
        """チャートレイアウトを適用"""
        fig.update_layout(
            title=title,
            width=settings.width,
            height=settings.height,
            template=settings.theme.value,
            showlegend=True,
            xaxis_rangeslider_visible=settings.show_rangeslider,
            xaxis=dict(
                title="日付",
                showgrid=settings.show_grid,
                gridcolor=settings.color_scheme["grid"]
            ),
            yaxis=dict(
                title="価格 (円)",
                showgrid=settings.show_grid,
                gridcolor=settings.color_scheme["grid"]
            )
        )
        
        # 注釈を追加
        for annotation in settings.annotations:
            fig.add_annotation(
                x=annotation.x,
                y=annotation.y,
                text=annotation.text,
                showarrow=annotation.arrow,
                arrowcolor=annotation.color,
                bgcolor="rgba(255,255,255,0.8)" if annotation.background else None
            )
    
    # テクニカル指標計算メソッド
    def _calculate_sma(self, data: pd.DataFrame, period: int) -> pd.Series:
        """単純移動平均を計算"""
        return data['Close'].rolling(window=period).mean()
    
    def _calculate_ema(self, data: pd.DataFrame, period: int) -> pd.Series:
        """指数移動平均を計算"""
        return data['Close'].ewm(span=period).mean()
    
    def _calculate_bollinger_bands(self, data: pd.DataFrame, period: int, std: float) -> pd.DataFrame:
        """ボリンジャーバンドを計算"""
        sma = data['Close'].rolling(window=period).mean()
        std_dev = data['Close'].rolling(window=period).std()
        
        return pd.DataFrame({
            'Middle': sma,
            'Upper': sma + (std_dev * std),
            'Lower': sma - (std_dev * std)
        })
    
    def _calculate_rsi(self, data: pd.DataFrame, period: int) -> pd.Series:
        """RSIを計算"""
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, data: pd.DataFrame, fast: int, slow: int, signal: int) -> pd.DataFrame:
        """MACDを計算"""
        ema_fast = data['Close'].ewm(span=fast).mean()
        ema_slow = data['Close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return pd.DataFrame({
            'MACD': macd,
            'Signal': signal_line,
            'Histogram': histogram
        })
    
    def _calculate_volume_sma(self, data: pd.DataFrame, period: int) -> pd.Series:
        """出来高移動平均を計算"""
        if 'Volume' in data.columns:
            return data['Volume'].rolling(window=period).mean()
        return pd.Series()
    
    def _calculate_heiken_ashi(self, data: pd.DataFrame) -> pd.DataFrame:
        """平均足を計算"""
        ha_data = pd.DataFrame(index=data.index)
        
        ha_data['HA_Close'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4
        
        ha_data['HA_Open'] = 0.0
        for i in range(len(data)):
            if i == 0:
                ha_data.iloc[i]['HA_Open'] = (data.iloc[i]['Open'] + data.iloc[i]['Close']) / 2
            else:
                ha_data.iloc[i]['HA_Open'] = (ha_data.iloc[i-1]['HA_Open'] + ha_data.iloc[i-1]['HA_Close']) / 2
        
        ha_data['HA_High'] = data[['High']].join(ha_data[['HA_Open', 'HA_Close']]).max(axis=1)
        ha_data['HA_Low'] = data[['Low']].join(ha_data[['HA_Open', 'HA_Close']]).min(axis=1)
        
        return ha_data
    
    def _calculate_renko_blocks(self, data: pd.DataFrame, box_size: float = None) -> pd.DataFrame:
        """レンコーブロックを計算（簡易版）"""
        if box_size is None:
            # ATRの10%をボックスサイズとする
            box_size = ((data['High'] - data['Low']).rolling(14).mean().iloc[-1]) * 0.1
        
        renko_data = []
        current_price = data.iloc[0]['Close']
        
        for i, row in data.iterrows():
            close_price = row['Close']
            
            # 上昇ブロック
            while close_price >= current_price + box_size:
                renko_data.append({
                    'Time': i,
                    'Low': current_price,
                    'High': current_price + box_size,
                    'Direction': 1
                })
                current_price += box_size
            
            # 下降ブロック
            while close_price <= current_price - box_size:
                renko_data.append({
                    'Time': i,
                    'Low': current_price - box_size,
                    'High': current_price,
                    'Direction': -1
                })
                current_price -= box_size
        
        return pd.DataFrame(renko_data)
    
    def add_chart_annotation(self, x: Any, y: float, text: str, color: str = "#000000") -> ChartAnnotation:
        """チャート注釈を追加"""
        annotation = ChartAnnotation(x=x, y=y, text=text, color=color)
        
        # セッション状態の設定を更新
        if 'chart_settings' in st.session_state:
            st.session_state['chart_settings'].annotations.append(annotation)
        
        return annotation
    
    def save_chart_preset(self, name: str, settings: ChartSettings):
        """チャート設定をプリセットとして保存"""
        self.chart_presets[name] = settings
        st.success(f"プリセット '{name}' を保存しました")
    
    def export_chart_settings(self, settings: ChartSettings) -> str:
        """チャート設定をJSONとしてエクスポート"""
        settings_dict = {
            "chart_type": settings.chart_type.value,
            "theme": settings.theme.value,
            "width": settings.width,
            "height": settings.height,
            "show_volume": settings.show_volume,
            "show_grid": settings.show_grid,
            "show_rangeslider": settings.show_rangeslider,
            "time_range": settings.time_range,
            "color_scheme": settings.color_scheme,
            "technical_indicators": [
                {
                    "name": ti.name,
                    "enabled": ti.enabled,
                    "parameters": ti.parameters,
                    "color": ti.color
                }
                for ti in settings.technical_indicators
            ]
        }
        
        return json.dumps(settings_dict, indent=2, ensure_ascii=False)

# グローバルインスタンス
chart_manager = EnhancedChartManager()

if __name__ == "__main__":
    # テスト実行
    st.title("強化されたチャートシステム テスト")
    
    # サンプルデータ生成
    dates = pd.date_range('2024-01-01', periods=100)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    test_data = pd.DataFrame({
        'Open': prices + np.random.randn(100) * 0.2,
        'High': prices + np.abs(np.random.randn(100)) * 0.5,
        'Low': prices - np.abs(np.random.randn(100)) * 0.5,
        'Close': prices,
        'Volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # カスタマイズパネル
    settings = chart_manager.show_chart_customization_panel()
    
    # チャート表示
    fig = chart_manager.create_customized_chart(test_data, settings, "テスト株価")
    
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
    
    # 設定エクスポート
    if st.button("設定をエクスポート"):
        settings_json = chart_manager.export_chart_settings(settings)
        st.download_button(
            "設定ファイルをダウンロード",
            settings_json,
            "chart_settings.json",
            "application/json"
        )
