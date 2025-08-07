import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# セッション状態の初期化
def init_session_state():
    """セッション状態を初期化"""
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ['7203.T', '9984.T', '6758.T', '7974.T']
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'theme': 'light',
            'default_period': '1y',
            'default_indicators': ['MA', 'RSI', 'BB']
        }

def calculate_technical_indicators(df):
    """テクニカル指標を計算"""
    if df.empty:
        return df
    
    try:
        # 移動平均線
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA25'] = df['Close'].rolling(window=25).mean()
        df['MA75'] = df['Close'].rolling(window=75).mean()
        
        # ボリンジャーバンド
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        
        # ストキャスティクス
        high14 = df['High'].rolling(window=14).max()
        low14 = df['Low'].rolling(window=14).min()
        df['%K'] = 100 * ((df['Close'] - low14) / (high14 - low14))
        df['%D'] = df['%K'].rolling(window=3).mean()
        
        return df
    except Exception as e:
        st.error(f"テクニカル指標計算エラー: {str(e)}")
        return df

def get_fundamental_data(symbol):
    """ファンダメンタルデータを取得"""
    if not YFINANCE_AVAILABLE:
        return None
    
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        fundamental_data = {
            '企業名': info.get('longName', 'N/A'),
            '業種': info.get('sector', 'N/A'),
            '業界': info.get('industry', 'N/A'),
            '時価総額': info.get('marketCap', 'N/A'),
            'PER': info.get('trailingPE', 'N/A'),
            'PBR': info.get('priceToBook', 'N/A'),
            'ROE': info.get('returnOnEquity', 'N/A'),
            'ROA': info.get('returnOnAssets', 'N/A'),
            '配当利回り': info.get('dividendYield', 'N/A'),
            '52週高値': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52週安値': info.get('fiftyTwoWeekLow', 'N/A'),
            'Beta': info.get('beta', 'N/A'),
            '従業員数': info.get('fullTimeEmployees', 'N/A'),
            'EPS': info.get('trailingEps', 'N/A'),
            '売上総利益率': info.get('grossMargins', 'N/A'),
            '営業利益率': info.get('operatingMargins', 'N/A')
        }
        
        return fundamental_data
    except Exception as e:
        st.error(f"ファンダメンタルデータ取得エラー: {str(e)}")
        return None

def get_market_summary():
    """市場サマリーを取得"""
    if not YFINANCE_AVAILABLE:
        return None
    
    try:
        # 主要指数
        indices = {
            '日経平均': '^N225',
            'TOPIX': '^TPX',
            'マザーズ': '^MOTHERS',
            'JASDAQ': '^JSDA'
        }
        
        market_data = {}
        for name, symbol in indices.items():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='2d')
            if not hist.empty:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest
                change = latest['Close'] - prev['Close']
                change_pct = (change / prev['Close']) * 100 if prev['Close'] != 0 else 0
                
                market_data[name] = {
                    'price': latest['Close'],
                    'change': change,
                    'change_pct': change_pct
                }
        
        return market_data
    except Exception as e:
        st.error(f"市場データ取得エラー: {str(e)}")
        return None

def show_dashboard():
    """ダッシュボードを表示"""
    st.title("📊 ダッシュボード")
    
    # 市場サマリー
    st.subheader("🏛️ 市場概況")
    market_data = get_market_summary()
    
    if market_data:
        cols = st.columns(len(market_data))
        for i, (name, data) in enumerate(market_data.items()):
            with cols[i]:
                st.metric(
                    name,
                    f"{data['price']:.2f}",
                    f"{data['change']:+.2f} ({data['change_pct']:+.2f}%)"
                )
    else:
        st.info("市場データを取得できませんでした")
    
    # ウォッチリスト
    st.subheader("👀 ウォッチリスト")
    if st.session_state.watchlist and YFINANCE_AVAILABLE:
        watchlist_data = []
        
        for symbol in st.session_state.watchlist:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='2d')
                if not hist.empty:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2] if len(hist) > 1 else latest
                    change = latest['Close'] - prev['Close']
                    change_pct = (change / prev['Close']) * 100 if prev['Close'] != 0 else 0
                    
                    watchlist_data.append({
                        '銘柄コード': symbol,
                        '終値': latest['Close'],
                        '前日比': change,
                        '変化率(%)': change_pct,
                        '出来高': latest['Volume']
                    })
            except Exception:
                continue
        
        if watchlist_data:
            df_watchlist = pd.DataFrame(watchlist_data)
            
            # カラーマップを適用
            def color_change(val):
                color = 'red' if val < 0 else 'green' if val > 0 else 'black'
                return f'color: {color}'
            
            styled_df = df_watchlist.style.applymap(
                color_change, subset=['前日比', '変化率(%)']
            ).format({
                '終値': '¥{:.0f}',
                '前日比': '{:+.0f}',
                '変化率(%)': '{:+.2f}%',
                '出来高': '{:,.0f}'
            })
            
            st.dataframe(styled_df, use_container_width=True)
        else:
            st.info("ウォッチリストのデータを取得できませんでした")
    else:
        st.info("ウォッチリストが空です")
    
    # ポートフォリオサマリー
    st.subheader("💼 ポートフォリオ")
    if st.session_state.portfolio:
        total_value = 0
        total_gain_loss = 0
        
        portfolio_data = []
        for holding in st.session_state.portfolio:
            try:
                if YFINANCE_AVAILABLE:
                    ticker = yf.Ticker(holding['symbol'])
                    current_price = ticker.history(period='1d')['Close'].iloc[-1]
                    
                    current_value = current_price * holding['shares']
                    cost_basis = holding['avg_price'] * holding['shares']
                    gain_loss = current_value - cost_basis
                    gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis != 0 else 0
                    
                    portfolio_data.append({
                        '銘柄': holding['symbol'],
                        '株数': holding['shares'],
                        '平均取得価格': holding['avg_price'],
                        '現在価格': current_price,
                        '評価額': current_value,
                        '損益': gain_loss,
                        '損益率(%)': gain_loss_pct
                    })
                    
                    total_value += current_value
                    total_gain_loss += gain_loss
            except Exception:
                continue
        
        if portfolio_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総評価額", f"¥{total_value:,.0f}")
            with col2:
                st.metric("総損益", f"¥{total_gain_loss:+,.0f}")
            with col3:
                total_cost = sum(h['avg_price'] * h['shares'] for h in st.session_state.portfolio)
                total_return_pct = (total_gain_loss / total_cost) * 100 if total_cost != 0 else 0
                st.metric("総合収益率", f"{total_return_pct:+.2f}%")
            
            # ポートフォリオ詳細
            df_portfolio = pd.DataFrame(portfolio_data)
            
            def color_pnl(val):
                color = 'red' if val < 0 else 'green' if val > 0 else 'black'
                return f'color: {color}'
            
            styled_portfolio = df_portfolio.style.applymap(
                color_pnl, subset=['損益', '損益率(%)']
            ).format({
                '平均取得価格': '¥{:.0f}',
                '現在価格': '¥{:.0f}',
                '評価額': '¥{:,.0f}',
                '損益': '¥{:+,.0f}',
                '損益率(%)': '{:+.2f}%'
            })
            
            st.dataframe(styled_portfolio, use_container_width=True)
        else:
            st.info("ポートフォリオデータを取得できませんでした")
    else:
        st.info("ポートフォリオが空です。「ポートフォリオ管理」で銘柄を追加してください。")

def show_stock_search():
    """銘柄検索画面"""
    st.title("🔍 銘柄検索・分析")
    
    # 検索機能
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "銘柄コードまたは企業名を入力",
            placeholder="例: 7203.T, トヨタ, TOYOTA"
        )
    
    with col2:
        search_type = st.selectbox("検索タイプ", ["コード検索", "テーマ検索"])
    
    # 人気銘柄・テーマ検索
    if search_type == "テーマ検索":
        st.subheader("📈 テーマ別銘柄")
        
        themes = {
            "高配当": ["8306.T", "8031.T", "8411.T", "9984.T"],
            "成長株": ["6758.T", "7974.T", "4755.T", "6861.T"],
            "ディフェンシブ": ["2914.T", "4502.T", "4503.T", "4506.T"],
            "インバウンド": ["9020.T", "9021.T", "3092.T", "7203.T"]
        }
        
        selected_theme = st.selectbox("テーマを選択", list(themes.keys()))
        
        if selected_theme:
            st.write(f"**{selected_theme}関連銘柄:**")
            theme_stocks = themes[selected_theme]
            
            cols = st.columns(min(len(theme_stocks), 4))
            for i, symbol in enumerate(theme_stocks):
                with cols[i % 4]:
                    if st.button(f"{symbol}", key=f"theme_{symbol}"):
                        st.session_state.selected_symbol = symbol
                        st.rerun()
    
    # 検索結果表示
    if search_query:
        if search_query.upper().endswith('.T') or search_query.isdigit():
            # 銘柄コード検索
            symbol = search_query.upper()
            if not symbol.endswith('.T'):
                symbol += '.T'
            
            if st.button("この銘柄を分析", type="primary"):
                st.session_state.selected_symbol = symbol
                st.session_state.current_page = "分析"
                st.rerun()
        else:
            st.info("企業名での検索は現在開発中です。銘柄コードをご利用ください。")

def show_portfolio_management():
    """ポートフォリオ管理画面"""
    st.title("💼 ポートフォリオ管理")
    
    # 新規追加
    st.subheader("📝 新規銘柄追加")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        new_symbol = st.text_input("銘柄コード", placeholder="例: 7203.T")
    
    with col2:
        new_shares = st.number_input("株数", min_value=1, value=100)
    
    with col3:
        new_price = st.number_input("平均取得価格", min_value=0.0, value=1000.0)
    
    if st.button("ポートフォリオに追加"):
        if new_symbol:
            # 既存銘柄の確認
            existing = next((h for h in st.session_state.portfolio if h['symbol'] == new_symbol), None)
            
            if existing:
                # 平均取得価格を再計算
                total_shares = existing['shares'] + new_shares
                total_cost = (existing['shares'] * existing['avg_price']) + (new_shares * new_price)
                new_avg_price = total_cost / total_shares
                
                existing['shares'] = total_shares
                existing['avg_price'] = new_avg_price
                st.success(f"{new_symbol} の保有情報を更新しました")
            else:
                st.session_state.portfolio.append({
                    'symbol': new_symbol,
                    'shares': new_shares,
                    'avg_price': new_price,
                    'date_added': datetime.now().strftime('%Y-%m-%d')
                })
                st.success(f"{new_symbol} をポートフォリオに追加しました")
            
            st.rerun()
    
    # 現在のポートフォリオ
    st.subheader("📊 現在のポートフォリオ")
    
    if st.session_state.portfolio:
        # ポートフォリオの編集・削除機能
        for i, holding in enumerate(st.session_state.portfolio):
            with st.expander(f"{holding['symbol']} - {holding['shares']}株"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**平均取得価格:** ¥{holding['avg_price']:.0f}")
                    st.write(f"**追加日:** {holding['date_added']}")
                
                with col2:
                    if YFINANCE_AVAILABLE:
                        try:
                            ticker = yf.Ticker(holding['symbol'])
                            current_price = ticker.history(period='1d')['Close'].iloc[-1]
                            current_value = current_price * holding['shares']
                            cost_basis = holding['avg_price'] * holding['shares']
                            gain_loss = current_value - cost_basis
                            gain_loss_pct = (gain_loss / cost_basis) * 100 if cost_basis != 0 else 0
                            
                            st.write(f"**現在価格:** ¥{current_price:.0f}")
                            st.write(f"**評価額:** ¥{current_value:,.0f}")
                            
                            color = "🔴" if gain_loss < 0 else "🟢" if gain_loss > 0 else "⚪"
                            st.write(f"**損益:** {color} ¥{gain_loss:+,.0f} ({gain_loss_pct:+.2f}%)")
                        except Exception:
                            st.write("価格情報を取得できませんでした")
                
                with col3:
                    if st.button("削除", key=f"delete_{i}"):
                        st.session_state.portfolio.pop(i)
                        st.rerun()
                    
                    if st.button("ウォッチリストに追加", key=f"watch_{i}"):
                        if holding['symbol'] not in st.session_state.watchlist:
                            st.session_state.watchlist.append(holding['symbol'])
                            st.success("ウォッチリストに追加しました")
                        else:
                            st.info("既にウォッチリストに登録されています")
    else:
        st.info("ポートフォリオが空です。上記のフォームから銘柄を追加してください。")

def show_analysis_page():
    """分析画面"""
    if 'selected_symbol' not in st.session_state:
        st.info("分析する銘柄を選択してください")
        return
    
    symbol = st.session_state.selected_symbol
    st.title(f"📈 {symbol} 詳細分析")
    
    # 期間選択
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader(f"銘柄: {symbol}")
    
    with col2:
        period = st.selectbox("分析期間", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
    
    if YFINANCE_AVAILABLE:
        try:
            with st.spinner("データを取得中..."):
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    # テクニカル指標を計算
                    hist_with_indicators = calculate_technical_indicators(hist.copy())
                    
                    # 基本情報
                    latest = hist_with_indicators.iloc[-1]
                    prev = hist_with_indicators.iloc[-2] if len(hist_with_indicators) > 1 else latest
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        change = latest['Close'] - prev['Close']
                        change_pct = (change / prev['Close']) * 100 if prev['Close'] != 0 else 0
                        st.metric("終値", f"¥{latest['Close']:.0f}", f"{change:+.0f} ({change_pct:+.1f}%)")
                    
                    with col2:
                        st.metric("高値", f"¥{latest['High']:.0f}")
                    
                    with col3:
                        st.metric("安値", f"¥{latest['Low']:.0f}")
                    
                    with col4:
                        st.metric("出来高", f"{latest['Volume']:,.0f}")
                    
                    # タブで分析を分割
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 価格チャート", "📈 テクニカル分析", "📋 ファンダメンタル", "🎯 総合判定"])
                    
                    with tab1:
                        if PLOTLY_AVAILABLE:
                            fig = go.Figure(data=go.Candlestick(
                                x=hist_with_indicators.index,
                                open=hist_with_indicators['Open'],
                                high=hist_with_indicators['High'],
                                low=hist_with_indicators['Low'],
                                close=hist_with_indicators['Close']
                            ))
                            
                            # 移動平均を追加
                            fig.add_trace(go.Scatter(
                                x=hist_with_indicators.index, y=hist_with_indicators['MA25'],
                                mode='lines', name='MA25',
                                line=dict(color='blue', width=2)
                            ))
                            
                            fig.update_layout(
                                title=f"{symbol} - 株価チャート",
                                yaxis_title="価格 (¥)",
                                height=500,
                                xaxis_rangeslider_visible=False
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with tab2:
                        # テクニカル分析の詳細実装は前回と同様
                        st.write("テクニカル分析機能（前回実装と同様）")
                        
                        # 主要指標表示
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if not pd.isna(latest['RSI']):
                                st.metric("RSI", f"{latest['RSI']:.1f}")
                        
                        with col2:
                            if not pd.isna(latest['MA25']):
                                st.metric("MA25", f"¥{latest['MA25']:.0f}")
                        
                        with col3:
                            if not pd.isna(latest['MACD']):
                                st.metric("MACD", f"{latest['MACD']:.3f}")
                        
                        with col4:
                            if not pd.isna(latest['%K']):
                                st.metric("Stoch %K", f"{latest['%K']:.1f}")
                    
                    with tab3:
                        # ファンダメンタル分析
                        fundamental_data = get_fundamental_data(symbol)
                        
                        if fundamental_data:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("🏢 企業情報")
                                st.write(f"**企業名:** {fundamental_data['企業名']}")
                                st.write(f"**業種:** {fundamental_data['業種']}")
                                st.write(f"**業界:** {fundamental_data['業界']}")
                                
                                if fundamental_data['従業員数'] != 'N/A':
                                    st.write(f"**従業員数:** {fundamental_data['従業員数']:,}人")
                            
                            with col2:
                                st.subheader("💰 主要指標")
                                
                                if fundamental_data['時価総額'] != 'N/A':
                                    market_cap = fundamental_data['時価総額'] / 1000000000
                                    st.metric("時価総額", f"{market_cap:.0f}億円")
                                
                                if fundamental_data['PER'] != 'N/A':
                                    st.metric("PER", f"{fundamental_data['PER']:.2f}")
                                
                                if fundamental_data['PBR'] != 'N/A':
                                    st.metric("PBR", f"{fundamental_data['PBR']:.2f}")
                                
                                if fundamental_data['ROE'] != 'N/A':
                                    st.metric("ROE", f"{fundamental_data['ROE']*100:.1f}%")
                    
                    with tab4:
                        st.subheader("🎯 投資判定サマリー")
                        
                        # 簡易スコアリング
                        technical_score = 0
                        fundamental_score = 0
                        
                        # テクニカルスコア
                        if not pd.isna(latest['RSI']):
                            if 30 <= latest['RSI'] <= 70:
                                technical_score += 1
                        
                        if not pd.isna(latest['MA25']) and not pd.isna(latest['Close']):
                            if latest['Close'] > latest['MA25']:
                                technical_score += 1
                        
                        # ファンダメンタルスコア
                        if fundamental_data:
                            if fundamental_data['PER'] != 'N/A' and 0 < fundamental_data['PER'] < 20:
                                fundamental_score += 1
                            
                            if fundamental_data['PBR'] != 'N/A' and 0 < fundamental_data['PBR'] < 1.5:
                                fundamental_score += 1
                            
                            if fundamental_data['ROE'] != 'N/A' and fundamental_data['ROE'] > 0.1:
                                fundamental_score += 1
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("テクニカルスコア", f"{technical_score}/2")
                        
                        with col2:
                            st.metric("ファンダメンタルスコア", f"{fundamental_score}/3")
                        
                        with col3:
                            total_score = technical_score + fundamental_score
                            max_score = 5
                            overall_rating = "買い" if total_score >= 4 else "hold" if total_score >= 2 else "様子見"
                            st.metric("総合評価", overall_rating)
                        
                        # アクションボタン
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("ポートフォリオに追加"):
                                st.session_state.add_to_portfolio_symbol = symbol
                                st.info("ポートフォリオ管理画面で詳細を入力してください")
                        
                        with col2:
                            if st.button("ウォッチリストに追加"):
                                if symbol not in st.session_state.watchlist:
                                    st.session_state.watchlist.append(symbol)
                                    st.success("ウォッチリストに追加しました")
                                else:
                                    st.info("既にウォッチリストに登録されています")
                
                else:
                    st.error("データを取得できませんでした")
        
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")
    else:
        st.error("yfinanceが利用できません")

def show_news_page():
    """ニュース画面（模擬）"""
    st.title("📰 マーケットニュース")
    
    # 模擬ニュース
    news_items = [
        {
            "title": "日経平均、3日続伸で取引終了",
            "time": "2時間前",
            "category": "市況",
            "summary": "本日の日経平均株価は前日比150円高の28,500円で取引を終了しました..."
        },
        {
            "title": "トヨタ自動車、来期業績予想を上方修正",
            "time": "4時間前", 
            "category": "個別銘柄",
            "summary": "トヨタ自動車は来期の業績予想を上方修正すると発表しました..."
        },
        {
            "title": "日銀、金融政策決定会合の結果を発表",
            "time": "1日前",
            "category": "金融政策",
            "summary": "日本銀行は金融政策決定会合において、現行の金融政策を維持することを決定..."
        }
    ]
    
    st.subheader("📈 最新のマーケットニュース")
    
    for news in news_items:
        with st.expander(f"[{news['category']}] {news['title']} - {news['time']}"):
            st.write(news['summary'])
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.button("詳細を読む", key=f"news_{news['title'][:10]}")
            with col2:
                st.info("📱 実際のニュースAPIとの連携は今後実装予定です")

def main():
    """メイン関数"""
    # ページ設定
    st.set_page_config(
        page_title="日本株データ分析アプリ",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # セッション状態の初期化
    init_session_state()
    
    # サイドバーナビゲーション
    with st.sidebar:
        st.title("📈 株式分析アプリ")
        st.markdown("---")
        
        # ナビゲーションメニュー
        pages = {
            "📊 ダッシュボード": "dashboard",
            "🔍 銘柄検索": "search",
            "📈 詳細分析": "analysis",
            "💼 ポートフォリオ": "portfolio",
            "📰 ニュース": "news"
        }
        
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "dashboard"
        
        for page_name, page_key in pages.items():
            if st.button(page_name, key=page_key, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # システム状態
        st.subheader("⚙️ システム状態")
        
        if YFINANCE_AVAILABLE:
            st.success("✅ データ取得")
        else:
            st.error("❌ データ取得")
        
        if PLOTLY_AVAILABLE:
            st.success("✅ チャート表示")
        else:
            st.error("❌ チャート表示")
        
        st.markdown("---")
        
        # クイック操作
        st.subheader("🚀 クイック操作")
        
        # ウォッチリスト管理
        with st.expander("👀 ウォッチリスト"):
            new_watch = st.text_input("銘柄追加", placeholder="7203.T")
            if st.button("追加", key="add_watch"):
                if new_watch and new_watch not in st.session_state.watchlist:
                    st.session_state.watchlist.append(new_watch)
                    st.success("追加しました")
            
            for i, symbol in enumerate(st.session_state.watchlist):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(symbol, key=f"watch_select_{i}"):
                        st.session_state.selected_symbol = symbol
                        st.session_state.current_page = "analysis"
                        st.rerun()
                with col2:
                    if st.button("❌", key=f"watch_remove_{i}"):
                        st.session_state.watchlist.remove(symbol)
                        st.rerun()
    
    # メインコンテンツ
    if st.session_state.current_page == "dashboard":
        show_dashboard()
    elif st.session_state.current_page == "search":
        show_stock_search()
    elif st.session_state.current_page == "analysis":
        show_analysis_page()
    elif st.session_state.current_page == "portfolio":
        show_portfolio_management()
    elif st.session_state.current_page == "news":
        show_news_page()
    
    # フッター
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        📈 日本株データ分析アプリ v2.0 | 
        データ提供: Yahoo Finance | 
        ⚠️ 投資は自己責任で行ってください
        </div>
        """, 
        unsafe_allow_html=True
    )

# エントリーポイント
if __name__ == "__main__":
    main()
else:
    main()
# Debug marker added
# Updated 08/07/2025 14:09:41
