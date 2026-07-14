"""SQLAlchemy models + engine helpers — the source-of-truth schema.

Canonical per-user usage is stored once, split by model (usage_daily_model).
Boards are just filtered *views* over member usage, so a single push updates
every board a user belongs to.
"""

from __future__ import annotations

import datetime as dt
import os
import secrets
import uuid

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    handle: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    tokens: Mapped[list["ApiToken"]] = relationship(back_populates="user")


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    # sha256 of the secret token; the raw token is shown to the user exactly once.
    token_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    # Human-readable head of the token for display, e.g. "cclb_live_ab12".
    prefix: Mapped[str] = mapped_column(String)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_used_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="tokens")


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    invite_code: Mapped[str] = mapped_column(String, index=True, default=lambda: secrets.token_urlsafe(9))
    visibility: Mapped[str] = mapped_column(String, default="private")  # private | unlisted
    default_metric: Mapped[str] = mapped_column(String, default="total_tokens")
    default_window: Mapped[str] = mapped_column(String, default="7d")
    show_cost: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    members: Mapped[list["BoardMember"]] = relationship(back_populates="board")


class BoardMember(Base):
    __tablename__ = "board_members"
    __table_args__ = (UniqueConstraint("board_id", "user_id", name="uq_board_user"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    board_id: Mapped[str] = mapped_column(ForeignKey("boards.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    alias: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String, default="member")  # owner | admin | member
    # Per-member cost visibility override. NULL means "inherit board.show_cost".
    share_cost: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    joined_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)

    board: Mapped[Board] = relationship(back_populates="members")


class UsageDailyModel(Base):
    """One user's usage for one day and one normalized model family.

    Idempotent upsert keyed by (user_id, date, model): re-pushing a day
    overwrites rather than double-counts, because ccusage recomputes historical
    days and today's totals grow through the day.
    """

    __tablename__ = "usage_daily_model"
    __table_args__ = (UniqueConstraint("user_id", "date", "model", name="uq_usage_key"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    model: Mapped[str] = mapped_column(String)  # normalized family, e.g. "opus"
    label: Mapped[str] = mapped_column(String, default="")  # display label, e.g. "Opus 4.1"

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_creation_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    source: Mapped[str | None] = mapped_column(String, nullable=True)  # e.g. "ccusage@16.x"
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


# ---------------------------------------------------------------------------
# Engine helpers


def make_engine(url: str | None = None):
    url = url or os.environ.get("DATABASE_URL", "postgresql+psycopg://cctracker:cctracker@localhost:5432/cctracker")
    return create_engine(url, pool_pre_ping=True, future=True)


def make_session_factory(engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db(engine) -> None:
    """Create tables if absent. A fresh project has no migration history, so
    create_all is sufficient; introduce Alembic if/when the schema evolves."""
    Base.metadata.create_all(engine)
