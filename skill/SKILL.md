---
name: cc-leaderboard-push
description: Push your Claude Code usage (from ccusage) to a CCTracker leaderboard. Use when the user wants to update their usage on a board, "push my usage", or set up automatic usage syncing.
---

# cc-leaderboard-push

Pushes your **aggregate** Claude Code usage — per day, per model, tokens and
cost — to a CCTracker backend so it appears on any leaderboard you've joined.
It reads only `ccusage`'s aggregate numbers: never project names, file paths, or
prompt content.

## One-time config

Create `~/.cc-leaderboard/config.json`:

```json
{
  "api_base": "https://cctracker.mattpchoy.com",
  "token": "cclb_live_your_secret_token"
}
```

(Or set `CCLB_API_BASE` and `CCLB_TOKEN` env vars — they take precedence.)

Get the token by registering at the CCTracker site (shown once on registration).

## Manual push

Run the bundled script — it reads a trailing window (default 3 days) so same-day
growth and late writes get corrected, and records a watermark so re-runs are safe:

```sh
./push.sh
```

Under the hood it runs:

```sh
ccusage daily --breakdown --json --since <watermark>
```

then normalizes cost/model fields and POSTs to `POST /v1/usage`. Ingestion is
idempotent, keyed by `(user, date, model)`, so re-pushing a day overwrites
rather than double-counts.

## Automatic pushing (pick one)

**cron (Linux)** — every 3 hours:

```
0 */3 * * *  /path/to/skill/push.sh >> ~/.cc-leaderboard/push.log 2>&1
```

**launchd (macOS)** — a `~/Library/LaunchAgents/com.cctracker.push.plist` with a
`StartInterval` of 10800 running `push.sh`.

**Claude Code hook** — fire a push after each session. In your Claude Code
`settings.json`:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [{ "type": "command", "command": "/path/to/skill/push.sh" }] }
    ]
  }
}
```

## Privacy

Only aggregate daily/per-model token counts and cost are sent. Cost visibility on
a board is further gated server-side by the board's `show_cost` and your
per-board `share_cost` override. The token is a bearer secret — keep it out of
shared shell history and world-readable files.
