"""FastAPI dependencies + app-level DB state."""

from __future__ import annotations

from sqlalchemy.orm import Session

from . import db as dbm

_state: dict[str, object] = {"engine": None, "session_factory": None}


def set_engine(engine) -> None:
    _state["engine"] = engine
    _state["session_factory"] = dbm.make_session_factory(engine)


def get_engine():
    return _state["engine"]


def get_session() -> Session:
    factory = _state["session_factory"]
    assert factory is not None, "session factory not initialised"
    with factory() as session:  # type: ignore[operator]
        yield session
