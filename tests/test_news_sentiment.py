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


def test_listing_pages_are_filtered():
    from src.news import clean_headlines, is_listing_page

    assert is_listing_page("TCS Share Price - Upstox")
    assert is_listing_page("TCS Share Price Prediction for Monday - Univest")
    assert not is_listing_page("TCS shares rally 6% after Q2 results - Inshorts")

    items = [
        {"title": "TCS Share Price - Upstox"},
        {"title": "TCS wins big deal - Mint"},
        {"title": "TCS wins big deal - Other Site"},
    ]
    assert len(clean_headlines(items)) == 1


def test_clean_company_name():
    from src.news import clean_company_name

    assert clean_company_name("Tata Consultancy Services Limited") == "Tata Consultancy Services"
    assert clean_company_name("Apple Inc.") == "Apple"


def test_query_uses_company_name():
    assert (
        ticker_to_query("TCS.NS", "Tata Consultancy Services")
        == '"Tata Consultancy Services" stock'
    )


def test_describe_sentiment():
    from src.sentiment import describe_sentiment

    few = {"count": 2, "mean_score": 0.9}
    assert describe_sentiment(few) == "Not enough recent news to score"
    assert describe_sentiment({"count": 10, "mean_score": 0.3}) == "Mostly positive"
    assert describe_sentiment({"count": 10, "mean_score": -0.3}) == "Mostly negative"
    assert describe_sentiment({"count": 10, "mean_score": 0.0}) == "Mixed or neutral"


def test_is_available_returns_bool():
    from src.sentiment import is_available

    assert isinstance(is_available(), bool)
