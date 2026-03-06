"""
SEC EDGAR の公開 API を使ってティッカー → CIK の変換と
申告書メタデータの取得を行う。
"""
import time
from functools import lru_cache

import requests

from src.config import EDGAR_COMPANY_NAME, EDGAR_EMAIL


def _headers() -> dict:
    return {
        "User-Agent": f"{EDGAR_COMPANY_NAME()} {EDGAR_EMAIL()}",
        "Accept-Encoding": "gzip, deflate",
    }

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


def _get(url: str) -> dict:
    """レート制限（10 req/s）を考慮したシンプルな GET ラッパー。"""
    time.sleep(0.1)
    resp = requests.get(url, headers=_headers(), timeout=15)
    resp.raise_for_status()
    return resp.json()


@lru_cache(maxsize=256)
def get_cik(ticker: str) -> str:
    """
    ティッカーシンボルから CIK（10 桁ゼロ埋め文字列）を返す。

    Raises
    ------
    ValueError
        ティッカーが見つからない場合
    """
    data = _get(_TICKERS_URL)
    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry["ticker"].upper() == ticker_upper:
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker '{ticker}' not found in SEC EDGAR.")


def get_company_name(cik: str) -> str:
    """CIK から会社名を取得する。"""
    data = _get(_SUBMISSIONS_URL.format(cik=cik))
    return data.get("name", "Unknown")
