#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
カスタムアラート管理システム
価格閾値やテクニカル指標に基づくパーソナライズされたアラート機能
"""

import streamlit as st
import pandas as pd
import numpy as np
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

# メール関連のインポートをオプション化
try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    smtplib = None
    MIMEText = None
    MIMEMultipart = None

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """アラートタイプの定義"""
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    VOLUME_SPIKE = "volume_spike"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MACD_SIGNAL = "macd_signal"
    MOVING_AVERAGE_CROSS = "ma_cross"
    PERCENT_CHANGE = "percent_change"

class AlertStatus(Enum):
    """アラート状態の定義"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    EXPIRED = "expired"

@dataclass
class AlertCondition:
    """アラート条件のデータクラス"""
    alert_id: str
    user_id: str
    symbol: str
    company_name: str
    alert_type: AlertType
    condition_value: float
    comparison_operator: str  # >, <, >=, <=, ==
    message: str
    notification_methods: List[str]  # email, ui, sound
    status: AlertStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_checked: Optional[datetime]
    trigger_count: int = 0
    max_triggers: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        if self.last_checked:
            data['last_checked'] = self.last_checked.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertCondition':
        """辞書から復元"""
        data['alert_type'] = AlertType(data['alert_type'])
        data['status'] = AlertStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        if data.get('last_checked'):
            data['last_checked'] = datetime.fromisoformat(data['last_checked'])
        return cls(**data)

class AlertManager:
    """アラート管理クラス"""
    
    def __init__(self, storage_path: str = "data/alerts.json"):
        """初期化"""
        self.storage_path = storage_path
        self.alerts: Dict[str, AlertCondition] = {}
        self.notification_settings = {
            "email_enabled": False,
            "email_smtp_server": "smtp.gmail.com",
            "email_smtp_port": 587,
            "email_username": "",
            "email_password": "",
            "ui_notifications": True,
            "sound_notifications": True
        }
        
        # ストレージディレクトリの作成
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # アラートの読み込み
        self.load_alerts()
        
        logger.info("アラート管理システムを初期化しました")
    
    def create_alert(self, 
                    user_id: str,
                    symbol: str,
                    company_name: str,
                    alert_type: AlertType,
                    condition_value: float,
                    comparison_operator: str,
                    message: str = "",
                    notification_methods: List[str] = None,
                    expires_hours: Optional[int] = None,
                    max_triggers: int = 1) -> str:
        """新しいアラートを作成"""
        
        if notification_methods is None:
            notification_methods = ["ui"]
        
        # アラートIDの生成
        alert_id = f"{user_id}_{symbol}_{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 有効期限の設定
        expires_at = None
        if expires_hours:
            expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        # デフォルトメッセージの設定
        if not message:
            message = self._generate_default_message(symbol, company_name, alert_type, condition_value, comparison_operator)
        
        # アラート条件の作成
        alert = AlertCondition(
            alert_id=alert_id,
            user_id=user_id,
            symbol=symbol,
            company_name=company_name,
            alert_type=alert_type,
            condition_value=condition_value,
            comparison_operator=comparison_operator,
            message=message,
            notification_methods=notification_methods,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=expires_at,
            last_checked=None,
            max_triggers=max_triggers
        )
        
        # アラートを保存
        self.alerts[alert_id] = alert
        self.save_alerts()
        
        logger.info(f"新しいアラートを作成しました: {alert_id}")
        return alert_id
    
    def _generate_default_message(self, symbol: str, company_name: str, 
                                 alert_type: AlertType, condition_value: float, 
                                 comparison_operator: str) -> str:
        """デフォルトメッセージの生成"""
        
        messages = {
            AlertType.PRICE_ABOVE: f"{company_name}({symbol})の株価が{condition_value:,.0f}円を上回りました",
            AlertType.PRICE_BELOW: f"{company_name}({symbol})の株価が{condition_value:,.0f}円を下回りました",
            AlertType.VOLUME_SPIKE: f"{company_name}({symbol})の出来高が通常の{condition_value}倍に急増しました",
            AlertType.RSI_OVERBOUGHT: f"{company_name}({symbol})のRSIが{condition_value}を超えました（買われすぎ）",
            AlertType.RSI_OVERSOLD: f"{company_name}({symbol})のRSIが{condition_value}を下回りました（売られすぎ）",
            AlertType.MACD_SIGNAL: f"{company_name}({symbol})でMACDシグナルが発生しました",
            AlertType.MOVING_AVERAGE_CROSS: f"{company_name}({symbol})で移動平均線のクロスが発生しました",
            AlertType.PERCENT_CHANGE: f"{company_name}({symbol})の変動率が{condition_value}%に達しました"
        }
        
        return messages.get(alert_type, f"{company_name}({symbol})でアラート条件が満たされました")
    
    def check_alerts(self, market_data: Dict[str, pd.DataFrame]) -> List[AlertCondition]:
        """アラート条件をチェック"""
        triggered_alerts = []
        current_time = datetime.now()
        
        for alert_id, alert in list(self.alerts.items()):
            # 非アクティブなアラートをスキップ
            if alert.status != AlertStatus.ACTIVE:
                continue
            
            # 期限切れチェック
            if alert.expires_at and current_time > alert.expires_at:
                alert.status = AlertStatus.EXPIRED
                continue
            
            # 最大トリガー数チェック
            if alert.trigger_count >= alert.max_triggers:
                alert.status = AlertStatus.TRIGGERED
                continue
            
            # 市場データの取得
            if alert.symbol not in market_data:
                continue
            
            data = market_data[alert.symbol]
            if data.empty:
                continue
            
            # アラート条件のチェック
            if self._check_alert_condition(alert, data):
                alert.trigger_count += 1
                alert.last_checked = current_time
                
                if alert.trigger_count >= alert.max_triggers:
                    alert.status = AlertStatus.TRIGGERED
                
                triggered_alerts.append(alert)
                
                # 通知の送信
                self._send_notification(alert)
            
            alert.last_checked = current_time
        
        # 変更を保存
        if triggered_alerts:
            self.save_alerts()
        
        return triggered_alerts
    
    def _check_alert_condition(self, alert: AlertCondition, data: pd.DataFrame) -> bool:
        """個別のアラート条件をチェック"""
        try:
            latest_data = data.iloc[-1]
            
            if alert.alert_type == AlertType.PRICE_ABOVE:
                return latest_data['Close'] > alert.condition_value
            
            elif alert.alert_type == AlertType.PRICE_BELOW:
                return latest_data['Close'] < alert.condition_value
            
            elif alert.alert_type == AlertType.VOLUME_SPIKE:
                avg_volume = data['Volume'].tail(20).mean()
                return latest_data['Volume'] > avg_volume * alert.condition_value
            
            elif alert.alert_type == AlertType.RSI_OVERBOUGHT:
                rsi = self._calculate_rsi(data['Close'])
                return rsi > alert.condition_value
            
            elif alert.alert_type == AlertType.RSI_OVERSOLD:
                rsi = self._calculate_rsi(data['Close'])
                return rsi < alert.condition_value
            
            elif alert.alert_type == AlertType.PERCENT_CHANGE:
                if len(data) >= 2:
                    prev_close = data.iloc[-2]['Close']
                    current_close = latest_data['Close']
                    pct_change = ((current_close - prev_close) / prev_close) * 100
                    
                    if alert.comparison_operator == ">":
                        return abs(pct_change) > alert.condition_value
                    elif alert.comparison_operator == ">=":
                        return abs(pct_change) >= alert.condition_value
                    
            return False
            
        except Exception as e:
            logger.error(f"アラート条件チェックエラー {alert.alert_id}: {e}")
            return False
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSIを計算"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]
        except:
            return 50.0  # デフォルト値
    
    def _send_notification(self, alert: AlertCondition):
        """通知を送信"""
        try:
            # UI通知
            if "ui" in alert.notification_methods and self.notification_settings["ui_notifications"]:
                self._send_ui_notification(alert)
            
            # メール通知
            if "email" in alert.notification_methods and self.notification_settings["email_enabled"]:
                self._send_email_notification(alert)
            
            # サウンド通知
            if "sound" in alert.notification_methods and self.notification_settings["sound_notifications"]:
                self._send_sound_notification(alert)
                
        except Exception as e:
            logger.error(f"通知送信エラー {alert.alert_id}: {e}")
    
    def _send_ui_notification(self, alert: AlertCondition):
        """UI通知を送信"""
        # Streamlitのセッション状態に通知を追加
        if 'notifications' not in st.session_state:
            st.session_state.notifications = []
        
        notification = {
            'id': alert.alert_id,
            'type': 'alert',
            'title': f'アラート: {alert.company_name}',
            'message': alert.message,
            'timestamp': datetime.now().isoformat(),
            'symbol': alert.symbol
        }
        
        st.session_state.notifications.append(notification)
        
        # 最新10件のみ保持
        if len(st.session_state.notifications) > 10:
            st.session_state.notifications = st.session_state.notifications[-10:]
    
    def _send_email_notification(self, alert: AlertCondition):
        """メール通知を送信"""
        if not self.notification_settings.get("email_username"):
            return
        
        try:
            if not EMAIL_AVAILABLE:
                logger.warning("メール機能が利用できません。インポートエラーです。")
                return
                
            msg = MIMEMultipart()
            msg['From'] = self.notification_settings["email_username"]
            msg['To'] = self.notification_settings["email_username"]  # 自分宛て
            msg['Subject'] = f"株価アラート: {alert.company_name}({alert.symbol})"
            
            body = f"""
アラートが発生しました。

銘柄: {alert.company_name} ({alert.symbol})
アラートタイプ: {alert.alert_type.value}
条件値: {alert.condition_value}
メッセージ: {alert.message}
発生時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

日本株式データ分析システム
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SMTP送信
            server = smtplib.SMTP(self.notification_settings["email_smtp_server"], 
                                self.notification_settings["email_smtp_port"])
            server.starttls()
            server.login(self.notification_settings["email_username"], 
                        self.notification_settings["email_password"])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"メール通知を送信しました: {alert.alert_id}")
            
        except Exception as e:
            logger.error(f"メール送信エラー: {e}")
    
    def _send_sound_notification(self, alert: AlertCondition):
        """サウンド通知（ブラウザのbeep音）"""
        # JavaScriptを使用してブラウザでbeep音を再生
        st.markdown("""
        <script>
        // ブラウザでbeep音を再生
        const context = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = context.createOscillator();
        const gainNode = context.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(context.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.setValueAtTime(0.3, context.currentTime);
        
        oscillator.start();
        oscillator.stop(context.currentTime + 0.2);
        </script>
        """, unsafe_allow_html=True)
    
    def get_active_alerts(self, user_id: str = None) -> List[AlertCondition]:
        """アクティブなアラート一覧を取得"""
        alerts = list(self.alerts.values())
        
        if user_id:
            alerts = [alert for alert in alerts if alert.user_id == user_id]
        
        return alerts
    
    def get_alert_by_id(self, alert_id: str) -> Optional[AlertCondition]:
        """IDでアラートを取得"""
        return self.alerts.get(alert_id)
    
    def update_alert_status(self, alert_id: str, status: AlertStatus) -> bool:
        """アラートの状態を更新"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = status
            self.save_alerts()
            logger.info(f"アラート状態を更新しました: {alert_id} -> {status.value}")
            return True
        return False
    
    def delete_alert(self, alert_id: str) -> bool:
        """アラートを削除"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self.save_alerts()
            logger.info(f"アラートを削除しました: {alert_id}")
            return True
        return False
    
    def save_alerts(self):
        """アラートをファイルに保存"""
        try:
            data = {
                'alerts': {alert_id: alert.to_dict() for alert_id, alert in self.alerts.items()},
                'notification_settings': self.notification_settings
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"アラート保存エラー: {e}")
    
    def load_alerts(self):
        """ファイルからアラートを読み込み"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # アラートの復元
                if 'alerts' in data:
                    for alert_id, alert_data in data['alerts'].items():
                        self.alerts[alert_id] = AlertCondition.from_dict(alert_data)
                
                # 通知設定の復元
                if 'notification_settings' in data:
                    self.notification_settings.update(data['notification_settings'])
                
                logger.info(f"{len(self.alerts)}件のアラートを読み込みました")
                
        except Exception as e:
            logger.error(f"アラート読み込みエラー: {e}")
    
    def get_alert_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """アラート統計情報を取得"""
        alerts = list(self.alerts.values())
        
        if user_id:
            alerts = [alert for alert in alerts if alert.user_id == user_id]
        
        total_alerts = len(alerts)
        active_alerts = len([a for a in alerts if a.status == AlertStatus.ACTIVE])
        triggered_alerts = len([a for a in alerts if a.status == AlertStatus.TRIGGERED])
        expired_alerts = len([a for a in alerts if a.status == AlertStatus.EXPIRED])
        
        # アラートタイプ別統計
        type_stats = {}
        for alert in alerts:
            alert_type = alert.alert_type.value
            if alert_type not in type_stats:
                type_stats[alert_type] = 0
            type_stats[alert_type] += 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'triggered_alerts': triggered_alerts,
            'expired_alerts': expired_alerts,
            'alert_types': type_stats
        }

# Streamlit UI関数
def show_alert_management_ui():
    """アラート管理UIを表示"""
    st.markdown("## 🔔 カスタムアラート管理")
    
    # アラートマネージャーの初期化
    if 'alert_manager' not in st.session_state:
        st.session_state.alert_manager = AlertManager()
    
    alert_manager = st.session_state.alert_manager
    
    # タブの作成
    tab1, tab2, tab3, tab4 = st.tabs(["新規作成", "アラート一覧", "通知設定", "統計"])
    
    with tab1:
        show_create_alert_ui(alert_manager)
    
    with tab2:
        show_alert_list_ui(alert_manager)
    
    with tab3:
        show_notification_settings_ui(alert_manager)
    
    with tab4:
        show_alert_statistics_ui(alert_manager)

def show_create_alert_ui(alert_manager: AlertManager):
    """新規アラート作成UI"""
    st.markdown("### 📝 新しいアラートを作成")
    
    with st.form("create_alert_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("銘柄コード", placeholder="7203", help="4桁の銘柄コードを入力")
            company_name = st.text_input("会社名", placeholder="トヨタ自動車", help="会社名を入力")
            
            alert_type = st.selectbox(
                "アラートタイプ",
                options=[
                    AlertType.PRICE_ABOVE,
                    AlertType.PRICE_BELOW,
                    AlertType.VOLUME_SPIKE,
                    AlertType.RSI_OVERBOUGHT,
                    AlertType.RSI_OVERSOLD,
                    AlertType.PERCENT_CHANGE
                ],
                format_func=lambda x: {
                    AlertType.PRICE_ABOVE: "📈 価格上昇",
                    AlertType.PRICE_BELOW: "📉 価格下落", 
                    AlertType.VOLUME_SPIKE: "📊 出来高急増",
                    AlertType.RSI_OVERBOUGHT: "⬆️ RSI買われすぎ",
                    AlertType.RSI_OVERSOLD: "⬇️ RSI売られすぎ",
                    AlertType.PERCENT_CHANGE: "📊 変動率"
                }[x]
            )
        
        with col2:
            condition_value = st.number_input(
                "条件値",
                min_value=0.0,
                value=1000.0 if alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_BELOW] else 70.0,
                help="アラート発生の閾値"
            )
            
            comparison_operator = st.selectbox(
                "比較演算子",
                options=[">", ">=", "<", "<="],
                index=0 if alert_type == AlertType.PRICE_ABOVE else 2
            )
            
            expires_hours = st.number_input(
                "有効期限（時間）",
                min_value=1,
                max_value=8760,  # 1年
                value=24,
                help="アラートの有効期限（時間単位）"
            )
            
            max_triggers = st.number_input(
                "最大トリガー数",
                min_value=1,
                max_value=100,
                value=1,
                help="何回まで通知するか"
            )
        
        # 通知方法
        st.markdown("#### 通知方法")
        notification_methods = []
        
        col3, col4, col5 = st.columns(3)
        with col3:
            if st.checkbox("UI通知", value=True):
                notification_methods.append("ui")
        with col4:
            if st.checkbox("メール通知"):
                notification_methods.append("email")
        with col5:
            if st.checkbox("サウンド通知"):
                notification_methods.append("sound")
        
        # カスタムメッセージ
        custom_message = st.text_area(
            "カスタムメッセージ（オプション）",
            placeholder="独自のメッセージを入力（空白の場合は自動生成）",
            height=80
        )
        
        # 作成ボタン
        if st.form_submit_button("🔔 アラートを作成", type="primary"):
            if symbol and company_name and notification_methods:
                try:
                    user_id = "default_user"  # 実際の認証システムと連携する場合は適切なIDを取得
                    
                    alert_id = alert_manager.create_alert(
                        user_id=user_id,
                        symbol=symbol.upper(),
                        company_name=company_name,
                        alert_type=alert_type,
                        condition_value=condition_value,
                        comparison_operator=comparison_operator,
                        message=custom_message,
                        notification_methods=notification_methods,
                        expires_hours=expires_hours,
                        max_triggers=max_triggers
                    )
                    
                    st.success(f"✅ アラートを作成しました！ ID: {alert_id}")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ アラート作成エラー: {e}")
            else:
                st.warning("⚠️ すべての必須項目を入力してください")

def show_alert_list_ui(alert_manager: AlertManager):
    """アラート一覧UI"""
    st.markdown("### 📋 アラート一覧")
    
    user_id = "default_user"
    alerts = alert_manager.get_active_alerts(user_id)
    
    if not alerts:
        st.info("📭 アクティブなアラートはありません")
        return
    
    # フィルター
    status_filter = st.selectbox(
        "状態でフィルター",
        options=["すべて"] + [status.value for status in AlertStatus]
    )
    
    # アラート表示
    for alert in alerts:
        if status_filter != "すべて" and alert.status.value != status_filter:
            continue
        
        with st.expander(f"{alert.company_name} ({alert.symbol}) - {alert.alert_type.value}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**メッセージ**: {alert.message}")
                st.markdown(f"**条件**: {alert.comparison_operator} {alert.condition_value}")
                st.markdown(f"**通知方法**: {', '.join(alert.notification_methods)}")
                st.markdown(f"**作成日時**: {alert.created_at.strftime('%Y-%m-%d %H:%M')}")
                if alert.expires_at:
                    st.markdown(f"**期限**: {alert.expires_at.strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                status_colors = {
                    AlertStatus.ACTIVE: "🟢",
                    AlertStatus.TRIGGERED: "🔴", 
                    AlertStatus.PAUSED: "🟡",
                    AlertStatus.EXPIRED: "⚫"
                }
                st.markdown(f"**状態**: {status_colors[alert.status]} {alert.status.value}")
                st.markdown(f"**トリガー数**: {alert.trigger_count}/{alert.max_triggers}")
            
            with col3:
                # 操作ボタン
                if alert.status == AlertStatus.ACTIVE:
                    if st.button("一時停止", key=f"pause_{alert.alert_id}"):
                        alert_manager.update_alert_status(alert.alert_id, AlertStatus.PAUSED)
                        st.rerun()
                
                elif alert.status == AlertStatus.PAUSED:
                    if st.button("再開", key=f"resume_{alert.alert_id}"):
                        alert_manager.update_alert_status(alert.alert_id, AlertStatus.ACTIVE)
                        st.rerun()
                
                if st.button("削除", key=f"delete_{alert.alert_id}", type="secondary"):
                    alert_manager.delete_alert(alert.alert_id)
                    st.success("アラートを削除しました")
                    st.rerun()

def show_notification_settings_ui(alert_manager: AlertManager):
    """通知設定UI"""
    st.markdown("### ⚙️ 通知設定")
    
    settings = alert_manager.notification_settings.copy()
    
    with st.form("notification_settings"):
        # UI通知設定
        st.markdown("#### 🖥️ UI通知")
        settings["ui_notifications"] = st.checkbox(
            "UI通知を有効化", 
            value=settings["ui_notifications"]
        )
        settings["sound_notifications"] = st.checkbox(
            "サウンド通知を有効化",
            value=settings["sound_notifications"]
        )
        
        # メール通知設定
        st.markdown("#### 📧 メール通知")
        settings["email_enabled"] = st.checkbox(
            "メール通知を有効化",
            value=settings["email_enabled"]
        )
        
        if settings["email_enabled"]:
            col1, col2 = st.columns(2)
            with col1:
                settings["email_smtp_server"] = st.text_input(
                    "SMTPサーバー",
                    value=settings["email_smtp_server"]
                )
                settings["email_username"] = st.text_input(
                    "メールアドレス",
                    value=settings["email_username"]
                )
            
            with col2:
                settings["email_smtp_port"] = st.number_input(
                    "ポート番号",
                    value=settings["email_smtp_port"]
                )
                settings["email_password"] = st.text_input(
                    "パスワード",
                    type="password",
                    value=settings["email_password"]
                )
        
        if st.form_submit_button("💾 設定を保存", type="primary"):
            alert_manager.notification_settings.update(settings)
            alert_manager.save_alerts()
            st.success("✅ 通知設定を保存しました")

def show_alert_statistics_ui(alert_manager: AlertManager):
    """アラート統計UI"""
    st.markdown("### 📊 アラート統計")
    
    user_id = "default_user"
    stats = alert_manager.get_alert_statistics(user_id)
    
    # 概要メトリクス
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総アラート数", stats['total_alerts'])
    with col2:
        st.metric("アクティブ", stats['active_alerts'])
    with col3:
        st.metric("発動済み", stats['triggered_alerts'])
    with col4:
        st.metric("期限切れ", stats['expired_alerts'])
    
    # アラートタイプ別統計
    if stats['alert_types']:
        st.markdown("#### アラートタイプ別統計")
        
        type_names = {
            'price_above': '価格上昇',
            'price_below': '価格下落',
            'volume_spike': '出来高急増',
            'rsi_overbought': 'RSI買われすぎ',
            'rsi_oversold': 'RSI売られすぎ',
            'percent_change': '変動率'
        }
        
        chart_data = pd.DataFrame([
            {'タイプ': type_names.get(k, k), '件数': v}
            for k, v in stats['alert_types'].items()
        ])
        
        st.bar_chart(chart_data.set_index('タイプ'), use_container_width=True)

# 通知表示用関数
def show_notifications():
    """通知を表示"""
    if 'notifications' in st.session_state and st.session_state.notifications:
        st.markdown("### 🔔 最新の通知")
        
        for notification in reversed(st.session_state.notifications[-5:]):  # 最新5件
            timestamp = datetime.fromisoformat(notification['timestamp'])
            
            with st.container():
                st.markdown(f"""
                <div style="
                    padding: 10px;
                    border-left: 4px solid #ff6b6b;
                    background-color: #fff5f5;
                    margin: 5px 0;
                    border-radius: 5px;
                ">
                    <strong>{notification['title']}</strong><br>
                    {notification['message']}<br>
                    <small>{timestamp.strftime('%H:%M:%S')}</small>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    # テスト実行
    st.title("🔔 カスタムアラート機能テスト")
    show_alert_management_ui()
    show_notifications()

def run_background_alert_checks(fetcher=None, interval_seconds: int = 60):
    """簡易バックグラウンドチェック（Streamlit上でページ描画時に随時呼び出し）"""
    try:
        from core.stock_data_fetcher import JapaneseStockDataFetcher
        from datetime import datetime, timedelta

        if 'alert_manager' not in st.session_state:
            st.session_state.alert_manager = AlertManager()
        alert_manager: AlertManager = st.session_state.alert_manager

        fetcher = fetcher or JapaneseStockDataFetcher()

        symbols = sorted({a.symbol for a in alert_manager.get_active_alerts() if a.status == AlertStatus.ACTIVE})
        if not symbols:
            return

        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        data = fetcher.fetch_multiple_stocks(symbols, start_date, end_date, source="stooq")
        alert_manager.check_alerts(data)
    except Exception:
        pass