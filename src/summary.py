import pandas as pd

from src.data import get_price_history
from src.indicators import macd, rsi, sma


def _num(x):
    """Round a number, or return None if it is missing."""
    return None if pd.isna(x) else round(float(x), 2)


def summarize(df: pd.DataFrame, ticker: str) -> dict:
    """Build a summary dict from a price DataFrame (no network needed)."""
    close = df["Close"]
    macd_df = macd(close)
    return {
        "ticker": ticker,
        "last_close": _num(close.iloc[-1]),
        "change_1d_pct": _num((close.iloc[-1] / close.iloc[-2] - 1) * 100),
        "high_52w": _num(df["High"].max()),
        "low_52w": _num(df["Low"].min()),
        "rsi_14": _num(rsi(close).iloc[-1]),
        "sma_50": _num(sma(close, 50).iloc[-1]),
        "sma_200": _num(sma(close, 200).iloc[-1]),
        "macd": _num(macd_df["macd"].iloc[-1]),
        "macd_signal": _num(macd_df["signal"].iloc[-1]),
    }


def get_stock_summary(ticker: str) -> dict:
    """Fetch one year of data and return a summary for the ticker."""
    return summarize(get_price_history(ticker, period="1y"), ticker)
