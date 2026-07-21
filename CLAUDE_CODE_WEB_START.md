# Paste This Into Claude Code

You are beginning the initial engineering stage of Master Character.

First, locate the repository selected for this session. The intended repository is
`OVERLORDNO1/First`, but the authoritative test is the presence of the sentinel files
listed in `docs/REPOSITORY_SELECTION.md`.

Do not scaffold a substitute project.

If the sentinel files are missing, stop immediately and respond with:

`REPOSITORY_NOT_READY`

Then list the missing paths. Do not build from scratch.

If the repository is ready:

1. Read `CLAUDE.md`.
2. Read `docs/PROJECT_CONTEXT.md`.
3. Read `docs/REPOSITORY_SELECTION.md`.
4. Read `docs/INITIAL_STAGE.md`.
5. Read `docs/CURRENT_MISSION.md`.
6. Inspect the provider, usage, store, runtime, CLI, and tests.
7. Run the baseline test suite before editing.
8. Record the exact baseline result.
9. Work only on Session Zero: Live Anthropic Provider Hardening.
10. Implement code and tests, not merely an audit.
11. Do not run a live API call unless `ANTHROPIC_API_KEY` already exists locally and the
    repository mission permits it.
12. Never ask Ryan to paste a secret into chat.
13. Do not modify the Charter or immutable rules.
14. Do not reduce the project into Siteupfit or another single workflow.
15. Do not continue into later stages automatically.

Create or update:

- `docs/CLAUDE_PROVIDER_AUDIT.md`
- `docs/CLAUDE_PROVIDER_HANDOFF.md`

End with:

- exact files changed;
- exact tests run and results;
- unresolved defects;
- the exact next command Ryan should run.
