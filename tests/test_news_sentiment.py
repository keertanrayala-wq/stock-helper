from src.news import ticker_to_query
from src.sentiment import aggregate_sentiment, signed_score


def test_ticker_to_query():
    assert ticker_to_query("TCS.NS") == "TCS stock"
    assert ticker_to_query("aapl") == "AAPL stock"


def test_signed_score():
    assert signed_score("positive", 0.9) == 0.9
    assert signed_score("negative", 0.8) == -0.8
    assert signed_score("neutral", 0.7) == 0.0


def test_aggregate_sentiment():
    scored = [
        {"label": "positive", "score": 0.9},
        {"label": "negative", "score": -0.5},
        {"label": "neutral", "score": 0.0},
    ]
    result = aggregate_sentiment(scored)
    assert result["count"] == 3
    assert result["positive"] == 1 and result["negative"] == 1
    assert result["mean_score"] == 0.133


def test_aggregate_empty():
    assert aggregate_sentiment([])["count"] == 0
