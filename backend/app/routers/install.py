"""Serve the OS-specific installers and skill assets from the deployed origin.

These are explicit routes so the SPA catch-all in main.py can't swallow them.
The installers carry a `__DEFAULT_API_BASE__` placeholder that we substitute
with the request's own origin, so a self-hosted deployment bakes in its own URL
with no edits.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse

router = APIRouter(tags=["install"])

_SKILL_DIR = Path(os.environ.get("CCTRACKER_SKILL_DIR", "/app/skill"))

# GitHub repo that hosts INSTALL.md (the cross-platform, OS-deciding guide).
_INSTALL_GUIDE_URL = "https://raw.githubusercontent.com/MattPChoy/CCTracker/main/INSTALL.md"


def _install_prompt(origin: str, token: str) -> str:
    return (
        f"Download the CCTracker install guide from\n{_INSTALL_GUIDE_URL}\n"
        f'and follow it to install the "update-leaderboard" Claude Code skill for my OS.\n\n'
        f"Use these values:\n"
        f"  api_base = {origin}\n"
        f"  token = {token}\n\n"
        f"When it's done, run /update-leaderboard to confirm my usage pushed.\n"
    )


@router.get("/install")
def install_prompt(request: Request, token: str = "<your token>") -> PlainTextResponse:
    """The plaintext Claude Code install prompt. Paste it into Claude Code.

    `?token=` fills in the secret; otherwise a placeholder is shown.
    """
    origin = str(request.base_url).rstrip("/")
    return PlainTextResponse(_install_prompt(origin, token))


def _render_installer(name: str, request: Request, media_type: str) -> PlainTextResponse:
    path = _SKILL_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"{name} not available")
    origin = str(request.base_url).rstrip("/")
    body = path.read_text().replace("__DEFAULT_API_BASE__", origin)
    return PlainTextResponse(body, media_type=media_type)


@router.get("/install.sh")
def install_sh(request: Request) -> PlainTextResponse:
    return _render_installer("install.sh", request, "text/x-shellscript")


@router.get("/install.ps1")
def install_ps1(request: Request) -> PlainTextResponse:
    return _render_installer("install.ps1", request, "text/plain")


@router.get("/skill/{filename}")
def skill_asset(filename: str) -> FileResponse:
    # Only allow the known skill files — no path traversal.
    if filename not in {"SKILL.md", "push.sh", "push.ps1"}:
        raise HTTPException(status_code=404, detail="Not found")
    path = _SKILL_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    media = "text/markdown" if filename.endswith(".md") else "text/plain"
    return FileResponse(path, media_type=media)
