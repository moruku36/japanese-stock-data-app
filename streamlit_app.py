"""
日本株データ分析アプリ - セキュア版
セキュリティ機能を統合した軽量版
"""
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import secrets
import re
from typing import Optional

# 高度なテクニカル分析用ライブラリ（軽量化）
ADVANCED_FEATURES_AVAILABLE = False
try:
    import pandas_ta as ta
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    pass

# 統計分析ライブラリ（オプション）
SCIPY_AVAILABLE = False
SKLEARN_AVAILABLE = False
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    pass

try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

class SecurityManager:
    """軽量セキュリティ管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.session_timeout = 3600  # 1時間
        self.max_requests_per_minute = 60
        self.request_history = []
        
        # デフォルトユーザー
        self.users = {
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "role": "admin",
                "permissions": ["read", "write", "admin"]
            },
            "user": {
                "password_hash": self._hash_password("user123"),
                "role": "user", 
                "permissions": ["read", "write"]
            }
        }
    
    def _hash_password(self, password: str) -> str:
        """パスワードをハッシュ化"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """パスワードを検証"""
        try:
            salt, pwd_hash = hashed.split('$')
            verify_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return pwd_hash == verify_hash.hex()
        except:
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """ユーザー認証"""
        if username in self.users:
            user = self.users[username]
            if self.verify_password(password, user["password_hash"]):
                return {
                    "username": username,
                    "role": user["role"],
                    "permissions": user["permissions"]
                }
        return None
    
    def validate_input(self, text: str) -> str:
        """入力検証とサニタイゼーション"""
        if not text:
            return ""
        
        # 危険な文字を除去
        dangerous_chars = ['<', '>', '"', "'", '&', '`', '(', ')', '{', '}', '[', ']']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # 長さ制限
        return text[:100]
    
    def validate_search_query(self, query: str) -> str:
        """検索クエリの検証"""
        if not query:
            return ""
        
        # 日本語、英数字、スペース、ハイフンのみ許可
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -・ー')
        # ひらがな、カタカナ、漢字の範囲を追加
        allowed_chars.update(chr(i) for i in range(0x3040, 0x309F))  # ひらがな
        allowed_chars.update(chr(i) for i in range(0x30A0, 0x30FF))  # カタカナ
        allowed_chars.update(chr(i) for i in range(0x4E00, 0x9FAF))  # 漢字
        
        filtered_query = ''.join(c for c in query if c in allowed_chars)
        return filtered_query[:50]  # 長さ制限
    
    def validate_stock_code(self, code: str) -> bool:
        """株式コードの検証"""
        if not code:
            return False
        
        # 日本株コードの基本パターン（4桁.T）
        pattern = r'^\d{4}\.T$'
        return bool(re.match(pattern, code))
    
    def check_rate_limit(self) -> bool:
        """レート制限チェック"""
        current_time = datetime.now()
        
        # 1分前より古い記録を削除
        cutoff_time = current_time - timedelta(minutes=1)
        self.request_history = [t for t in self.request_history if t > cutoff_time]
        
        # 制限チェック
        if len(self.request_history) >= self.max_requests_per_minute:
            return False
        
        # 記録追加
        self.request_history.append(current_time)
        return True

class StockDatabase:
    """日本株データベース"""
    
    def __init__(self):
        # 主要な日本株のデータベース
        self.stocks = {
            # 自動車
            "7203.T": {"name": "トヨタ自動車", "sector": "自動車", "keywords": ["トヨタ", "TOYOTA", "自動車"]},
            "7201.T": {"name": "日産自動車", "sector": "自動車", "keywords": ["日産", "NISSAN", "自動車"]},
            "7267.T": {"name": "ホンダ", "sector": "自動車", "keywords": ["ホンダ", "HONDA", "本田", "自動車"]},
            "7269.T": {"name": "スズキ", "sector": "自動車", "keywords": ["スズキ", "SUZUKI", "自動車"]},
            "7211.T": {"name": "三菱自動車", "sector": "自動車", "keywords": ["三菱自動車", "MITSUBISHI", "自動車"]},
            
            # 電機・IT
            "6758.T": {"name": "ソニーグループ", "sector": "電機", "keywords": ["ソニー", "SONY", "電機", "エンターテイメント"]},
            "6861.T": {"name": "キーエンス", "sector": "電機", "keywords": ["キーエンス", "KEYENCE", "センサー", "計測"]},
            "6954.T": {"name": "ファナック", "sector": "電機", "keywords": ["ファナック", "FANUC", "ロボット", "工作機械"]},
            "6752.T": {"name": "パナソニック", "sector": "電機", "keywords": ["パナソニック", "Panasonic", "電機"]},
            "6971.T": {"name": "京セラ", "sector": "電機", "keywords": ["京セラ", "KYOCERA", "セラミック", "電子部品"]},
            
            # 通信・IT
            "9984.T": {"name": "ソフトバンクグループ", "sector": "通信", "keywords": ["ソフトバンク", "SoftBank", "通信", "投資"]},
            "9432.T": {"name": "日本電信電話", "sector": "通信", "keywords": ["NTT", "日本電信電話", "通信", "ドコモ"]},
            "9433.T": {"name": "KDDI", "sector": "通信", "keywords": ["KDDI", "au", "通信", "携帯"]},
            "4689.T": {"name": "ヤフー", "sector": "IT", "keywords": ["ヤフー", "Yahoo", "インターネット", "IT"]},
            
            # 小売
            "9983.T": {"name": "ファーストリテイリング", "sector": "小売", "keywords": ["ファーストリテイリング", "ユニクロ", "UNIQLO", "衣料"]},
            "3382.T": {"name": "セブン&アイ・ホールディングス", "sector": "小売", "keywords": ["セブンイレブン", "セブン&アイ", "コンビニ", "小売"]},
            "8267.T": {"name": "イオン", "sector": "小売", "keywords": ["イオン", "AEON", "スーパー", "小売"]},
            
            # 金融
            "8306.T": {"name": "三菱UFJフィナンシャル・グループ", "sector": "金融", "keywords": ["三菱UFJ", "MUFG", "銀行", "金融"]},
            "8316.T": {"name": "三井住友フィナンシャルグループ", "sector": "金融", "keywords": ["三井住友", "SMFG", "銀行", "金融"]},
            "8411.T": {"name": "みずほフィナンシャルグループ", "sector": "金融", "keywords": ["みずほ", "銀行", "金融"]},
            
            # 化学・素材
            "4063.T": {"name": "信越化学工業", "sector": "化学", "keywords": ["信越化学", "化学", "シリコン", "素材"]},
            "4452.T": {"name": "花王", "sector": "化学", "keywords": ["花王", "Kao", "日用品", "化粧品"]},
            "4188.T": {"name": "三菱ケミカルグループ", "sector": "化学", "keywords": ["三菱ケミカル", "化学", "素材"]},
            
            # ゲーム・エンターテイメント
            "7974.T": {"name": "任天堂", "sector": "ゲーム", "keywords": ["任天堂", "Nintendo", "ゲーム", "エンターテイメント"]},
            "9697.T": {"name": "カプコン", "sector": "ゲーム", "keywords": ["カプコン", "CAPCOM", "ゲーム"]},
            "7832.T": {"name": "バンダイナムコ", "sector": "ゲーム", "keywords": ["バンダイナムコ", "ゲーム", "玩具"]},
            
            # 医薬品
            "4523.T": {"name": "エーザイ", "sector": "医薬品", "keywords": ["エーザイ", "Eisai", "医薬品", "製薬"]},
            "4568.T": {"name": "第一三共", "sector": "医薬品", "keywords": ["第一三共", "医薬品", "製薬"]},
            "4502.T": {"name": "武田薬品工業", "sector": "医薬品", "keywords": ["武田薬品", "Takeda", "医薬品", "製薬"]},
        }
    
    def search_stocks(self, query: str, limit: int = 20) -> list:
        """銘柄を検索"""
        if not query:
            return []
        
        query_lower = query.lower()
        results = []
        
        for code, data in self.stocks.items():
            # 会社名での完全一致
            if query in data["name"]:
                results.append({
                    "code": code,
                    "name": data["name"],
                    "sector": data["sector"],
                    "match_type": "exact_name"
                })
                continue
            
            # キーワードでの部分一致
            for keyword in data["keywords"]:
                if query_lower in keyword.lower():
                    results.append({
                        "code": code,
                        "name": data["name"],
                        "sector": data["sector"],
                        "match_type": "keyword"
                    })
                    break
        
        # 完全一致を優先してソート
        results.sort(key=lambda x: (x["match_type"] != "exact_name", x["name"]))
        return results[:limit]
    
    def get_all_stocks(self) -> list:
        """全銘柄を取得"""
        return [
            {
                "code": code,
                "name": data["name"],
                "sector": data["sector"]
            }
            for code, data in self.stocks.items()
        ]

def init_session_state():
    """セッション状態を初期化"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'security_manager' not in st.session_state:
        st.session_state.security_manager = SecurityManager()
    if 'stock_database' not in st.session_state:
        st.session_state.stock_database = StockDatabase()
    if 'selected_stock_code' not in st.session_state:
        st.session_state.selected_stock_code = None
    if 'selected_stock_name' not in st.session_state:
        st.session_state.selected_stock_name = None

def show_login():
    """ログイン画面を表示"""
    st.title("🔐 ログイン")
    
    with st.form("login_form"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        submit = st.form_submit_button("ログイン")
        
        if submit:
            if username and password:
                # 入力検証
                username = st.session_state.security_manager.validate_input(username)
                
                # 認証
                user_info = st.session_state.security_manager.authenticate(username, password)
                
                if user_info:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.success("ログインしました")
                    st.rerun()
                else:
                    st.error("ユーザー名またはパスワードが正しくありません")
            else:
                st.error("ユーザー名とパスワードを入力してください")
    
    # ゲストアクセス
    if st.button("ゲストとしてアクセス"):
        st.session_state.authenticated = True
        st.session_state.user_info = {
            "username": "guest",
            "role": "guest",
            "permissions": ["read"]
        }
        st.rerun()
    
        # テスト用アカウント情報
        with st.expander("テスト用アカウント"):
            st.info("""
            **管理者**: admin / admin123
            **ユーザー**: user / user123
            **ゲスト**: ゲストボタンをクリック
            """)

def show_all_stocks_list():
    """対応銘柄一覧を表示"""
    st.subheader("📋 対応銘柄一覧")
    
    stock_db = st.session_state.stock_database
    all_stocks = stock_db.get_all_stocks()
    
    # セクター別に分類
    sectors = {}
    for stock in all_stocks:
        sector = stock['sector']
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(stock)
    
    # セクター別にタブで表示
    sector_tabs = list(sectors.keys())
    tabs = st.tabs(sector_tabs)
    
    for i, sector in enumerate(sector_tabs):
        with tabs[i]:
            sector_stocks = sectors[sector]
            
            # データフレームで表示
            df_data = []
            for stock in sector_stocks:
                df_data.append({
                    "銘柄コード": stock['code'],
                    "銘柄名": stock['name'],
                    "セクター": stock['sector']
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.info(f"**{sector}セクター**: {len(sector_stocks)}銘柄")
    
    st.markdown("---")
    st.info("💡 銘柄名の一部を入力して検索することができます。例: 「トヨタ」「ソニー」「銀行」など")

def calculate_technical_indicators(hist):
    """基本的なテクニカル指標を計算"""
    # 移動平均
    hist['MA5'] = hist['Close'].rolling(window=5).mean()
    hist['MA25'] = hist['Close'].rolling(window=25).mean()
    hist['MA75'] = hist['Close'].rolling(window=75).mean()
    
    # RSI
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    hist['RSI'] = 100 - (100 / (1 + rs))
    
    # ボリンジャーバンド
    bb_period = 20
    bb_std = 2
    hist['BB_Middle'] = hist['Close'].rolling(window=bb_period).mean()
    bb_std_dev = hist['Close'].rolling(window=bb_period).std()
    hist['BB_Upper'] = hist['BB_Middle'] + (bb_std_dev * bb_std)
    hist['BB_Lower'] = hist['BB_Middle'] - (bb_std_dev * bb_std)
    
    return hist

def calculate_advanced_indicators(hist, indicators_config):
    """高度なテクニカル指標を計算"""
    if not ADVANCED_FEATURES_AVAILABLE:
        return hist
    
    try:
        # pandas_taを使用して高度な指標を計算
        df = hist.copy()
        
        # EMA (指数移動平均)
        if indicators_config.get('ema_enabled', False):
            ema_periods = indicators_config.get('ema_periods', [12, 26, 50])
            for period in ema_periods:
                if len(df) > period:
                    df[f'EMA_{period}'] = ta.ema(df['Close'], length=period)
        
        # MACD
        if indicators_config.get('macd_enabled', False):
            macd_fast = indicators_config.get('macd_fast', 12)
            macd_slow = indicators_config.get('macd_slow', 26)
            macd_signal = indicators_config.get('macd_signal', 9)
            
            macd_data = ta.macd(df['Close'], fast=macd_fast, slow=macd_slow, signal=macd_signal)
            if macd_data is not None and len(macd_data.columns) >= 3:
                df['MACD'] = macd_data.iloc[:, 0]
                df['MACD_histogram'] = macd_data.iloc[:, 1]
                df['MACD_signal'] = macd_data.iloc[:, 2]
        
        # Stochastic Oscillator
        if indicators_config.get('stoch_enabled', False):
            stoch_k = indicators_config.get('stoch_k', 14)
            stoch_d = indicators_config.get('stoch_d', 3)
            
            stoch_data = ta.stoch(df['High'], df['Low'], df['Close'], k=stoch_k, d=stoch_d)
            if stoch_data is not None and len(stoch_data.columns) >= 2:
                df['Stoch_K'] = stoch_data.iloc[:, 0]
                df['Stoch_D'] = stoch_data.iloc[:, 1]
        
        # Williams %R
        if indicators_config.get('willr_enabled', False):
            willr_period = indicators_config.get('willr_period', 14)
            df['WillR'] = ta.willr(df['High'], df['Low'], df['Close'], length=willr_period)
        
        # ATR (Average True Range)
        if indicators_config.get('atr_enabled', False):
            atr_period = indicators_config.get('atr_period', 14)
            df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=atr_period)
        
        # CCI (Commodity Channel Index)
        if indicators_config.get('cci_enabled', False):
            cci_period = indicators_config.get('cci_period', 20)
            df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'], length=cci_period)
        
        # OBV (On-Balance Volume)
        if indicators_config.get('obv_enabled', False):
            df['OBV'] = ta.obv(df['Close'], df['Volume'])
        
        # VWAP (Volume Weighted Average Price)
        if indicators_config.get('vwap_enabled', False):
            df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
        
        # ADX (Average Directional Index)
        if indicators_config.get('adx_enabled', False):
            adx_period = indicators_config.get('adx_period', 14)
            adx_data = ta.adx(df['High'], df['Low'], df['Close'], length=adx_period)
            if adx_data is not None and len(adx_data.columns) >= 3:
                df['ADX'] = adx_data.iloc[:, 0]
                df['DMP'] = adx_data.iloc[:, 1]  # +DI
                df['DMN'] = adx_data.iloc[:, 2]  # -DI
        
        return df
        
    except Exception as e:
        st.warning(f"高度な指標の計算中にエラーが発生しました: {str(e)}")
        return hist

def detect_anomalies(hist, method='isolation_forest'):
    """異常値検出"""
    if not ADVANCED_FEATURES_AVAILABLE or not SKLEARN_AVAILABLE:
        return hist, []
    
    try:
        # 価格データの準備
        price_data = hist[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        price_data = price_data.dropna()
        
        if len(price_data) < 10:
            return hist, []
        
        # データの正規化
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(price_data)
        
        anomalies = []
        
        if method == 'isolation_forest':
            # Isolation Forest による異常値検出
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(scaled_data)
            
            anomaly_indices = np.where(anomaly_labels == -1)[0]
            for idx in anomaly_indices:
                if idx < len(hist):
                    anomalies.append({
                        'date': hist.index[idx],
                        'price': hist['Close'].iloc[idx],
                        'type': 'isolation_forest',
                        'score': iso_forest.score_samples(scaled_data[idx:idx+1])[0]
                    })
        
        elif method == 'zscore':
            # Z-score による異常値検出
            for col in ['Close', 'Volume']:
                if col in hist.columns:
                    z_scores = np.abs(stats.zscore(hist[col].dropna()))
                    anomaly_indices = np.where(z_scores > 3)[0]
                    
                    for idx in anomaly_indices:
                        if idx < len(hist):
                            anomalies.append({
                                'date': hist.index[idx],
                                'price': hist['Close'].iloc[idx],
                                'type': f'zscore_{col.lower()}',
                                'score': z_scores[idx]
                            })
        
        return hist, anomalies
        
    except Exception as e:
        st.warning(f"異常値検出中にエラーが発生しました: {str(e)}")
        return hist, []

def analyze_trend(hist, method='linear_regression'):
    """トレンド分析"""
    if not ADVANCED_FEATURES_AVAILABLE or not SCIPY_AVAILABLE:
        return {}
    
    try:
        # データの準備
        prices = hist['Close'].dropna()
        if len(prices) < 10:
            return {}
        
        x = np.arange(len(prices))
        y = prices.values
        
        trend_analysis = {}
        
        if method == 'linear_regression':
            # 線形回帰によるトレンド分析
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            trend_analysis = {
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value**2,
                'p_value': p_value,
                'trend_direction': 'up' if slope > 0 else 'down',
                'trend_strength': abs(r_value),
                'trend_line': intercept + slope * x
            }
        
        elif method == 'polynomial':
            # 多項式回帰によるトレンド分析
            degree = 2
            coeffs = np.polyfit(x, y, degree)
            trend_line = np.polyval(coeffs, x)
            
            # R²の計算
            ss_res = np.sum((y - trend_line) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            trend_analysis = {
                'coefficients': coeffs,
                'r_squared': r_squared,
                'trend_line': trend_line,
                'degree': degree
            }
        
        return trend_analysis
        
    except Exception as e:
        st.warning(f"トレンド分析中にエラーが発生しました: {str(e)}")
        return {}

def calculate_support_resistance(hist, method='pivot_points'):
    """サポート・レジスタンスレベルの計算"""
    try:
        levels = []
        
        if method == 'pivot_points':
            # ピボットポイント法
            high = hist['High'].max()
            low = hist['Low'].min()
            close = hist['Close'].iloc[-1]
            
            pivot = (high + low + close) / 3
            
            # サポート・レジスタンスレベル
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)
            
            levels = [
                {'level': s3, 'type': 'support', 'strength': 3},
                {'level': s2, 'type': 'support', 'strength': 2},
                {'level': s1, 'type': 'support', 'strength': 1},
                {'level': pivot, 'type': 'pivot', 'strength': 0},
                {'level': r1, 'type': 'resistance', 'strength': 1},
                {'level': r2, 'type': 'resistance', 'strength': 2},
                {'level': r3, 'type': 'resistance', 'strength': 3}
            ]
        
        elif method == 'local_extrema':
            # ローカル極値法
            prices = hist['Close'].values
            window = 10
            
            for i in range(window, len(prices) - window):
                # ローカル最大値（レジスタンス）
                if all(prices[i] >= prices[i-j] and prices[i] >= prices[i+j] for j in range(1, window+1)):
                    levels.append({
                        'level': prices[i],
                        'type': 'resistance',
                        'strength': 1,
                        'date': hist.index[i]
                    })
                
                # ローカル最小値（サポート）
                elif all(prices[i] <= prices[i-j] and prices[i] <= prices[i+j] for j in range(1, window+1)):
                    levels.append({
                        'level': prices[i],
                        'type': 'support',
                        'strength': 1,
                        'date': hist.index[i]
                    })
        
        return levels
        
    except Exception as e:
        st.warning(f"サポート・レジスタンス計算中にエラーが発生しました: {str(e)}")
        return []

def show_fundamental_analysis(stock, info, hist, user_info, security_manager):
    """ファンダメンタル分析を表示"""
    st.subheader("💹 ファンダメンタル分析")
    
    if "write" not in user_info["permissions"]:
        st.warning("ファンダメンタル分析の表示には書き込み権限が必要です")
        return
    
    if not info:
        st.warning("企業情報を取得できませんでした")
        return
    
    try:
        # 財務指標の計算と表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📈 株価指標**")
            
            # 基本指標
            metrics_data = []
            
            # PER (株価収益率)
            if 'trailingPE' in info and info['trailingPE']:
                per = info['trailingPE']
                if per > 0:
                    metrics_data.append(("PER (株価収益率)", f"{per:.2f}倍"))
            
            # PBR (株価純資産倍率)
            if 'priceToBook' in info and info['priceToBook']:
                pbr = info['priceToBook']
                if pbr > 0:
                    metrics_data.append(("PBR (株価純資産倍率)", f"{pbr:.2f}倍"))
            
            # 配当利回り
            if 'dividendYield' in info and info['dividendYield']:
                div_yield = info['dividendYield'] * 100
                metrics_data.append(("配当利回り", f"{div_yield:.2f}%"))
            
            # 時価総額
            if 'marketCap' in info and info['marketCap']:
                market_cap = info['marketCap'] / 1e12
                metrics_data.append(("時価総額", f"{market_cap:.1f}兆円"))
            
            if metrics_data:
                metrics_df = pd.DataFrame(metrics_data, columns=["指標", "値"])
                st.dataframe(metrics_df, hide_index=True)
            else:
                st.info("株価指標データがありません")
        
        with col2:
            st.write("**💰 収益性指標**")
            
            profit_data = []
            
            # ROE (自己資本利益率)
            if 'returnOnEquity' in info and info['returnOnEquity']:
                roe = info['returnOnEquity'] * 100
                profit_data.append(("ROE (自己資本利益率)", f"{roe:.2f}%"))
            
            # ROA (総資産利益率)  
            if 'returnOnAssets' in info and info['returnOnAssets']:
                roa = info['returnOnAssets'] * 100
                profit_data.append(("ROA (総資産利益率)", f"{roa:.2f}%"))
            
            # 営業利益率
            if 'operatingMargins' in info and info['operatingMargins']:
                op_margin = info['operatingMargins'] * 100
                profit_data.append(("営業利益率", f"{op_margin:.2f}%"))
            
            # 純利益率
            if 'profitMargins' in info and info['profitMargins']:
                profit_margin = info['profitMargins'] * 100
                profit_data.append(("純利益率", f"{profit_margin:.2f}%"))
            
            if profit_data:
                profit_df = pd.DataFrame(profit_data, columns=["指標", "値"])
                st.dataframe(profit_df, hide_index=True)
            else:
                st.info("収益性指標データがありません")
        
        # 成長性分析
        st.write("**📊 成長性分析**")
        growth_col1, growth_col2 = st.columns(2)
        
        with growth_col1:
            growth_data = []
            
            # 売上成長率
            if 'revenueGrowth' in info and info['revenueGrowth']:
                revenue_growth = info['revenueGrowth'] * 100
                growth_data.append(("売上成長率", f"{revenue_growth:.2f}%"))
            
            # 利益成長率
            if 'earningsGrowth' in info and info['earningsGrowth']:
                earnings_growth = info['earningsGrowth'] * 100
                growth_data.append(("利益成長率", f"{earnings_growth:.2f}%"))
            
            if growth_data:
                growth_df = pd.DataFrame(growth_data, columns=["指標", "値"])
                st.dataframe(growth_df, hide_index=True)
            else:
                st.info("成長性データがありません")
        
        with growth_col2:
            # 財務健全性
            financial_data = []
            
            # 自己資本比率
            if 'debtToEquity' in info and info['debtToEquity']:
                debt_to_equity = info['debtToEquity']
                equity_ratio = 100 / (1 + debt_to_equity / 100)
                financial_data.append(("自己資本比率", f"{equity_ratio:.1f}%"))
            
            # 流動比率
            if 'currentRatio' in info and info['currentRatio']:
                current_ratio = info['currentRatio']
                financial_data.append(("流動比率", f"{current_ratio:.2f}倍"))
            
            if financial_data:
                financial_df = pd.DataFrame(financial_data, columns=["指標", "値"])
                st.dataframe(financial_df, hide_index=True)
            else:
                st.info("財務健全性データがありません")
        
        # 評価チャート
        st.write("**📈 バリュエーション分析**")
        
        # PERとPBRの可視化
        valuation_metrics = []
        labels = []
        
        if 'trailingPE' in info and info['trailingPE'] and info['trailingPE'] > 0:
            # PERの業界平均との比較（仮想的な業界平均）
            per_value = min(info['trailingPE'], 50)  # 異常値を制限
            valuation_metrics.append(per_value)
            labels.append(f"PER: {per_value:.1f}")
        
        if 'priceToBook' in info and info['priceToBook'] and info['priceToBook'] > 0:
            # PBRの表示
            pbr_value = min(info['priceToBook'], 10)  # 異常値を制限
            valuation_metrics.append(pbr_value)
            labels.append(f"PBR: {pbr_value:.1f}")
        
        if valuation_metrics:
            fig_valuation = go.Figure()
            
            fig_valuation.add_trace(go.Bar(
                x=labels,
                y=valuation_metrics,
                marker_color=['#FF6B6B', '#4ECDC4']
            ))
            
            fig_valuation.update_layout(
                title="主要バリュエーション指標",
                yaxis_title="倍率",
                height=300
            )
            
            st.plotly_chart(fig_valuation, use_container_width=True)
        
        # 投資判断の参考情報
        st.write("**🎯 投資判断の参考**")
        st.info("""
        **PER（株価収益率）**
        - 15倍未満: 割安
        - 15-25倍: 適正
        - 25倍超: 割高
        
        **PBR（株価純資産倍率）**
        - 1倍未満: 割安
        - 1-2倍: 適正
        - 2倍超: 割高
        
        **ROE（自己資本利益率）**
        - 10%以上: 優秀
        - 5-10%: 普通
        - 5%未満: 改善余地あり
        """)
        
    except Exception as e:
        st.error("ファンダメンタル分析の処理中にエラーが発生しました")
        if "admin" in user_info["permissions"]:
            with st.expander("詳細エラー（管理者のみ）"):
                st.code(str(e))

def show_technical_analysis(hist, selected_stock, user_info):
    """高度なテクニカル分析を表示"""
    st.subheader("📈 高度なテクニカル分析")
    
    if "write" not in user_info["permissions"]:
        st.warning("テクニカル分析の表示には書き込み権限が必要です")
        return
    
    # 分析設定のサイドバー
    with st.sidebar:
        st.markdown("---")
        st.subheader("⚙️ テクニカル分析設定")
        
        # 基本設定
        analysis_type = st.selectbox(
            "分析タイプ",
            ["カスタム指標", "基本指標", "高度分析", "異常値検出", "トレンド分析"],
            key="tech_analysis_type"
        )
    
    if analysis_type == "基本指標":
        show_basic_technical_analysis(hist, selected_stock)
    
    elif analysis_type == "カスタム指標" and ADVANCED_FEATURES_AVAILABLE:
        show_custom_indicators(hist, selected_stock)
    
    elif analysis_type == "高度分析" and ADVANCED_FEATURES_AVAILABLE:
        show_advanced_analysis(hist, selected_stock)
    
    elif analysis_type == "異常値検出" and ADVANCED_FEATURES_AVAILABLE and SKLEARN_AVAILABLE:
        show_anomaly_detection(hist, selected_stock)
    
    elif analysis_type == "トレンド分析" and ADVANCED_FEATURES_AVAILABLE and SCIPY_AVAILABLE:
        show_trend_analysis(hist, selected_stock)
    
    else:
        if not ADVANCED_FEATURES_AVAILABLE:
            st.info("💡 高度な分析機能を利用するには、pandas-taライブラリが必要です")
        elif analysis_type == "異常値検出" and not SKLEARN_AVAILABLE:
            st.info("💡 異常値検出にはscikit-learnライブラリが必要です")
        elif analysis_type == "トレンド分析" and not SCIPY_AVAILABLE:
            st.info("💡 トレンド分析にはscipyライブラリが必要です")
        show_basic_technical_analysis(hist, selected_stock)

def show_basic_technical_analysis(hist, selected_stock):
    """基本的なテクニカル分析を表示"""
    try:
        # テクニカル指標を計算
        hist_with_indicators = calculate_technical_indicators(hist.copy())
        
        # 移動平均チャート
        st.write("**📊 移動平均線**")
        
        fig_ma = go.Figure()
        
        # ローソク足
        fig_ma.add_trace(go.Candlestick(
            x=hist_with_indicators.index,
            open=hist_with_indicators['Open'],
            high=hist_with_indicators['High'],
            low=hist_with_indicators['Low'],
            close=hist_with_indicators['Close'],
            name="価格",
            opacity=0.6
        ))
        
        # 移動平均線
        fig_ma.add_trace(go.Scatter(
            x=hist_with_indicators.index,
            y=hist_with_indicators['MA5'],
            mode='lines',
            name='5日移動平均',
            line=dict(color='red', width=1)
        ))
        
        fig_ma.add_trace(go.Scatter(
            x=hist_with_indicators.index,
            y=hist_with_indicators['MA25'],
            mode='lines',
            name='25日移動平均',
            line=dict(color='blue', width=1)
        ))
        
        fig_ma.add_trace(go.Scatter(
            x=hist_with_indicators.index,
            y=hist_with_indicators['MA75'],
            mode='lines',
            name='75日移動平均',
            line=dict(color='green', width=1)
        ))
        
        fig_ma.update_layout(
            title=f"{selected_stock} - 移動平均線",
            yaxis_title="価格 (¥)",
            height=400
        )
        
        st.plotly_chart(fig_ma, use_container_width=True)
        
        # ボリンジャーバンドとRSI
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📊 ボリンジャーバンド**")
            
            fig_bb = go.Figure()
            
            fig_bb.add_trace(go.Candlestick(
                x=hist_with_indicators.index,
                open=hist_with_indicators['Open'],
                high=hist_with_indicators['High'],
                low=hist_with_indicators['Low'],
                close=hist_with_indicators['Close'],
                name="価格",
                opacity=0.6
            ))
            
            fig_bb.add_trace(go.Scatter(
                x=hist_with_indicators.index,
                y=hist_with_indicators['BB_Upper'],
                mode='lines',
                name='上限バンド',
                line=dict(color='red', dash='dash')
            ))
            
            fig_bb.add_trace(go.Scatter(
                x=hist_with_indicators.index,
                y=hist_with_indicators['BB_Middle'],
                mode='lines',
                name='中央線(20日MA)',
                line=dict(color='blue')
            ))
            
            fig_bb.add_trace(go.Scatter(
                x=hist_with_indicators.index,
                y=hist_with_indicators['BB_Lower'],
                mode='lines',
                name='下限バンド',
                line=dict(color='red', dash='dash')
            ))
            
            fig_bb.update_layout(
                title="ボリンジャーバンド",
                yaxis_title="価格 (¥)",
                height=300
            )
            
            st.plotly_chart(fig_bb, use_container_width=True)
        
        with col2:
            st.write("**📊 RSI（相対力指数）**")
            
            fig_rsi = go.Figure()
            
            fig_rsi.add_trace(go.Scatter(
                x=hist_with_indicators.index,
                y=hist_with_indicators['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple')
            ))
            
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="買われすぎ(70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="blue", annotation_text="売られすぎ(30)")
            
            fig_rsi.update_layout(
                title="RSI",
                yaxis_title="RSI",
                yaxis=dict(range=[0, 100]),
                height=300
            )
            
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        # シグナル分析
        show_basic_signals(hist_with_indicators)
        
    except Exception as e:
        st.error("基本テクニカル分析の処理中にエラーが発生しました")
        st.code(str(e))

def show_custom_indicators(hist, selected_stock):
    """カスタマイズ可能な指標を表示"""
    st.write("**⚙️ カスタムテクニカル指標**")
    
    # サイドバーで指標設定
    with st.sidebar:
        st.write("**指標設定**")
        
        # EMA設定
        ema_enabled = st.checkbox("EMA (指数移動平均)", value=True)
        ema_periods = []
        if ema_enabled:
            ema_12 = st.checkbox("EMA 12", value=True)
            ema_26 = st.checkbox("EMA 26", value=True)
            ema_50 = st.checkbox("EMA 50", value=False)
            if ema_12: ema_periods.append(12)
            if ema_26: ema_periods.append(26)
            if ema_50: ema_periods.append(50)
        
        # MACD設定
        macd_enabled = st.checkbox("MACD", value=True)
        if macd_enabled:
            macd_fast = st.slider("MACD Fast", 5, 20, 12)
            macd_slow = st.slider("MACD Slow", 20, 35, 26)
            macd_signal = st.slider("MACD Signal", 5, 15, 9)
        
        # その他の指標
        stoch_enabled = st.checkbox("Stochastic Oscillator", value=False)
        willr_enabled = st.checkbox("Williams %R", value=False)
        atr_enabled = st.checkbox("ATR", value=False)
        cci_enabled = st.checkbox("CCI", value=False)
        obv_enabled = st.checkbox("OBV", value=False)
        vwap_enabled = st.checkbox("VWAP", value=False)
        adx_enabled = st.checkbox("ADX", value=False)
    
    # 指標設定
    indicators_config = {
        'ema_enabled': ema_enabled,
        'ema_periods': ema_periods,
        'macd_enabled': macd_enabled,
        'stoch_enabled': stoch_enabled,
        'willr_enabled': willr_enabled,
        'atr_enabled': atr_enabled,
        'cci_enabled': cci_enabled,
        'obv_enabled': obv_enabled,
        'vwap_enabled': vwap_enabled,
        'adx_enabled': adx_enabled,
    }
    
    if macd_enabled:
        indicators_config.update({
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal
        })
    
    # 高度な指標を計算
    hist_advanced = calculate_advanced_indicators(hist.copy(), indicators_config)
    
    # チャート表示
    if ema_enabled and ema_periods:
        show_ema_chart(hist_advanced, selected_stock, ema_periods)
    
    if macd_enabled:
        show_macd_chart(hist_advanced, selected_stock)
    
    # その他の指標を2列で表示
    col1, col2 = st.columns(2)
    
    with col1:
        if stoch_enabled and 'Stoch_K' in hist_advanced.columns:
            show_stochastic_chart(hist_advanced)
        
        if atr_enabled and 'ATR' in hist_advanced.columns:
            show_atr_chart(hist_advanced)
        
        if obv_enabled and 'OBV' in hist_advanced.columns:
            show_obv_chart(hist_advanced)
    
    with col2:
        if willr_enabled and 'WillR' in hist_advanced.columns:
            show_willr_chart(hist_advanced)
        
        if cci_enabled and 'CCI' in hist_advanced.columns:
            show_cci_chart(hist_advanced)
        
        if adx_enabled and 'ADX' in hist_advanced.columns:
            show_adx_chart(hist_advanced)

def show_ema_chart(hist, selected_stock, periods):
    """EMAチャートを表示"""
    st.write("**📊 EMA (指数移動平均)**")
    
    fig = go.Figure()
    
    # 価格
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['Close'],
        mode='lines',
        name='終値',
        line=dict(color='black', width=2)
    ))
    
    # EMA
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    for i, period in enumerate(periods):
        if f'EMA_{period}' in hist.columns:
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist[f'EMA_{period}'],
                mode='lines',
                name=f'EMA {period}',
                line=dict(color=colors[i % len(colors)], width=1)
            ))
    
    fig.update_layout(
        title=f"{selected_stock} - EMA",
        yaxis_title="価格 (¥)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_macd_chart(hist, selected_stock):
    """MACDチャートを表示"""
    if 'MACD' not in hist.columns:
        return
    
    st.write("**📊 MACD**")
    
    fig = go.Figure()
    
    # MACD線
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['MACD'],
        mode='lines',
        name='MACD',
        line=dict(color='blue')
    ))
    
    # シグナル線
    if 'MACD_signal' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['MACD_signal'],
            mode='lines',
            name='Signal',
            line=dict(color='red')
        ))
    
    # ヒストグラム
    if 'MACD_histogram' in hist.columns:
        fig.add_trace(go.Bar(
            x=hist.index,
            y=hist['MACD_histogram'],
            name='Histogram',
            marker_color='gray',
            opacity=0.6
        ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    
    fig.update_layout(
        title=f"{selected_stock} - MACD",
        yaxis_title="MACD",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_stochastic_chart(hist):
    """ストキャスティクスチャートを表示"""
    st.write("**📊 Stochastic Oscillator**")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['Stoch_K'],
        mode='lines',
        name='%K',
        line=dict(color='blue')
    ))
    
    if 'Stoch_D' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Stoch_D'],
            mode='lines',
            name='%D',
            line=dict(color='red')
        ))
    
    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="買われすぎ(80)")
    fig.add_hline(y=20, line_dash="dash", line_color="blue", annotation_text="売られすぎ(20)")
    
    fig.update_layout(
        title="Stochastic Oscillator",
        yaxis_title="Stochastic",
        yaxis=dict(range=[0, 100]),
        height=250
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_willr_chart(hist):
    """Williams %Rチャートを表示"""
    st.write("**📊 Williams %R**")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['WillR'],
        mode='lines',
        name='Williams %R',
        line=dict(color='purple')
    ))
    
    fig.add_hline(y=-20, line_dash="dash", line_color="red", annotation_text="買われすぎ(-20)")
    fig.add_hline(y=-80, line_dash="dash", line_color="blue", annotation_text="売られすぎ(-80)")
    
    fig.update_layout(
        title="Williams %R",
        yaxis_title="Williams %R",
        yaxis=dict(range=[-100, 0]),
        height=250
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_atr_chart(hist):
    """ATRチャートを表示"""
    st.write("**📊 ATR (Average True Range)**")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['ATR'],
        mode='lines',
        name='ATR',
        line=dict(color='orange'),
        fill='tonexty'
    ))
    
    fig.update_layout(
        title="ATR - ボラティリティ指標",
        yaxis_title="ATR",
        height=250
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_cci_chart(hist):
    """CCIチャートを表示"""
    st.write("**📊 CCI (Commodity Channel Index)**")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['CCI'],
        mode='lines',
        name='CCI',
        line=dict(color='green')
    ))
    
    fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="買われすぎ(100)")
    fig.add_hline(y=-100, line_dash="dash", line_color="blue", annotation_text="売られすぎ(-100)")
    fig.add_hline(y=0, line_dash="solid", line_color="black")
    
    fig.update_layout(
        title="CCI",
        yaxis_title="CCI",
        height=250
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_obv_chart(hist):
    """OBVチャートを表示"""
    st.write("**📊 OBV (On-Balance Volume)**")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['OBV'],
        mode='lines',
        name='OBV',
        line=dict(color='brown')
    ))
    
    fig.update_layout(
        title="OBV - 出来高指標",
        yaxis_title="OBV",
        height=250
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_adx_chart(hist):
    """ADXチャートを表示"""
    st.write("**📊 ADX (Average Directional Index)**")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hist.index,
        y=hist['ADX'],
        mode='lines',
        name='ADX',
        line=dict(color='black', width=2)
    ))
    
    if 'DMP' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['DMP'],
            mode='lines',
            name='+DI',
            line=dict(color='green')
        ))
    
    if 'DMN' in hist.columns:
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['DMN'],
            mode='lines',
            name='-DI',
            line=dict(color='red')
        ))
    
    fig.add_hline(y=25, line_dash="dash", line_color="orange", annotation_text="強いトレンド(25)")
    
    fig.update_layout(
        title="ADX - トレンド強度",
        yaxis_title="ADX",
        height=250
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_advanced_analysis(hist, selected_stock):
    """高度な統計分析を表示"""
    st.write("**🔬 高度な統計分析**")
    
    # サポート・レジスタンス分析
    st.write("**📊 サポート・レジスタンスレベル**")
    
    method = st.selectbox("計算方法", ["pivot_points", "local_extrema"], key="sr_method")
    levels = calculate_support_resistance(hist, method)
    
    if levels:
        # チャートに表示
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name="価格"
        ))
        
        # レベル線を追加
        for level in levels:
            color = 'red' if level['type'] == 'resistance' else 'blue' if level['type'] == 'support' else 'gray'
            line_style = 'solid' if level['strength'] >= 2 else 'dash'
            
            fig.add_hline(
                y=level['level'],
                line_dash=line_style,
                line_color=color,
                annotation_text=f"{level['type'].title()} {level['level']:.0f}"
            )
        
        fig.update_layout(
            title=f"{selected_stock} - サポート・レジスタンスレベル",
            yaxis_title="価格 (¥)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # レベル一覧表
        levels_df = pd.DataFrame(levels)
        if not levels_df.empty:
            levels_df['level'] = levels_df['level'].round(0)
            st.dataframe(levels_df, use_container_width=True)

def show_anomaly_detection(hist, selected_stock):
    """異常値検出を表示"""
    st.write("**⚠️ 異常値検出**")
    
    method = st.selectbox("検出方法", ["isolation_forest", "zscore"], key="anomaly_method")
    hist_analyzed, anomalies = detect_anomalies(hist, method)
    
    if anomalies:
        # 異常値をチャートに表示
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name="価格"
        ))
        
        # 異常値をマーク
        anomaly_dates = [a['date'] for a in anomalies]
        anomaly_prices = [a['price'] for a in anomalies]
        
        fig.add_trace(go.Scatter(
            x=anomaly_dates,
            y=anomaly_prices,
            mode='markers',
            name='異常値',
            marker=dict(
                symbol='x',
                size=10,
                color='red'
            )
        ))
        
        fig.update_layout(
            title=f"{selected_stock} - 異常値検出",
            yaxis_title="価格 (¥)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 異常値一覧
        st.write(f"**検出された異常値: {len(anomalies)}件**")
        anomalies_df = pd.DataFrame(anomalies)
        if not anomalies_df.empty:
            anomalies_df['date'] = pd.to_datetime(anomalies_df['date']).dt.strftime('%Y-%m-%d')
            anomalies_df['price'] = anomalies_df['price'].round(0)
            st.dataframe(anomalies_df, use_container_width=True)
    else:
        st.info("異常値は検出されませんでした")

def show_trend_analysis(hist, selected_stock):
    """トレンド分析を表示"""
    st.write("**📈 トレンド分析**")
    
    method = st.selectbox("分析方法", ["linear_regression", "polynomial"], key="trend_method")
    trend_analysis = analyze_trend(hist, method)
    
    if trend_analysis:
        # トレンドラインをチャートに表示
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'],
            mode='lines',
            name='終値',
            line=dict(color='blue')
        ))
        
        if 'trend_line' in trend_analysis:
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=trend_analysis['trend_line'],
                mode='lines',
                name='トレンドライン',
                line=dict(color='red', dash='dash')
            ))
        
        fig.update_layout(
            title=f"{selected_stock} - トレンド分析",
            yaxis_title="価格 (¥)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 分析結果
        col1, col2 = st.columns(2)
        
        with col1:
            if method == 'linear_regression':
                direction = "上昇トレンド" if trend_analysis.get('slope', 0) > 0 else "下降トレンド"
                st.metric("トレンド方向", direction)
                st.metric("R²決定係数", f"{trend_analysis.get('r_squared', 0):.3f}")
            
        with col2:
            if method == 'linear_regression':
                strength = trend_analysis.get('trend_strength', 0)
                strength_text = "強い" if strength > 0.7 else "中程度" if strength > 0.4 else "弱い"
                st.metric("トレンド強度", strength_text)
                st.metric("傾き", f"{trend_analysis.get('slope', 0):.2f}")

def show_basic_signals(hist):
    """基本的なシグナル分析を表示"""
    st.write("**🎯 テクニカルシグナル**")
    
    latest_data = hist.iloc[-1]
    signals = []
    
    # 移動平均のシグナル
    if not pd.isna(latest_data['MA5']) and not pd.isna(latest_data['MA25']):
        if latest_data['MA5'] > latest_data['MA25']:
            signals.append("✅ 短期移動平均が中期移動平均を上回る（買いシグナル）")
        else:
            signals.append("❌ 短期移動平均が中期移動平均を下回る（売りシグナル）")
    
    # RSIのシグナル
    if not pd.isna(latest_data['RSI']):
        if latest_data['RSI'] > 70:
            signals.append("⚠️ RSI買われすぎ圏（売り検討）")
        elif latest_data['RSI'] < 30:
            signals.append("⚠️ RSI売られすぎ圏（買い検討）")
        else:
            signals.append("📊 RSI中立圏")
    
    # ボリンジャーバンドのシグナル
    if (not pd.isna(latest_data['BB_Upper']) and 
        not pd.isna(latest_data['BB_Lower']) and
        not pd.isna(latest_data['Close'])):
        
        if latest_data['Close'] > latest_data['BB_Upper']:
            signals.append("⚠️ ボリンジャーバンド上限突破（売り検討）")
        elif latest_data['Close'] < latest_data['BB_Lower']:
            signals.append("⚠️ ボリンジャーバンド下限突破（買い検討）")
        else:
            signals.append("📊 ボリンジャーバンド範囲内")
    
    for signal in signals:
        st.write(signal)
    
    st.info("""
    **テクニカル分析の注意点**
    - 過去のデータに基づく分析であり、将来の株価を保証するものではありません
    - 複数の指標を組み合わせて総合的に判断することが重要です
    - ファンダメンタル分析も併用してください
    """)

def show_stock_comparison(base_stock_code, base_stock_name, period, user_info, security_manager):
    """銘柄比較機能"""
    st.subheader("🔄 銘柄比較")
    
    if "write" not in user_info["permissions"]:
        st.warning("銘柄比較機能の利用には書き込み権限が必要です")
        return
    
    st.write(f"**基準銘柄**: {base_stock_name} ({base_stock_code})")
    
    # 比較対象銘柄の選択
    st.write("**比較対象銘柄を選択してください（最大3銘柄まで）:**")
    
    stock_db = st.session_state.stock_database
    all_stocks = stock_db.get_all_stocks()
    
    # 基準銘柄を除外
    comparison_options = [
        f"{stock['name']} ({stock['code']})"
        for stock in all_stocks 
        if stock['code'] != base_stock_code
    ]
    
    selected_comparisons = st.multiselect(
        "比較銘柄を選択",
        options=comparison_options,
        max_selections=3,
        key="stock_comparison_selector"
    )
    
    if not selected_comparisons:
        st.info("比較対象の銘柄を選択してください")
        return
    
    try:
        # 基準銘柄のデータを取得
        base_stock = yf.Ticker(base_stock_code)
        base_hist = base_stock.history(period=period)
        
        if len(base_hist) == 0:
            st.error("基準銘柄のデータを取得できませんでした")
            return
        
        # 比較対象のデータを取得
        comparison_data = {}
        comparison_codes = []
        
        for comp_selection in selected_comparisons:
            # 銘柄コードを抽出
            comp_code = comp_selection.split('(')[-1].split(')')[0]
            comp_name = comp_selection.split(' (')[0]
            
            if not security_manager.validate_stock_code(comp_code):
                st.warning(f"無効な株式コード: {comp_code}")
                continue
            
            try:
                comp_stock = yf.Ticker(comp_code)
                comp_hist = comp_stock.history(period=period)
                
                if len(comp_hist) > 0:
                    comparison_data[comp_name] = {
                        'code': comp_code,
                        'hist': comp_hist,
                        'stock': comp_stock
                    }
                    comparison_codes.append(comp_code)
                
            except Exception as e:
                st.warning(f"{comp_name}のデータ取得に失敗しました")
        
        if not comparison_data:
            st.error("比較データを取得できませんでした")
            return
        
        # 価格比較チャート（正規化）
        st.subheader("📊 価格推移比較（正規化）")
        
        fig_comparison = go.Figure()
        
        # 基準銘柄（正規化）
        base_normalized = (base_hist['Close'] / base_hist['Close'].iloc[0]) * 100
        fig_comparison.add_trace(go.Scatter(
            x=base_hist.index,
            y=base_normalized,
            mode='lines',
            name=f"{base_stock_name} (基準)",
            line=dict(width=3)
        ))
        
        # 比較銘柄（正規化）
        colors = ['red', 'green', 'orange']
        for i, (comp_name, comp_data) in enumerate(comparison_data.items()):
            comp_hist = comp_data['hist']
            comp_normalized = (comp_hist['Close'] / comp_hist['Close'].iloc[0]) * 100
            
            fig_comparison.add_trace(go.Scatter(
                x=comp_hist.index,
                y=comp_normalized,
                mode='lines',
                name=comp_name,
                line=dict(color=colors[i % len(colors)], width=2)
            ))
        
        fig_comparison.update_layout(
            title="価格推移比較（開始日=100として正規化）",
            yaxis_title="正規化価格",
            xaxis_title="日付",
            height=500
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)
        
        # パフォーマンス比較表
        st.subheader("📈 パフォーマンス比較")
        
        performance_data = []
        
        # 基準銘柄のパフォーマンス
        base_start = base_hist['Close'].iloc[0]
        base_end = base_hist['Close'].iloc[-1]
        base_return = ((base_end - base_start) / base_start) * 100
        base_volatility = base_hist['Close'].pct_change().std() * (252 ** 0.5) * 100  # 年率化
        
        performance_data.append({
            "銘柄": f"{base_stock_name} (基準)",
            "開始価格": f"¥{base_start:,.0f}",
            "現在価格": f"¥{base_end:,.0f}",
            "リターン": f"{base_return:+.2f}%",
            "ボラティリティ": f"{base_volatility:.2f}%"
        })
        
        # 比較銘柄のパフォーマンス
        for comp_name, comp_data in comparison_data.items():
            comp_hist = comp_data['hist']
            comp_start = comp_hist['Close'].iloc[0]
            comp_end = comp_hist['Close'].iloc[-1]
            comp_return = ((comp_end - comp_start) / comp_start) * 100
            comp_volatility = comp_hist['Close'].pct_change().std() * (252 ** 0.5) * 100
            
            performance_data.append({
                "銘柄": comp_name,
                "開始価格": f"¥{comp_start:,.0f}",
                "現在価格": f"¥{comp_end:,.0f}",
                "リターン": f"{comp_return:+.2f}%",
                "ボラティリティ": f"{comp_volatility:.2f}%"
            })
        
        performance_df = pd.DataFrame(performance_data)
        st.dataframe(performance_df, use_container_width=True, hide_index=True)
        
        # 出来高比較
        st.subheader("📊 出来高比較")
        
        fig_volume_comp = go.Figure()
        
        # 基準銘柄の出来高
        fig_volume_comp.add_trace(go.Bar(
            x=base_hist.index,
            y=base_hist['Volume'],
            name=f"{base_stock_name} (基準)",
            opacity=0.7
        ))
        
        # 比較銘柄の出来高（縮小表示）
        for comp_name, comp_data in comparison_data.items():
            comp_hist = comp_data['hist']
            fig_volume_comp.add_trace(go.Bar(
                x=comp_hist.index,
                y=comp_hist['Volume'],
                name=comp_name,
                opacity=0.5
            ))
        
        fig_volume_comp.update_layout(
            title="出来高比較",
            yaxis_title="出来高",
            xaxis_title="日付",
            height=400,
            barmode='overlay'
        )
        
        st.plotly_chart(fig_volume_comp, use_container_width=True)
        
        # 相関分析
        st.subheader("🔗 相関分析")
        
        if len(comparison_data) >= 1:
            correlation_data = pd.DataFrame()
            correlation_data[base_stock_name] = base_hist['Close'].pct_change()
            
            for comp_name, comp_data in comparison_data.items():
                comp_hist = comp_data['hist']
                # データの長さを合わせる
                min_len = min(len(correlation_data), len(comp_hist))
                if min_len > 1:
                    correlation_data = correlation_data.tail(min_len)
                    comp_returns = comp_hist['Close'].pct_change().tail(min_len)
                    correlation_data[comp_name] = comp_returns.values
            
            # 相関行列を計算
            corr_matrix = correlation_data.corr()
            
            # ヒートマップで表示
            fig_corr = px.imshow(
                corr_matrix,
                text_auto='.2f',
                aspect="auto",
                title="株価変動率の相関係数",
                color_continuous_scale='RdBu'
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
            
            st.info("""
            **相関係数の解釈:**
            - 1.0に近い: 同じような動きをする
            - 0.0に近い: 関係性が薄い
            - -1.0に近い: 逆の動きをする
            """)
        
    except Exception as e:
        st.error("銘柄比較の処理中にエラーが発生しました")
        if "admin" in user_info["permissions"]:
            with st.expander("詳細エラー（管理者のみ）"):
                st.code(str(e))

def show_main_app():
    """メインアプリケーションを表示"""
    security_manager = st.session_state.security_manager
    user_info = st.session_state.user_info
    
    # レート制限チェック
    if not security_manager.check_rate_limit():
        st.error("アクセス制限に達しました。しばらくお待ちください。")
        return
    
    # ヘッダー
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📈 日本株データ分析アプリ（セキュア版）")
    with col2:
        st.write(f"ログイン: {user_info['username']} ({user_info['role']})")
        if st.button("ログアウト"):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()
    
    st.markdown("---")
    
    # 権限チェック
    if "read" not in user_info["permissions"]:
        st.error("データ閲覧権限がありません")
        return
    
    # サイドバーで銘柄検索
    st.sidebar.header("🔍 銘柄検索")
    
    # 検索方法の選択
    search_method = st.sidebar.radio(
        "検索方法を選択",
        ["銘柄名で検索", "人気銘柄から選択"],
        index=0
    )
    
    stock_code = None
    selected_stock = None
    
    if search_method == "銘柄名で検索":
        # 検索フォーム
        search_query = st.sidebar.text_input(
            "銘柄名を入力してください",
            placeholder="例: トヨタ、ソニー、任天堂"
        )
        
        if search_query:
            # 入力検証
            validated_query = security_manager.validate_search_query(search_query)
            
            if validated_query:
                # 検索実行
                search_results = st.session_state.stock_database.search_stocks(validated_query)
                
                if search_results:
                    st.sidebar.write(f"**検索結果: {len(search_results)}件**")
                    
                    # 検索結果を表示
                    result_options = []
                    result_mapping = {}
                    
                    for result in search_results:
                        display_text = f"{result['name']} ({result['code']}) - {result['sector']}"
                        result_options.append(display_text)
                        result_mapping[display_text] = result
                    
                    selected_result = st.sidebar.selectbox(
                        "銘柄を選択してください",
                        options=result_options,
                        key="search_result_selector"
                    )
                    
                    if selected_result:
                        selected_data = result_mapping[selected_result]
                        stock_code = selected_data['code']
                        selected_stock = selected_data['name']
                        
                        # セッション状態に保存
                        st.session_state.selected_stock_code = stock_code
                        st.session_state.selected_stock_name = selected_stock
                else:
                    st.sidebar.warning("検索結果が見つかりませんでした")
                    st.sidebar.info("人気銘柄から選択するか、別のキーワードをお試しください")
            else:
                st.sidebar.error("無効な検索クエリです")
    
    else:  # 人気銘柄から選択
        # よく使われる銘柄コード（検証済み）
        popular_stocks = {
            "トヨタ自動車": "7203.T",
            "ソフトバンクグループ": "9984.T", 
            "ファーストリテイリング": "9983.T",
            "キーエンス": "6861.T",
            "信越化学工業": "4063.T",
            "ソニーグループ": "6758.T",
            "任天堂": "7974.T",
            "ホンダ": "7267.T"
        }
        
        selected_stock = st.sidebar.selectbox(
            "人気銘柄から選択",
            options=list(popular_stocks.keys()),
            key="popular_stock_selector"
        )
        
        stock_code = popular_stocks[selected_stock]
        
        # セッション状態に保存
        st.session_state.selected_stock_code = stock_code
        st.session_state.selected_stock_name = selected_stock
    
    # セッション状態から銘柄情報を取得
    if not stock_code and st.session_state.selected_stock_code:
        stock_code = st.session_state.selected_stock_code
        selected_stock = st.session_state.selected_stock_name
    
    # 銘柄が選択されていない場合
    if not stock_code:
        st.info("👆 サイドバーから銘柄を検索・選択してください")
        
        # 全銘柄一覧を表示（読み取り権限のみで可能）
        if st.button("📋 対応銘柄一覧を表示"):
            show_all_stocks_list()
        return
    
    # 株式コードの検証
    if not security_manager.validate_stock_code(stock_code):
        st.error("無効な株式コードです")
        return
    
    # 期間選択
    period_options = {
        "1ヶ月": "1mo",
        "3ヶ月": "3mo", 
        "6ヶ月": "6mo",
        "1年": "1y",
        "2年": "2y"
    }
    
    selected_period = st.sidebar.selectbox(
        "期間を選択",
        options=list(period_options.keys()),
        index=2  # デフォルトは6ヶ月
    )
    
    period = period_options[selected_period]
    
    try:
        # データ取得（エラーハンドリング強化）
        with st.spinner(f"{selected_stock}のデータを取得中..."):
            stock = yf.Ticker(stock_code)
            hist = stock.history(period=period)
            
            # 情報取得は管理者権限のみ
            info = None
            if "admin" in user_info["permissions"]:
                try:
                    info = stock.info
                except:
                    info = None
        
        if len(hist) == 0:
            st.warning("データが取得できませんでした。別の銘柄をお試しください。")
            return
        
        # 基本情報表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = hist['Close'].iloc[-1]
            st.metric("現在価格", f"¥{current_price:,.0f}")
        
        with col2:
            if len(hist) > 1:
                price_change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                change_pct = (price_change / hist['Close'].iloc[-2]) * 100
                st.metric("前日比", f"¥{price_change:+,.0f}", f"{change_pct:+.2f}%")
        
        with col3:
            max_price = hist['High'].max()
            st.metric(f"{selected_period}最高値", f"¥{max_price:,.0f}")
        
        with col4:
            min_price = hist['Low'].min()
            st.metric(f"{selected_period}最安値", f"¥{min_price:,.0f}")
        
        # 検索された銘柄の詳細情報を表示
        if search_method == "銘柄名で検索" and 'search_query' in locals() and search_query:
            st.markdown("---")
            st.subheader("🔍 検索結果の詳細")
            
            # 関連銘柄も表示
            validated_query = security_manager.validate_search_query(search_query)
            if validated_query:
                all_results = st.session_state.stock_database.search_stocks(validated_query, limit=10)
                if len(all_results) > 1:
                    st.write("**関連する他の銘柄:**")
                    
                    related_stocks = [r for r in all_results if r['code'] != stock_code]
                    if related_stocks:
                        related_cols = st.columns(min(3, len(related_stocks)))
                        for i, related in enumerate(related_stocks[:3]):  # 最大3つまで表示
                            with related_cols[i]:
                                if st.button(f"📊 {related['name']}\n({related['code']})", key=f"related_{i}"):
                                    st.session_state.selected_stock_code = related['code']
                                    st.session_state.selected_stock_name = related['name']
                                    st.rerun()
        
        st.markdown("---")
        
        # タブを作成
        tab1, tab2, tab3, tab4 = st.tabs(["📊 株価チャート", "💹 ファンダメンタル分析", "📈 テクニカル分析", "🔄 銘柄比較"])
        
        with tab1:
            # 株価チャート
            st.subheader("📊 株価チャート")
            
            fig = go.Figure()
            
            fig.add_trace(go.Candlestick(
                x=hist.index,
                open=hist['Open'],
                high=hist['High'], 
                low=hist['Low'],
                close=hist['Close'],
                name=selected_stock
            ))
            
            fig.update_layout(
                title=f"{selected_stock} ({stock_code}) - {selected_period}",
                yaxis_title="価格 (¥)",
                xaxis_title="日付",
                height=500,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 出来高チャート（書き込み権限が必要）
            if "write" in user_info["permissions"]:
                st.subheader("📊 出来高")
                
                fig_volume = px.bar(
                    x=hist.index,
                    y=hist['Volume'],
                    title="出来高"
                )
                
                fig_volume.update_layout(
                    xaxis_title="日付",
                    yaxis_title="出来高",
                    height=300
                )
                
                st.plotly_chart(fig_volume, use_container_width=True)
            
            # 基本統計
            st.subheader("📈 基本統計")
            
            stats_col1, stats_col2 = st.columns(2)
            
            with stats_col1:
                st.write("**価格統計**")
                price_stats = pd.DataFrame({
                    "項目": ["平均価格", "標準偏差", "最高値", "最安値"],
                    "値": [
                        f"¥{hist['Close'].mean():,.0f}",
                        f"¥{hist['Close'].std():,.0f}",
                        f"¥{hist['Close'].max():,.0f}",
                        f"¥{hist['Close'].min():,.0f}"
                    ]
                })
                st.dataframe(price_stats, hide_index=True)
            
            with stats_col2:
                if "write" in user_info["permissions"]:
                    st.write("**出来高統計**")
                    volume_stats = pd.DataFrame({
                        "項目": ["平均出来高", "最大出来高", "最小出来高"],
                        "値": [
                            f"{hist['Volume'].mean():,.0f}",
                            f"{hist['Volume'].max():,.0f}",
                            f"{hist['Volume'].min():,.0f}"
                        ]
                    })
                    st.dataframe(volume_stats, hide_index=True)
        
        with tab2:
            # ファンダメンタル分析
            show_fundamental_analysis(stock, info, hist, user_info, security_manager)
        
        with tab3:
            # テクニカル分析
            show_technical_analysis(hist, selected_stock, user_info)
        
        with tab4:
            # 銘柄比較
            show_stock_comparison(stock_code, selected_stock, period, user_info, security_manager)
        
        # 会社情報（管理者権限のみ）
        if info and "admin" in user_info["permissions"]:
            st.markdown("---")
            st.subheader("🏢 会社情報")
            
            info_items = []
            safe_fields = ['longName', 'sector', 'industry']  # 安全なフィールドのみ
            
            for field in safe_fields:
                if field in info:
                    value = security_manager.validate_input(str(info[field]))
                    if value:
                        field_names = {
                            'longName': '会社名',
                            'sector': 'セクター', 
                            'industry': '業界'
                        }
                        info_items.append((field_names[field], value))
            
            if 'marketCap' in info and isinstance(info['marketCap'], (int, float)):
                market_cap = info['marketCap'] / 1e12
                if market_cap > 0:
                    info_items.append(("時価総額", f"約{market_cap:.1f}兆円"))
            
            if info_items:
                info_df = pd.DataFrame(info_items, columns=["項目", "値"])
                st.dataframe(info_df, hide_index=True)
    
    except Exception as e:
        # セキュアなエラーメッセージ
        st.error("データの処理中にエラーが発生しました。")
        
        # 管理者のみ詳細エラーを表示
        if "admin" in user_info["permissions"]:
            with st.expander("詳細エラー情報（管理者のみ）"):
                st.code(str(e))

def main():
    """メインエントリーポイント"""
    st.set_page_config(
        page_title="日本株データ分析",
        page_icon="📈",
        layout="wide"
    )
    
    # セッション状態を初期化
    init_session_state()
    
    # 認証チェック
    if not st.session_state.authenticated:
        show_login()
    else:
        show_main_app()

if __name__ == "__main__":
    main() 