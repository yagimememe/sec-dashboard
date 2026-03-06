"""
Plotly を使ったグラフコンポーネント。
各関数は plotly.graph_objects.Figure を返す。
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.financials.extractor import COLUMN_LABELS

_COLORS = {
    "revenue": "#4C9BE8",
    "operating_income": "#56C77A",
    "net_income": "#F5A623",
    "operating_cashflow": "#9B59B6",
}

_METRIC_ORDER = ["revenue", "operating_income", "net_income", "operating_cashflow"]


def income_summary_chart(df: pd.DataFrame) -> go.Figure:
    """
    売上高・営業利益・純利益を1つのグループ棒グラフで表示する。
    """
    fig = go.Figure()
    for col in ["revenue", "operating_income", "net_income"]:
        if col not in df.columns:
            continue
        fig.add_trace(
            go.Bar(
                name=COLUMN_LABELS[col],
                x=df.index.astype(str),
                y=df[col],
                marker_color=_COLORS[col],
                text=df[col].apply(lambda v: f"{v:,.0f}" if pd.notna(v) else "N/A"),
                textposition="outside",
                textfont_size=11,
            )
        )
    fig.update_layout(
        title="損益サマリー（百万 USD）",
        barmode="group",
        xaxis_title="会計年度",
        yaxis_title="百万 USD",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
        margin=dict(t=80),
    )
    return fig


def cashflow_chart(df: pd.DataFrame) -> go.Figure:
    """
    営業キャッシュフローの棒グラフ。
    """
    if "operating_cashflow" not in df.columns:
        return go.Figure()

    colors = [
        _COLORS["operating_cashflow"] if v >= 0 else "#E74C3C"
        for v in df["operating_cashflow"].fillna(0)
    ]
    fig = go.Figure(
        go.Bar(
            x=df.index.astype(str),
            y=df["operating_cashflow"],
            marker_color=colors,
            text=df["operating_cashflow"].apply(
                lambda v: f"{v:,.0f}" if pd.notna(v) else "N/A"
            ),
            textposition="outside",
            textfont_size=11,
        )
    )
    fig.update_layout(
        title="営業キャッシュフロー（百万 USD）",
        xaxis_title="会計年度",
        yaxis_title="百万 USD",
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
        margin=dict(t=80),
    )
    return fig


def yoy_growth_chart(df_growth: pd.DataFrame) -> go.Figure:
    """
    前年比成長率の折れ線グラフ（全指標を1チャートに重ねる）。
    """
    fig = go.Figure()
    for col in _METRIC_ORDER:
        if col not in df_growth.columns:
            continue
        series = df_growth[col].dropna()
        if series.empty:
            continue
        fig.add_trace(
            go.Scatter(
                name=COLUMN_LABELS[col],
                x=series.index.astype(str),
                y=series.values,
                mode="lines+markers+text",
                line=dict(color=_COLORS[col], width=2),
                marker=dict(size=7),
                text=series.apply(lambda v: f"{v:+.1f}%"),
                textposition="top center",
                textfont_size=10,
            )
        )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        title="前年比（YoY）成長率（%）",
        xaxis_title="会計年度",
        yaxis_title="成長率 (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0", zeroline=False),
        margin=dict(t=80),
    )
    return fig


def margin_chart(df: pd.DataFrame) -> go.Figure:
    """
    営業利益率・純利益率の折れ線グラフ。
    """
    if "revenue" not in df.columns:
        return go.Figure()

    fig = go.Figure()
    margin_defs = [
        ("operating_income", "営業利益率", "#56C77A"),
        ("net_income", "純利益率", "#F5A623"),
    ]
    for col, label, color in margin_defs:
        if col not in df.columns:
            continue
        margin = (df[col] / df["revenue"] * 100).round(1)
        fig.add_trace(
            go.Scatter(
                name=label,
                x=margin.index.astype(str),
                y=margin.values,
                mode="lines+markers+text",
                line=dict(color=color, width=2),
                marker=dict(size=7),
                text=margin.apply(lambda v: f"{v:.1f}%" if pd.notna(v) else ""),
                textposition="top center",
                textfont_size=10,
            )
        )
    fig.update_layout(
        title="利益率（%）",
        xaxis_title="会計年度",
        yaxis_title="%",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="#f0f0f0"),
        margin=dict(t=80),
    )
    return fig
