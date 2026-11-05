from datetime import date

import pandas as pd
import pytest

from src.move import benchmark_for, classify_move, compute_move, sector_index_for


def _frame(closes, volumes=None, start="2026-10-01"):
    idx = pd.date_range(start, periods=len(closes), freq="D")
    volumes = volumes or [1000] * len(closes)
    return pd.DataFrame({"Close": closes, "Volume": volumes}, index=idx)


def test_benchmark_for():
    assert benchmark_for("TCS.NS") == "^NSEI"
    assert benchmark_for("AAPL") == "^GSPC"
    assert benchmark_for("VOD.L") is None


def test_sector_index_for():
    assert sector_index_for("TCS.NS", "Technology") == "^CNXIT"
    assert sector_index_for("AAPL", "Technology") == "XLK"
    assert sector_index_for("AAPL", None) is None
    assert sector_index_for("VOD.L", "Technology") is None
    assert sector_index_for("TCS.NS", "Aerospace") is None


def test_classify_move():
    assert classify_move(2.0, 1.5) == "mostly market-wide"
    assert classify_move(3.0, 0.2) == "mostly stock-specific"
    assert classify_move(-2.0, 1.0) == "mostly stock-specific"
    assert classify_move(0.3, 1.0) == "small move"
    assert classify_move(2.0, None).startswith("unknown")


def test_classify_move_with_sector():
    assert classify_move(-2.5, 0.6, -1.5) == "mostly sector-wide"
    assert classify_move(-2.5, 0.6, 0.5) == "mostly stock-specific"
    assert classify_move(2.0, 1.5, 0.1) == "mostly market-wide"


def test_compute_move():
    stock = _frame([100.0] * 29 + [103.0], volumes=[1000] * 29 + [3000])
    bench = _frame([200.0] * 29 + [201.0])
    result = compute_move(stock, bench, date(2026, 10, 30))
    assert result["change_pct"] == 3.0
    assert result["benchmark_change_pct"] == 0.5
    assert result["relative_pct"] == 2.5
    assert result["volume_ratio"] == 3.0
    assert result["classification"] == "mostly stock-specific"
    assert result["sector_change_pct"] is None


def test_compute_move_sector_wide():
    stock = _frame([100.0] * 29 + [97.5])
    bench = _frame([200.0] * 29 + [201.2])
    sector = _frame([100.0] * 29 + [98.5])
    result = compute_move(stock, bench, date(2026, 10, 30), sector)
    assert result["sector_change_pct"] == pytest.approx(-1.5)
    assert result["relative_to_sector_pct"] == pytest.approx(-1.0)
    assert result["classification"] == "mostly sector-wide"


def test_compute_move_no_trading_day():
    stock = _frame([100.0] * 30)
    with pytest.raises(ValueError):
        compute_move(stock, None, date(2026, 12, 1))