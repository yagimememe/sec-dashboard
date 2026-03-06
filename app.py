"""
SEC 10-K Financial Dashboard
=============================
- sec-edgar-downloader で 10-K 申告書をローカルに保存
- SEC EDGAR company-facts API（XBRL）から財務データを取得
- Streamlit でインタラクティブに表示

【免責事項】
このダッシュボードは SEC EDGAR の公開データを可視化するツールです。
投資の売買を推奨するものではありません。
表示されるすべての数値は SEC 申告書に基づく事実データですが、
分析・解釈の判断はご自身で行ってください。
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.edgar.downloader import download_10k_filings, list_accession_numbers
from src.edgar.finder import get_cik, get_company_name
from src.edgar.xbrl_parser import parse_financials
from src.financials.extractor import normalize, to_display_df
from src.financials.metrics import calculate_yoy_growth, cagr
from src.ui.charts import (
    cashflow_chart,
    income_summary_chart,
    margin_chart,
    yoy_growth_chart,
)
from src.ui.layout import render_cagr_table, render_data_table, render_metric_cards

NUM_YEARS = 5

st.set_page_config(
    page_title="SEC 10-K Dashboard",
    page_icon="📊",
    layout="wide",
)

# ── ヘッダー ──────────────────────────────────────────────────────────────────
st.title("📊 SEC 10-K Financial Dashboard")
st.caption(
    "出典: [SEC EDGAR](https://www.sec.gov/developer) — "
    "公開データの可視化ツールです。投資の推奨ではありません。"
)

# ── サイドバー ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("設定")
    ticker_input = st.text_input(
        "ティッカーシンボル",
        value="AAPL",
        max_chars=10,
        placeholder="例: AAPL, MSFT, GOOGL",
    ).strip().upper()

    num_years = st.slider("表示年数", min_value=2, max_value=10, value=NUM_YEARS)
    analyze_btn = st.button("分析を実行", type="primary", use_container_width=True)

    st.divider()
    st.caption(
        "データは SEC EDGAR の company-facts API（XBRL）から取得します。\n"
        "10-K 申告書のファイルは `data/` に保存されます。"
    )

# ── メイン処理 ────────────────────────────────────────────────────────────────
if not analyze_btn:
    st.info("左のサイドバーでティッカーを入力し、「分析を実行」を押してください。")
    st.stop()

ticker = ticker_input

with st.spinner(f"{ticker} の 10-K 申告書をダウンロード中..."):
    try:
        filing_dir = download_10k_filings(ticker, limit=num_years)
        accessions = list_accession_numbers(ticker)
    except Exception as e:
        st.error(f"10-K のダウンロードに失敗しました: {e}")
        st.stop()

with st.spinner("XBRL データを取得中..."):
    try:
        cik = get_cik(ticker)
        company_name = get_company_name(cik)
        df_raw = parse_financials(cik, num_years=num_years)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        st.stop()

if df_raw.empty:
    st.warning(
        f"{ticker} の財務データが見つかりませんでした。"
        "ティッカーシンボルを確認してください。"
    )
    st.stop()

# 正規化（百万 USD）
df = normalize(df_raw)
df_growth = calculate_yoy_growth(df)
df_cagr = cagr(df)

# ── 会社情報 ──────────────────────────────────────────────────────────────────
st.subheader(f"{company_name}（{ticker}）")
col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("CIK", cik.lstrip("0"))
col_info2.metric("取得した 10-K 数", len(accessions))
col_info3.metric(
    "データ期間",
    f"{int(df.index.min())} – {int(df.index.max())}",
)

st.divider()

# ── メトリクスカード ──────────────────────────────────────────────────────────
st.subheader("最新年度サマリー")
render_metric_cards(df, df_growth)

st.divider()

# ── グラフ ────────────────────────────────────────────────────────────────────
st.subheader("財務トレンド")

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(income_summary_chart(df), use_container_width=True)
with col2:
    st.plotly_chart(margin_chart(df), use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(cashflow_chart(df), use_container_width=True)
with col4:
    st.plotly_chart(yoy_growth_chart(df_growth), use_container_width=True)

st.divider()

# ── テーブル・CAGR ────────────────────────────────────────────────────────────
render_data_table(df, df_growth)
render_cagr_table(df_cagr, years=len(df) - 1)

# ── ダウンロード済みファイル一覧 ───────────────────────────────────────────────
with st.expander("ダウンロード済み 10-K 申告書（アクセッション番号）"):
    st.caption(f"保存先: `{filing_dir}`")
    if accessions:
        for acc in accessions:
            st.text(acc)
    else:
        st.text("（なし）")

# ── フッター ──────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "【免責事項】このツールは投資の売買を推奨しません。"
    "表示データは SEC EDGAR 公開情報に基づきますが、"
    "正確性を保証するものではありません。"
    "投資判断はご自身の責任で行ってください。"
)
