# CCTracker — agent notes

Claude Code usage leaderboard. FastAPI + Postgres backend (serves the built Vue
SPA + REST API from one container on `:8080`), Vue 3 + TS frontend, a `ccusage`
push skill, and a Cloudflare Tunnel to `cctracker.mattpchoy.com`.

## Git commits

- **Use [Conventional Commits](https://www.conventionalcommits.org/)** (`feat:`,
  `fix:`, `chore:`, `docs:`, `refactor:`, …), scoped where useful
  (`feat(api): …`, `feat(web): …`).
- **One commit per feature chunk** — keep each commit a single coherent change,
  not a grab-bag.
- **Do not add AI attribution** — no `Co-Authored-By: Claude …` trailers, no
  "Generated with Claude Code" lines, in commits or PR bodies.

## Run / rebuild

```sh
docker compose up -d --build      # postgres + app + cloudflared
curl -s localhost:8080/health     # -> {"status":"ok"}
```

The app image is multi-stage: it builds the Vue frontend with Node, then serves
`web/dist` as static files plus the API from Python. No host Node/Python needed.

## Layout

- `backend/app/` — FastAPI: `db.py` (models), `auth.py`, `normalize.py`
  (ccusage cost/model normalization), `routers/` (users, boards, usage,
  leaderboard).
- `web/` — Vue 3 + Vite SPA.
- `skill/` — `SKILL.md` + `push.sh`: run `ccusage`, POST to `/v1/usage`.

## Tests

```sh
cd backend && python -m pytest    # normalization unit tests (no DB needed)
```

## Secrets

`.env` (gitignored) holds Postgres creds and the Cloudflare tunnel token. Never
commit it; `.env.example` documents the shape.
