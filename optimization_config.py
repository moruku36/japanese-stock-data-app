#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
システム最適化設定
パフォーマンス、メモリ、キャッシュなどの最適化設定を管理
"""

import os
from typing import Dict, Any

class OptimizationConfig:
    """最適化設定クラス"""
    
    # パフォーマンス設定
    PERFORMANCE = {
        "max_workers": 5,  # 並行処理の最大ワーカー数
        "batch_size": 10,  # バッチ処理サイズ
        "timeout": 30,     # タイムアウト（秒）
        "retry_count": 3,  # リトライ回数
    }
    
    # メモリ設定
    MEMORY = {
        "max_cache_size": 1000,  # キャッシュ最大サイズ
        "cache_ttl_hours": 24,   # キャッシュTTL（時間）
        "auto_cleanup": True,    # 自動クリーンアップ
        "memory_limit_mb": 1024, # メモリ制限（MB）
    }
    
    # キャッシュ設定
    CACHE = {
        "enabled": True,
        "max_size": 500,
        "ttl_hours": 6,
        "persistent": False,
    }
    
    # データ処理設定
    DATA_PROCESSING = {
        "chunk_size": 1000,      # チャンクサイズ
        "optimize_dataframes": True,  # データフレーム最適化
        "compress_data": True,   # データ圧縮
    }
    
    # WebUI設定
    WEBUI = {
        "enable_caching": True,
        "cache_ttl_seconds": 3600,  # 1時間
        "max_concurrent_requests": 10,
        "enable_progress_bars": True,
    }
    
    @classmethod
    def get_performance_config(cls) -> Dict[str, Any]:
        """パフォーマンス設定を取得"""
        return cls.PERFORMANCE.copy()
    
    @classmethod
    def get_memory_config(cls) -> Dict[str, Any]:
        """メモリ設定を取得"""
        return cls.MEMORY.copy()
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """キャッシュ設定を取得"""
        return cls.CACHE.copy()
    
    @classmethod
    def get_data_processing_config(cls) -> Dict[str, Any]:
        """データ処理設定を取得"""
        return cls.DATA_PROCESSING.copy()
    
    @classmethod
    def get_webui_config(cls) -> Dict[str, Any]:
        """WebUI設定を取得"""
        return cls.WEBUI.copy()
    
    @classmethod
    def update_config(cls, section: str, key: str, value: Any):
        """設定を更新"""
        if hasattr(cls, section.upper()):
            config_dict = getattr(cls, section.upper())
            config_dict[key] = value
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Dict[str, Any]]:
        """全設定を取得"""
        return {
            "performance": cls.get_performance_config(),
            "memory": cls.get_memory_config(),
            "cache": cls.get_cache_config(),
            "data_processing": cls.get_data_processing_config(),
            "webui": cls.get_webui_config(),
        }

# 環境変数から設定を読み込み
def load_optimization_config():
    """環境変数から最適化設定を読み込み"""
    # パフォーマンス設定
    if os.getenv("MAX_WORKERS"):
        OptimizationConfig.update_config("performance", "max_workers", 
                                       int(os.getenv("MAX_WORKERS")))
    
    if os.getenv("BATCH_SIZE"):
        OptimizationConfig.update_config("performance", "batch_size", 
                                       int(os.getenv("BATCH_SIZE")))
    
    # メモリ設定
    if os.getenv("MAX_CACHE_SIZE"):
        OptimizationConfig.update_config("memory", "max_cache_size", 
                                       int(os.getenv("MAX_CACHE_SIZE")))
    
    if os.getenv("MEMORY_LIMIT_MB"):
        OptimizationConfig.update_config("memory", "memory_limit_mb", 
                                       int(os.getenv("MEMORY_LIMIT_MB")))
    
    # キャッシュ設定
    if os.getenv("CACHE_ENABLED"):
        OptimizationConfig.update_config("cache", "enabled", 
                                       os.getenv("CACHE_ENABLED").lower() == "true")
    
    if os.getenv("CACHE_TTL_HOURS"):
        OptimizationConfig.update_config("cache", "ttl_hours", 
                                       int(os.getenv("CACHE_TTL_HOURS")))

# 設定を読み込み
load_optimization_config() 