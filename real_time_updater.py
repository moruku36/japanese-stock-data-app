#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
リアルタイムデータ更新システム
WebSocketとプッシュ通知によるリアルタイム更新
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable
import threading
import time
from dataclasses import dataclass
from queue import Queue

# ログ設定
logger = logging.getLogger(__name__)

try:
    import redis
except ImportError:
    logger.warning("redisがインストールされていません。Redis機能を無効化します。")
    redis = None

try:
    import websockets
except ImportError:
    logger.warning("websocketsがインストールされていません。WebSocket機能を無効化します。")
    websockets = None

@dataclass
class RealTimeUpdate:
    """リアルタイム更新データ"""
    ticker: str
    data_type: str
    timestamp: datetime
    data: Dict[str, Any]
    priority: int = 1  # 1: 低, 2: 中, 3: 高

class RealTimeDataManager:
    """リアルタイムデータ管理クラス"""
    
    def __init__(self):
        self.subscribers = {}  # ticker -> [callbacks]
        self.update_queue = Queue()
        self.running = False
        self.redis_client = None
        self.update_interval = 30  # 30秒ごとに更新
        
        # Redisクライアントの初期化（利用可能な場合のみ）
        if redis is not None:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                logger.info("Redisクライアントを初期化しました")
            except Exception as e:
                logger.warning(f"Redisクライアントの初期化に失敗しました: {e}")
                self.redis_client = None
        
        logger.info("リアルタイムデータ管理クラスを初期化しました")
    
    def start(self):
        """リアルタイム更新を開始"""
        if not self.running:
            self.running = True
            self.update_thread = threading.Thread(target=self._update_loop)
            self.update_thread.daemon = True
            self.update_thread.start()
            logger.info("リアルタイム更新を開始しました")
    
    def stop(self):
        """リアルタイム更新を停止"""
        self.running = False
        logger.info("リアルタイム更新を停止しました")
    
    def subscribe(self, ticker: str, callback: Callable):
        """銘柄の更新を購読"""
        if ticker not in self.subscribers:
            self.subscribers[ticker] = []
        self.subscribers[ticker].append(callback)
        logger.info(f"銘柄 {ticker} の購読を開始しました")
    
    def unsubscribe(self, ticker: str, callback: Callable):
        """銘柄の購読を解除"""
        if ticker in self.subscribers and callback in self.subscribers[ticker]:
            self.subscribers[ticker].remove(callback)
            logger.info(f"銘柄 {ticker} の購読を解除しました")
    
    def _update_loop(self):
        """更新ループ"""
        while self.running:
            try:
                # 主要銘柄のリアルタイムデータを取得
                major_tickers = ["9984", "9433", "7203", "6758", "6861"]
                
                for ticker in major_tickers:
                    if ticker in self.subscribers:
                        # リアルタイムデータを取得
                        update_data = self._get_real_time_data(ticker)
                        if update_data:
                            # 購読者に通知
                            for callback in self.subscribers[ticker]:
                                try:
                                    callback(update_data)
                                except Exception as e:
                                    logger.error(f"コールバック実行エラー: {e}")
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"リアルタイム更新エラー: {e}")
                time.sleep(5)  # エラー時は5秒待機
    
    def _get_real_time_data(self, ticker: str) -> RealTimeUpdate:
        """リアルタイムデータを取得"""
        try:
            # 実際のAPIからリアルタイムデータを取得
            # ここではサンプルデータを生成
            current_time = datetime.now()
            
            # ランダムな価格変動をシミュレート
            import random
            base_price = 1000 + random.randint(-100, 100)
            price_change = random.randint(-50, 50)
            
            data = {
                'ticker': ticker,
                'current_price': base_price + price_change,
                'price_change': price_change,
                'price_change_percent': (price_change / base_price) * 100,
                'volume': random.randint(1000000, 10000000),
                'timestamp': current_time.isoformat(),
                'market_status': 'open' if 9 <= current_time.hour < 15 else 'closed'
            }
            
            return RealTimeUpdate(
                ticker=ticker,
                data_type='price_update',
                timestamp=current_time,
                data=data,
                priority=2
            )
            
        except Exception as e:
            logger.error(f"リアルタイムデータ取得エラー: {e}")
            return None

class WebSocketServer:
    """WebSocketサーバー"""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.data_manager = RealTimeDataManager()
        logger.info(f"WebSocketサーバーを初期化しました: {host}:{port}")
    
    async def start(self):
        """WebSocketサーバーを開始"""
        if websockets is None:
            logger.warning("websocketsが利用できません。WebSocketサーバーを開始できません。")
            return
        
        async with websockets.serve(self._handle_client, self.host, self.port):
            logger.info(f"WebSocketサーバーを開始しました: ws://{self.host}:{self.port}")
            await asyncio.Future()  # 無限ループ
    
    async def _handle_client(self, websocket, path):
        """クライアント接続を処理"""
        if websockets is None:
            logger.warning("websocketsが利用できません。クライアント接続を処理できません。")
            return
        
        self.clients.add(websocket)
        logger.info(f"クライアントが接続しました: {len(self.clients)} 接続")
        
        try:
            async for message in websocket:
                await self._process_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"クライアントが切断しました: {len(self.clients)} 接続")
    
    async def _process_message(self, websocket, message):
        """メッセージを処理"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                ticker = data.get('ticker')
                if ticker:
                    # 銘柄の購読を開始
                    self.data_manager.subscribe(ticker, 
                        lambda update: asyncio.create_task(self._send_update(websocket, update)))
                    await websocket.send(json.dumps({
                        'type': 'subscribed',
                        'ticker': ticker,
                        'status': 'success'
                    }))
            
            elif message_type == 'unsubscribe':
                ticker = data.get('ticker')
                if ticker:
                    # 銘柄の購読を解除
                    await websocket.send(json.dumps({
                        'type': 'unsubscribed',
                        'ticker': ticker,
                        'status': 'success'
                    }))
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"メッセージ処理エラー: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def _send_update(self, websocket, update: RealTimeUpdate):
        """更新データを送信"""
        try:
            message = {
                'type': 'update',
                'ticker': update.ticker,
                'data_type': update.data_type,
                'timestamp': update.timestamp.isoformat(),
                'data': update.data,
                'priority': update.priority
            }
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"更新データ送信エラー: {e}")

class PushNotificationService:
    """プッシュ通知サービス"""
    
    def __init__(self):
        self.notification_queue = Queue()
        self.running = False
        logger.info("プッシュ通知サービスを初期化しました")
    
    def start(self):
        """プッシュ通知サービスを開始"""
        if not self.running:
            self.running = True
            self.notification_thread = threading.Thread(target=self._notification_loop)
            self.notification_thread.daemon = True
            self.notification_thread.start()
            logger.info("プッシュ通知サービスを開始しました")
    
    def stop(self):
        """プッシュ通知サービスを停止"""
        self.running = False
        logger.info("プッシュ通知サービスを停止しました")
    
    def send_notification(self, title: str, message: str, data: Dict[str, Any] = None):
        """通知を送信"""
        notification = {
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': datetime.now().isoformat()
        }
        self.notification_queue.put(notification)
    
    def _notification_loop(self):
        """通知ループ"""
        while self.running:
            try:
                if not self.notification_queue.empty():
                    notification = self.notification_queue.get()
                    self._process_notification(notification)
                time.sleep(1)
            except Exception as e:
                logger.error(f"通知処理エラー: {e}")
    
    def _process_notification(self, notification: Dict[str, Any]):
        """通知を処理"""
        try:
            # 実際のプッシュ通知サービス（Firebase、OneSignal等）に送信
            # ここではログ出力のみ
            logger.info(f"プッシュ通知: {notification['title']} - {notification['message']}")
            
            # WebSocketクライアントにも通知
            # 実際の実装ではWebSocketサーバーと連携
            
        except Exception as e:
            logger.error(f"通知処理エラー: {e}")

# グローバルインスタンス
real_time_manager = RealTimeDataManager()
websocket_server = WebSocketServer()
push_service = PushNotificationService()

def start_real_time_services():
    """リアルタイムサービスを開始"""
    real_time_manager.start()
    push_service.start()
    
    # WebSocketサーバーを非同期で開始
    def run_websocket_server():
        asyncio.run(websocket_server.start())
    
    websocket_thread = threading.Thread(target=run_websocket_server)
    websocket_thread.daemon = True
    websocket_thread.start()
    
    logger.info("すべてのリアルタイムサービスを開始しました")

def stop_real_time_services():
    """リアルタイムサービスを停止"""
    real_time_manager.stop()
    push_service.stop()
    logger.info("すべてのリアルタイムサービスを停止しました")

if __name__ == "__main__":
    # テスト実行
    start_real_time_services()
    
    try:
        # テスト通知を送信
        time.sleep(5)
        push_service.send_notification(
            "株価アラート",
            "9984（ソフトバンクG）が5%上昇しました",
            {'ticker': '9984', 'change': 5.0}
        )
        
        # 10秒間実行
        time.sleep(10)
    finally:
        stop_real_time_services() 