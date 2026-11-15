import math

import pandas as pd

MIN_HEADLINES = 3
SIGNAL_THRESHOLD = 0.1
HORIZONS = {"1d": 1, "5d": 5}
COLUMNS = ["date", "sentiment", "count", "ret_1d", "ret_5d", "ex_1d", "ex_5d"]
MARKET_CLOSE_UTC_HOUR = 10  # 15:30 IST


def binomial_p_value(hits: int, n: int, p: float = 0.5):
    """Exact two-sided p-value for `hits` successes out of `n` at chance `p`.

    Computed with logarithms so it stays accurate for thousands of trials.
    """
    if n == 0:
        return None
    log_p, log_q = math.log(p), math.log(1 - p)

    def log_pmf(k: int) -> float:
        return (
            math.lgamma(n + 1)
            - math.lgamma(k + 1)
            - math.lgamma(n - k + 1)
            + k * log_p
            + (n - k) * log_q
        )

    observed = log_pmf(hits)
    total = 0.0
    for k in range(n + 1):
        lp = log_pmf(k)
        if lp <= observed + 1e-9:
            total += math.exp(lp)
    return min(1.0, total)


def _prepare_close(prices: pd.DataFrame) -> pd.Series:
    df = prices.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df["Close"].dropna()
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    return close


def _forward_return(close: pd.Series, pos: int, h: int):
    if pos + h >= len(close):
        return None
    return float(close.iloc[pos + h] / close.iloc[pos] - 1) * 100


def _excess_return(close: pd.Series, bench, pos: int, h: int):
    """Stock return minus benchmark return over the same dates, in percent."""
    if bench is None or pos + h >= len(close):
        return None
    d0, d1 = close.index[pos], close.index[pos + h]
    if d0 not in bench.index or d1 not in bench.index:
        return None
    stock = close.iloc[pos + h] / close.iloc[pos] - 1
    market = bench.loc[d1] / bench.loc[d0] - 1
    return float(stock - market) * 100


def build_dataset(
    sentiment: dict,
    prices: pd.DataFrame,
    min_count: int = MIN_HEADLINES,
    benchmark: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Pair each day's mean sentiment with later price returns (in percent).

    A news day that is not a trading day uses the last trading day before it,
    so the return measured is the next trading day's move. With a benchmark,
    market-adjusted (ex_) returns are also computed.
    """
    close = _prepare_close(prices)
    bench = _prepare_close(benchmark) if benchmark is not None else None
    rows = []
    for day_text, info in sentiment.items():
        if info.get("mean") is None or info.get("count", 0) < min_count:
            continue
        day = pd.Timestamp(day_text)
        pos = close.index.searchsorted(day, side="right") - 1
        if pos < 0:
            continue
        row = {"date": day_text, "sentiment": info["mean"], "count": info["count"]}
        for name, h in HORIZONS.items():
            row[f"ret_{name}"] = _forward_return(close, pos, h)
            row[f"ex_{name}"] = _excess_return(close, bench, pos, h)
        rows.append(row)
    return pd.DataFrame(rows, columns=COLUMNS)


def evaluate(df: pd.DataFrame, column: str, threshold: float = SIGNAL_THRESHOLD) -> dict:
    """Hit rate, p-value, and correlation of sentiment versus later returns."""
    data = df.dropna(subset=["sentiment", column])
    result = {
        "days": int(len(data)),
        "signal_days": 0,
        "hits": 0,
        "hit_rate": None,
        "base_rate_up": None,
        "p_value": None,
        "correlation": None,
    }
    if data.empty:
        return result
    if len(data) >= 3 and data["sentiment"].nunique() > 1 and data[column].nunique() > 1:
        result["correlation"] = round(float(data["sentiment"].corr(data[column])), 3)
    signal = data[data["sentiment"].abs() >= threshold]
    signal = signal[signal[column] != 0]
    n = int(len(signal))
    hits = int(((signal["sentiment"] > 0) == (signal[column] > 0)).sum())
    result["signal_days"] = n
    result["hits"] = hits
    if n:
        result["hit_rate"] = round(hits / n, 3)
        result["base_rate_up"] = round(float((signal[column] > 0).mean()), 3)
        result["p_value"] = round(binomial_p_value(hits, n), 3)
    return result


def daily_ic(pooled: pd.DataFrame, column: str, min_companies: int = 8) -> dict:
    """Each day, rank-correlate sentiment with returns across companies.

    Returns the average of those daily correlations and a sign test on how many
    days were positive. Comparing companies on the same day removes the part of
    the move that the whole market shares.
    """
    ics = []
    for _, group in pooled.dropna(subset=["sentiment", column]).groupby("date"):
        if len(group) < min_companies:
            continue
        if group["sentiment"].nunique() < 2 or group[column].nunique() < 2:
            continue
        ic = group["sentiment"].rank().corr(group[column].rank())
        if not pd.isna(ic):
            ics.append(float(ic))
    n = len(ics)
    positive = sum(1 for x in ics if x > 0)
    return {
        "days": n,
        "mean_ic": round(sum(ics) / n, 3) if n else None,
        "positive_days": positive,
        "p_value": round(binomial_p_value(positive, n), 3) if n else None,
    }


def daily_sentiment(items: list, trading_days) -> dict:
    """Group scored headlines by the first market close after they were published.

    A headline published before a day's close counts toward that day's signal,
    and one published after the close counts toward the next trading day.
    Returns are measured from the close, so no headline can know the return.
    """
    days = pd.DatetimeIndex(sorted(pd.to_datetime(list(trading_days)))).normalize()
    closes = days + pd.Timedelta(hours=MARKET_CLOSE_UTC_HOUR)
    groups = {}
    for item in items:
        pos = closes.searchsorted(pd.Timestamp(item["t"]), side="right")
        if pos >= len(closes):
            continue
        groups.setdefault(days[pos].date().isoformat(), []).append(item["s"])
    return {
        d: {"mean": round(sum(v) / len(v), 3), "count": len(v)}
        for d, v in groups.items()
    }