"""The public global leaderboard — unauthenticated, shown on the landing page.

Ranks every user by token usage. Cost is always hidden here (the public board
never exposes spend); token counts are considered shareable per the privacy
model.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import User
from ..deps import get_session
from ..leaderboard_core import METRICS, WINDOWS, rank_users
from ..schemas import LeaderboardOut

router = APIRouter(prefix="/v1/public", tags=["public"])

# Cost is never a public metric; only token/activity metrics are rankable here.
_PUBLIC_METRICS = METRICS - {"cost_usd"}


@router.get("/leaderboard", response_model=LeaderboardOut)
def public_leaderboard(
    metric: str = Query(default="total_tokens"),
    window: str = Query(default="7d"),
    limit: int = Query(default=25, ge=1, le=100),
    session: Session = Depends(get_session),
) -> LeaderboardOut:
    if metric not in _PUBLIC_METRICS:
        raise HTTPException(status_code=400, detail=f"Unknown public metric: {metric}")
    if window not in WINDOWS:
        raise HTTPException(status_code=400, detail=f"Unknown window: {window}")

    users = session.execute(select(User)).scalars().all()
    entries = rank_users(session, users, metric, window, cost_visible=lambda _uid: False)
    # Only surface users who actually have usage in the window, capped at limit.
    entries = [e for e in entries if e.value > 0][:limit]
    for i, e in enumerate(entries, start=1):
        e.rank = i
    return LeaderboardOut(board=None, metric=metric, window=window, entries=entries)
