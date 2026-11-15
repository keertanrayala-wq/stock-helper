from datetime import date, datetime
from urllib.parse import quote_plus

import feedparser

from src.news import clean_headlines, get_company_name, ticker_to_query


def fetch_timed_headlines(
    ticker: str, start: date, end: date, max_items: int = 100
) -> list[dict]:
    """Headlines with publication times (naive UTC) between two dates."""
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
    items = []
    for e in feed.entries[:max_items]:
        parsed = getattr(e, "published_parsed", None)
        if not parsed:
            continue
        items.append(
            {"title": e.title, "link": e.link, "published": datetime(*parsed[:6])}
        )
    return clean_headlines(items)
