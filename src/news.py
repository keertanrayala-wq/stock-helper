from datetime import datetime
from urllib.parse import quote_plus

import feedparser


def ticker_to_query(ticker: str) -> str:
    """Turn a ticker like 'TCS.NS' into a news search query."""
    base = ticker.upper().replace(".NS", "").replace(".BO", "")
    return f"{base} stock"


def fetch_headlines(ticker: str, max_items: int = 20) -> list[dict]:
    """Fetch recent headlines for a ticker from Google News RSS."""
    query = quote_plus(ticker_to_query(ticker) + " when:7d")
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
