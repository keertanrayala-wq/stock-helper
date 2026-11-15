import hashlib
import json
import socket
import sys
import time
from datetime import date, timedelta
from pathlib import Path

from src.sentiment import is_available, score_headlines
from src.timed_news import fetch_timed_headlines

OLD = Path("results/sentiment.json")
OUT = Path("results/sentiment_v2.json")
DAYS_BACK = 60
PAUSE_SECONDS = 1.0
THROTTLE_WAIT_SECONDS = 600
MIN_USABLE_OLD = 15
socket.setdefaulttimeout(30)


def pick_tickers(limit: int) -> list[str]:
    """Best-covered companies first, using the earlier collection run."""
    old = json.loads(OLD.read_text())
    ranked = []
    for ticker, days in old.items():
        usable = sum(1 for v in days.values() if v["count"] >= 3)
        total = sum(v["count"] for v in days.values())
        if usable >= MIN_USABLE_OLD:
            ranked.append((total, ticker))
    ranked.sort(reverse=True)
    return [t for _, t in ranked[:limit]]


def windows(start: date, end: date):
    """One request per weekday. Friday also covers the weekend."""
    day = start
    while day <= end:
        if day.weekday() < 5:
            span = 3 if day.weekday() == 4 else 1
            yield day, day + timedelta(days=span)
        day += timedelta(days=1)


def save(data: dict) -> None:
    OUT.parent.mkdir(exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(OUT)


def is_throttled() -> bool:
    """Canary: a big company always has recent headlines, so none means blocked."""
    day = date.today() - timedelta(days=3)
    try:
        return len(fetch_timed_headlines("RELIANCE.NS", day, day + timedelta(days=1))) == 0
    except Exception:
        return True


def collect_ticker(ticker: str, entry: dict, wins: list) -> None:
    seen = set(entry["seen"])
    done = set(entry["days_done"])
    for day, end in wins:
        key = day.isoformat()
        if key in done:
            continue
        while True:
            try:
                items = fetch_timed_headlines(ticker, day, end)
            except Exception as exc:
                print(f"  {key}: skipped ({type(exc).__name__})", flush=True)
                items = None
                break
            if items or not is_throttled():
                break
            print("  Google News looks throttled. Waiting 10 minutes...", flush=True)
            time.sleep(THROTTLE_WAIT_SECONDS)
        if items is None:
            continue
        fresh = []
        for it in items:
            k = hashlib.md5(it["link"].encode()).hexdigest()[:12]
            if k not in seen:
                seen.add(k)
                fresh.append(it)
        if fresh:
            scored = score_headlines([x["title"] for x in fresh])
            entry["items"].extend(
                {"t": x["published"].isoformat(), "s": s["score"]}
                for x, s in zip(fresh, scored)
            )
        entry["days_done"].append(key)
        entry["seen"] = list(seen)
        time.sleep(PAUSE_SECONDS)


def main() -> None:
    if not is_available():
        raise SystemExit("FinBERT is not installed. Run: pip install -r requirements-ml.txt")
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    tickers = pick_tickers(limit)
    print(f"{len(tickers)} companies selected.", flush=True)

    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    end = date.today() - timedelta(days=1)
    wins = list(windows(end - timedelta(days=DAYS_BACK), end))

    for n, ticker in enumerate(tickers, start=1):
        entry = data.setdefault(ticker, {"days_done": [], "seen": [], "items": []})
        todo = sum(1 for day, _ in wins if day.isoformat() not in set(entry["days_done"]))
        if not todo:
            continue
        print(f"[{n}/{len(tickers)}] {ticker}: {todo} days", flush=True)
        collect_ticker(ticker, entry, wins)
        save(data)
    print("Done.")


if __name__ == "__main__":
    main()