# CCTracker one-command installer (Windows PowerShell).
#
#   $env:CCLB_API_BASE='{origin}'; $env:CCLB_TOKEN='cclb_live_xxx'; irm {origin}/install.ps1 | iex
#
# Writes ~/.cc-leaderboard/config.json, installs the /update-leaderboard skill
# into ~/.claude/skills/update-leaderboard/, and runs a first usage push.
$ErrorActionPreference = "Stop"

$ApiBase = if ($env:CCLB_API_BASE) { $env:CCLB_API_BASE } else { "__DEFAULT_API_BASE__" }
$ApiBase = $ApiBase.TrimEnd("/")
$Token = $env:CCLB_TOKEN
if ([string]::IsNullOrEmpty($Token)) {
    Write-Error "CCLB_TOKEN is not set. Get your setup command from $ApiBase."
    exit 1
}

$SkillName = "update-leaderboard"
$ConfigDir = Join-Path $HOME ".cc-leaderboard"
$SkillDir = Join-Path $HOME ".claude/skills/$SkillName"

Write-Host "CCTracker: installing the $SkillName skill from $ApiBase"

# 1. config (holds a secret token)
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
$config = [ordered]@{ api_base = $ApiBase; token = $Token } | ConvertTo-Json
Set-Content -Path (Join-Path $ConfigDir "config.json") -Value $config -Encoding UTF8

# 2. install the skill
New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
Invoke-WebRequest -UseBasicParsing -Uri "$ApiBase/skill/SKILL.md" -OutFile (Join-Path $SkillDir "SKILL.md")
Invoke-WebRequest -UseBasicParsing -Uri "$ApiBase/skill/push.ps1" -OutFile (Join-Path $SkillDir "push.ps1")

# 3. sanity + first push
if (-not (Get-Command ccusage -ErrorAction SilentlyContinue)) {
    Write-Host "note: 'ccusage' not found — will use 'npx -y ccusage@latest'"
}

Write-Host "CCTracker: pushing your usage for the first time…"
$setTrailingDays = -not $env:CCLB_TRAILING_DAYS
if ($setTrailingDays) { $env:CCLB_TRAILING_DAYS = "10" }
try {
    & (Join-Path $SkillDir "push.ps1")
} catch {
    Write-Warning "first push failed — run /update-leaderboard in Claude Code to retry"
} finally {
    if ($setTrailingDays) { Remove-Item Env:\CCLB_TRAILING_DAYS -ErrorAction SilentlyContinue }
}

Write-Host "CCTracker: done. Invoke /update-leaderboard in Claude Code anytime to update."
