"""
parse_financials で得た DataFrame を表示用に正規化する。
- 単位を百万ドル（M USD）に変換
- カラム名を日本語ラベルに対応付け
"""
import pandas as pd

# 内部カラム名 → 表示ラベルのマッピング
COLUMN_LABELS: dict[str, str] = {
    "revenue": "売上高",
    "operating_income": "営業利益",
    "net_income": "純利益",
    "operating_cashflow": "営業キャッシュフロー",
}

_USD_TO_M = 1_000_000  # 百万ドル換算


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """
    財務 DataFrame を百万 USD 単位に変換して返す。

    Parameters
    ----------
    df : pd.DataFrame
        xbrl_parser.parse_financials の戻り値（USD 原単位）

    Returns
    -------
    pd.DataFrame
        同一構造、値を百万 USD 単位に変換済み
    """
    return (df / _USD_TO_M).round(1)


def to_display_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    カラム名を日本語ラベルに変換した表示用 DataFrame を返す。
    存在しないカラムは無視する。
    """
    rename_map = {k: v for k, v in COLUMN_LABELS.items() if k in df.columns}
    result = df.rename(columns=rename_map)
    result.index.name = "会計年度"
    return result
