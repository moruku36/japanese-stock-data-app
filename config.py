#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
システム設定管理
環境変数、デフォルト設定、ログ設定などを管理
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """システム設定クラス"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初期化
        
        Args:
            config_file (str): 設定ファイルのパス
        """
        self.config_file = config_file
        self.config = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定を読み込み"""
        default_config = {
            # データソース設定
            "data_sources": {
                "stooq": {
                    "enabled": True,
                    "timeout": 30,
                    "retry_count": 3
                },
                "yahoo": {
                    "enabled": True,
                    "timeout": 30,
                    "retry_count": 3
                }
            },
            
            # データ保存設定
            "data": {
                "directory": "stock_data",
                "max_file_size_mb": 100,
                "auto_cleanup_days": 30
            },
            
            # チャート設定
            "charts": {
                "default_figsize": (12, 8),
                "dpi": 200,
                "style": "seaborn-v0_8",
                "font_family": ["Arial Unicode MS", "DejaVu Sans"],
                "save_format": "png"
            },
            
            # ログ設定
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "stock_system.log",
                "max_size_mb": 10,
                "backup_count": 5
            },
            
            # 検索設定
            "search": {
                "max_results": 20,
                "similarity_threshold": 0.3,
                "cache_enabled": True,
                "cache_ttl_hours": 24
            },
            
            # 分析設定
            "analysis": {
                "default_period_days": 30,
                "max_period_days": 3650,
                "technical_indicators": {
                    "rsi_period": 14,
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9,
                    "ma_short": 5,
                    "ma_long": 20,
                    "bb_period": 20,
                    "bb_std": 2
                }
            },
            
            # UI設定
            "ui": {
                "show_progress": True,
                "confirm_actions": True,
                "auto_save": True,
                "theme": "default"
            }
        }
        
        # 設定ファイルが存在する場合は読み込み
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # デフォルト設定とマージ
                    self._merge_config(default_config, file_config)
            except Exception as e:
                print(f"⚠️ 設定ファイルの読み込みに失敗: {e}")
                print("デフォルト設定を使用します")
        
        # 環境変数でオーバーライド
        self._apply_environment_overrides(default_config)
        
        return default_config
    
    def _merge_config(self, default: Dict, override: Dict):
        """設定をマージ"""
        for key, value in override.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def _apply_environment_overrides(self, config: Dict):
        """環境変数で設定をオーバーライド"""
        env_mappings = {
            "STOCK_DATA_DIR": ("data", "directory"),
            "LOG_LEVEL": ("logging", "level"),
            "CHART_DPI": ("charts", "dpi"),
            "SEARCH_MAX_RESULTS": ("search", "max_results"),
            "DEFAULT_PERIOD": ("analysis", "default_period_days")
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # 設定パスに従って値を設定
                current = config
                for key in config_path[:-1]:
                    current = current[key]
                current[config_path[-1]] = env_value
    
    def _setup_logging(self):
        """ログ設定を初期化"""
        log_config = self.config["logging"]
        
        # ログレベルを設定
        log_level = getattr(logging, log_config["level"].upper(), logging.INFO)
        
        # ログフォーマットを設定
        formatter = logging.Formatter(log_config["format"])
        
        # ファイルハンドラーを設定
        if log_config["file"]:
            log_file = Path(log_config["file"])
            log_file.parent.mkdir(exist_ok=True)
            
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=log_config["max_size_mb"] * 1024 * 1024,
                backupCount=log_config["backup_count"]
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            
            # ルートロガーに追加
            logging.getLogger().addHandler(file_handler)
        
        # コンソールハンドラーを設定
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        
        # ルートロガーを設定
        logging.getLogger().setLevel(log_level)
        logging.getLogger().addHandler(console_handler)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key_path (str): 設定キーのパス（例: "data.directory"）
            default (Any): デフォルト値
            
        Returns:
            Any: 設定値
        """
        keys = key_path.split('.')
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set(self, key_path: str, value: Any):
        """
        設定値を設定
        
        Args:
            key_path (str): 設定キーのパス
            value (Any): 設定値
        """
        keys = key_path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def save(self):
        """設定をファイルに保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✅ 設定を保存しました: {self.config_file}")
        except Exception as e:
            print(f"❌ 設定の保存に失敗: {e}")
    
    def get_data_source_config(self, source: str) -> Dict[str, Any]:
        """データソース設定を取得"""
        return self.config["data_sources"].get(source, {})
    
    def is_data_source_enabled(self, source: str) -> bool:
        """データソースが有効かチェック"""
        return self.get_data_source_config(source).get("enabled", True)
    
    def get_retry_config(self, source: str) -> Dict[str, Any]:
        """リトライ設定を取得"""
        config = self.get_data_source_config(source)
        return {
            "retry_count": config.get("retry_count", 3),
            "timeout": config.get("timeout", 30)
        }

# グローバル設定インスタンス
config = Config() 