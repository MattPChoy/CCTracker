"""Registration, token rotation, and /me."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import current_user, mint_token
from ..db import ApiToken, Board, BoardMember, User, _now
from ..deps import get_session
from ..schemas import (
    MeOut,
    MembershipOut,
    MePatchIn,
    RegisterIn,
    RegisterOut,
    TokenOut,
)

router = APIRouter(prefix="/v1", tags=["users"])

# Word lists for auto-generated handles (e.g. "swift-otter-1834"). Hyphens and
# digits are allowed by the handle pattern, so generated handles validate too.
_ADJ = [
    "swift", "quiet", "brave", "clever", "sunny", "cosmic", "mellow", "nimble",
    "brisk", "lucky", "vivid", "bold", "calm", "eager", "fuzzy", "gentle",
    "jolly", "keen", "lush", "merry", "plucky", "spry", "witty", "zesty",
]
_NOUN = [
    "otter", "falcon", "cedar", "comet", "maple", "lynx", "heron", "willow",
    "badger", "finch", "koala", "marmot", "newt", "osprey", "puffin", "quokka",
    "raven", "sparrow", "tapir", "vole", "walrus", "yak", "zebra", "ibex",
]


def _generate_handle(session: Session) -> str:
    for _ in range(12):
        cand = f"{secrets.choice(_ADJ)}-{secrets.choice(_NOUN)}-{secrets.randbelow(9000) + 1000}"
        if session.execute(select(User).where(User.handle == cand)).scalar_one_or_none() is None:
            return cand
    return f"user-{secrets.token_hex(4)}"


@router.post("/users", response_model=RegisterOut)
def register(body: RegisterIn, session: Session = Depends(get_session)) -> RegisterOut:
    if body.handle:
        exists = session.execute(
            select(User).where(User.handle == body.handle)
        ).scalar_one_or_none()
        if exists is not None:
            raise HTTPException(status_code=409, detail="Handle already taken")
        handle = body.handle
    else:
        handle = _generate_handle(session)
    user = User(handle=handle, email=body.email)
    session.add(user)
    session.flush()
    raw, token_hash, prefix = mint_token()
    session.add(ApiToken(user_id=user.id, token_hash=token_hash, prefix=prefix))
    session.commit()
    return RegisterOut(handle=user.handle, token=raw, prefix=prefix)


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
        MembershipOut(board_id=b.id, slug=b.slug, name=b.name, role=m.role)
        for m, b in rows
    ]
    return MeOut(handle=user.handle, memberships=memberships)


@router.patch("/me", response_model=MeOut)
def update_me(
    body: MePatchIn,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> MeOut:
    if body.handle != user.handle:
        taken = session.execute(
            select(User).where(User.handle == body.handle)
        ).scalar_one_or_none()
        if taken is not None:
            raise HTTPException(status_code=409, detail="Handle already taken")
        user.handle = body.handle
    session.commit()
    return me(user, session)
