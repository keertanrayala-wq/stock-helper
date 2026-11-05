import yfinance as yf


def format_option(match: dict) -> str:
    """Label shown in the dropdown, e.g. 'Wipro Limited (WIPRO.NS, NSE)'."""
    name = match.get("name") or match["symbol"]
    exchange = match.get("exchange")
    suffix = f", {exchange}" if exchange else ""
    return f"{name} ({match['symbol']}{suffix})"


def search_companies(query: str, max_results: int = 8) -> list[dict]:
    """Search Yahoo Finance for companies matching a name or ticker."""
    query = query.strip()
    if not query:
        return []
    try:
        quotes = yf.Search(query, max_results=max_results).quotes
    except Exception:
        return []
    results = []
    for q in quotes:
        if q.get("quoteType") not in ("EQUITY", "ETF"):
            continue
        symbol = q.get("symbol")
        if not symbol:
            continue
        results.append(
            {
                "symbol": symbol,
                "name": q.get("longname") or q.get("shortname"),
                "exchange": q.get("exchDisp") or q.get("exchange"),
            }
        )
    return results
