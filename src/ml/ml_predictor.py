#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
機械学習による株価予測システム
LSTM、Prophet、XGBoostを使用した予測モデル
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import joblib
import os
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class MLPredictor:
    """機械学習予測クラス"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_dir = "ml_models"
        self._ensure_model_dir()
        logger.info("機械学習予測クラスを初期化しました")
    
    def _ensure_model_dir(self):
        """モデル保存ディレクトリを作成"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'close', 
                    sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """データを準備"""
        try:
            # 特徴量を選択
            features = ['open', 'high', 'low', 'close', 'volume']
            data = df[features].values
            
            # データを正規化
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(data)
            
            X, y = [], []
            for i in range(sequence_length, len(scaled_data)):
                X.append(scaled_data[i-sequence_length:i])
                y.append(scaled_data[i, 3])  # close price
            
            return np.array(X), np.array(y), scaler
            
        except Exception as e:
            logger.error(f"データ準備エラー: {e}")
            return None, None, None
    
    def train_lstm_model(self, ticker: str, df: pd.DataFrame) -> bool:
        """LSTMモデルを訓練（TensorFlow非依存版）"""
        try:
            logger.info(f"LSTMモデルを訓練中: {ticker}")
            logger.warning("TensorFlowが削除されたため、LSTMモデルの訓練をスキップします。XGBoostモデルのみ利用可能です。")
            return False
            
        except Exception as e:
            logger.error(f"LSTMモデル訓練エラー: {e}")
            return False
    
    def train_xgboost_model(self, ticker: str, df: pd.DataFrame) -> bool:
        """XGBoostモデルを訓練"""
        try:
            logger.info(f"XGBoostモデルを訓練中: {ticker}")
            
            # 特徴量エンジニアリング
            df_ml = df.copy()
            df_ml['sma_5'] = df_ml['close'].rolling(window=5).mean()
            df_ml['sma_20'] = df_ml['close'].rolling(window=20).mean()
            df_ml['rsi'] = self._calculate_rsi(df_ml['close'])
            df_ml['price_change'] = df_ml['close'].pct_change()
            df_ml['volume_change'] = df_ml['volume'].pct_change()
            
            # 欠損値を処理
            df_ml = df_ml.dropna()
            
            # 特徴量を選択
            features = ['open', 'high', 'low', 'close', 'volume', 
                       'sma_5', 'sma_20', 'rsi', 'price_change', 'volume_change']
            
            # ターゲット（翌日の価格）
            df_ml['target'] = df_ml['close'].shift(-1)
            df_ml = df_ml.dropna()
            
            X = df_ml[features].values
            y = df_ml['target'].values
            
            # データを分割
            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]
            
            # XGBoostモデルを訓練
            try:
                import xgboost as xgb
            except ImportError:
                logger.error("XGBoostがインストールされていません。XGBoostモデルの訓練をスキップします。")
                return False
            
            model = xgb.XGBRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # モデルを保存
            model_path = os.path.join(self.model_dir, f"{ticker}_xgboost_model.pkl")
            joblib.dump(model, model_path)
            
            # モデルを登録
            self.models[f"{ticker}_xgboost"] = model
            
            # 評価
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            logger.info(f"XGBoostモデル訓練完了: {ticker}, MSE: {mse:.4f}, MAE: {mae:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"XGBoostモデル訓練エラー: {e}")
            return False
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSIを計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def predict_lstm(self, ticker: str, df: pd.DataFrame, days: int = 30) -> List[float]:
        """LSTMで予測（TensorFlow非依存版）"""
        try:
            logger.warning("TensorFlowが削除されたため、LSTM予測をスキップします。XGBoost予測のみ利用可能です。")
            return []
            
        except Exception as e:
            logger.error(f"LSTM予測エラー: {e}")
            return []
    
    def predict_xgboost(self, ticker: str, df: pd.DataFrame, days: int = 30) -> List[float]:
        """XGBoostで予測"""
        try:
            # XGBoostが利用可能かチェック
            try:
                import xgboost as xgb
            except ImportError:
                logger.error("XGBoostがインストールされていません。XGBoost予測をスキップします。")
                return []
            
            model_key = f"{ticker}_xgboost"
            if model_key not in self.models:
                logger.error(f"XGBoostモデルが見つかりません: {ticker}")
                return []
            
            model = self.models[model_key]
            
            # 最新データを準備
            df_ml = df.copy()
            df_ml['sma_5'] = df_ml['close'].rolling(window=5).mean()
            df_ml['sma_20'] = df_ml['close'].rolling(window=20).mean()
            df_ml['rsi'] = self._calculate_rsi(df_ml['close'])
            df_ml['price_change'] = df_ml['close'].pct_change()
            df_ml['volume_change'] = df_ml['volume'].pct_change()
            
            features = ['open', 'high', 'low', 'close', 'volume', 
                       'sma_5', 'sma_20', 'rsi', 'price_change', 'volume_change']
            
            # 最新の特徴量
            latest_features = df_ml[features].iloc[-1].values
            
            predictions = []
            current_features = latest_features.copy()
            
            for _ in range(days):
                # 予測
                pred = model.predict([current_features])[0]
                predictions.append(pred)
                
                # 特徴量を更新（簡易版）
                current_features[3] = pred  # close price
                current_features[4] = current_features[4] * 1.01  # volume
                current_features[8] = (pred - current_features[3]) / current_features[3]  # price_change
            
            return predictions
            
        except Exception as e:
            logger.error(f"XGBoost予測エラー: {e}")
            return []
    
    def get_prediction_summary(self, ticker: str, df: pd.DataFrame) -> Dict[str, Any]:
        """予測サマリーを取得"""
        try:
            # 両方のモデルで予測
            lstm_pred = self.predict_lstm(ticker, df, days=30)
            xgb_pred = self.predict_xgboost(ticker, df, days=30)
            
            if not lstm_pred or not xgb_pred:
                return {}
            
            # 予測日付を生成
            last_date = df.index[-1]
            future_dates = [last_date + timedelta(days=i+1) for i in range(30)]
            
            # 統計情報を計算
            current_price = df['close'].iloc[-1]
            
            # LSTM予測が空の場合の処理
            if not lstm_pred:
                lstm_info = {
                    'values': [],
                    'dates': [],
                    'max_price': current_price,
                    'min_price': current_price,
                    'avg_price': current_price,
                    'trend': 'neutral',
                    'status': 'unavailable'
                }
            else:
                lstm_info = {
                    'values': lstm_pred,
                    'dates': [d.strftime('%Y-%m-%d') for d in future_dates],
                    'max_price': max(lstm_pred),
                    'min_price': min(lstm_pred),
                    'avg_price': np.mean(lstm_pred),
                    'trend': 'up' if lstm_pred[-1] > current_price else 'down',
                    'status': 'available'
                }
            
            summary = {
                'ticker': ticker,
                'current_price': current_price,
                'predictions': {
                    'lstm': lstm_info,
                    'xgboost': {
                        'values': xgb_pred,
                        'dates': [d.strftime('%Y-%m-%d') for d in future_dates],
                        'max_price': max(xgb_pred),
                        'min_price': min(xgb_pred),
                        'avg_price': np.mean(xgb_pred),
                        'trend': 'up' if xgb_pred[-1] > current_price else 'down'
                    }
                },
                'confidence': {
                    'lstm': self._calculate_confidence(lstm_pred, current_price) if lstm_pred else 0.0,
                    'xgboost': self._calculate_confidence(xgb_pred, current_price)
                },
                'recommendation': self._generate_recommendation(lstm_pred, xgb_pred, current_price)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"予測サマリー取得エラー: {e}")
            return {}
    
    def _calculate_confidence(self, predictions: List[float], current_price: float) -> float:
        """予測の信頼度を計算"""
        try:
            # 予測値の分散を計算
            variance = np.var(predictions)
            # 現在価格との相関を計算
            correlation = np.corrcoef([current_price] * len(predictions), predictions)[0, 1]
            
            # 信頼度スコア（0-100）
            confidence = max(0, min(100, (1 - variance/10000) * 50 + abs(correlation) * 50))
            return round(confidence, 2)
            
        except Exception as e:
            logger.error(f"信頼度計算エラー: {e}")
            return 50.0
    
    def _generate_recommendation(self, lstm_pred: List[float], xgb_pred: List[float], 
                               current_price: float) -> str:
        """投資推奨を生成"""
        try:
            # LSTM予測が利用できない場合はXGBoostのみで判断
            if not lstm_pred:
                xgb_trend = 'up' if xgb_pred[-1] > current_price else 'down'
                xgb_change = (xgb_pred[-1] - current_price) / current_price * 100
                
                if xgb_trend == 'up':
                    if abs(xgb_change) > 10:
                        return "買い推奨（XGBoostモデル）"
                    else:
                        return "弱い買い推奨（XGBoostモデル）"
                else:
                    if abs(xgb_change) > 10:
                        return "売り推奨（XGBoostモデル）"
                    else:
                        return "弱い売り推奨（XGBoostモデル）"
            
            # 両方のモデルが利用可能な場合
            lstm_trend = 'up' if lstm_pred[-1] > current_price else 'down'
            xgb_trend = 'up' if xgb_pred[-1] > current_price else 'down'
            
            lstm_change = (lstm_pred[-1] - current_price) / current_price * 100
            xgb_change = (xgb_pred[-1] - current_price) / current_price * 100
            
            if lstm_trend == xgb_trend:
                if lstm_trend == 'up':
                    if abs(lstm_change) > 10 and abs(xgb_change) > 10:
                        return "強力な買い推奨"
                    else:
                        return "買い推奨"
                else:
                    if abs(lstm_change) > 10 and abs(xgb_change) > 10:
                        return "強力な売り推奨"
                    else:
                        return "売り推奨"
            else:
                return "中立（モデル間で意見が分かれています）"
                
        except Exception as e:
            logger.error(f"推奨生成エラー: {e}")
            return "推奨なし"

# グローバルインスタンス
ml_predictor = MLPredictor()

def train_all_models(ticker: str, df: pd.DataFrame) -> bool:
    """すべてのモデルを訓練"""
    try:
        success_lstm = ml_predictor.train_lstm_model(ticker, df)
        success_xgb = ml_predictor.train_xgboost_model(ticker, df)
        # XGBoostが成功すればTrueを返す（LSTMはTensorFlow非依存版では常にFalse）
        return success_xgb
    except Exception as e:
        logger.error(f"モデル訓練エラー: {e}")
        return False

def get_predictions(ticker: str, df: pd.DataFrame) -> Dict[str, Any]:
    """予測結果を取得"""
    try:
        return ml_predictor.get_prediction_summary(ticker, df)
    except Exception as e:
        logger.error(f"予測取得エラー: {e}")
        return {} 