"""Re-test sentiment vs later returns with timestamp-based news assignment.

Method fixed before looking at results:
- Each headline counts toward the first market close after it was published.
- Return is measured from that close to the next trading day's close.
- PRIMARY: mean daily cross-company rank correlation between sentiment and
  next-day market-adjusted (stock minus Nifty) return, with a permutation test.
- The 5-day horizon is a secondary check.
"""

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from analyze_scoreboard import download_prices
from src.scoreboard import build_dataset, daily_ic, daily_sentiment, evaluate

IN_FILE = Path("results/sentiment_v2.json")
OUT = Path("results/scoreboard_v2.json")
PERMUTATIONS = 300
COLUMNS = ["ex_1d", "ex_5d"]


def permutation_test(pooled: pd.DataFrame, column: str, n: int = PERMUTATIONS, seed: int = 0):
    """Shuffle sentiment across companies within each date and recompute the IC."""
    observed = daily_ic(pooled, column)["mean_ic"]
    if observed is None:
        return None
    rng = np.random.default_rng(seed)
    data = pooled.dropna(subset=["sentiment", column]).copy()
    null = []
    for _ in range(n):
        data["sentiment"] = data.groupby("date")["sentiment"].transform(
            lambda s: pd.Series(rng.permutation(s.to_numpy()), index=s.index)
        )
        m = daily_ic(data, column)["mean_ic"]
        if m is not None:
            null.append(m)
    if not null:
        return None
    extreme = sum(1 for x in null if abs(x) >= abs(observed))
    return {
        "observed": observed,
        "null_mean": round(float(np.mean(null)), 3),
        "null_sd": round(float(np.std(null)), 3),
        "p_value": round((extreme + 1) / (len(null) + 1), 3),
    }


def main() -> None:
    data = json.loads(IN_FILE.read_text())
    tickers = [t for t, e in data.items() if e["items"] and e["days_done"]]
    print(f"{len(tickers)} companies with timestamped headlines")
    if len(tickers) < 8:
        raise SystemExit("Need at least 8 companies. Let the collector run longer.")

    all_days = [d for t in tickers for d in data[t]["days_done"]]
    start = date.fromisoformat(min(all_days)) - timedelta(days=7)
    end = date.today() + timedelta(days=1)

    nifty = yf.download("^NSEI", start=start, end=end, auto_adjust=True, progress=False)
    if nifty.empty:
        raise SystemExit("Could not download the Nifty index data.")
    prices = download_prices(tickers, start, end)

    frames = []
    for t in tickers:
        if t not in prices:
            continue
        entry = data[t]
        first, last = min(entry["days_done"]), max(entry["days_done"])
        idx = pd.to_datetime(prices[t].index).tz_localize(None).normalize()
        daily = daily_sentiment(entry["items"], idx)
        daily = {d: v for d, v in daily.items() if first < d <= last}
        df = build_dataset(daily, prices[t], benchmark=nifty)
        if not df.empty:
            df.insert(0, "ticker", t)
            frames.append(df)
    if not frames:
        raise SystemExit("No company had both sentiment and price data.")

    pooled = pd.concat(frames, ignore_index=True)
    for col in COLUMNS:
        pooled[col] = pd.to_numeric(pooled[col], errors="coerce")

    results = {
        "generated": date.today().isoformat(),
        "data_through": max(all_days),
        "companies": int(pooled["ticker"].nunique()),
        "observations": int(len(pooled)),
        "dates": int(pooled["date"].nunique()),
        "pooled": {col: evaluate(pooled, col) for col in COLUMNS},
        "daily_ic": {col: daily_ic(pooled, col) for col in COLUMNS},
        "permutation_ex_1d": permutation_test(pooled, "ex_1d"),
    }
    OUT.write_text(json.dumps(results, indent=1))

    print(
        f"\n{results['companies']} companies, {results['observations']} "
        f"company-days, {results['dates']} dates, data through {results['data_through']}"
    )
    labels = {"ex_1d": "next day, vs Nifty", "ex_5d": "5 days, vs Nifty"}
    print("\nPooled hit rates (sentiment sign matched the return sign):")
    for col in COLUMNS:
        r = results["pooled"][col]
        print(
            f"  {labels[col]:<20} signal days={r['signal_days']:<6} "
            f"hit rate={r['hit_rate']}  up-day rate={r['base_rate_up']}  p={r['p_value']}"
        )
    print("\nPRIMARY: daily cross-company rank correlation")
    for col in COLUMNS:
        r = results["daily_ic"][col]
        print(
            f"  {labels[col]:<20} days={r['days']:<4} mean IC={r['mean_ic']}  "
            f"positive days={r['positive_days']}  p={r['p_value']}"
        )
    perm = results["permutation_ex_1d"]
    print(f"\nPermutation test (next day, shuffled sentiment): {perm}")
    print(f"\nSaved {OUT}")


if __name__ == "__main__":
    main()