"""The leaderboard endpoint: ranked members with a per-model breakdown."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Board, BoardMember, UsageDailyModel, User
from ..deps import get_session
from ..schemas import BoardOut, LeaderboardEntry, LeaderboardOut, PerModel

router = APIRouter(prefix="/v1/boards", tags=["leaderboard"])

_METRICS = {"total_tokens", "cost_usd", "output_tokens", "active_days"}
_WINDOWS = {"today", "7d", "30d", "all_time"}


def _window_start(window: str) -> dt.date | None:
    today = dt.datetime.now(dt.timezone.utc).date()
    if window == "today":
        return today
    if window == "7d":
        return today - dt.timedelta(days=6)
    if window == "30d":
        return today - dt.timedelta(days=29)
    return None  # all_time


@router.get("/{board_id}/leaderboard", response_model=LeaderboardOut)
def leaderboard(
    board_id: str,
    metric: str = Query(default=None),
    window: str = Query(default=None),
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> LeaderboardOut:
    board = session.get(Board, board_id) or session.execute(
        select(Board).where(Board.slug == board_id)
    ).scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    if session.execute(
        select(BoardMember).where(
            BoardMember.board_id == board.id, BoardMember.user_id == user.id
        )
    ).scalar_one_or_none() is None:
        raise HTTPException(status_code=403, detail="Not a member of this board")

    metric = metric or board.default_metric
    window = window or board.default_window
    if metric not in _METRICS:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")
    if window not in _WINDOWS:
        raise HTTPException(status_code=400, detail=f"Unknown window: {window}")

    members = session.execute(
        select(BoardMember, User)
        .join(User, User.id == BoardMember.user_id)
        .where(BoardMember.board_id == board.id)
    ).all()
    if not members:
        return LeaderboardOut(
            board=_board_out(board), metric=metric, window=window, entries=[]
        )

    start = _window_start(window)
    user_ids = [u.id for _, u in members]
    q = select(UsageDailyModel).where(UsageDailyModel.user_id.in_(user_ids))
    if start is not None:
        q = q.where(UsageDailyModel.date >= start)
    rows = session.execute(q).scalars().all()

    # Aggregate per (user, model) and per user overall.
    per_user: dict[str, dict] = {}
    for r in rows:
        u = per_user.setdefault(
            r.user_id,
            {"total_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "days": set(), "models": {}},
        )
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

    board_hides_cost = not board.show_cost

    def metric_value(agg: dict) -> float:
        if metric == "active_days":
            return float(len(agg["days"]))
        return float(agg[metric])

    entries: list[LeaderboardEntry] = []
    for mem, u in members:
        agg = per_user.get(
            u.id, {"total_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "days": set(), "models": {}}
        )
        # Cost visible unless the board hides it or the member opted out.
        member_hides = mem.share_cost is False or (mem.share_cost is None and board_hides_cost)
        show_cost = not (board_hides_cost or member_hides)

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
                alias=mem.alias,
                value=round(metric_value(agg), 4),
                cost_usd=round(agg["cost_usd"], 4) if show_cost else None,
                per_model=per_model,
            )
        )

    entries.sort(key=lambda e: e.value, reverse=True)
    for i, e in enumerate(entries, start=1):
        e.rank = i

    return LeaderboardOut(board=_board_out(board), metric=metric, window=window, entries=entries)


def _board_out(board: Board) -> BoardOut:
    return BoardOut(
        id=board.id,
        slug=board.slug,
        name=board.name,
        visibility=board.visibility,
        default_metric=board.default_metric,
        default_window=board.default_window,
        show_cost=board.show_cost,
    )
