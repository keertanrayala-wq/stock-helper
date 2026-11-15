"""Test whether news sentiment lines up with later price moves.

Method fixed before looking at results:
- Only companies with at least 15 usable days (3 or more headlines) are used.
- A day's signal is its mean FinBERT score; signals need a size of 0.1 or more.
- Return is measured from that day's close to the next trading day's close.
- PRIMARY measure: the daily cross-company rank correlation between sentiment
  and next-day market-adjusted (stock minus Nifty) return.
- The 5-day horizon and raw returns are secondary checks.
"""

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from src.scoreboard import build_dataset, daily_ic, evaluate

SENTIMENT_FILE = Path("results/sentiment.json")
OUT = Path("results/scoreboard.json")
MIN_USABLE_DAYS = 15
USABLE_COUNT = 3
CHUNK = 40
COLUMNS = ["ret_1d", "ret_5d", "ex_1d", "ex_5d"]


def usable_days(info: dict) -> int:
    return sum(1 for v in info.values() if v["count"] >= USABLE_COUNT)


def download_prices(tickers: list, start: date, end: date) -> dict:
    prices = {}
    for i in range(0, len(tickers), CHUNK):
        chunk = tickers[i : i + CHUNK]
        raw = yf.download(
            chunk,
            start=start,
            end=end,
            auto_adjust=True,
            group_by="ticker",
            progress=False,
            threads=True,
        )
        if raw.empty:
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            available = set(raw.columns.get_level_values(0))
            for t in chunk:
                if t in available:
                    df = raw[t].dropna(how="all")
                    if not df.empty and "Close" in df:
                        prices[t] = df
        elif len(chunk) == 1:
            prices[chunk[0]] = raw
        print(f"  prices downloaded for {len(prices)} companies so far", flush=True)
    return prices


def show(label: str, r: dict) -> None:
    print(
        f"  {label:<26} days={r['days']:<6} signal days={r['signal_days']:<6} "
        f"hit rate={r['hit_rate']}  up-day rate={r['base_rate_up']}  "
        f"p={r['p_value']}  corr={r['correlation']}"
    )


def main() -> None:
    data = json.loads(SENTIMENT_FILE.read_text())
    tickers = [t for t, info in data.items() if usable_days(info) >= MIN_USABLE_DAYS]
    print(f"{len(data)} companies collected, {len(tickers)} with enough usable days")
    if not tickers:
        raise SystemExit("Not enough usable data yet.")

    all_days = [d for t in tickers for d in data[t]]
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
        df = build_dataset(data[t], prices[t], benchmark=nifty)
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
        "daily_ic": {col: daily_ic(pooled, col) for col in ["ex_1d", "ex_5d"]},
    }
    OUT.write_text(json.dumps(results, indent=1))

    print(
        f"\n{results['companies']} companies, {results['observations']} "
        f"company-days, {results['dates']} dates, data through {results['data_through']}"
    )
    print("\nPooled results (hit rate = sentiment sign matched the return sign):")
    labels = {
        "ret_1d": "next day, raw",
        "ex_1d": "next day, vs Nifty",
        "ret_5d": "5 days, raw",
        "ex_5d": "5 days, vs Nifty",
    }
    for col in COLUMNS:
        show(labels[col], results["pooled"][col])
    print("\nPRIMARY: daily cross-company rank correlation")
    for col in ["ex_1d", "ex_5d"]:
        r = results["daily_ic"][col]
        print(
            f"  {labels[col]:<26} days={r['days']:<5} mean IC={r['mean_ic']}  "
            f"positive days={r['positive_days']}  p={r['p_value']}"
        )
    print(f"\nSaved {OUT}")


if __name__ == "__main__":
    main()