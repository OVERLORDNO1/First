#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f "CLAUDE.md" ]]; then
  echo "Run this script from the Master Character repository root." >&2
  exit 1
fi

echo "Master Character Claude Code session"
echo "Active mission: docs/CURRENT_MISSION.md"
echo "Paste docs/CLAUDE_CODE_START_HERE.md when Claude Code opens."

claude --permission-mode acceptEdits
