# Current Claude Code Mission

## Session Zero: Live Anthropic Provider Hardening

This is the only active workstream.

Do not build the research engine, evolution arena, new interface, new business workflow, or additional autonomous features during this session.

## Purpose

Make the existing Anthropic cognition adapter reliable and financially bounded enough for the first real live smoke test.

The present adapter accepts `cost_budget_usd` but does not enforce it. It records `estimated_cost_usd=0.0`, which makes task and daily cost policies ineffective. The current mock lifecycle therefore does not prove that the live cognition layer is safe or operational.

## Required work

### 1. Inspect and baseline

- Read the provider protocol, Anthropic adapter, configuration, domain usage models, store, execution runtime, CLI, and provider tests.
- Run all existing tests before editing.
- Create `docs/CLAUDE_PROVIDER_AUDIT.md` containing concrete defects only.

### 2. Real cost accounting

Implement a configurable pricing registry keyed by provider and exact model identifier.

Account for every usage field returned by the provider that affects cost, including where available:

- uncached input tokens;
- output tokens;
- cache creation input tokens;
- cache read input tokens;
- server-tool usage or other billable usage.

Requirements:

- Unknown pricing must fail closed or require explicit configuration.
- Never silently assume zero cost.
- `ModelUsage` and persisted usage records must retain the relevant token categories.
- Daily cost and task cost must be based on real recorded values.

### 3. Enforce the task budget

Before making an initial call or any continuation call:

- calculate accumulated task cost;
- determine whether another call is permitted;
- reserve or bound the possible next-call exposure;
- stop cleanly before the configured task budget can be exceeded.

A successful response with zero recorded cost is a failure in live mode.

### 4. Provider resilience

Implement explicit handling for:

- HTTP 429 with bounded exponential backoff and jitter;
- retryable 5xx responses;
- non-retryable 4xx responses;
- connection and read timeouts;
- malformed JSON responses;
- truncated responses or `max_tokens` stop reason;
- `pause_turn` continuation;
- malformed tool input;
- unknown tool names;
- missing or invalid `tool_result` relationships;
- structured-result validation failure;
- max-turn exhaustion;
- cancellation.

Retries must be classified and bounded. A retry is not free and must remain inside the cost and turn budgets.

### 5. Failure records

Persist a sanitized provider failure record containing, where available:

- correlation ID;
- provider;
- model;
- HTTP status;
- request turn;
- stop reason;
- token usage;
- estimated cost;
- retry decision;
- exception category;
- sanitized message;
- timestamp.

Never store API keys, authorization headers, full secret-bearing requests, or `.env` contents.

### 6. Live smoke command

Add one explicit CLI command for a minimal live provider smoke test.

The command must:

- use the normal provider abstraction;
- make one minimal structured request;
- use no web search;
- use no external side-effecting tools;
- accept a hard total cost ceiling;
- print the model, token categories, calls, retries, stop reason, and estimated cost;
- persist the usage record;
- exit non-zero if a successful live call records zero cost;
- exit non-zero if the configured budget is breached;
- never print the API key.

Suggested command shape:

```bash
master-character provider-smoke --budget-usd 0.10
```

Choose the final command based on the existing CLI design.

### 7. Tests

Add deterministic tests using mocked HTTP transport or an equivalent fake provider boundary for:

- accurate cost calculation;
- cache token accounting;
- unknown model pricing;
- task-budget refusal before a call;
- task-budget refusal before a continuation;
- 429 retry and exhaustion;
- retryable 5xx;
- non-retryable 4xx;
- timeout;
- `max_tokens` handling;
- `pause_turn` continuation;
- invalid tool input;
- invalid structured output;
- max-turn exhaustion;
- cancellation;
- sanitized failure persistence;
- live-smoke success with non-zero cost ledger;
- live-smoke failure when the ledger remains zero.

Existing tests must continue to pass.

## Hard constraints

- Do not edit the Charter or immutable rules.
- Do not redesign the whole runtime.
- Do not add a new UI.
- Do not build Siteupfit-specific code.
- Do not add web search.
- Do not add unrestricted shell execution.
- Do not add external messaging, publishing, payment, or trading capabilities.
- Do not run the live smoke test unless `ANTHROPIC_API_KEY` already exists locally.
- Do not ask Ryan to paste an API key into chat.
- Do not declare victory from mock tests alone.

## Mechanical kill criterion

If the live adapter cannot complete a bounded structured tool loop after the implemented fixes, stop feature work and produce the failure evidence. Do not continue building higher layers on the mock provider.

## Definition of done

The session is complete only when:

1. All existing tests pass.
2. All new provider tests pass.
3. Package compilation succeeds.
4. Lint succeeds, or every remaining lint issue is listed exactly.
5. The live smoke CLI command exists.
6. The adapter cannot continue beyond the configured task budget.
7. A successful live call cannot be recorded with zero cost.
8. Sanitized provider failures are persisted.
9. `docs/CLAUDE_PROVIDER_AUDIT.md` exists.
10. `docs/CLAUDE_PROVIDER_HANDOFF.md` exists and follows `docs/HANDOFF_TEMPLATE.md`.
11. The final response provides the exact next command for Ryan.

Do not run later sessions automatically.
