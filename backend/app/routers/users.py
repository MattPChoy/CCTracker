"""Registration, token rotation, and /me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, mint_token
from ..db import ApiToken, Board, BoardMember, User, _now
from ..deps import get_session
from ..schemas import (
    MeOut,
    MembershipOut,
    RegisterIn,
    RegisterOut,
    TokenOut,
)

router = APIRouter(prefix="/v1", tags=["users"])


@router.post("/users", response_model=RegisterOut)
def register(body: RegisterIn, session: Session = Depends(get_session)) -> RegisterOut:
    exists = session.execute(select(User).where(User.handle == body.handle)).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=409, detail="Handle already taken")
    user = User(handle=body.handle, display_name=body.display_name or body.handle, email=body.email)
    session.add(user)
    session.flush()
    raw, token_hash, prefix = mint_token()
    session.add(ApiToken(user_id=user.id, token_hash=token_hash, prefix=prefix))
    session.commit()
    return RegisterOut(handle=user.handle, display_name=user.display_name, token=raw, prefix=prefix)


@router.post("/tokens/rotate", response_model=TokenOut)
def rotate_token(
    user: User = Depends(current_user), session: Session = Depends(get_session)
) -> TokenOut:
    # Revoke every live token for this user, then mint a fresh one.
    for tok in session.execute(
        select(ApiToken).where(ApiToken.user_id == user.id, ApiToken.revoked_at.is_(None))
    ).scalars():
        tok.revoked_at = _now()
    raw, token_hash, prefix = mint_token()
    session.add(ApiToken(user_id=user.id, token_hash=token_hash, prefix=prefix))
    session.commit()
    return TokenOut(token=raw, prefix=prefix)


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(current_user), session: Session = Depends(get_session)) -> MeOut:
    rows = session.execute(
        select(BoardMember, Board)
        .join(Board, Board.id == BoardMember.board_id)
        .where(BoardMember.user_id == user.id)
    ).all()
    memberships = [
        MembershipOut(board_id=b.id, slug=b.slug, name=b.name, role=m.role, alias=m.alias)
        for m, b in rows
    ]
    return MeOut(handle=user.handle, display_name=user.display_name, memberships=memberships)
