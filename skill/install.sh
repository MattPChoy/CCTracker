#!/usr/bin/env bash
# CCTracker one-command installer (macOS / Linux).
#
#   curl -fsSL {origin}/install.sh | CCLB_API_BASE={origin} CCLB_TOKEN=cclb_live_xxx bash
#
# Writes ~/.cc-leaderboard/config.json, installs the /update-leaderboard skill
# into ~/.claude/skills/update-leaderboard/, and runs a first usage push.
set -euo pipefail

API_BASE="${CCLB_API_BASE:-__DEFAULT_API_BASE__}"
TOKEN="${CCLB_TOKEN:-}"
if [[ -z "${TOKEN}" ]]; then
  echo "error: CCLB_TOKEN is not set. Get your setup command from ${API_BASE}." >&2
  exit 1
fi

SKILL_NAME="update-leaderboard"
CONFIG_DIR="${HOME}/.cc-leaderboard"
SKILL_DIR="${HOME}/.claude/skills/${SKILL_NAME}"

echo "CCTracker: installing the ${SKILL_NAME} skill from ${API_BASE}"

# 1. config (0600 — it holds a secret token)
mkdir -p "${CONFIG_DIR}"
( umask 177
  printf '{\n  "api_base": "%s",\n  "token": "%s"\n}\n' "${API_BASE%/}" "${TOKEN}" \
    > "${CONFIG_DIR}/config.json" )
chmod 600 "${CONFIG_DIR}/config.json"

# 2. install the skill
mkdir -p "${SKILL_DIR}"
curl -fsSL "${API_BASE%/}/skill/SKILL.md" -o "${SKILL_DIR}/SKILL.md"
curl -fsSL "${API_BASE%/}/skill/push.sh" -o "${SKILL_DIR}/push.sh"
chmod +x "${SKILL_DIR}/push.sh"

# 3. sanity + first push
for bin in curl jq; do
  command -v "${bin}" >/dev/null 2>&1 || echo "warn: '${bin}' not found — the skill needs it" >&2
done
command -v ccusage >/dev/null 2>&1 || echo "note: 'ccusage' not found — will use 'npx -y ccusage@latest'" >&2

echo "CCTracker: pushing your usage for the first time…"
CCLB_TRAILING_DAYS="${CCLB_TRAILING_DAYS:-10}" "${SKILL_DIR}/push.sh" \
  || echo "warn: first push failed — run /update-leaderboard in Claude Code to retry" >&2

echo "CCTracker: done. Invoke /update-leaderboard in Claude Code anytime to update."
