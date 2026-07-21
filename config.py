from __future__ import annotations

from pathlib import Path
import sys

SENTINELS = [
    "pyproject.toml",
    "CLAUDE.md",
    "README.md",
    "charter/MASTER_CHARACTER_CHARTER.md",
    "config/immutable_rules.yaml",
    "src/master_character/core.py",
    "src/master_character/providers/anthropic.py",
    "tests/test_birth.py",
    "docs/CURRENT_MISSION.md",
]

root = Path.cwd()
missing = [path for path in SENTINELS if not (root / path).exists()]

if missing:
    print("REPOSITORY_NOT_READY")
    for path in missing:
        print(f"MISSING: {path}")
    sys.exit(2)

print("REPOSITORY_READY")
for path in SENTINELS:
    print(f"OK: {path}")
