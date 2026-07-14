"""Shared leaderboard ranking — used by both the per-board and public endpoints.

Aggregates usage_daily_model rows per user (and per model) over a window, then
ranks users by a metric and builds entries with a per-model breakdown.
"""

from __future__ import annotations

import datetime as dt
from typing import Callable, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import User, UsageDailyModel
from .schemas import LeaderboardEntry, PerModel

METRICS = {"total_tokens", "cost_usd", "output_tokens", "active_days"}
WINDOWS = {"today", "7d", "30d", "all_time"}


def window_start(window: str) -> dt.date | None:
    today = dt.datetime.now(dt.timezone.utc).date()
    if window == "today":
        return today
    if window == "7d":
        return today - dt.timedelta(days=6)
    if window == "30d":
        return today - dt.timedelta(days=29)
    return None  # all_time


def _empty_agg() -> dict:
    return {"total_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "days": set(), "models": {}}


def rank_users(
    session: Session,
    users: Iterable[User],
    metric: str,
    window: str,
    cost_visible: Callable[[str], bool],
) -> list[LeaderboardEntry]:
    """Rank `users` by `metric` over `window`. `cost_visible(user_id)` decides
    whether that user's cost fields are exposed (else they're None)."""
    users = list(users)
    if not users:
        return []

    start = window_start(window)
    user_ids = [u.id for u in users]
    q = select(UsageDailyModel).where(UsageDailyModel.user_id.in_(user_ids))
    if start is not None:
        q = q.where(UsageDailyModel.date >= start)
    rows = session.execute(q).scalars().all()

    per_user: dict[str, dict] = {}
    for r in rows:
        u = per_user.setdefault(r.user_id, _empty_agg())
        u["total_tokens"] += r.total_tokens
        u["output_tokens"] += r.output_tokens
        u["cost_usd"] += r.cost_usd
        u["days"].add(r.date)
        m = u["models"].setdefault(
            r.model, {"label": r.label, "total_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        )
        m["label"] = r.label or m["label"]
        m["total_tokens"] += r.total_tokens
        m["output_tokens"] += r.output_tokens
        m["cost_usd"] += r.cost_usd

    def metric_value(agg: dict) -> float:
        if metric == "active_days":
            return float(len(agg["days"]))
        return float(agg[metric])

    entries: list[LeaderboardEntry] = []
    for u in users:
        agg = per_user.get(u.id, _empty_agg())
        show_cost = cost_visible(u.id)
        total = agg["total_tokens"] or 1  # avoid /0 for share
        per_model = [
            PerModel(
                model=fam,
                label=mstats["label"] or fam,
                total_tokens=mstats["total_tokens"],
                output_tokens=mstats["output_tokens"],
                cost_usd=round(mstats["cost_usd"], 4) if show_cost else None,
                share=round(mstats["total_tokens"] / total, 4),
            )
            for fam, mstats in agg["models"].items()
        ]
        per_model.sort(key=lambda p: p.total_tokens, reverse=True)
        entries.append(
            LeaderboardEntry(
                rank=0,  # filled after sort
                handle="@" + u.handle,
                value=round(metric_value(agg), 4),
                cost_usd=round(agg["cost_usd"], 4) if show_cost else None,
                per_model=per_model,
            )
        )

    entries.sort(key=lambda e: e.value, reverse=True)
    for i, e in enumerate(entries, start=1):
        e.rank = i
    return entries
