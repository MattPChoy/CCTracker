"""The board leaderboard endpoint: ranked members with a per-model breakdown."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Board, BoardMember, User
from ..deps import get_session
from ..leaderboard_core import METRICS, WINDOWS, rank_users
from ..schemas import BoardOut, LeaderboardOut

router = APIRouter(prefix="/v1/boards", tags=["leaderboard"])


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
    if metric not in METRICS:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")
    if window not in WINDOWS:
        raise HTTPException(status_code=400, detail=f"Unknown window: {window}")

    members = session.execute(
        select(BoardMember, User)
        .join(User, User.id == BoardMember.user_id)
        .where(BoardMember.board_id == board.id)
    ).all()
    users = [u for _, u in members]

    board_hides_cost = not board.show_cost
    # Cost visible unless the board hides it or the member opted out.
    share_by_user = {u.id: mem.share_cost for mem, u in members}

    def cost_visible(user_id: str) -> bool:
        if board_hides_cost:
            return False
        return share_by_user.get(user_id) is not False

    entries = rank_users(session, users, metric, window, cost_visible)
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
