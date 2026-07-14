# CCTracker

A Claude Code usage leaderboard. People install a **skill** that runs
[`ccusage`](https://github.com/ryoppippi/ccusage) locally and pushes their
aggregate daily/per-model usage to this backend. They create and join
**boards** (a friends board, a work board) and see ranked usage with a
**per-model breakdown** (Opus vs. Sonnet vs. Haiku, in tokens and cost).

Usage is stored **once per user, globally**; a board is just a filtered view, so
one push updates every board you're on.

## Join a leaderboard (one command)

Hit **Get started** at `https://cctracker.mattpchoy.com` — no signup form, you're
signed in instantly with an auto-assigned name (changeable later). It then shows
a single command with your token already in it that installs the
`/update-leaderboard` skill and pushes your usage:

- **macOS / Linux:**
  `curl -fsSL https://cctracker.mattpchoy.com/install.sh | CCLB_API_BASE=https://cctracker.mattpchoy.com CCLB_TOKEN=<token> bash`
- **Windows (PowerShell):**
  `$env:CCLB_API_BASE='https://cctracker.mattpchoy.com'; $env:CCLB_TOKEN='<token>'; irm https://cctracker.mattpchoy.com/install.ps1 | iex`

Prefer to let Claude Code detect your OS and install it? The site also gives a
copy-paste Claude Code prompt. Details in [`skill/SKILL.md`](skill/SKILL.md).

## Stack

- **Backend:** FastAPI + SQLAlchemy + Postgres. Serves the REST API under `/v1`
  and the built SPA for everything else, from one container on `:8080`.
- **Frontend:** Vue 3 + TypeScript + Vite (built into the image).
- **Skill:** `skill/` — a `SKILL.md` + `push.sh` that runs `ccusage` and POSTs
  to `/v1/usage`.
- **Edge:** a Cloudflare Tunnel (`cloudflared`) exposes it at
  `https://cctracker.mattpchoy.com`.

## Run it

```sh
cp .env.example .env    # then fill in POSTGRES_* and CLOUDFLARE_TUNNEL_TOKEN
docker compose up -d --build
```

- App (local): http://localhost:8080
- Public: https://cctracker.mattpchoy.com (once the tunnel's public hostname is
  mapped to `http://app:8080` in the Cloudflare Zero Trust dashboard)

Health check: `curl -s localhost:8080/health`.

## API

| Method & path | Purpose |
|---|---|
| `POST /v1/users` | Register; returns the secret token **once** + handle. |
| `POST /v1/tokens/rotate` | Rotate the caller's token (invalidates the old one). |
| `GET /v1/me` | Current user + memberships. |
| `POST /v1/boards` | Create a board (caller becomes owner). |
| `GET /v1/boards/:id` | Board metadata (invite code shown to admins). |
| `POST /v1/boards/:id/join` | Join with `invite_code`; set an alias. |
| `PATCH /v1/boards/:id` | Owner/admin: update settings, rotate invite. |
| `DELETE /v1/boards/:id/members/:userId` | Remove a member. |
| `POST /v1/usage` | Ingest daily per-model rows (idempotent upsert). |
| `GET /v1/boards/:id/leaderboard?metric=&window=` | Ranked entries with per-model breakdown. |

Auth is `Authorization: Bearer <token>` on everything except `POST /v1/users`.

Metrics: `total_tokens` (default), `output_tokens`, `cost_usd`, `active_days`.
Windows: `today`, `7d`, `30d`, `all_time`.

## Data model

- **users** — global account: `handle`, `display_name`, `email?`.
- **api_tokens** — `token_hash` (sha256), `prefix`, revocable/rotatable.
- **boards** — `slug`, `invite_code`, `visibility`, default metric/window, `show_cost`.
- **board_members** — `(board, user)` with `alias`, `role`, `share_cost` override.
- **usage_daily_model** — canonical usage, PK `(user_id, date, model)`, idempotent upsert.

## Tests

```sh
cd backend && python -m pytest        # normalization unit tests (no DB needed)
```

## Trust model

Numbers come from the client and are not audited — this is a friendly
leaderboard, not fraud-proof accounting. The skill sends aggregate numbers only,
never project names or prompt content.

## Status

Implements PRD Phases 0–4 (auth, ingestion, boards/membership, leaderboard with
per-model breakdown) plus the push skill. Not yet done: automatic-push recipes
polish (Phase 5) and richer UI/streaks/billing-block window (Phase 6).
