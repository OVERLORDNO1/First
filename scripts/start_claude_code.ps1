$ErrorActionPreference = "Stop"

if (-not (Test-Path "CLAUDE.md")) {
    Write-Error "Run this script from the Master Character repository root."
}

Write-Host "Master Character Claude Code session" -ForegroundColor Cyan
Write-Host "Active mission: docs/CURRENT_MISSION.md" -ForegroundColor Yellow
Write-Host "Paste docs/CLAUDE_CODE_START_HERE.md when Claude Code opens." -ForegroundColor Green

claude --permission-mode acceptEdits
