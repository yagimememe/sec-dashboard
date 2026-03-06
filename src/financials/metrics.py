"""
財務指標の前年比（YoY）成長率を計算する。

【推測の明記】
成長率はデータから機械的に計算した数値であり、
将来の業績を示唆するものではない。
"""
import pandas as pd


def calculate_yoy_growth(df: pd.DataFrame) -> pd.DataFrame:
    """
    各カラムの前年比成長率（%）を計算する。

    Parameters
    ----------
    df : pd.DataFrame
        normalize 済みの財務 DataFrame（百万 USD）

    Returns
    -------
    pd.DataFrame
        同一インデックス、値は YoY 成長率（%）
        初年度は NaN
    """
    growth = df.pct_change() * 100
    return growth.round(1)


def latest_yoy(df: pd.DataFrame, df_growth: pd.DataFrame) -> dict[str, dict]:
    """
    最新年度の値と前年比をカラムごとに返す。

    Returns
    -------
    dict
        {column_name: {"value": float, "yoy": float | None}}
    """
    result: dict[str, dict] = {}
    if df.empty:
        return result

    latest_year = df.index[-1]
    for col in df.columns:
        value = df.loc[latest_year, col] if col in df.columns else None
        yoy = (
            df_growth.loc[latest_year, col]
            if (col in df_growth.columns and latest_year in df_growth.index)
            else None
        )
        result[col] = {"value": value, "yoy": yoy, "year": latest_year}
    return result


def cagr(df: pd.DataFrame) -> pd.Series:
    """
    期間全体の CAGR（年平均成長率）を計算する。

    【推測】CAGR は過去の数値から計算した参考値であり、
    将来の成長を保証するものではない。
    """
    if len(df) < 2:
        return pd.Series(dtype=float)

    n = len(df) - 1
    first = df.iloc[0]
    last = df.iloc[-1]

    # 損失（負値）の場合は CAGR が意味をなさないため NaN
    rates = {}
    for col in df.columns:
        f, l_ = first[col], last[col]
        if pd.isna(f) or pd.isna(l_) or f <= 0 or l_ <= 0:
            rates[col] = float("nan")
        else:
            rates[col] = round(((l_ / f) ** (1 / n) - 1) * 100, 1)

    return pd.Series(rates)
