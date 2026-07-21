# Claude Code Development Protocol

This protocol applies to every future Claude Code session.

## One mission at a time

`docs/CURRENT_MISSION.md` defines the active scope. Do not combine later workstreams merely because they are related.

## Required sequence

### 1. Intake

- Read `CLAUDE.md`.
- Read the Charter and Vision.
- Read `docs/CURRENT_MISSION.md`.
- Inspect all source and tests relevant to that mission.

### 2. Baseline

Before editing, run:

```bash
python -m pytest -q
python -m compileall src tests
ruff check .
git status --short
```

Record failures as baseline facts. Do not attribute existing failures to new changes.

### 3. Audit

When requested, write a short audit containing:

- exact defect;
- affected file and symbol;
- observable consequence;
- proof or reproduction;
- recommended correction.

No broad project philosophy. No repeated debate about whether Master Character should exist.

### 4. Implement

- Work directly in the repository.
- Keep changes inside mission scope.
- Prefer explicit domain types and errors.
- Preserve compatibility unless the mission authorizes a migration.
- Add tests with every behaviour change.
- Do not leave silent fallback behaviour for costs, permissions, or state transitions.

### 5. Verify

Run the smallest relevant tests while iterating, then the full suite.

Required final verification:

```bash
python -m pytest -q
python -m compileall src tests
ruff check .
git status --short
git diff --stat
```

Live tests are opt-in and must have an explicit budget.

### 6. Handoff

Create the handoff file requested by the mission. Use `docs/HANDOFF_TEMPLATE.md`.

The handoff must distinguish:

- implemented and tested;
- implemented but not live-tested;
- not implemented;
- blocked;
- new risks discovered.

### 7. Stop

Do not begin the next workstream. Give Ryan one exact next command or decision.

## Evidence standard

Use these confidence levels:

- **Verified:** observed in tests or a live bounded run.
- **Implemented, unverified live:** code and deterministic tests pass, but no live provider run occurred.
- **Hypothesis:** reasoned expectation without execution evidence.
- **Blocked:** cannot be tested because a dependency or permission is absent.

Never label a mock lifecycle as proof of live-provider behaviour.
