"""
Streamlit のレイアウト部品。
"""
import pandas as pd
import streamlit as st

from src.financials.extractor import COLUMN_LABELS
from src.financials.metrics import latest_yoy


def render_metric_cards(df: pd.DataFrame, df_growth: pd.DataFrame) -> None:
    """
    最新年度の4指標をメトリクスカードで表示する。
    """
    summary = latest_yoy(df, df_growth)
    if not summary:
        st.warning("表示可能なデータがありません。")
        return

    cols = st.columns(4)
    order = ["revenue", "operating_income", "net_income", "operating_cashflow"]

    for i, key in enumerate(order):
        if key not in summary:
            continue
        info = summary[key]
        value = info["value"]
        yoy = info["yoy"]
        year = info["year"]

        value_str = f"${value:,.0f}M" if pd.notna(value) else "N/A"
        delta_str = f"{yoy:+.1f}%" if pd.notna(yoy) else None

        with cols[i]:
            st.metric(
                label=f"{COLUMN_LABELS[key]}（{year}）",
                value=value_str,
                delta=delta_str,
            )


def render_data_table(df: pd.DataFrame, df_growth: pd.DataFrame) -> None:
    """
    財務数値と成長率を並べた表を折りたたみで表示する。
    """
    with st.expander("生データを表示（百万 USD）"):
        display = df.rename(columns=COLUMN_LABELS).copy()
        display.index.name = "会計年度"
        st.dataframe(display.style.format("{:,.1f}"), use_container_width=True)

    with st.expander("前年比成長率（%）"):
        growth_display = df_growth.rename(columns=COLUMN_LABELS).copy()
        growth_display.index.name = "会計年度"
        st.dataframe(
            growth_display.style.format("{:+.1f}%").highlight_between(
                left=0, right=float("inf"), color="#d4edda"
            ).highlight_between(
                left=float("-inf"), right=0, color="#f8d7da"
            ),
            use_container_width=True,
        )


def render_cagr_table(cagr: pd.Series, years: int) -> None:
    """
    CAGR テーブルを表示する。

    【推測】CAGR は過去データの計算値。将来の成長を示唆しない。
    """
    with st.expander(f"CAGR（過去 {years} 年間、推測）"):
        st.caption("※ CAGR は過去の数値から計算した参考値です。将来の業績を保証するものではありません。")
        cagr_df = cagr.rename(COLUMN_LABELS).to_frame(name="CAGR (%)").T
        st.dataframe(cagr_df.style.format("{:+.1f}%"), use_container_width=True)
