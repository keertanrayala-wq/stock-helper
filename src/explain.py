def explain_rsi(rsi: float | None) -> str:
    """Plain-English reading of the RSI value."""
    if rsi is None:
        return "Not enough data to calculate RSI."
    if rsi >= 70:
        return (
            f"RSI is {rsi}, above 70. This is usually called overbought: "
            "the price has risen quickly and may be due for a pause. "
            "It is a signal, not a guarantee."
        )
    if rsi <= 30:
        return (
            f"RSI is {rsi}, below 30. This is usually called oversold: "
            "the price has fallen quickly and may be due for a bounce. "
            "It is a signal, not a guarantee."
        )
    return f"RSI is {rsi}, between 30 and 70. That is a neutral zone."


def explain_macd(macd: float | None, signal: float | None) -> str:
    """Plain-English reading of MACD versus its signal line."""
    if macd is None or signal is None:
        return "Not enough data to calculate MACD."
    if macd > signal:
        return (
            "MACD is above its signal line, which suggests recent upward "
            "momentum is stronger than the recent average."
        )
    return (
        "MACD is below its signal line, which suggests recent momentum is "
        "weaker than the recent average."
    )


def explain_trend(
    close: float | None, sma_50: float | None, sma_200: float | None
) -> str:
    """Plain-English reading of price versus its moving averages."""
    if close is None or sma_50 is None or sma_200 is None:
        return "Not enough history to compare against the 50 and 200-day averages."
    if close > sma_50 > sma_200:
        return "Price is above both averages, and the 50-day is above the 200-day: a steady uptrend."
    if close < sma_50 < sma_200:
        return "Price is below both averages, and the 50-day is below the 200-day: a steady downtrend."
    return "Price and the averages are giving mixed signals, so there is no clear trend."
