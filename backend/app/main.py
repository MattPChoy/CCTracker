"""CCTracker api — Claude Code usage leaderboard.

Serves the REST API under /v1 and (in the built image) the Vue SPA for every
other path. One container, one port (8080).
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import db as dbm
from .deps import set_engine
from .routers.boards import router as boards_router
from .routers.install import router as install_router
from .routers.leaderboard import router as leaderboard_router
from .routers.public import router as public_router
from .routers.usage import router as usage_router
from .routers.user_daily import router as user_daily_router
from .routers.users import router as users_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cctracker")

# Where the built Vue bundle lands in the image (see backend/Dockerfile).
_STATIC_DIR = Path(os.environ.get("CCTRACKER_STATIC_DIR", "/app/static"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = dbm.make_engine()
    for attempt in range(30):
        try:
            dbm.init_db(engine)
            break
        except Exception as exc:  # noqa: BLE001
            log.warning("DB not ready (attempt %d): %s", attempt + 1, exc)
            time.sleep(2)
    else:
        raise RuntimeError("Postgres never became ready")
    set_engine(engine)
    log.info("cctracker ready")
    yield


app = FastAPI(title="CCTracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id(request: Request, call_next):
    rid = request.headers.get("x-request-id", str(uuid.uuid4())[:8])
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(boards_router)
app.include_router(usage_router)
app.include_router(leaderboard_router)
app.include_router(public_router)
app.include_router(user_daily_router)
app.include_router(install_router)


# --- SPA static serving (only when the built bundle is present) -----------
if _STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # Serve real files if they exist, else fall back to index.html (SPA routing).
        candidate = _STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_STATIC_DIR / "index.html")
