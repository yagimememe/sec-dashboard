"""
SEC EDGAR の company-facts API（XBRL JSON）から財務データを取得・解析する。

エンドポイント: https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json

company-facts は XBRL タクソノミに基づく構造化データを返す。
us-gaap 名前空間から各財務指標を抽出し、10-K（通期）のみをフィルタする。

【事実（Fact）】
- データソース: SEC EDGAR company-facts API
  https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany
- 各数値の accession number（出典）は戻り値 DataFrame の "accn" 列に含まれる
"""
import time
from datetime import date
from functools import lru_cache

import pandas as pd
import requests

from src.config import EDGAR_COMPANY_NAME, EDGAR_EMAIL


def _headers() -> dict:
    return {"User-Agent": f"{EDGAR_COMPANY_NAME()} {EDGAR_EMAIL()}"}
_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# 各財務指標に対応する us-gaap コンセプト名（優先順に列挙）
# 企業によって使用するタグが異なるためフォールバックが必要
_CONCEPT_CANDIDATES: dict[str, list[str]] = {
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "RevenuesNetOfInterestExpense",          # 銀行・金融機関
        "InterestAndDividendIncomeOperating",    # 銀行（最終フォールバック）
    ],
    "operating_income": [
        "OperatingIncomeLoss",
    ],
    "net_income": [
        "NetIncomeLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    "operating_cashflow": [
        "NetCashProvidedByUsedInOperatingActivities",
    ],
}


@lru_cache(maxsize=64)
def fetch_company_facts(cik: str) -> dict:
    """
    CIK に対応する company-facts JSON を取得してキャッシュする。
    （同一セッション内での重複取得を防ぐ）

    Parameters
    ----------
    cik : str
        10 桁ゼロ埋め CIK 文字列

    Returns
    -------
    dict
        company-facts JSON レスポンス全体
    """
    time.sleep(0.1)  # レート制限対策
    url = _FACTS_URL.format(cik=cik)
    resp = requests.get(url, headers=_headers(), timeout=20)
    resp.raise_for_status()
    return resp.json()


def _extract_annual_series(
    facts: dict,
    metric_key: str,
    num_years: int = 5,
) -> pd.Series:
    """
    company-facts から指定指標の通期（FY / 10-K）時系列を抽出する。

    全コンセプトのデータを統合して返す。
    優先順位: リスト先頭コンセプトを優先し、不足年をフォールバックで補う。

    Returns
    -------
    pd.Series
        index = 会計年度（int）、値 = 金額（USD）
        直近 num_years 年分のみ返す
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})

    # 全コンセプトのデータを統合する。
    # 背景: 企業は会計基準変更でタグ名を変えることがある
    #       (例: AAPL は FY2019 に Revenues → RevenueFromContractWith... へ移行)。
    #       最初に見つかったコンセプトで即リターンすると最新年が欠落する。
    all_by_year: dict[int, dict] = {}

    for concept in _CONCEPT_CANDIDATES[metric_key]:
        concept_data = us_gaap.get(concept)
        if not concept_data:
            continue

        entries = concept_data.get("units", {}).get("USD", [])
        # 通期（fp == "FY"）かつ 10-K フォームのみ
        annual = [e for e in entries if e.get("fp") == "FY" and e.get("form") == "10-K"]
        if not annual:
            continue

        # 期間が約12ヶ月（300〜400日）のエントリのみ残す。
        # start がない場合はそのまま通す（古い申告書への対応）。
        # 背景: 10-K には当期＋比較期間の複数エントリが含まれ、
        #       全て同じ `fy`（申告年度）でタグ付けされる。
        #       期間フィルタで四半期・半期データを除外する。
        filtered = []
        for e in annual:
            start_str = e.get("start")
            end_str = e.get("end")
            if start_str and end_str:
                d1 = date.fromisoformat(start_str)
                d2 = date.fromisoformat(end_str)
                days = (d2 - d1).days
                if 300 <= days <= 400:
                    filtered.append(e)
            else:
                filtered.append(e)

        if not filtered:
            continue

        # 同一 fy では end 日付が最新のエントリを採用する。
        # 理由: `fy` は「その 10-K を提出した会計年度」であり、
        #       1つの 10-K が複数年の比較データを同じ fy でタグ付けする。
        #       end 日付が最新 = 当該 fy の当期データ（比較数値ではない）。
        by_year: dict[int, dict] = {}
        for e in filtered:
            fy = e.get("fy")
            if fy and (fy not in by_year or e.get("end", "") > by_year[fy].get("end", "")):
                by_year[fy] = e

        # ギャップ補完: 上位コンセプトで既に埋まっている年はスキップ
        for fy, e in by_year.items():
            if fy not in all_by_year:
                all_by_year[fy] = e

    if not all_by_year:
        return pd.Series(dtype=float)

    return (
        pd.Series({fy: e["val"] for fy, e in all_by_year.items()})
        .sort_index()
        .tail(num_years)
    )


def parse_financials(cik: str, num_years: int = 5) -> pd.DataFrame:
    """
    CIK に対応する財務データを DataFrame として返す。

    Columns
    -------
    revenue, operating_income, net_income, operating_cashflow
        単位: USD（そのまま）

    Index
    -----
    会計年度（int）

    【事実（Fact）】
    - 出典: SEC EDGAR company-facts API（CIK={cik}）
    - 各数値は 10-K 申告書に基づく XBRL データ
    """
    facts = fetch_company_facts(cik)

    data = {
        key: _extract_annual_series(facts, key, num_years)
        for key in _CONCEPT_CANDIDATES
    }

    df = pd.DataFrame(data)
    df.index.name = "fiscal_year"
    return df.dropna(how="all")
