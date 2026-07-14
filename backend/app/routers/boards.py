"""Board CRUD, invite-code join, membership management."""

from __future__ import annotations

import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user
from ..db import Board, BoardMember, User
from ..deps import get_session
from ..schemas import BoardCreateIn, BoardJoinIn, BoardOut, BoardPatchIn

router = APIRouter(prefix="/v1/boards", tags=["boards"])


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or secrets.token_urlsafe(4).lower()


def _membership(session: Session, board_id: str, user_id: str) -> BoardMember | None:
    return session.execute(
        select(BoardMember).where(
            BoardMember.board_id == board_id, BoardMember.user_id == user_id
        )
    ).scalar_one_or_none()


def _board_out(board: Board, *, include_invite: bool) -> BoardOut:
    return BoardOut(
        id=board.id,
        slug=board.slug,
        name=board.name,
        invite_code=board.invite_code if include_invite else None,
        visibility=board.visibility,
        default_metric=board.default_metric,
        default_window=board.default_window,
        show_cost=board.show_cost,
    )


@router.post("", response_model=BoardOut)
def create_board(
    body: BoardCreateIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> BoardOut:
    slug = body.slug or _slugify(body.name)
    if session.execute(select(Board).where(Board.slug == slug)).scalar_one_or_none():
        slug = f"{slug}-{secrets.token_urlsafe(3).lower()}"
    board = Board(
        slug=slug,
        name=body.name,
        owner_user_id=user.id,
        visibility=body.visibility,
        default_metric=body.default_metric,
        default_window=body.default_window,
        show_cost=body.show_cost,
    )
    session.add(board)
    session.flush()
    session.add(BoardMember(board_id=board.id, user_id=user.id, role="owner"))
    session.commit()
    return _board_out(board, include_invite=True)


@router.get("/{board_id}", response_model=BoardOut)
def get_board(
    board_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> BoardOut:
    board = session.get(Board, board_id) or _by_slug(session, board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    mem = _membership(session, board.id, user.id)
    is_admin = mem is not None and mem.role in ("owner", "admin")
    return _board_out(board, include_invite=is_admin)


def _by_slug(session: Session, slug: str) -> Board | None:
    return session.execute(select(Board).where(Board.slug == slug)).scalar_one_or_none()


@router.post("/{board_id}/join", response_model=BoardOut)
def join_board(
    board_id: str,
    body: BoardJoinIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> BoardOut:
    board = session.get(Board, board_id) or _by_slug(session, board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    if body.invite_code != board.invite_code:
        raise HTTPException(status_code=403, detail="Bad invite code")
    if _membership(session, board.id, user.id) is None:
        session.add(BoardMember(board_id=board.id, user_id=user.id, role="member"))
        session.commit()
    return _board_out(board, include_invite=False)


@router.patch("/{board_id}", response_model=BoardOut)
def patch_board(
    board_id: str,
    body: BoardPatchIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> BoardOut:
    board = session.get(Board, board_id) or _by_slug(session, board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    mem = _membership(session, board.id, user.id)
    if mem is None or mem.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admins only")
    for field in ("name", "visibility", "default_metric", "default_window", "show_cost"):
        val = getattr(body, field)
        if val is not None:
            setattr(board, field, val)
    if body.rotate_invite:
        board.invite_code = secrets.token_urlsafe(9)
    session.commit()
    return _board_out(board, include_invite=True)


@router.delete("/{board_id}/members/{member_user_id}")
def remove_member(
    board_id: str,
    member_user_id: str,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> dict:
    board = session.get(Board, board_id) or _by_slug(session, board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    mem = _membership(session, board.id, user.id)
    if mem is None or mem.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admins only")
    if member_user_id == board.owner_user_id:
        raise HTTPException(status_code=400, detail="Cannot remove the board owner")
    target = _membership(session, board.id, member_user_id)
    if target is not None:
        session.delete(target)
        session.commit()
    return {"removed": member_user_id}
