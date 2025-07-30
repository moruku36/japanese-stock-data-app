#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日本の株価データ取得・分析システム - WebUI版
Streamlitを使用したWebインターフェース
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import sys

# プロジェクトのモジュールをインポート
from stock_data_fetcher import JapaneseStockDataFetcher
from stock_analyzer import StockAnalyzer
from company_search import CompanySearch
from fundamental_analyzer import FundamentalAnalyzer
from config import config
from utils import format_currency, format_number

# ページ設定
st.set_page_config(
    page_title="🇯🇵 日本の株価データ分析システム",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def initialize_system():
    """システムの初期化（キャッシュ付き）"""
    try:
        fetcher = JapaneseStockDataFetcher()
        analyzer = StockAnalyzer(fetcher)
        company_searcher = CompanySearch()
        fundamental_analyzer = FundamentalAnalyzer(fetcher)
        return fetcher, analyzer, company_searcher, fundamental_analyzer
    except Exception as e:
        st.error(f"システムの初期化に失敗しました: {e}")
        return None, None, None, None

def format_currency_web(value):
    """通貨フォーマット（Web用）"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:,.0f}円"

def format_percentage(value):
    """パーセンテージフォーマット"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.1f}%"

def create_stock_price_chart(df, ticker_symbol):
    """株価チャートを作成"""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    # ローソク足チャート
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='株価',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ))
    
    # 移動平均線
    if len(df) >= 20:
        ma20 = df['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=ma20,
            mode='lines',
            name='20日移動平均',
            line=dict(color='orange', width=2)
        ))
    
    fig.update_layout(
        title=f'{ticker_symbol} 株価チャート',
        xaxis_title='日付',
        yaxis_title='株価 (円)',
        height=500,
        showlegend=True
    )
    
    return fig

def main():
    """メイン関数"""
    # ヘッダー
    st.title("🇯🇵 日本の株価データ分析システム")
    
    # システム初期化
    with st.spinner('システムを初期化中...'):
        fetcher, analyzer, company_searcher, fundamental_analyzer = initialize_system()
    
    if not all([fetcher, analyzer, company_searcher, fundamental_analyzer]):
        st.error("システムの初期化に失敗しました。")
        return
    
    # サイドバー
    st.sidebar.title("📊 機能選択")
    
    # 機能選択
    page = st.sidebar.selectbox(
        "機能を選択してください",
        [
            "🏠 ホーム",
            "📈 最新株価",
            "📊 株価チャート",
            "🏢 ファンダメンタル分析",
            "⚖️ 財務指標比較",
            "📦 複数銘柄分析",
            "💾 データエクスポート"
        ]
    )
    
    # ホームページ
    if page == "🏠 ホーム":
        st.markdown("## 🏠 ホーム")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📊 登録企業数", len(company_searcher.companies))
        
        with col2:
            st.metric("🏢 ファンダメンタル分析対応", len(fundamental_analyzer.financial_data))
        
        with col3:
            st.metric("🌐 データソース", 2)
        
        st.markdown("---")
        
        # 主要企業の一覧
        st.markdown("## ⭐ 主要企業")
        
        popular_companies = company_searcher.get_popular_companies(10)
        
        cols = st.columns(2)
        for i, company in enumerate(popular_companies):
            col_idx = i % 2
            with cols[col_idx]:
                with st.expander(f"{company['name']} ({company['code']})"):
                    st.write(f"**業種:** {company['sector']}")
                    st.write(f"**市場:** {company['market']}")
                    
                    # 最新株価を取得
                    try:
                        price_data = fetcher.get_latest_price(company['code'], "stooq")
                        if "error" not in price_data:
                            st.write(f"**現在値:** {format_currency_web(price_data['close'])}")
                            st.write(f"**日付:** {price_data['date']}")
                        else:
                            st.write("**現在値:** データ取得エラー")
                    except:
                        st.write("**現在値:** データ取得エラー")
    
    # 最新株価ページ
    elif page == "📈 最新株価":
        st.markdown("## 📈 最新株価取得")
        
        # 銘柄コード入力
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ticker_input = st.text_input("銘柄コードを入力してください", placeholder="例: 7203, 6758, 9984")
        
        with col2:
            source = st.selectbox("データソース", ["stooq", "yahoo", "both"])
        
        if st.button("📊 株価を取得", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}の株価を取得中..."):
                    try:
                        if source == "both":
                            stooq_data = fetcher.get_latest_price(ticker, "stooq")
                            yahoo_data = fetcher.get_latest_price(ticker, "yahoo")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("### 📊 stooq データ")
                                if "error" not in stooq_data:
                                    st.metric("終値", format_currency_web(stooq_data['close']))
                                    st.write(f"**日付:** {stooq_data['date']}")
                                    st.write(f"**出来高:** {format_number(stooq_data['volume'])}株")
                                else:
                                    st.error(f"エラー: {stooq_data['error']}")
                            
                            with col2:
                                st.markdown("### 📊 Yahoo Finance データ")
                                if "error" not in yahoo_data:
                                    st.metric("終値", format_currency_web(yahoo_data['close']))
                                    st.write(f"**日付:** {yahoo_data['date']}")
                                    st.write(f"**出来高:** {format_number(yahoo_data['volume'])}株")
                                else:
                                    st.warning(f"Yahoo Finance: {yahoo_data['error']}")
                        else:
                            data = fetcher.get_latest_price(ticker, source)
                            
                            if "error" not in data:
                                st.success("✅ データ取得成功!")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("終値", format_currency_web(data['close']))
                                with col2:
                                    st.metric("始値", format_currency_web(data['open']))
                                with col3:
                                    st.metric("高値", format_currency_web(data['high']))
                                with col4:
                                    st.metric("安値", format_currency_web(data['low']))
                                
                                st.write(f"**出来高:** {format_number(data['volume'])}株")
                                st.write(f"**日付:** {data['date']}")
                                st.write(f"**データソース:** {data['source']}")
                            else:
                                st.error(f"❌ エラー: {data['error']}")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
    
    # 株価チャートページ
    elif page == "📊 株価チャート":
        st.markdown("## 📊 株価チャート")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ticker_input = st.text_input("銘柄コード", placeholder="例: 7203")
        
        with col2:
            source = st.selectbox("データソース", ["stooq", "yahoo"])
        
        with col3:
            period = st.selectbox("期間", [7, 30, 90, 365], format_func=lambda x: f"{x}日間")
        
        if st.button("📈 チャートを表示", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}のチャートを生成中..."):
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=period)
                        
                        if source == "stooq":
                            df = fetcher.fetch_stock_data_stooq(
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d')
                            )
                        else:
                            df = fetcher.fetch_stock_data_yahoo(
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d')
                            )
                        
                        if not df.empty:
                            chart = create_stock_price_chart(df, ticker)
                            if chart:
                                st.plotly_chart(chart, use_container_width=True)
                            else:
                                st.warning("チャートの生成に失敗しました")
                        else:
                            st.error("データが見つかりませんでした")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
    
    # ファンダメンタル分析ページ
    elif page == "🏢 ファンダメンタル分析":
        st.markdown("## 🏢 ファンダメンタル分析")
        
        ticker_input = st.text_input("銘柄コードを入力してください", placeholder="例: 7203, 6758, 9984")
        
        if st.button("🏢 分析を実行", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}のファンダメンタル分析を実行中..."):
                    try:
                        financial_data = fundamental_analyzer.get_financial_data(ticker)
                        
                        if financial_data:
                            # 基本情報
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("企業名", financial_data['company_name'])
                            with col2:
                                st.metric("業種", financial_data['sector'])
                            with col3:
                                market_cap_trillion = financial_data['market_cap'] / 1000000000000
                                st.metric("時価総額", f"{market_cap_trillion:.1f}兆円")
                            with col4:
                                st.metric("ROE", format_percentage(financial_data['roe']))
                            
                            # 財務指標
                            st.markdown("### 📊 財務指標")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 💰 収益性")
                                st.write(f"**ROE (自己資本利益率):** {format_percentage(financial_data['roe'])}")
                                st.write(f"**ROA (総資産利益率):** {format_percentage(financial_data['roa'])}")
                                st.write(f"**P/E (株価収益率):** {financial_data['pe_ratio']:.1f}倍")
                                st.write(f"**P/B (株価純資産倍率):** {financial_data['pb_ratio']:.1f}倍")
                            
                            with col2:
                                st.markdown("#### 🏥 財務健全性")
                                st.write(f"**負債比率:** {financial_data['debt_to_equity']:.2f}")
                                st.write(f"**流動比率:** {financial_data['current_ratio']:.1f}")
                                st.write(f"**配当利回り:** {format_percentage(financial_data['dividend_yield'])}")
                                st.write(f"**ベータ値:** {financial_data['beta']:.1f}")
                        
                        else:
                            st.error(f"❌ {ticker}の財務データが見つかりません")
                            st.info("📋 利用可能な銘柄: 7203 (トヨタ自動車), 6758 (ソニーグループ), 9984 (ソフトバンクグループ), 6861 (キーエンス), 9434 (NTTドコモ), 4784 (GMOアドパートナーズ)")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
    
    # 財務指標比較ページ
    elif page == "⚖️ 財務指標比較":
        st.markdown("## ⚖️ 財務指標比較")
        
        st.info("📋 比較したい銘柄を選択してください（最大3銘柄）")
        
        # 利用可能な銘柄
        available_tickers = ["7203", "6758", "9984", "6861", "9434", "4784", "7974", "6954", "6594", "7733", "9983", "7269", "7267", "8058", "8001", "8306", "8316", "8411", "9432", "9433", "4502", "4519", "6501", "6502", "6752", "9201", "9202"]
        available_names = ["トヨタ自動車", "ソニーグループ", "ソフトバンクグループ", "キーエンス", "NTTドコモ", "GMOアドパートナーズ", "任天堂", "ファナック", "ニデック", "オリンパス", "ファーストリテイリング", "スズキ", "ホンダ", "三菱商事", "伊藤忠商事", "三菱UFJフィナンシャル・グループ", "三井住友フィナンシャルグループ", "みずほフィナンシャルグループ", "NTT", "KDDI", "武田薬品工業", "中外製薬", "日立製作所", "東芝", "パナソニック", "日本航空", "ANAホールディングス"]
        
        selected_tickers = []
        
        for i in range(3):
            col1, col2 = st.columns([3, 1])
            with col1:
                ticker = st.selectbox(
                    f"銘柄 {i+1}",
                    [""] + available_tickers,
                    format_func=lambda x: f"{x} ({available_names[available_tickers.index(x)]})" if x in available_tickers else x
                )
            with col2:
                if ticker and ticker not in selected_tickers:
                    selected_tickers.append(ticker)
        
        if st.button("⚖️ 比較を実行", type="primary"):
            if len(selected_tickers) >= 2:
                with st.spinner("財務指標を比較中..."):
                    try:
                        comparison_data = {}
                        
                        for ticker in selected_tickers:
                            financial_data = fundamental_analyzer.get_financial_data(ticker)
                            if financial_data:
                                comparison_data[ticker] = financial_data
                        
                        if len(comparison_data) >= 2:
                            # 比較チャート
                            st.markdown("### 📊 財務指標比較")
                            
                            # ROE比較
                            roe_data = [(ticker, comparison_data[ticker]['roe']) for ticker in comparison_data.keys()]
                            roe_df = pd.DataFrame(roe_data, columns=['銘柄', 'ROE'])
                            roe_df['企業名'] = [comparison_data[ticker]['company_name'] for ticker in roe_df['銘柄']]
                            
                            fig_roe = px.bar(
                                roe_df,
                                x='企業名',
                                y='ROE',
                                title='ROE比較 (%)',
                                color='ROE',
                                color_continuous_scale='RdYlGn'
                            )
                            st.plotly_chart(fig_roe, use_container_width=True)
                            
                            # 詳細比較表
                            st.markdown("### 📋 詳細比較表")
                            
                            comparison_table = []
                            for ticker in comparison_data.keys():
                                data = comparison_data[ticker]
                                comparison_table.append({
                                    '銘柄': ticker,
                                    '企業名': data['company_name'],
                                    '業種': data['sector'],
                                    'ROE (%)': f"{data['roe']:.1f}",
                                    'P/E (倍)': f"{data['pe_ratio']:.1f}",
                                    'P/B (倍)': f"{data['pb_ratio']:.1f}",
                                    '配当利回り (%)': f"{data['dividend_yield']:.1f}",
                                    '負債比率': f"{data['debt_to_equity']:.2f}"
                                })
                            
                            st.dataframe(pd.DataFrame(comparison_table), use_container_width=True)
                        
                        else:
                            st.error("比較可能な財務データが不足しています")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")
            else:
                st.warning("比較には最低2銘柄が必要です")
    
    # 複数銘柄分析ページ
    elif page == "📦 複数銘柄分析":
        st.markdown("## 📦 複数銘柄分析")
        
        st.info("📋 分析したい銘柄をカンマ区切りで入力してください")
        
        tickers_input = st.text_input("銘柄コード", placeholder="例: 7203, 6758, 9984")
        source = st.selectbox("データソース", ["stooq", "yahoo"])
        
        if st.button("📦 一括分析", type="primary"):
            if tickers_input:
                tickers = [t.strip() for t in tickers_input.split(",") if t.strip().isdigit()]
                
                if tickers:
                    with st.spinner(f"{len(tickers)}銘柄のデータを取得中..."):
                        results = []
                        
                        for ticker in tickers:
                            try:
                                data = fetcher.get_latest_price(ticker, source)
                                if "error" not in data:
                                    results.append({
                                        '銘柄': ticker,
                                        '終値': data['close'],
                                        '日付': data['date'],
                                        '出来高': data['volume']
                                    })
                                else:
                                    results.append({
                                        '銘柄': ticker,
                                        '終値': 'エラー',
                                        '日付': 'N/A',
                                        '出来高': 'N/A'
                                    })
                            except Exception as e:
                                results.append({
                                    '銘柄': ticker,
                                    '終値': f'エラー: {e}',
                                    '日付': 'N/A',
                                    '出来高': 'N/A'
                                })
                        
                        if results:
                            df_results = pd.DataFrame(results)
                            st.dataframe(df_results, use_container_width=True)
                else:
                    st.error("有効な銘柄コードが入力されていません")
    
    # データエクスポートページ
    elif page == "💾 データエクスポート":
        st.markdown("## 💾 データエクスポート")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ticker_input = st.text_input("銘柄コード", placeholder="例: 7203")
        
        with col2:
            source = st.selectbox("データソース", ["stooq", "yahoo"])
        
        with col3:
            period = st.selectbox("期間", [30, 90, 365], format_func=lambda x: f"{x}日間")
        
        if st.button("💾 CSVに保存", type="primary"):
            if ticker_input:
                ticker = ticker_input.strip()
                
                with st.spinner(f"{ticker}のデータをCSVに保存中..."):
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=period)
                        
                        if source == "stooq":
                            df = fetcher.fetch_stock_data_stooq(
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d')
                            )
                        else:
                            df = fetcher.fetch_stock_data_yahoo(
                                ticker,
                                start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d')
                            )
                        
                        if not df.empty:
                            fetcher.save_to_csv(df, ticker, source)
                            st.success(f"✅ データが保存されました: stock_data/{source}_stock_data_{ticker}.csv")
                            
                            # データのプレビュー
                            st.markdown("### 📊 データプレビュー")
                            st.dataframe(df.head(10), use_container_width=True)
                        else:
                            st.error("データが見つかりませんでした")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main() 