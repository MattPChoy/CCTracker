"""Pydantic request/response models for the public API."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


# --- users / auth ---------------------------------------------------------
class RegisterIn(BaseModel):
    # Optional: when omitted the server auto-generates a friendly handle so the
    # user never has to invent (or copy) anything to get started.
    handle: str | None = Field(default=None, min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str | None = None


class MePatchIn(BaseModel):
    handle: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")


class RegisterOut(BaseModel):
    handle: str
    token: str  # shown exactly once
    prefix: str


class TokenOut(BaseModel):
    token: str
    prefix: str


class MembershipOut(BaseModel):
    board_id: str
    slug: str
    name: str
    role: str


class MeOut(BaseModel):
    handle: str
    memberships: list[MembershipOut]


# --- boards ---------------------------------------------------------------
class BoardCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    slug: str | None = None
    visibility: str = "private"
    default_metric: str = "total_tokens"
    default_window: str = "7d"
    show_cost: bool = True


class BoardOut(BaseModel):
    id: str
    slug: str
    name: str
    invite_code: str | None = None  # only surfaced to owners/admins
    visibility: str
    default_metric: str
    default_window: str
    show_cost: bool


class BoardJoinIn(BaseModel):
    invite_code: str


class BoardPatchIn(BaseModel):
    name: str | None = None
    visibility: str | None = None
    default_metric: str | None = None
    default_window: str | None = None
    show_cost: bool | None = None
    rotate_invite: bool = False


# --- ingestion ------------------------------------------------------------
class IngestModelRow(BaseModel):
    model: str
    # Accept ccusage's camelCase verbatim; normalization handles the rest.
    model_config = {"extra": "allow"}


class IngestDay(BaseModel):
    date: dt.date
    models: list[dict]


class IngestIn(BaseModel):
    source: str | None = None
    days: list[IngestDay]


class IngestOut(BaseModel):
    upserted_rows: int
    days: int


# --- leaderboard ----------------------------------------------------------
class PerModel(BaseModel):
    model: str
    label: str
    total_tokens: int
    output_tokens: int
    cost_usd: float | None
    share: float


class LeaderboardEntry(BaseModel):
    rank: int
    handle: str
    value: float
    cost_usd: float | None
    per_model: list[PerModel]


class LeaderboardOut(BaseModel):
    # board is present for a board leaderboard, omitted for the public one.
    board: BoardOut | None = None
    metric: str
    window: str
    entries: list[LeaderboardEntry]
