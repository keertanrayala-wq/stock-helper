from src.search import format_option


def test_format_option():
    m = {"symbol": "WIPRO.NS", "name": "Wipro Limited", "exchange": "NSE"}
    assert format_option(m) == "Wipro Limited (WIPRO.NS, NSE)"


def test_format_option_without_name_or_exchange():
    assert format_option({"symbol": "XYZ", "name": None, "exchange": None}) == "XYZ (XYZ)"
