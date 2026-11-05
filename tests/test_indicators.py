import pandas as pd

from src.indicators import rsi, sma


def test_sma_basic():
    prices = pd.Series([1, 2, 3, 4, 5])
    result = sma(prices, window=3)
    assert result.iloc[2] == 2.0
    assert result.iloc[4] == 4.0


def test_rsi_bounds():
    prices = pd.Series(range(1, 40))  # steadily rising
    result = rsi(prices).dropna()
    assert (result >= 0).all() and (result <= 100).all()
    assert result.iloc[-1] > 90  # strong uptrend -> high RSI
