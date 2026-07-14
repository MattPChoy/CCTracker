# Install the CCTracker `update-leaderboard` skill

This guide installs the **`/update-leaderboard`** Claude Code skill. The skill
runs [`ccusage`](https://github.com/ryoppippi/ccusage) and pushes your Claude
Code usage stats to your CCTracker leaderboard. It is written so **Claude Code
can read it and perform the install for you** on any operating system.

## Inputs you need

| Input | What it is |
| --- | --- |
| `api_base` | The CCTracker origin, e.g. `https://cctracker.mattpchoy.com` or `http://localhost:8080`. |
| `token` | Your personal secret, revealed by the **Get started** button on the site. Treat it like a password. |

Throughout this guide, `<api_base>` is your CCTracker origin and `<token>` is
your personal secret — substitute your own values.

## What gets installed

- `~/.cc-leaderboard/config.json` (mode `600`) — `{ "api_base": "...", "token": "..." }`
- `~/.claude/skills/update-leaderboard/` — the skill (`SKILL.md`, `push.sh`, `push.ps1`)

## Step 1 — Detect the OS

- **macOS or Linux** → use `install.sh` (Step 2a).
- **Windows** → use `install.ps1` (Step 2b).

## Step 2a — macOS / Linux

Prerequisites: `ccusage` (the installer falls back to `npx -y ccusage@latest`),
plus `curl` and `jq`.

```sh
curl -fsSL <api_base>/install.sh | CCLB_API_BASE=<api_base> CCLB_TOKEN=<token> bash
```

The installer reads `CCLB_API_BASE` and `CCLB_TOKEN` from the environment,
writes `~/.cc-leaderboard/config.json` at mode `600`, and installs the skill
into `~/.claude/skills/update-leaderboard/`.

## Step 2b — Windows (PowerShell)

Prerequisites: `ccusage` (falls back to `npx -y ccusage@latest`).

```powershell
$env:CCLB_API_BASE='<api_base>'; $env:CCLB_TOKEN='<token>'; irm <api_base>/install.ps1 | iex
```

Same result: config at `~/.cc-leaderboard/config.json` and the skill under
`~/.claude/skills/update-leaderboard/`.

## Step 3 — Confirm success

The installer performs a first push. **Success = an HTTP `200` response** from
`<api_base>`. Your entry should now appear on the leaderboard.

To push again later, just run the skill from Claude Code:

```
/update-leaderboard
```

## Manual fallback

If the install scripts can't run, set it up by hand.

1. Create `~/.cc-leaderboard/config.json` with mode `600`:

   ```json
   { "api_base": "<api_base>", "token": "<token>" }
   ```

   ```sh
   mkdir -p ~/.cc-leaderboard
   chmod 600 ~/.cc-leaderboard/config.json
   ```

2. Create `~/.claude/skills/update-leaderboard/` and download the skill files
   from the `/skill/...` routes on your CCTracker origin:

   ```sh
   mkdir -p ~/.claude/skills/update-leaderboard
   curl -fsSL <api_base>/skill/SKILL.md  -o ~/.claude/skills/update-leaderboard/SKILL.md
   curl -fsSL <api_base>/skill/push.sh   -o ~/.claude/skills/update-leaderboard/push.sh   # macOS/Linux
   curl -fsSL <api_base>/skill/push.ps1  -o ~/.claude/skills/update-leaderboard/push.ps1  # Windows
   ```

3. Run `/update-leaderboard` in Claude Code to push and confirm a `200`.
