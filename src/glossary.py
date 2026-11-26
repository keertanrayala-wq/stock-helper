import json

GLOSSARY = {
    "RSI": (
        "RSI (Relative Strength Index) is a score from 0 to 100 that compares a "
        "stock's recent up days with its recent down days, usually over 14 days. "
        "Above about 70 is often called overbought (it rose fast), below about 30 "
        "is called oversold (it fell fast), and in between is neutral. Think of it "
        "as a speedometer for recent price moves. It does not predict where the "
        "price goes next."
    ),
    "MACD": (
        "MACD measures short-term momentum. It subtracts a 26-day average price "
        "from a 12-day average price. The signal line is a smoothed version of "
        "the MACD line. When the MACD line is above the signal line, recent "
        "momentum is stronger than the recent average, and when it is below, "
        "momentum is weaker. It only describes the past."
    ),
    "Moving average": (
        "A moving average is the average closing price over the last N days, such "
        "as 50 or 200. It smooths out daily ups and downs so the general direction "
        "is easier to see. A price above its 200-day average means the stock has "
        "recently traded higher than its long-run average. When the 50-day average "
        "is above the 200-day average, recent prices have been higher than older ones."
    ),
    "Overbought and oversold": (
        "These are labels from indicators like RSI. Overbought means the price rose "
        "quickly in the recent past, and oversold means it fell quickly. Neither "
        "means the price will reverse, since a stock can stay overbought or "
        "oversold for a long time."
    ),
    "Volume": (
        "Volume is the number of shares traded in a day. The volume ratio in this "
        "app compares today's volume with the recent 20-day average. A value of "
        "1.0x is normal, 2.0x means twice as busy as usual, and 0.5x means half as busy."
    ),
    "52-week high and low": (
        "These are the highest and lowest prices a stock has traded at over the "
        "past year. They show how far today's price is from its recent extremes."
    ),
    "Candlestick chart": (
        "Each candle shows one trading day. The thick body spans the opening and "
        "closing prices, and the thin lines (wicks) reach the day's highest and "
        "lowest prices. In this app's charts, green candles are days the price "
        "rose and red candles are days it fell."
    ),
    "Volatility": (
        "Volatility is how much and how quickly a price moves up and down. A calm "
        "stock changes a little each day, while a volatile one swings a lot. "
        "Higher volatility means bigger possible gains and bigger possible losses."
    ),
    "Index": (
        "An index is a basket that tracks a group of companies to show how a market "
        "is doing. The Nifty 50 tracks 50 large companies on India's National Stock "
        "Exchange, and the Sensex tracks 30 large companies on the BSE. If the index "
        "is up, large companies as a group rose."
    ),
    "Sector index": (
        "A sector index tracks companies in one industry, such as the Nifty IT index "
        "for technology companies. Comparing a stock with its sector shows whether a "
        "move was shared by similar companies or was special to that stock."
    ),
    "Market capitalization": (
        "Market capitalization (market cap) is the total value of all of a company's "
        "shares: the share price times the number of shares. It shows how big the "
        "company is, not how good it is."
    ),
    "P/E ratio": (
        "The P/E ratio is the share price divided by the company's yearly profit per "
        "share. A P/E of 20 means investors pay about ₹20 for each ₹1 of yearly "
        "profit. A high or low P/E is not automatically good or bad, so it is best "
        "compared with similar companies."
    ),
    "Dividend": (
        "A dividend is a share of a company's profit that it pays to its shareholders, "
        "usually in cash. Not every company pays one."
    ),
    "Bull and bear markets": (
        "In a bull market prices are generally rising over a long period, and in a "
        "bear market they are generally falling, often described as a drop of 20% "
        "or more from a recent high."
    ),
    "Stop-loss": (
        "A stop-loss is an instruction to your broker to sell automatically if the "
        "price falls to a level you choose, to limit a loss. It does not guarantee "
        "the sale price, because in a fast-falling market the sale can happen lower."
    ),
    "Sentiment": (
        "Sentiment here is a score for the mood of news headlines (positive, negative, "
        "or neutral), produced by a language model trained on financial text. It is a "
        "rough signal, not a measure of truth and not a forecast."
    ),
}

_ALIASES = {
    "relative strength index": "RSI",
    "sma": "Moving average",
    "ema": "Moving average",
    "50-day average": "Moving average",
    "200-day average": "Moving average",
    "overbought": "Overbought and oversold",
    "oversold": "Overbought and oversold",
    "volume ratio": "Volume",
    "trading volume": "Volume",
    "52-week high": "52-week high and low",
    "52-week low": "52-week high and low",
    "52 week high": "52-week high and low",
    "52 week low": "52-week high and low",
    "candlestick": "Candlestick chart",
    "candle": "Candlestick chart",
    "candles": "Candlestick chart",
    "nifty": "Index",
    "nifty 50": "Index",
    "sensex": "Index",
    "benchmark": "Index",
    "market index": "Index",
    "sector": "Sector index",
    "market cap": "Market capitalization",
    "market capitalisation": "Market capitalization",
    "pe": "P/E ratio",
    "pe ratio": "P/E ratio",
    "p/e": "P/E ratio",
    "price to earnings": "P/E ratio",
    "bull market": "Bull and bear markets",
    "bear market": "Bull and bear markets",
    "bullish": "Bull and bear markets",
    "bearish": "Bull and bear markets",
    "stop loss": "Stop-loss",
    "news sentiment": "Sentiment",
}

_INDEX = {key.lower(): key for key in GLOSSARY}
_INDEX.update(_ALIASES)
GLOSSARY_TOOL = {
    "name": "explain_term",
    "description": (
        "Get a beginner-friendly definition of a finance or investing term, such as "
        "RSI, MACD, moving average, volume, volatility, P/E ratio, market cap, or "
        "candlestick chart. Use it whenever the user asks what a term means, or when "
        "you need to define a term for a beginner."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "term": {"type": "string", "description": "The term, for example 'RSI'"}
        },
        "required": ["term"],
    },
}


def lookup_term(term: str) -> str:
    """Return a glossary definition as JSON, or an error with the available terms."""
    key = _INDEX.get(term.strip().lower())
    if key is None:
        return json.dumps(
            {
                "error": f"'{term}' is not in the glossary",
                "available_terms": sorted(GLOSSARY),
            }
        )
    return json.dumps({"term": key, "definition": GLOSSARY[key]})