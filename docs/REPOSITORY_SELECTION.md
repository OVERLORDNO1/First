# Repository Selection and Readiness

## Intended repository

The current intended GitHub repository is:

`OVERLORDNO1/First`

Claude Code may select a different repository only if Ryan explicitly chooses another one.

## Sentinel files

The correct repository must contain all of these at its root:

- `pyproject.toml`
- `CLAUDE.md`
- `README.md`
- `charter/MASTER_CHARACTER_CHARTER.md`
- `config/immutable_rules.yaml`
- `src/master_character/core.py`
- `src/master_character/providers/anthropic.py`
- `tests/test_birth.py`
- `docs/CURRENT_MISSION.md`

## Claude Code rule

Before editing anything, verify the sentinel files.

If they are absent:

1. Do not build a replacement project from scratch.
2. Do not create a minimal substitute.
3. Stop and report `REPOSITORY_NOT_READY`.
4. List exactly which sentinel files are missing.
5. Ask Ryan to upload and commit the clean initial-stage package.

If they exist:

1. Treat that repository as the project source of truth.
2. Read `CLAUDE.md`.
3. Read `docs/PROJECT_CONTEXT.md`.
4. Read `docs/CURRENT_MISSION.md`.
5. Run baseline tests.
6. Continue only with the active mission.

## Branch

Preferred working branch:

`claude/session-zero-provider-hardening`

If Claude Code cannot create a branch in its environment, it should state that clearly before editing the default branch.
