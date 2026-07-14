"""Pydantic request/response models for the public API."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field


# --- users / auth ---------------------------------------------------------
class RegisterIn(BaseModel):
    handle: str = Field(min_length=2, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    display_name: str | None = None
    email: str | None = None


class RegisterOut(BaseModel):
    handle: str
    display_name: str | None
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
    alias: str | None


class MeOut(BaseModel):
    handle: str
    display_name: str | None
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
    alias: str | None = None


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
    alias: str | None
    value: float
    cost_usd: float | None
    per_model: list[PerModel]


class LeaderboardOut(BaseModel):
    board: BoardOut
    metric: str
    window: str
    entries: list[LeaderboardEntry]
