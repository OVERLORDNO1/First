# Claude Provider Audit — Session Zero

Date: 2026-07-21
Scope: `src/master_character/providers/anthropic.py` and the cost/usage path it feeds.
Baseline before edits: `python -m pytest -q` → 7 passed; `python -m compileall src tests` → OK; `ruff check .` → 72 pre-existing errors.

Concrete defects only.

## D1. Cost is hardcoded to zero

- File/symbol: `providers/anthropic.py`, `AnthropicProvider.structured` (return path).
- Defect: `estimated_cost_usd=0.0` is emitted for every successful call. There is no pricing source anywhere in the repository.
- Consequence: `Store.daily_cost()` always sums zero for live runs, so `TaskExecutor.execute`'s daily-cost gate (`execution.py:25`) and `Settings.max_daily_cost_usd` are inert. Live spend is unbounded by the kernel.
- Proof: grep for `estimated_cost_usd` — the only non-default assignment is the literal `0.0` at the provider return.
- Correction: pricing registry keyed by (provider, exact model id), fail-closed for unknown models; compute per-call cost from returned usage.

## D2. `cost_budget_usd` is accepted and ignored

- File/symbol: `AnthropicProvider.structured` parameter `cost_budget_usd`.
- Defect: the parameter is never read inside the method. The loop can make `max_turns` full-size calls regardless of budget.
- Consequence: task budgets (`Task.cost_budget_usd`, `AgentSpec.cost_budget_usd`) are decorative in live mode.
- Proof: no reference to `cost_budget_usd` after the signature line.
- Correction: before every call (initial and continuation), compute accumulated cost plus a bounded worst-case next-call exposure; refuse cleanly when the budget cannot cover it.

## D3. Cache token categories are dropped

- File/symbol: `AnthropicProvider.structured` usage parsing; `domain.ModelUsage`; `Store.record_usage` / `usage` table.
- Defect: only `input_tokens` and `output_tokens` are read. `cache_creation_input_tokens` and `cache_read_input_tokens` are discarded, even though the adapter itself enables `cache_control` when `settings.prompt_cache` is true.
- Consequence: cache writes (billed above base input rate) and cache reads are invisible; any future cost computation over the persisted record would be wrong.
- Proof: `usage.get("input_tokens", 0)` / `usage.get("output_tokens", 0)` are the only fields consumed; the `usage` table has no cache columns.
- Correction: extend `ModelUsage` and the `usage` table with cache-creation and cache-read token counts, plus calls/retries/stop-reason metadata.

## D4. No retry or backoff classification

- File/symbol: `AnthropicProvider.structured`, `response.raise_for_status()`.
- Defect: every HTTP error — 429, 500, 529, 400 — raises `httpx.HTTPStatusError` identically, with no retry, backoff, jitter, or classification. Timeouts and connection failures propagate raw.
- Consequence: a single transient 429 or overloaded-529 kills the whole task; conversely nothing prevents a naive caller from hammering retries outside any budget.
- Proof: `raise_for_status()` is the only status handling; no `try` around the POST.
- Correction: bounded exponential backoff with jitter for 429/5xx/timeouts; immediate typed failure for other 4xx; retries counted and kept inside the cost and turn budgets.

## D5. Malformed JSON responses are unhandled

- File/symbol: `response.json()` call.
- Defect: a truncated or non-JSON body raises a raw `json.JSONDecodeError` from deep inside httpx.
- Consequence: no classification, no failure record, no sanitized message.
- Correction: catch decode failure, classify as retryable transport corruption, bound retries.

## D6. `stop_reason` is never inspected

- File/symbol: response handling in the turn loop.
- Defect: `data["stop_reason"]` is ignored. A `max_tokens` truncation silently falls through to the "you have not returned the structured result" nudge with the truncated assistant content left in history; `pause_turn` is not continued correctly.
- Consequence: truncated tool-use JSON can be treated as complete; long-turn server pauses derail the loop.
- Correction: explicit handling for `max_tokens` (bounded continuation nudge) and `pause_turn` (resume with assistant content, no injected user message).

## D7. Structured-result validation failure is fatal with no feedback loop

- File/symbol: the `ValidationError` branch → `raise ValueError`.
- Defect: one invalid `emit_structured_result` input aborts the task instead of returning the validation error to the model as a `tool_result` within the remaining turn/cost budget. The accumulated usage is also lost (nothing recorded).
- Consequence: avoidable task failures and unaccounted spend.
- Correction: feed the validation error back as an error `tool_result` and continue while turns/budget remain; record usage regardless of outcome.

## D8. Malformed tool input and unknown tools are conflated

- File/symbol: tool dispatch loop.
- Defect: a non-dict `input`, or a hallucinated tool name, reaches `tool_executor` unchecked (or produces a generic "No executor" result without `is_error`).
- Consequence: executor crashes on bad input; the model gets no structured error signal.
- Correction: validate tool input shape, return `is_error: true` tool results for unknown tools and malformed input.

## D9. Usage is lost on every failure path

- File/symbol: all raise paths in `structured`; `TaskExecutor.execute` records usage only after success.
- Defect: if the loop raises (validation, max turns, HTTP error), tokens already consumed are never persisted anywhere.
- Consequence: real money spent on failed calls is invisible to the daily ledger — the exact spend that most needs recording.
- Correction: persist usage and a sanitized provider-failure record on failure paths.

## D10. No failure records at all

- File/symbol: whole provider; `Store` has no failures table.
- Defect: there is no persistence of correlation id, status, stop reason, retry decision, or sanitized error for provider failures.
- Consequence: live incidents are undiagnosable after the fact.
- Correction: `provider_failures` table + sanitized record writer; never store keys, auth headers, or request bodies.

## D11. Cancellation is unhandled

- File/symbol: turn loop.
- Defect: `asyncio.CancelledError` propagates with no usage/failure persistence.
- Correction: on cancellation, persist what was already spent, then re-raise.

## D12. Max-turn exhaustion raises a bare `RuntimeError`

- File/symbol: final `raise RuntimeError(...)`.
- Defect: untyped error, no usage recording, no failure record.
- Correction: typed `MaxTurnsExceededError` with usage persisted.

## D13. No live smoke path exists

- File/symbol: `cli.py`.
- Defect: there is no command that exercises the live provider in a bounded way; the only lifecycle proof is the mock.
- Correction: `master-character provider-smoke --budget-usd 0.10` per the mission specification.

## Non-defect observations (baseline facts)

- `ruff check .` reports 72 pre-existing errors across the package (unused imports, line lengths). Not introduced by this session; listed in the handoff.
- The mock provider returns `ModelUsage` with zero cost by design; acceptable for `provider="mock"` only. Zero-cost success must remain an error in live mode only.
