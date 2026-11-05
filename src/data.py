import pandas as pd
import yfinance as yf


def get_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch daily OHLCV price data for a ticker (e.g. 'TCS.NS')."""
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data found for ticker '{ticker}'")
    # yfinance can return multi-level columns; flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df
