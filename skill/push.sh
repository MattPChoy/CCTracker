#!/usr/bin/env bash
# update-leaderboard — push Claude Code usage to a CCTracker backend.
#
# Reads config from ~/.cc-leaderboard/config.json (or CCLB_API_BASE / CCLB_TOKEN
# env vars), runs `ccusage daily --breakdown --json` over a trailing window,
# and POSTs the per-day/per-model rows to /v1/usage. Idempotent + safe to re-run.
set -euo pipefail

CONFIG="${HOME}/.cc-leaderboard/config.json"
STATE_DIR="${HOME}/.cc-leaderboard"
WATERMARK_FILE="${STATE_DIR}/last_pushed"
TRAILING_DAYS="${CCLB_TRAILING_DAYS:-3}"

# --- resolve config -------------------------------------------------------
api_base="${CCLB_API_BASE:-}"
token="${CCLB_TOKEN:-}"
if [[ -z "${api_base}" || -z "${token}" ]]; then
  if [[ -f "${CONFIG}" ]]; then
    api_base="${api_base:-$(jq -r '.api_base // empty' "${CONFIG}")}"
    token="${token:-$(jq -r '.token // empty' "${CONFIG}")}"
  fi
fi
if [[ -z "${api_base}" || -z "${token}" ]]; then
  echo "error: set api_base + token in ${CONFIG} or CCLB_API_BASE/CCLB_TOKEN" >&2
  exit 1
fi

# --- trailing window ------------------------------------------------------
# Re-push the last N days so today's growth and late writes get corrected.
if command -v gdate >/dev/null 2>&1; then DATE=gdate; else DATE=date; fi
since="$(${DATE} -d "-${TRAILING_DAYS} days" +%Y%m%d 2>/dev/null || ${DATE} -v-"${TRAILING_DAYS}"d +%Y%m%d)"

echo "update-leaderboard: since=${since} -> ${api_base}"

# --- collect usage --------------------------------------------------------
raw="$(ccusage daily --breakdown --json --since "${since}" 2>/dev/null || npx -y ccusage@latest daily --breakdown --json --since "${since}")"

# --- reshape ccusage JSON into the ingest payload -------------------------
# ccusage emits { "daily": [ { date, modelBreakdowns: [ {modelName, inputTokens, ...} ] } ] }.
# We pass model rows close to verbatim; the server normalizes cost/model keys.
payload="$(printf '%s' "${raw}" | jq -c '{
  source: "ccusage",
  days: [ .daily[] | {
    date: (.date // .period),
    models: [ (.modelBreakdowns // .breakdown // [])[] | {
      model: (.modelName // .model),
      inputTokens: (.inputTokens // 0),
      outputTokens: (.outputTokens // 0),
      cacheCreationTokens: (.cacheCreationTokens // 0),
      cacheReadTokens: (.cacheReadTokens // 0),
      totalTokens: (.totalTokens // 0),
      costUSD: (.cost // .costUSD // 0)
    } ]
  } ]
}')"

# --- push -----------------------------------------------------------------
code="$(curl -sS -o /tmp/cclb_resp.json -w '%{http_code}' \
  -X POST "${api_base%/}/v1/usage" \
  -H "Authorization: Bearer ${token}" \
  -H "Content-Type: application/json" \
  -d "${payload}")"

if [[ "${code}" == "200" ]]; then
  mkdir -p "${STATE_DIR}"
  printf '%s' "$(${DATE} +%Y-%m-%dT%H:%M:%S)" > "${WATERMARK_FILE}"
  echo "pushed ok: $(cat /tmp/cclb_resp.json)"
else
  echo "push failed (HTTP ${code}): $(cat /tmp/cclb_resp.json)" >&2
  exit 1
fi
