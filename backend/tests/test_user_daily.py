"""Unit tests for the per-date usage aggregation (pure, no DB needed)."""

import datetime as dt
from dataclasses import dataclass

from app.routers.user_daily import aggregate_daily


@dataclass
class _Row:
    date: dt.date
    total_tokens: int
    cost_usd: float


def test_sums_across_models_same_day():
    d = dt.date(2026, 7, 1)
    rows = [
        _Row(date=d, total_tokens=100, cost_usd=1.0),
        _Row(date=d, total_tokens=50, cost_usd=0.5),
    ]
    points = aggregate_daily(rows)
    assert len(points) == 1
    assert points[0].date == d
    assert points[0].total_tokens == 150
    assert points[0].cost_usd == 1.5


def test_sorted_oldest_to_newest_and_sparse():
    d1, d2, d3 = dt.date(2026, 7, 3), dt.date(2026, 7, 1), dt.date(2026, 7, 2)
    rows = [
        _Row(date=d1, total_tokens=1, cost_usd=0.0),
        _Row(date=d2, total_tokens=2, cost_usd=0.0),
        _Row(date=d3, total_tokens=3, cost_usd=0.0),
    ]
    points = aggregate_daily(rows)
    assert [p.date for p in points] == [d2, d3, d1]


def test_empty_rows_yields_empty_list():
    assert aggregate_daily([]) == []
