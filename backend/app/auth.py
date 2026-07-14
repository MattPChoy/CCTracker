"""API-token minting, hashing, and the Bearer auth dependency."""

from __future__ import annotations

import hashlib
import secrets

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import ApiToken, User, _now
from .deps import get_session

_TOKEN_ENV = "live"  # could be "test" for sandbox instances


def mint_token() -> tuple[str, str, str]:
    """Return (raw_token, token_hash, prefix). The raw token is shown once."""
    body = secrets.token_urlsafe(24)
    raw = f"cclb_{_TOKEN_ENV}_{body}"
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    prefix = raw[:16]  # e.g. "cclb_live_ab12cd"
    return raw, token_hash, prefix


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    raw = authorization.split(" ", 1)[1].strip()
    tok = session.execute(
        select(ApiToken).where(ApiToken.token_hash == hash_token(raw))
    ).scalar_one_or_none()
    if tok is None or tok.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid or revoked token")
    tok.last_used_at = _now()
    session.commit()
    user = session.get(User, tok.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Token has no user")
    return user
