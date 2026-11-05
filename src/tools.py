import json
from datetime import date

from src.move import get_move_evidence
from src.news import clean_headlines, fetch_headlines, get_company_name
from src.search import search_companies
from src.sentiment import (
    aggregate_sentiment,
    describe_sentiment,
    is_available,
    score_headlines,
)
from src.summary import get_stock_summary

TOOLS = [
    {
        "name": "search_company",
        "description": (
            "Find the ticker symbol for a company name. Use this whenever the "
            "user names a company instead of giving a ticker."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Company name, e.g. 'Infosys'"}
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_stock_summary",
        "description": (
            "Get the last close, 1-day change, 52-week high and low, RSI, "
            "50 and 200-day moving averages, and MACD for a ticker such as "
            "'INFY.NS' or 'AAPL'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string", "description": "Ticker symbol"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "get_news_sentiment",
        "description": (
            "Get recent news headlines for a ticker, with a sentiment summary "
            "when available."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"ticker": {"type": "string", "description": "Ticker symbol"}},
            "required": ["ticker"],
        },
    },
    {
        "name": "explain_move",
        "description": (
            "Gather evidence about how a stock moved on one past trading day: "
            "its percent change, the market index change, the sector index "
            "change, a market-wide/sector-wide/stock-specific classification, "
            "a volume ratio, and headlines from that window. Use it when the "
            "user asks why a stock rose or fell on a specific date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Ticker symbol, e.g. 'TCS.NS'"},
                "date": {"type": "string", "description": "The trading day as YYYY-MM-DD"},
            },
            "required": ["ticker", "date"],
        },
    },
]


def _news_sentiment(ticker: str) -> dict:
    items = clean_headlines(fetch_headlines(ticker))
    result = {
        "company": get_company_name(ticker),
        "headline_count": len(items),
    }
    if items and is_available():
        scored = score_headlines([i["title"] for i in items])
        summary = aggregate_sentiment(scored)
        result["sentiment_summary"] = {**summary, "label": describe_sentiment(summary)}
        result["headlines"] = [
            {"title": i["title"], "source": i["source"], "label": s["label"], "score": s["score"]}
            for i, s in zip(items[:10], scored[:10])
        ]
    else:
        result["sentiment_summary"] = "Sentiment scoring unavailable"
        result["headlines"] = [
            {"title": i["title"], "source": i["source"]} for i in items[:10]
        ]
    return result


def _explain_move(ticker: str, day_text: str) -> dict:
    evidence = get_move_evidence(ticker, date.fromisoformat(day_text))
    evidence["headlines"] = [
        {"title": h["title"], "source": h["source"]} for h in evidence["headlines"][:8]
    ]
    evidence["note"] = (
        "Evidence only. These figures and headlines coincided with the move; "
        "they do not prove what caused it."
    )
    return evidence


def run_tool(name: str, args: dict) -> str:
    """Run a tool by name and return its result as a JSON string."""
    try:
        if name == "search_company":
            data = search_companies(args["query"], max_results=5)
        elif name == "get_stock_summary":
            data = get_stock_summary(args["ticker"])
        elif name == "get_news_sentiment":
            data = _news_sentiment(args["ticker"])
        elif name == "explain_move":
            data = _explain_move(args["ticker"], args["date"])
        else:
            return json.dumps({"error": f"Unknown tool '{name}'"})
        return json.dumps(data, default=str)
    except Exception as exc:
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})