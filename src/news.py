import re
from datetime import datetime
from functools import lru_cache
from urllib.parse import quote_plus

import feedparser
import yfinance as yf

_SUFFIX = re.compile(
    r"[,\s]+(inc\.?|incorporated|ltd\.?|limited|corp\.?|corporation|plc|co\.?)$",
    re.IGNORECASE,
)

_LISTING_PHRASES = (
    "share price today",
    "price prediction",
    "stock price, news",
    "quote & history",
)


def clean_company_name(name: str) -> str:
    """Strip suffixes like 'Limited' or 'Inc.' from a company name."""
    name = name.strip()
    previous = None
    while previous != name:
        previous = name
        name = _SUFFIX.sub("", name).strip()
    return name


@lru_cache(maxsize=256)
def get_company_name(ticker: str) -> str | None:
    """Look up the company name for a ticker, or None if unavailable."""
    try:
        info = yf.Ticker(ticker).info
        name = info.get("longName") or info.get("shortName")
        return clean_company_name(name) if name else None
    except Exception:
        return None


def ticker_to_query(ticker: str, name: str | None = None) -> str:
    """Build a news search query from the company name, or the symbol."""
    if name:
        return f'"{name}" stock'
    base = ticker.upper().replace(".NS", "").replace(".BO", "")
    return f"{base} stock"


def fetch_headlines(ticker: str, max_items: int = 20) -> list[dict]:
    """Fetch recent headlines for a ticker from Google News RSS."""
    name = get_company_name(ticker)
    query = quote_plus(ticker_to_query(ticker, name) + " when:7d")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:max_items]:
        published = None
        if getattr(entry, "published_parsed", None):
            published = datetime(*entry.published_parsed[:6])
        source = entry.source.title if hasattr(entry, "source") else None
        items.append(
            {
                "title": entry.title,
                "source": source,
                "published": published,
                "link": entry.link,
            }
        )
    return items


def _base_title(title: str) -> str:
    """Drop the trailing ' - Source' that Google News adds."""
    return title.rsplit(" - ", 1)[0].strip()


def is_listing_page(title: str) -> bool:
    """True for price pages and prediction pages that are not real news."""
    base = _base_title(title).lower()
    if base.endswith("share price") or base.endswith("stock price"):
        return True
    return any(p in base for p in _LISTING_PHRASES)


def clean_headlines(items: list[dict]) -> list[dict]:
    """Remove listing pages and duplicate headlines."""
    seen = set()
    cleaned = []
    for item in items:
        if is_listing_page(item["title"]):
            continue
        key = _base_title(item["title"]).lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned
