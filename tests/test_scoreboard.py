import pandas as pd
import pytest

from src.scoreboard import (
    binomial_p_value,
    build_dataset,
    daily_ic,
    daily_sentiment,
    evaluate,
)


def _prices(dates, closes):
    return pd.DataFrame({"Close": closes}, index=pd.DatetimeIndex(dates))


def test_binomial_p_value():
    assert binomial_p_value(10, 10) == pytest.approx(2 * 0.5**10)
    assert binomial_p_value(5, 10) == pytest.approx(1.0)
    assert binomial_p_value(0, 0) is None


def test_binomial_p_value_large_sample():
    p = binomial_p_value(5100, 10000)
    assert 0.0 < p < 1.0
    assert binomial_p_value(5000, 10000) == pytest.approx(1.0)


def test_build_dataset_returns_and_filters():
    dates = pd.date_range("2026-10-01", periods=30, freq="D")
    prices = _prices(dates, [100.0 + i for i in range(30)])
    sentiment = {
        "2026-10-10": {"mean": 0.5, "count": 5},
        "2026-10-11": {"mean": -0.3, "count": 2},
        "2026-10-29": {"mean": 0.2, "count": 4},
    }
    df = build_dataset(sentiment, prices)
    assert len(df) == 2
    assert df.iloc[0]["ret_1d"] == pytest.approx(110 / 109 * 100 - 100)
    assert df.iloc[0]["ret_5d"] == pytest.approx(114 / 109 * 100 - 100)
    assert pd.isna(df.iloc[1]["ret_5d"])


def test_build_dataset_weekend_uses_last_trading_day():
    dates = pd.bdate_range("2026-11-02", periods=10)
    prices = _prices(dates, [100.0 + i for i in range(10)])
    df = build_dataset({"2026-11-07": {"mean": 0.4, "count": 5}}, prices)
    assert df.iloc[0]["ret_1d"] == pytest.approx(105 / 104 * 100 - 100)


def test_build_dataset_excess_returns():
    dates = pd.date_range("2026-10-01", periods=30, freq="D")
    stock = _prices(dates, [100.0 * 1.01**i for i in range(30)])
    flat = _prices(dates, [200.0] * 30)
    rising = _prices(dates, [200.0 * 1.01**i for i in range(30)])
    sentiment = {"2026-10-10": {"mean": 0.5, "count": 5}}
    vs_flat = build_dataset(sentiment, stock, benchmark=flat)
    vs_rising = build_dataset(sentiment, stock, benchmark=rising)
    assert vs_flat.iloc[0]["ex_1d"] == pytest.approx(1.0)
    assert vs_rising.iloc[0]["ex_1d"] == pytest.approx(0.0, abs=1e-9)


def test_evaluate_hit_rate_and_p_value():
    df = pd.DataFrame(
        {
            "sentiment": [0.5, 0.4, -0.5, -0.3, 0.05],
            "ret_1d": [1.0, 2.0, -1.0, 0.5, 3.0],
        }
    )
    result = evaluate(df, "ret_1d")
    assert result["days"] == 5
    assert result["signal_days"] == 4
    assert result["hits"] == 3
    assert result["hit_rate"] == 0.75
    assert result["base_rate_up"] == 0.75
    assert result["p_value"] == pytest.approx(0.625)


def test_evaluate_empty():
    result = evaluate(pd.DataFrame(columns=["sentiment", "ret_1d"]), "ret_1d")
    assert result["days"] == 0
    assert result["hit_rate"] is None


def test_daily_ic_perfect_signal():
    rows = []
    for d in ["2026-10-01", "2026-10-02", "2026-10-05"]:
        for i in range(10):
            rows.append({"date": d, "sentiment": i / 10, "ex_1d": float(i)})
    result = daily_ic(pd.DataFrame(rows), "ex_1d")
    assert result["days"] == 3
    assert result["mean_ic"] == 1.0
    assert result["positive_days"] == 3
    assert result["p_value"] == pytest.approx(0.25)


def test_daily_ic_skips_thin_days():
    rows = [{"date": "2026-10-01", "sentiment": i / 10, "ex_1d": float(i)} for i in range(5)]
    assert daily_ic(pd.DataFrame(rows), "ex_1d")["days"] == 0


def test_daily_sentiment_assigns_by_market_close():
    days = pd.to_datetime(["2026-11-04", "2026-11-05", "2026-11-06", "2026-11-09"])
    items = [
        {"t": "2026-11-04T09:00:00", "s": 0.5},
        {"t": "2026-11-04T10:33:00", "s": -0.5},
        {"t": "2026-11-07T08:00:00", "s": 0.2},
        {"t": "2026-11-10T08:00:00", "s": 0.9},
    ]
    result = daily_sentiment(items, days)
    assert result["2026-11-04"] == {"mean": 0.5, "count": 1}
    assert result["2026-11-05"] == {"mean": -0.5, "count": 1}
    assert result["2026-11-09"] == {"mean": 0.2, "count": 1}
    assert "2026-11-10" not in result