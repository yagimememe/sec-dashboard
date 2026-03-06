"""
設定値の取得ヘルパー。

優先順位:
1. Streamlit Secrets（クラウドデプロイ時）
2. 環境変数 / .env ファイル（ローカル開発時）
3. デフォルト値
"""
import os


def get_secret(key: str, default: str = "") -> str:
    """
    Streamlit Secrets → 環境変数 の順で設定値を取得する。
    streamlit が利用できない環境（テスト等）でも動作する。
    """
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(key, default)


EDGAR_COMPANY_NAME = lambda: get_secret("EDGAR_COMPANY_NAME", "FinancialDashboard")
EDGAR_EMAIL = lambda: get_secret("EDGAR_EMAIL", "user@example.com")
