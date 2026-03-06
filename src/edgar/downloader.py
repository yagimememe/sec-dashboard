"""
sec-edgar-downloader を使って 10-K 申告書をローカルに保存する。
保存先: data/sec-edgar-filings/{ticker}/10-K/{accession-number}/
"""
from pathlib import Path

from dotenv import load_dotenv
from sec_edgar_downloader import Downloader

from src.config import EDGAR_COMPANY_NAME, EDGAR_EMAIL

load_dotenv()

_BASE_DIR = Path(__file__).resolve().parents[2] / "data"


def download_10k_filings(ticker: str, limit: int = 5) -> Path:
    """
    指定ティッカーの 10-K を最大 limit 件ダウンロードする。

    Parameters
    ----------
    ticker : str
        例: "AAPL", "MSFT"
    limit : int
        取得する最大件数（直近から降順）

    Returns
    -------
    Path
        ダウンロード先ディレクトリ
        data/sec-edgar-filings/{ticker}/10-K/
    """
    dl = Downloader(EDGAR_COMPANY_NAME(), EDGAR_EMAIL(), _BASE_DIR)
    dl.get("10-K", ticker.upper(), limit=limit)

    filing_dir = _BASE_DIR / "sec-edgar-filings" / ticker.upper() / "10-K"
    return filing_dir


def list_accession_numbers(ticker: str) -> list[str]:
    """
    ローカルに保存済みの 10-K のアクセッション番号を返す（新しい順）。
    ディレクトリが存在しない場合は空リスト。
    """
    filing_dir = _BASE_DIR / "sec-edgar-filings" / ticker.upper() / "10-K"
    if not filing_dir.exists():
        return []
    accessions = sorted(
        [d.name for d in filing_dir.iterdir() if d.is_dir()],
        reverse=True,
    )
    return accessions
