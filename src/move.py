from datetime import date, timedelta
from functools import lru_cache
from urllib.parse import quote_plus

import feedparser
import pandas as pd
import yfinance as yf

from src.news import clean_headlines, get_company_name, ticker_to_query

ALIGN_RATIO = 0.5

_INDIA_SECTOR_INDEX = {
    "Technology": "^CNXIT",
    "Financial Services": "^NSEBANK",
    "Healthcare": "^CNXPHARMA",
    "Consumer Defensive": "^CNXFMCG",
}

_US_SECTOR_ETF = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Energy": "XLE",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Basic Materials": "XLB",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}


def benchmark_for(ticker: str) -> str | None:
    """Pick a market index to compare against, based on the ticker."""
    t = ticker.upper()
    if t.endswith((".NS", ".BO")):
        return "^NSEI"
    if "." not in t:
        return "^GSPC"
    return None


def sector_index_for(ticker: str, sector: str | None) -> str | None:
    """Pick a sector index or ETF for a ticker's sector, if we know one."""
    if not sector:
        return None
    t = ticker.upper()
    if t.endswith((".NS", ".BO")):
        return _INDIA_SECTOR_INDEX.get(sector)
    if "." not in t:
        return _US_SECTOR_ETF.get(sector)
    return None


@lru_cache(maxsize=256)
def get_sector(ticker: str) -> str | None:
    """Look up a ticker's sector from Yahoo Finance, or None."""
    try:
        return yf.Ticker(ticker).info.get("sector")
    except Exception:
        return None


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = out.columns.get_level_values(0)
    out.index = pd.to_datetime(out.index).tz_localize(None).normalize()
    return out


def _day_change(df: pd.DataFrame, ts: pd.Timestamp):
    close = df["Close"].dropna()
    if ts not in close.index:
        return None
    pos = close.index.get_loc(ts)
    if pos < 1:
        return None
    prev = float(close.iloc[pos - 1])
    last = float(close.iloc[pos])
    return {"close": last, "prev_close": prev, "change_pct": (last / prev - 1) * 100}


def _other_change(df, ts: pd.Timestamp):
    """Percent change for a comparison index on a day, or None."""
    if df is None or df.empty:
        return None
    c = _day_change(_prepare(df), ts)
    return None if c is None else c["change_pct"]


def _volume_ratio(df: pd.DataFrame, ts: pd.Timestamp):
    if "Volume" not in df:
        return None
    vol = df["Volume"].dropna()
    if ts not in vol.index:
        return None
    pos = vol.index.get_loc(ts)
    prior = vol.iloc[max(0, pos - 20):pos]
    if len(prior) < 5 or prior.mean() == 0:
        return None
    return float(vol.iloc[pos] / prior.mean())


def _r(x, digits: int = 2):
    return None if x is None else round(float(x), digits)


def _aligned(change_pct: float, other_pct) -> bool:
    """True if another index moved the same way, by a meaningful amount."""
    if other_pct is None:
        return False
    return change_pct * other_pct > 0 and abs(other_pct) >= ALIGN_RATIO * abs(change_pct)


def classify_move(
    change_pct: float,
    bench_change_pct: float | None,
    sector_change_pct: float | None = None,
) -> str:
    """Rough label: market-wide, sector-wide, or specific to the stock?"""
    if bench_change_pct is None and sector_change_pct is None:
        return "unknown (no market comparison available)"
    if abs(change_pct) < 0.5:
        return "small move"
    if _aligned(change_pct, bench_change_pct):
        return "mostly market-wide"
    if _aligned(change_pct, sector_change_pct):
        return "mostly sector-wide"
    return "mostly stock-specific"


def compute_move(stock_df, bench_df, day: date, sector_df=None) -> dict:
    """Work out how a stock moved on a day, compared with market and sector."""
    stock = _prepare(stock_df)
    ts = pd.Timestamp(day)
    s = _day_change(stock, ts)
    if s is None:
        raise ValueError(
            f"No trading data for {day}. It may be a weekend, a holiday, "
            "or outside the available history."
        )
    bench_change = _other_change(bench_df, ts)
    sector_change = _other_change(sector_df, ts)

    def rel(x):
        return None if x is None else s["change_pct"] - x

    return {
        "date": str(day),
        "close": _r(s["close"]),
        "prev_close": _r(s["prev_close"]),
        "change_pct": _r(s["change_pct"]),
        "benchmark_change_pct": _r(bench_change),
        "relative_pct": _r(rel(bench_change)),
        "sector_change_pct": _r(sector_change),
        "relative_to_sector_pct": _r(rel(sector_change)),
        "volume_ratio": _r(_volume_ratio(stock, ts)),
        "classification": classify_move(s["change_pct"], bench_change, sector_change),
    }


def _download(ticker: str, start: date, end: date) -> pd.DataFrame:
    return yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)


def fetch_headlines_between(
    ticker: str, start: date, end: date, max_items: int = 15
) -> list[dict]:
    """Fetch headlines published between two dates from Google News RSS."""
    name = get_company_name(ticker)
    query = (
        f"{ticker_to_query(ticker, name)} "
        f"after:{start.isoformat()} before:{end.isoformat()}"
    )
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    )
    feed = feedparser.parse(url)
    items = [
        {
            "title": e.title,
            "source": e.source.title if hasattr(e, "source") else None,
            "link": e.link,
        }
        for e in feed.entries[:max_items]
    ]
    return clean_headlines(items)


def get_move_evidence(ticker: str, day: date) -> dict:
    """Collect price, market, sector, volume, and news evidence for one day."""
    start, end = day - timedelta(days=45), day + timedelta(days=3)
    stock = _download(ticker, start, end)
    if stock.empty:
        raise ValueError(f"No data found for ticker '{ticker}'")
    bench_ticker = benchmark_for(ticker)
    bench = _download(bench_ticker, start, end) if bench_ticker else None
    sector_ticker = sector_index_for(ticker, get_sector(ticker))
    sector = _download(sector_ticker, start, end) if sector_ticker else None

    evidence = compute_move(stock, bench, day, sector)
    evidence["ticker"] = ticker
    evidence["benchmark"] = bench_ticker
    evidence["sector_index"] = sector_ticker
    evidence["headlines"] = fetch_headlines_between(
        ticker, day - timedelta(days=1), day + timedelta(days=2)
    )
    return evidence