---
name: update-leaderboard
description: Push your Claude Code usage (from ccusage) to a CCTracker leaderboard. Use when the user wants to update their usage on a board, "update the leaderboard", "push my usage", or set up automatic usage syncing.
---

# update-leaderboard

Pushes your **aggregate** Claude Code usage — per day, per model, tokens and
cost — to a CCTracker backend so it appears on any leaderboard you've joined.
It reads only `ccusage`'s aggregate numbers: never project names, file paths, or
prompt content.

When invoked, run the OS-appropriate push script in this skill folder:
`push.sh` on macOS/Linux, `push.ps1` on Windows.

## Install this skill (one command)

The easiest install is from the CCTracker site's "Get started" flow, which gives
you a single copy-paste command with your token already in it:

- **macOS / Linux:**
  `curl -fsSL <api_base>/install.sh | CCLB_API_BASE=<api_base> CCLB_TOKEN=<token> bash`
- **Windows (PowerShell):**
  `$env:CCLB_API_BASE='<api_base>'; $env:CCLB_TOKEN='<token>'; irm <api_base>/install.ps1 | iex`

`<api_base>` defaults to `https://cctracker.mattpchoy.com`. The installer writes
the config, downloads this skill into `~/.claude/skills/update-leaderboard/`, and
runs a first push.

### Or let Claude Code install it (any OS)

Paste this into Claude Code — it detects your OS and pulls the matching installer:

```text
Install the CCTracker "update-leaderboard" skill.

1. Detect my OS.
   - macOS/Linux: download https://cctracker.mattpchoy.com/install.sh and run it
     as: CCLB_API_BASE=https://cctracker.mattpchoy.com CCLB_TOKEN=<my token> bash install.sh
   - Windows: download https://cctracker.mattpchoy.com/install.ps1 and run it in
     PowerShell with $env:CCLB_API_BASE and $env:CCLB_TOKEN set.
2. Ask me for my token — I get it from the "Get started" button at the api_base.
3. After it finishes, run /update-leaderboard to confirm my usage pushed.
```

## Config

The installer creates `~/.cc-leaderboard/config.json`:

```json
{
  "api_base": "https://cctracker.mattpchoy.com",
  "token": "cclb_live_your_secret_token"
}
```

(Or set `CCLB_API_BASE` and `CCLB_TOKEN` env vars — they take precedence.)

Get the token from the "Get started" button on the CCTracker site.

## Manual push

Run the bundled script for your OS — it reads a trailing window (default 3 days)
so same-day growth and late writes get corrected, and records a watermark so
re-runs are safe:

```sh
./push.sh          # macOS / Linux
```
```powershell
./push.ps1         # Windows
```

Under the hood it runs `ccusage daily --breakdown --json --since <window>`, then
normalizes cost/model fields and POSTs to `POST /v1/usage`. Ingestion is
idempotent, keyed by `(user, date, model)`, so re-pushing a day overwrites
rather than double-counts.

## Automatic pushing (pick one)

**cron (Linux)** — every 3 hours:

```
0 */3 * * *  ~/.claude/skills/update-leaderboard/push.sh >> ~/.cc-leaderboard/push.log 2>&1
```

**launchd (macOS)** — a `~/Library/LaunchAgents/com.cctracker.push.plist` with a
`StartInterval` of 10800 running `push.sh`.

**Windows Task Scheduler** — a task running
`pwsh -File %USERPROFILE%\.claude\skills\update-leaderboard\push.ps1` every few hours.

**Claude Code hook** — fire a push after each session. In your Claude Code
`settings.json` (`push.ps1` on Windows):

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [{ "type": "command", "command": "~/.claude/skills/update-leaderboard/push.sh" }] }
    ]
  }
}
```

## Privacy

Only aggregate daily/per-model token counts and cost are sent. Cost visibility on
a board is further gated server-side by the board's `show_cost` and your
per-board `share_cost` override. The token is a bearer secret — keep it out of
shared shell history and world-readable files.
