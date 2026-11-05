import pandas as pd

from src.summary import summarize


def test_summarize_keys_and_values():
    close = pd.Series(range(1, 301), dtype=float)
    df = pd.DataFrame({"Close": close, "High": close + 1, "Low": close - 1})
    result = summarize(df, "TEST")
    assert result["ticker"] == "TEST"
    assert result["last_close"] == 300.0
    assert result["high_52w"] == 301.0
    assert result["low_52w"] == 0.0
    assert result["sma_200"] is not None
