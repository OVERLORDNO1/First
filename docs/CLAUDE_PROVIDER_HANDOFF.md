# Claude Code Handoff

## Session

- Mission: Session Zero — Live Anthropic Provider Hardening (`docs/CURRENT_MISSION.md`)
- Date: 2026-07-21
- Repository state before work: the GitHub repository contained a flattened, content-scrambled copy of the initial-stage package (filenames did not match contents; sentinel check failed). Ryan supplied `mastercharacterinitialstagev2.1.zip`; the clean tree was restored and committed first. Baseline on the restored tree: 7 tests passed, compile OK, 72 ruff errors.
- Repository state after work: branch `claude/session-091xzj`, 36 tests passing, provider hardening implemented.

## Result

The mission definition of done is met on the deterministic side: real cost accounting exists and fails closed for unknown models, the task budget is enforced before every initial and continuation call, provider failures are classified/retried/bounded and persisted sanitized, the `provider-smoke` CLI command exists with the required exit semantics, and 29 new deterministic tests cover every mission-listed case. No live API call was made because `ANTHROPIC_API_KEY` is not present in this environment, so live behaviour is implemented but not live-verified.

## Changed files

| File | Change | Reason |
|---|---|---|
| `docs/CLAUDE_PROVIDER_AUDIT.md` | new | Mission-required defect audit (D1–D13) |
| `docs/CLAUDE_PROVIDER_HANDOFF.md` | new | This handoff |
| `src/master_character/errors.py` | new | Typed provider error hierarchy with categories and retryability |
| `src/master_character/pricing.py` | new | Fail-closed pricing registry keyed by (provider, exact model id); overridable via `MASTER_MODEL_PRICING_JSON` |
| `src/master_character/domain.py` | edit | `ModelUsage` gains cache-creation/cache-read tokens, calls, retries, stop_reason, correlation_id; new `ProviderFailureRecord` |
| `src/master_character/store.py` | edit | `usage` table gains the new columns (with in-place ALTER migration), new `provider_failures` table, `record_provider_failure`, `list_provider_failures`, `task_cost(correlation_id)` |
| `src/master_character/config.py` | edit | New settings: pricing overrides, retry count, backoff base/max, provider max_tokens |
| `src/master_character/providers/anthropic.py` | rewrite | Budget enforcement before every call, classified retries with jittered backoff, stop-reason handling (`max_tokens`, `pause_turn`), tool-protocol discipline, zero-cost rejection, sanitized failure persistence, cancellation handling, injectable transport/sleep/rng for deterministic tests |
| `src/master_character/providers/base.py` | edit | `correlation_id` parameter added to the provider protocol |
| `src/master_character/providers/mock.py` | edit | Signature parity with the protocol |
| `src/master_character/providers/factory.py` | edit | `create_provider(settings, store)` so the live adapter can persist usage/failures |
| `src/master_character/core.py` | edit | Passes the store into the provider factory |
| `src/master_character/execution.py` | edit | Passes `correlation_id`; task budget now also capped by `MASTER_MAX_TASK_COST_USD` |
| `src/master_character/cli.py` | edit | New `provider-smoke --budget-usd` command |
| `tests/test_provider_anthropic.py` | new | 25 deterministic provider/pricing tests over a scripted httpx transport |
| `tests/test_provider_smoke.py` | new | 4 CLI smoke-command tests (success ledger, zero-cost failure, budget breach, missing key) |

## Implemented and verified

- Accurate cost calculation including cache-write and cache-read tokens — `test_cost_calculation_is_accurate`, `test_cache_tokens_are_billed`, `test_success_accumulates_all_token_categories`
- Unknown model pricing fails closed before any HTTP call — `test_unknown_model_pricing_fails_closed`, `test_unknown_model_refuses_before_any_call`
- Task-budget refusal before the first call, before a continuation, and against prior recorded task spend — `test_budget_refusal_before_first_call`, `test_budget_refusal_before_continuation`, `test_prior_task_cost_counts_against_budget`
- 429 retry with bounded jittered backoff and exhaustion; retryable 5xx; non-retryable 4xx; timeouts; malformed JSON — `test_429_*`, `test_retryable_5xx_recovers`, `test_non_retryable_4xx_fails_immediately`, `test_timeout_is_retried_then_raised`, `test_malformed_json_is_classified`
- `max_tokens` truncation continuation and `pause_turn` resumption — `test_max_tokens_truncation_gets_a_bounded_continuation`, `test_pause_turn_continues_without_injected_user_message`
- Malformed tool input, unknown tool names, missing tool_use ids, invalid structured output feedback — four dedicated tests
- Max-turn exhaustion typed and persisted with spend kept in the ledger — `test_max_turn_exhaustion_is_typed_and_persisted`
- Cancellation persists partial usage and a failure record — `test_cancellation_persists_partial_usage`
- Sanitized failure records never contain the API key — `test_failure_records_never_contain_the_api_key`
- Zero-cost live success rejected — `test_zero_cost_success_is_rejected_in_live_mode`
- Smoke CLI: success with non-zero persisted ledger exits 0; zero-cost success exits 1; budget breach exits 1; missing key exits 2 — `tests/test_provider_smoke.py`
- All 7 pre-existing tests still pass.

## Implemented but not live-verified

- The full live loop against api.anthropic.com (`provider-smoke`), because `ANTHROPIC_API_KEY` does not exist in this environment and the mission forbids asking for it. Every HTTP behaviour above was verified against a scripted transport, not the live service.
- Default pricing values in `pricing.py` were written from model list prices; verify against the current Anthropic pricing page before the live smoke run and override via `MASTER_MODEL_PRICING_JSON` if they have changed.

## Not implemented

- Retry-After header honouring on 429 (bounded backoff is used instead) — not required by the mission text.
- Streaming; the adapter remains non-streaming JSON, as before.

## Tests and commands

```text
python -m pytest -q
36 passed, 1 warning in 2.52s

python -m compileall src tests
OK (exit 0)

ruff check .
Found 70 errors (all pre-existing style issues; exact listing below).

git status --short / git diff --stat
10 source files modified, 6 files added; 615 insertions, 71 deletions (before docs)
```

Remaining ruff findings (pre-existing; none introduced by this session): E501 long lines in `birth.py` (13), `mock.py` (12), `evolution.py` (10), `store.py` (8), `tools.py` (6), `core.py` (4), `drive.py` (2), `agents.py`, `context.py`, `tests/test_birth.py` (1 each); I001 import sorting in `scripts/verify_repository.py`, `birth.py`, `core.py`, `evolution.py`; F401 unused imports in `core.py` (2), `execution.py`, `providers/mock.py`, `tests/test_evolution.py`; UP035 typing imports in `providers/base.py`, `store.py`, `tools.py`; UP017 in `util.py`; B008 typer defaults in `cli.py` lines 41–42. Run `ruff check --output-format=concise .` for the exact line-by-line list; 13 are auto-fixable with `ruff check --fix`.

## Cost and provider evidence

- Provider: anthropic (live) — not run
- Model: not run
- Calls: not run
- Input tokens: not run
- Output tokens: not run
- Cache creation tokens: not run
- Cache read tokens: not run
- Retries: not run
- Stop reason: not run
- Estimated cost: not run
- Configured budget: `provider-smoke` defaults to 0.10 USD

No live call occurred; all evidence above comes from deterministic mocked-transport tests.

## Risks discovered

| Risk | Severity | Evidence | Next action |
|---|---|---|---|
| Pricing table drift vs Anthropic's live prices | Medium | Values hardcoded in `pricing.py` from list prices | Check pricing page before first live run; override via `MASTER_MODEL_PRICING_JSON` |
| Worst-case exposure estimate uses chars/4 input heuristic | Low | `_enforce_budget` | Conservative for English prose; revisit if budgets are set very tight |
| `TaskExecutor` records usage only on success; provider records on failure — both paths covered, but a future second live provider must follow the same contract | Low | `execution.py` / `anthropic.py` | Document in provider protocol when a second provider is added |
| Original repo scramble root cause unknown (browser download flattening suspected) | Low | Git rename detection on the restore commit | Always push from a real git clone, not per-file uploads |

## Rollback notes

All changes are on branch `claude/session-091xzj` in two commits (restore + hardening). Revert the hardening commit to return to the clean v2.1 package, or delete the branch to discard everything. The `usage`-table migration only adds nullable/defaulted columns, so an old code version still works against a migrated database.

## Next exact action

Run locally, where your `.env` already contains `ANTHROPIC_API_KEY`:

```bash
master-character provider-smoke --budget-usd 0.10
```

Exit 0 with a non-zero cost table proves the live ledger; any non-zero exit brings back the printed failure category for the next session.
