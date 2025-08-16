#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
銘柄スクリーニング UI（Streamlit）
"""

import streamlit as st
import pandas as pd

from analysis.screener import StockScreener, ScreenerCriteria


def render_screener_page():
    st.markdown("## 🔎 銘柄スクリーニング")

    if 'screener' not in st.session_state:
        st.session_state.screener = StockScreener()
    screener: StockScreener = st.session_state.screener

    with st.expander("検索条件", expanded=True):
        sectors = screener.list_sectors()
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_sectors = st.multiselect("業種", options=sectors, default=[])
            pe_min, pe_max = st.slider("PER 範囲", 0.0, 100.0, (0.0, 30.0))
            pb_min, pb_max = st.slider("PBR 範囲", 0.0, 20.0, (0.0, 5.0))
        with col2:
            roe_min = st.slider("ROE 最小(%)", 0.0, 40.0, 8.0)
            dy_min = st.slider("配当利回り 最小(%)", 0.0, 10.0, 2.0)
            dte_max = st.slider("D/E 最大", 0.0, 3.0, 1.5)
        with col3:
            cr_min = st.slider("流動比率 最小", 0.0, 5.0, 1.0)
            mcap_min = st.number_input("時価総額 最小(兆円)", min_value=0.0, value=0.0, step=0.1)
            mcap_max = st.number_input("時価総額 最大(兆円)", min_value=0.0, value=100.0, step=0.1)

        col4, col5 = st.columns(2)
        with col4:
            pe_ntm_min, pe_ntm_max = st.slider("NTM PER 範囲", 0.0, 100.0, (0.0, 30.0))
            sort_by = st.selectbox("並び替え", [
                "roe", "dividend_yield", "pe_ratio", "pb_ratio", "market_cap", "pe_ratio_ntm", "upside"
            ], index=0)
        with col5:
            sort_asc = st.toggle("昇順でソート", value=False)
            compute_upside = st.toggle("ターゲットプライスの上昇余地(%)を計算", value=False,
                                      help="最新株価取得を伴うため多少時間がかかります")
            limit = st.number_input("表示件数", min_value=10, max_value=500, value=100, step=10)

    if st.button("スクリーニングを実行", type="primary"):
        criteria = ScreenerCriteria(
            sectors=selected_sectors or None,
            pe_range=(float(pe_min), float(pe_max)),
            pb_range=(float(pb_min), float(pb_max)),
            roe_min=float(roe_min),
            dividend_yield_min=float(dy_min),
            market_cap_min=float(mcap_min) * 1e12,
            market_cap_max=float(mcap_max) * 1e12,
            debt_to_equity_max=float(dte_max),
            current_ratio_min=float(cr_min),
            pe_ntm_range=(float(pe_ntm_min), float(pe_ntm_max)),
            sort_by=sort_by,
            sort_ascending=bool(sort_asc),
            limit=int(limit),
            compute_upside_to_target=bool(compute_upside),
        )

        df = screener.screen(criteria)
        if df is None or df.empty:
            st.warning("条件に合致する銘柄が見つかりませんでした。条件を緩めて再実行してください。")
        else:
            # 表示整形
            display_df = df.copy()
            if "market_cap" in display_df.columns:
                display_df["market_cap(兆円)"] = (display_df["market_cap"] / 1e12).round(2)
            cols_order = [
                "ticker", "company_name", "sector", "market_cap(兆円)",
                "pe_ratio", "pe_ratio_ntm", "pb_ratio", "roe", "dividend_yield",
                "debt_to_equity", "current_ratio"
            ]
            if "upside" in display_df.columns:
                display_df["upside(%)"] = display_df["upside"].round(1)
                cols_order.append("upside(%)")
            show_cols = [c for c in cols_order if c in display_df.columns]
            st.dataframe(display_df[show_cols], use_container_width=True, hide_index=True)


