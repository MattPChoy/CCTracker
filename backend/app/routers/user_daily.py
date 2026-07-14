"""Per-user daily usage — powers the public contribution heatmap.

Unauthenticated, read-only: given a handle, returns one point per day that
actually has usage (summed across models), sparse. The frontend fills in the
zero days for the calendar grid.
"""

from __future__ import annotations

import datetime as dt
from typing import Iterable, Protocol

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import User, UsageDailyModel
from ..deps import get_session

router = APIRouter(prefix="/v1/public", tags=["public"])


class DailyPoint(BaseModel):
    date: dt.date
    total_tokens: int
    cost_usd: float


class UserDailyOut(BaseModel):
    handle: str
    days: list[DailyPoint]


class _UsageRow(Protocol):
    date: dt.date
    total_tokens: int
    cost_usd: float


def aggregate_daily(rows: Iterable[_UsageRow]) -> list[DailyPoint]:
    """Sum `total_tokens`/`cost_usd` per date across (possibly several,
    one-per-model) rows, and return points sorted oldest to newest."""
    totals: dict[dt.date, dict[str, float]] = {}
    for row in rows:
        agg = totals.setdefault(row.date, {"total_tokens": 0, "cost_usd": 0.0})
        agg["total_tokens"] += row.total_tokens
        agg["cost_usd"] += row.cost_usd

    return [
        DailyPoint(date=day, total_tokens=int(agg["total_tokens"]), cost_usd=round(agg["cost_usd"], 4))
        for day, agg in sorted(totals.items())
    ]


@router.get("/users/{handle}/daily", response_model=UserDailyOut)
def user_daily(
    handle: str,
    days: int = Query(default=371, ge=28, le=3660),
    session: Session = Depends(get_session),
) -> UserDailyOut:
    clean_handle = handle.lstrip("@")
    user = session.execute(select(User).where(User.handle == clean_handle)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    start = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=days)
    rows = (
        session.execute(
            select(UsageDailyModel).where(
                UsageDailyModel.user_id == user.id,
                UsageDailyModel.date >= start,
            )
        )
        .scalars()
        .all()
    )

    return UserDailyOut(handle="@" + user.handle, days=aggregate_daily(rows))
