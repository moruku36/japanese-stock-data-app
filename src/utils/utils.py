#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ユーティリティ関数群
データ処理、検証、ファイル操作などの共通機能
"""

import os
import json
import time
import hashlib
import logging
import pickle
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
import psutil
import gc

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        self.start_time = None
        self.memory_start = None
    
    def start(self):
        """監視開始"""
        self.start_time = time.time()
        self.memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    def end(self, operation_name: str = "Operation"):
        """監視終了"""
        if self.start_time is None:
            return
        
        elapsed_time = time.time() - self.start_time
        memory_end = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_diff = memory_end - self.memory_start
        
        logger.info(f"{operation_name}: {elapsed_time:.2f}s, Memory: {memory_diff:+.1f}MB")
        
        self.start_time = None
        self.memory_start = None

def performance_monitor(func):
    """パフォーマンス監視デコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        monitor = PerformanceMonitor()
        monitor.start()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            monitor.end(func.__name__)
    return wrapper

class OptimizedCache:
    """最適化されたキャッシュクラス"""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache = {}
        self.access_times = {}
    
    def get(self, key: str) -> Any:
        """キャッシュから値を取得"""
        if key in self.cache:
            # TTLチェック
            if time.time() - self.access_times[key] > self.ttl_hours * 3600:
                del self.cache[key]
                del self.access_times[key]
                return None
            
            # アクセス時間を更新
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """キャッシュに値を設定"""
        # サイズ制限チェック
        if len(self.cache) >= self.max_size:
            # 最も古いアクセスを削除
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def clear(self):
        """キャッシュをクリア"""
        self.cache.clear()
        self.access_times.clear()

class MemoryOptimizer:
    """メモリ最適化クラス"""
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """データフレームのメモリ使用量を最適化"""
        for col in df.columns:
            if df[col].dtype == 'object':
                # 文字列カラムの最適化
                if df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')
            elif df[col].dtype == 'float64':
                # 浮動小数点の最適化
                if df[col].isnull().sum() == 0:
                    df[col] = pd.to_numeric(df[col], downcast='float')
            elif df[col].dtype == 'int64':
                # 整数の最適化
                df[col] = pd.to_numeric(df[col], downcast='integer')
        
        return df
    
    @staticmethod
    def cleanup_memory():
        """メモリクリーンアップ"""
        gc.collect()
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """メモリ使用量を取得"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        }

class BatchProcessor:
    """バッチ処理クラス"""
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
    
    def process_batch(self, items: List[Any], processor_func) -> List[Any]:
        """バッチ処理を実行"""
        results = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = [processor_func(item) for item in batch]
            results.extend(batch_results)
            
            # メモリクリーンアップ
            MemoryOptimizer.cleanup_memory()
        
        return results

class ProgressBar:
    """プログレスバークラス"""
    
    def __init__(self, total: int, description: str = "処理中", width: int = 50):
        """
        初期化
        
        Args:
            total (int): 総数
            description (str): 説明
            width (int): バーの幅
        """
        self.total = total
        self.description = description
        self.width = width
        self.current = 0
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """進捗を更新"""
        self.current += increment
        self._display()
    
    def _display(self):
        """プログレスバーを表示"""
        if self.total == 0:
            return
        
        progress = self.current / self.total
        filled = int(self.width * progress)
        bar = "█" * filled + "░" * (self.width - filled)
        
        # 経過時間と推定残り時間を計算
        elapsed = time.time() - self.start_time
        if progress > 0:
            eta = elapsed / progress * (1 - progress)
            eta_str = f"残り: {eta:.1f}s"
        else:
            eta_str = "残り: 計算中..."
        
        # パーセンテージを計算
        percentage = progress * 100
        
        # プログレスバーを表示
        print(f"\r{self.description}: |{bar}| {percentage:.1f}% ({self.current}/{self.total}) {eta_str}", end="", flush=True)
    
    def finish(self):
        """完了"""
        self.current = self.total
        self._display()
        print()  # 改行

class Cache:
    """キャッシュクラス"""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        """
        初期化
        
        Args:
            cache_dir (str): キャッシュディレクトリ
            ttl_hours (int): 有効期限（時間）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600
    
    def _get_cache_key(self, key: str) -> str:
        """キャッシュキーを生成"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """キャッシュファイルのパスを取得"""
        cache_key = self._get_cache_key(key)
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから値を取得
        
        Args:
            key (str): キャッシュキー
            
        Returns:
            Optional[Any]: キャッシュされた値（存在しない場合はNone）
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        # 有効期限をチェック
        if time.time() - cache_path.stat().st_mtime > self.ttl_seconds:
            cache_path.unlink()
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"キャッシュの読み込みに失敗: {e}")
            cache_path.unlink()
            return None
    
    def set(self, key: str, value: Any):
        """
        キャッシュに値を保存
        
        Args:
            key (str): キャッシュキー
            value (Any): 保存する値
        """
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.error(f"キャッシュの保存に失敗: {e}")
    
    def clear(self):
        """キャッシュをクリア"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"キャッシュファイルの削除に失敗: {e}")
    
    def cleanup_expired(self):
        """期限切れのキャッシュを削除"""
        current_time = time.time()
        for cache_file in self.cache_dir.glob("*.pkl"):
            if current_time - cache_file.stat().st_mtime > self.ttl_seconds:
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"期限切れキャッシュの削除に失敗: {e}")

class RetryHandler:
    """リトライ処理クラス"""
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        """
        初期化
        
        Args:
            max_retries (int): 最大リトライ回数
            delay (float): 初期待機時間（秒）
            backoff (float): バックオフ倍率
        """
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        関数をリトライ付きで実行
        
        Args:
            func (Callable): 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            Any: 関数の戻り値
            
        Raises:
            Exception: 最大リトライ回数に達した場合
        """
        last_exception = None
        current_delay = self.delay
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logger.warning(f"実行失敗 (試行 {attempt + 1}/{self.max_retries + 1}): {e}")
                    logger.info(f"{current_delay}秒後にリトライします...")
                    time.sleep(current_delay)
                    current_delay *= self.backoff
                else:
                    logger.error(f"最大リトライ回数に達しました: {e}")
        
        raise last_exception

class DataValidator:
    """データ検証クラス"""
    
    @staticmethod
    def validate_ticker_symbol(ticker: str) -> bool:
        """
        銘柄コードを検証
        
        Args:
            ticker (str): 銘柄コード
            
        Returns:
            bool: 有効な場合はTrue
        """
        if not ticker:
            return False
        
        # 4桁の数字かチェック
        if not ticker.isdigit() or len(ticker) != 4:
            return False
        
        return True
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """
        日付範囲を検証
        
        Args:
            start_date (str): 開始日
            end_date (str): 終了日
            
        Returns:
            bool: 有効な場合はTrue
        """
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start > end:
                return False
            
            # 10年以内かチェック
            if (end - start).days > 3650:
                return False
            
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_dataframe(df, required_columns: List[str] = None) -> bool:
        """
        DataFrameを検証
        
        Args:
            df: pandas DataFrame
            required_columns (List[str]): 必須カラム
            
        Returns:
            bool: 有効な場合はTrue
        """
        if df is None or df.empty:
            return False
        
        if required_columns:
            for col in required_columns:
                if col not in df.columns:
                    return False
        
        return True

class FileManager:
    """ファイル管理クラス"""
    
    def __init__(self, base_dir: str = "stock_data"):
        """
        初期化
        
        Args:
            base_dir (str): ベースディレクトリ
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def cleanup_old_files(self, days: int = 30):
        """
        古いファイルを削除
        
        Args:
            days (int): 削除する日数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file():
                if datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                    try:
                        file_path.unlink()
                        logger.info(f"古いファイルを削除: {file_path}")
                    except Exception as e:
                        logger.warning(f"ファイル削除に失敗: {e}")
    
    def get_file_size_mb(self, file_path: str) -> float:
        """
        ファイルサイズをMBで取得
        
        Args:
            file_path (str): ファイルパス
            
        Returns:
            float: ファイルサイズ（MB）
        """
        try:
            return Path(file_path).stat().st_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    def ensure_directory(self, directory: str):
        """
        ディレクトリを確実に作成
        
        Args:
            directory (str): ディレクトリパス
        """
        Path(directory).mkdir(parents=True, exist_ok=True)

def format_number(number: float, decimals: int = 2) -> str:
    """
    数値をフォーマット
    
    Args:
        number (float): 数値
        decimals (int): 小数点以下桁数
        
    Returns:
        str: フォーマットされた文字列
    """
    if number >= 1e12:
        return f"{number/1e12:.{decimals}f}兆"
    elif number >= 1e8:
        return f"{number/1e8:.{decimals}f}億"
    elif number >= 1e4:
        return f"{number/1e4:.{decimals}f}万"
    else:
        return f"{number:.{decimals}f}"

def format_currency(amount: float, currency: str = "円") -> str:
    """
    通貨をフォーマット
    
    Args:
        amount (float): 金額
        currency (str): 通貨単位
        
    Returns:
        str: フォーマットされた文字列
    """
    if amount >= 1e8:
        return f"{amount/1e8:.1f}億{currency}"
    elif amount >= 1e4:
        return f"{amount/1e4:.1f}万{currency}"
    else:
        return f"{amount:,.0f}{currency}"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全な除算
    
    Args:
        numerator (float): 分子
        denominator (float): 分母
        default (float): デフォルト値
        
    Returns:
        float: 除算結果
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except Exception:
        return default

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    変化率を計算
    
    Args:
        old_value (float): 古い値
        new_value (float): 新しい値
        
    Returns:
        float: 変化率（%）
    """
    if old_value == 0:
        return 0.0
    
    return ((new_value - old_value) / old_value) * 100 