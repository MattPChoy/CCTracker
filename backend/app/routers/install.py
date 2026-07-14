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
# The cross-platform, OS-deciding install guide (INSTALL.md), served from the
# origin so the whole flow stays on the deployment's own domain.
_INSTALL_GUIDE = Path(os.environ.get("CCTRACKER_INSTALL_GUIDE", "/app/INSTALL.md"))


@router.get("/install")
def install_guide(request: Request, token: str = "<token>") -> PlainTextResponse:
    """The install guide, with `<api_base>` filled in from the request origin.

    Paste `<origin>/install` into Claude Code (or open it) and follow it.
    `?token=` also fills in `<token>`; otherwise the placeholder is left in place.
    """
    if not _INSTALL_GUIDE.is_file():
        raise HTTPException(status_code=404, detail="install guide not available")
    origin = str(request.base_url).rstrip("/")
    body = _INSTALL_GUIDE.read_text().replace("<api_base>", origin)
    if token != "<token>":
        body = body.replace("<token>", token)
    return PlainTextResponse(body, media_type="text/markdown")


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
