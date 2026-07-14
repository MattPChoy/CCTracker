# update-leaderboard — push Claude Code usage to a CCTracker backend (Windows).
#
# Reads config from ~/.cc-leaderboard/config.json (or CCLB_API_BASE / CCLB_TOKEN
# env vars), runs `ccusage daily --breakdown --json` over a trailing window, and
# POSTs per-day/per-model rows to /v1/usage. Idempotent + safe to re-run.
$ErrorActionPreference = "Stop"

$ConfigPath = Join-Path $HOME ".cc-leaderboard/config.json"
$TrailingDays = if ($env:CCLB_TRAILING_DAYS) { [int]$env:CCLB_TRAILING_DAYS } else { 3 }

# --- resolve config -------------------------------------------------------
$ApiBase = $env:CCLB_API_BASE
$Token = $env:CCLB_TOKEN
if (-not $ApiBase -or -not $Token) {
    if (Test-Path $ConfigPath) {
        $cfg = Get-Content -Raw $ConfigPath | ConvertFrom-Json
        if (-not $ApiBase) { $ApiBase = $cfg.api_base }
        if (-not $Token) { $Token = $cfg.token }
    }
}
if (-not $ApiBase -or -not $Token) {
    Write-Error "set api_base + token in $ConfigPath or CCLB_API_BASE/CCLB_TOKEN"
    exit 1
}
$ApiBase = $ApiBase.TrimEnd("/")

# --- trailing window ------------------------------------------------------
$since = (Get-Date).AddDays(-$TrailingDays).ToString("yyyyMMdd")
Write-Host "update-leaderboard: since=$since -> $ApiBase"

# --- collect usage --------------------------------------------------------
try {
    $raw = & ccusage daily --breakdown --json --since $since 2>$null
    if (-not $raw) { throw "no output" }
} catch {
    $raw = & npx -y ccusage@latest daily --breakdown --json --since $since
}
$data = $raw | ConvertFrom-Json

# --- reshape into the ingest payload --------------------------------------
$days = @()
foreach ($d in $data.daily) {
    $breakdowns = if ($d.modelBreakdowns) { $d.modelBreakdowns } elseif ($d.breakdown) { $d.breakdown } else { @() }
    $models = @()
    foreach ($m in $breakdowns) {
        $models += [ordered]@{
            model               = if ($m.modelName) { $m.modelName } else { $m.model }
            inputTokens         = [int]($m.inputTokens         ?? 0)
            outputTokens        = [int]($m.outputTokens        ?? 0)
            cacheCreationTokens = [int]($m.cacheCreationTokens ?? 0)
            cacheReadTokens     = [int]($m.cacheReadTokens     ?? 0)
            totalTokens         = [int]($m.totalTokens         ?? 0)
            costUSD             = [double]($m.cost ?? $m.costUSD ?? 0)
        }
    }
    $days += [ordered]@{ date = if ($d.date) { $d.date } else { $d.period }; models = $models }
}
$payload = [ordered]@{ source = "ccusage"; days = $days } | ConvertTo-Json -Depth 8

# --- push -----------------------------------------------------------------
try {
    $resp = Invoke-RestMethod -Method Post -Uri "$ApiBase/v1/usage" `
        -Headers @{ Authorization = "Bearer $Token" } `
        -ContentType "application/json" -Body $payload
    $stateDir = Join-Path $HOME ".cc-leaderboard"
    New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
    (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") | Set-Content -Path (Join-Path $stateDir "last_pushed")
    Write-Host "pushed ok: $($resp | ConvertTo-Json -Compress)"
} catch {
    Write-Error "push failed: $($_.Exception.Message)"
    exit 1
}
