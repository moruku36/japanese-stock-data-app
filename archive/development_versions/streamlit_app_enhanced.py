import streamlit as st
import pandas as pd
import numpy as np

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

def calculate_technical_indicators(df):
    """テクニカル指標を計算"""
    if df.empty:
        return df
    
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
            '時価総額': info.get('marketCap', 'N/A'),
            'PER': info.get('trailingPE', 'N/A'),
            'PBR': info.get('priceToBook', 'N/A'),
            'ROE': info.get('returnOnEquity', 'N/A'),
            'ROA': info.get('returnOnAssets', 'N/A'),
            '配当利回り': info.get('dividendYield', 'N/A'),
            '52週高値': info.get('fiftyTwoWeekHigh', 'N/A'),
            '52週安値': info.get('fiftyTwoWeekLow', 'N/A'),
            'Beta': info.get('beta', 'N/A'),
            '従業員数': info.get('fullTimeEmployees', 'N/A')
        }
        
        return fundamental_data
    except Exception as e:
        st.error(f"ファンダメンタルデータ取得エラー: {str(e)}")
        return None

def show_technical_chart(df, symbol):
    """テクニカル分析チャートを表示"""
    if not PLOTLY_AVAILABLE or df.empty:
        return
    
    # サブプロットを作成
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('価格・移動平均', 'ボリンジャーバンド', 'RSI', 'MACD'),
        row_heights=[0.5, 0.2, 0.15, 0.15]
    )
    
    # 1. 価格チャートと移動平均
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='価格'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA5'],
        mode='lines', name='MA5',
        line=dict(color='red', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA25'],
        mode='lines', name='MA25',
        line=dict(color='blue', width=1)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MA75'],
        mode='lines', name='MA75',
        line=dict(color='green', width=1)
    ), row=1, col=1)
    
    # 2. ボリンジャーバンド
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines', name='終値',
        line=dict(color='black')
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BB_Upper'],
        mode='lines', name='BB上限',
        line=dict(color='red', dash='dash')
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BB_Middle'],
        mode='lines', name='BB中央',
        line=dict(color='blue')
    ), row=2, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['BB_Lower'],
        mode='lines', name='BB下限',
        line=dict(color='red', dash='dash')
    ), row=2, col=1)
    
    # 3. RSI
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'],
        mode='lines', name='RSI',
        line=dict(color='purple')
    ), row=3, col=1)
    
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="blue", row=3, col=1)
    
    # 4. MACD
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MACD'],
        mode='lines', name='MACD',
        line=dict(color='blue')
    ), row=4, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MACD_Signal'],
        mode='lines', name='Signal',
        line=dict(color='red')
    ), row=4, col=1)
    
    fig.add_trace(go.Bar(
        x=df.index, y=df['MACD_Histogram'],
        name='Histogram',
        marker_color='gray'
    ), row=4, col=1)
    
    fig.update_layout(
        title=f"{symbol} - テクニカル分析",
        height=800,
        showlegend=False,
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analyze_signals(df):
    """シグナル分析"""
    if df.empty:
        return []
    
    latest = df.iloc[-1]
    signals = []
    
    # 移動平均のシグナル
    if not pd.isna(latest['MA5']) and not pd.isna(latest['MA25']):
        if latest['MA5'] > latest['MA25']:
            signals.append("✅ 短期移動平均が中期移動平均を上回る（買いシグナル）")
        else:
            signals.append("❌ 短期移動平均が中期移動平均を下回る（売りシグナル）")
    
    # RSIのシグナル
    if not pd.isna(latest['RSI']):
        if latest['RSI'] > 70:
            signals.append("⚠️ RSI買われすぎ圏（売り検討）")
        elif latest['RSI'] < 30:
            signals.append("⚠️ RSI売られすぎ圏（買い検討）")
        else:
            signals.append("📊 RSI中立圏")
    
    # ボリンジャーバンドのシグナル
    if (not pd.isna(latest['BB_Upper']) and 
        not pd.isna(latest['BB_Lower']) and
        not pd.isna(latest['Close'])):
        
        if latest['Close'] > latest['BB_Upper']:
            signals.append("⚠️ ボリンジャーバンド上限突破（売り検討）")
        elif latest['Close'] < latest['BB_Lower']:
            signals.append("⚠️ ボリンジャーバンド下限突破（買い検討）")
        else:
            signals.append("📊 ボリンジャーバンド範囲内")
    
    # MACDのシグナル
    if not pd.isna(latest['MACD']) and not pd.isna(latest['MACD_Signal']):
        if latest['MACD'] > latest['MACD_Signal']:
            signals.append("✅ MACD買いシグナル")
        else:
            signals.append("❌ MACD売りシグナル")
    
    return signals

def main():
    """メイン関数 - Streamlit Cloud対応"""
    # ページ設定
    st.set_page_config(
        page_title="日本株データ分析",
        page_icon="📈",
        layout="wide"
    )
    
    # タイトル
    st.title("📈 日本株データ分析アプリ - 機能強化版")
    st.markdown("---")
    
    # システム状態表示
    st.subheader("📋 システム状態")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if YFINANCE_AVAILABLE:
            st.success("✅ yfinance 利用可能")
        else:
            st.error("❌ yfinance 利用不可")
    
    with col2:
        if PLOTLY_AVAILABLE:
            st.success("✅ plotly 利用可能")
        else:
            st.error("❌ plotly 利用不可")
    
    with col3:
        st.success("✅ streamlit 動作中")
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")
        
        symbol = st.text_input("銘柄コード", value="7203.T", help="例: 7203.T (トヨタ)")
        period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
        
        analysis_type = st.selectbox(
            "分析タイプ",
            ["基本情報", "テクニカル分析", "ファンダメンタル分析", "総合分析"]
        )
        
        if st.button("データ取得", type="primary"):
            if symbol and YFINANCE_AVAILABLE:
                with st.spinner("データを取得中..."):
                    try:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period=period)
                        
                        if not hist.empty:
                            # テクニカル指標を計算
                            hist_with_indicators = calculate_technical_indicators(hist.copy())
                            
                            st.session_state.stock_data = hist_with_indicators
                            st.session_state.selected_symbol = symbol
                            st.session_state.analysis_type = analysis_type
                            st.success("✅ データ取得完了！")
                            st.rerun()
                        else:
                            st.error("❌ データが見つかりませんでした")
                    except Exception as e:
                        st.error(f"❌ エラー: {str(e)}")
            else:
                st.error("❌ 銘柄コードを入力してください")
    
    # メインコンテンツ
    if hasattr(st.session_state, 'stock_data') and st.session_state.stock_data is not None:
        df = st.session_state.stock_data
        symbol = st.session_state.selected_symbol
        analysis_type = getattr(st.session_state, 'analysis_type', '基本情報')
        
        # 基本情報表示
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
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
        
        st.markdown("---")
        
        # 分析タイプに応じた表示
        if analysis_type == "基本情報":
            # 基本的な価格チャート
            if PLOTLY_AVAILABLE:
                fig = go.Figure(data=go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close']
                ))
                
                fig.update_layout(
                    title=f"{symbol} - 株価チャート",
                    yaxis_title="価格 (¥)",
                    height=500,
                    xaxis_rangeslider_visible=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # データテーブル
            with st.expander("📋 最新データ（10日分）"):
                st.dataframe(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10))
        
        elif analysis_type == "テクニカル分析":
            st.subheader("📊 テクニカル分析")
            
            # テクニカル分析チャート
            show_technical_chart(df, symbol)
            
            # シグナル分析
            st.subheader("🎯 シグナル分析")
            signals = analyze_signals(df)
            for signal in signals:
                st.write(signal)
            
            # テクニカル指標の数値
            with st.expander("📈 テクニカル指標（最新値）"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if not pd.isna(latest['RSI']):
                        st.metric("RSI", f"{latest['RSI']:.1f}")
                    if not pd.isna(latest['MA5']):
                        st.metric("MA5", f"¥{latest['MA5']:.0f}")
                
                with col2:
                    if not pd.isna(latest['MA25']):
                        st.metric("MA25", f"¥{latest['MA25']:.0f}")
                    if not pd.isna(latest['MA75']):
                        st.metric("MA75", f"¥{latest['MA75']:.0f}")
                
                with col3:
                    if not pd.isna(latest['BB_Upper']):
                        st.metric("BB上限", f"¥{latest['BB_Upper']:.0f}")
                    if not pd.isna(latest['BB_Lower']):
                        st.metric("BB下限", f"¥{latest['BB_Lower']:.0f}")
                
                with col4:
                    if not pd.isna(latest['MACD']):
                        st.metric("MACD", f"{latest['MACD']:.3f}")
                    if not pd.isna(latest['MACD_Signal']):
                        st.metric("MACD Signal", f"{latest['MACD_Signal']:.3f}")
        
        elif analysis_type == "ファンダメンタル分析":
            st.subheader("📊 ファンダメンタル分析")
            
            # ファンダメンタルデータ取得
            fundamental_data = get_fundamental_data(symbol)
            
            if fundamental_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🏢 企業情報")
                    st.write(f"**企業名**: {fundamental_data['企業名']}")
                    st.write(f"**業種**: {fundamental_data['業種']}")
                    if fundamental_data['従業員数'] != 'N/A':
                        st.write(f"**従業員数**: {fundamental_data['従業員数']:,}人")
                    
                    st.subheader("💰 財務指標")
                    if fundamental_data['時価総額'] != 'N/A':
                        market_cap = fundamental_data['時価総額'] / 1000000000  # 億円に変換
                        st.metric("時価総額", f"{market_cap:.0f}億円")
                    
                    if fundamental_data['PER'] != 'N/A':
                        st.metric("PER", f"{fundamental_data['PER']:.2f}")
                    
                    if fundamental_data['PBR'] != 'N/A':
                        st.metric("PBR", f"{fundamental_data['PBR']:.2f}")
                
                with col2:
                    st.subheader("📈 収益性指標")
                    if fundamental_data['ROE'] != 'N/A':
                        st.metric("ROE", f"{fundamental_data['ROE']*100:.1f}%")
                    
                    if fundamental_data['ROA'] != 'N/A':
                        st.metric("ROA", f"{fundamental_data['ROA']*100:.1f}%")
                    
                    if fundamental_data['配当利回り'] != 'N/A':
                        st.metric("配当利回り", f"{fundamental_data['配当利回り']*100:.2f}%")
                    
                    st.subheader("📊 株価レンジ")
                    if fundamental_data['52週高値'] != 'N/A':
                        st.metric("52週高値", f"¥{fundamental_data['52週高値']:.0f}")
                    
                    if fundamental_data['52週安値'] != 'N/A':
                        st.metric("52週安値", f"¥{fundamental_data['52週安値']:.0f}")
                    
                    if fundamental_data['Beta'] != 'N/A':
                        st.metric("Beta", f"{fundamental_data['Beta']:.2f}")
            else:
                st.error("ファンダメンタルデータの取得に失敗しました")
        
        elif analysis_type == "総合分析":
            st.subheader("🎯 総合分析")
            
            # タブで表示を分割
            tab1, tab2, tab3 = st.tabs(["📊 価格動向", "📈 テクニカル", "📋 ファンダメンタル"])
            
            with tab1:
                if PLOTLY_AVAILABLE:
                    fig = go.Figure(data=go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close']
                    ))
                    
                    # 移動平均を追加
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['MA25'],
                        mode='lines', name='MA25',
                        line=dict(color='blue', width=2)
                    ))
                    
                    fig.update_layout(
                        title=f"{symbol} - 株価チャート（移動平均付き）",
                        yaxis_title="価格 (¥)",
                        height=500,
                        xaxis_rangeslider_visible=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                # シグナル分析
                signals = analyze_signals(df)
                for signal in signals:
                    st.write(signal)
                
                # 主要指標
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if not pd.isna(latest['RSI']):
                        st.metric("RSI", f"{latest['RSI']:.1f}")
                
                with col2:
                    if not pd.isna(latest['MACD']):
                        st.metric("MACD", f"{latest['MACD']:.3f}")
                
                with col3:
                    # ボリンジャーバンド位置
                    if (not pd.isna(latest['BB_Upper']) and 
                        not pd.isna(latest['BB_Lower']) and
                        not pd.isna(latest['Close'])):
                        bb_position = (latest['Close'] - latest['BB_Lower']) / (latest['BB_Upper'] - latest['BB_Lower']) * 100
                        st.metric("BB位置", f"{bb_position:.0f}%")
            
            with tab3:
                fundamental_data = get_fundamental_data(symbol)
                if fundamental_data:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if fundamental_data['PER'] != 'N/A':
                            st.metric("PER", f"{fundamental_data['PER']:.2f}")
                        if fundamental_data['PBR'] != 'N/A':
                            st.metric("PBR", f"{fundamental_data['PBR']:.2f}")
                    
                    with col2:
                        if fundamental_data['ROE'] != 'N/A':
                            st.metric("ROE", f"{fundamental_data['ROE']*100:.1f}%")
                        if fundamental_data['配当利回り'] != 'N/A':
                            st.metric("配当利回り", f"{fundamental_data['配当利回り']*100:.2f}%")
    
    else:
        st.info("👈 サイドバーから銘柄を選択してデータを取得してください")
        
        # クイックアクセス
        st.subheader("🚀 クイックアクセス")
        if YFINANCE_AVAILABLE:
            col1, col2, col3, col4 = st.columns(4)
            
            sample_stocks = [
                {"code": "7203.T", "name": "🚗 トヨタ自動車"},
                {"code": "9984.T", "name": "📱 ソフトバンクG"},
                {"code": "6758.T", "name": "🎮 ソニーグループ"},
                {"code": "7974.T", "name": "🎯 任天堂"}
            ]
            
            for i, stock in enumerate(sample_stocks):
                with [col1, col2, col3, col4][i]:
                    if st.button(f"{stock['name']}\n({stock['code']})"):
                        with st.spinner("データを取得中..."):
                            try:
                                ticker = yf.Ticker(stock['code'])
                                hist = ticker.history(period="1y")
                                if not hist.empty:
                                    hist_with_indicators = calculate_technical_indicators(hist.copy())
                                    st.session_state.stock_data = hist_with_indicators
                                    st.session_state.selected_symbol = stock['code']
                                    st.session_state.analysis_type = "基本情報"
                                    st.rerun()
                            except Exception as e:
                                st.error(f"データ取得エラー: {str(e)}")
    
    st.markdown("---")
    st.info("💡 サイドバーで分析タイプを選択して、詳細な分析を表示できます")

# Streamlit Cloud対応のエントリーポイント
if __name__ == "__main__":
    main()
else:
    # Streamlit Cloudで実行される場合
    main()
