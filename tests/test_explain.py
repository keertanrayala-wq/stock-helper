from src.explain import explain_macd, explain_rsi, explain_trend


def test_rsi_overbought_oversold_neutral():
    assert "overbought" in explain_rsi(80)
    assert "oversold" in explain_rsi(20)
    assert "neutral" in explain_rsi(50)


def test_rsi_missing_data():
    assert "Not enough data" in explain_rsi(None)


def test_macd_direction():
    assert "above" in explain_macd(2.0, 1.0)
    assert "below" in explain_macd(1.0, 2.0)


def test_trend_uptrend_and_mixed():
    assert "uptrend" in explain_trend(120, 110, 100)
    assert "mixed" in explain_trend(105, 110, 100)
