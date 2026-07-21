# Master Character v2 Build Report

## What was built

Master Character v2 is a fresh main-body implementation, not a modification of the earlier lightweight prototype.

The kernel now includes:

- Persistent Master Character identity
- Charter and immutable rules
- Birth lineage: Trainer, Researcher, Evaluator, Mission Architect, Operator
- Master directive intake
- Typed mission planning
- Dynamic child-agent compilation
- Dependency-aware task graph
- Atomic task leasing and expired-lease recovery
- Bounded tool execution inside a controlled workspace
- Append-only event history enforced by SQLite triggers
- Memory and model-usage records
- Daily and per-task cost boundaries
- Background research and evolution drive
- Mutation proposal, structural evaluation, candidate staging, approval, and prompt-version promotion
- Conservative approval queue
- Replaceable cognition-provider interface
- Deterministic mock provider
- Anthropic Messages API adapter with structured-result tool calls and bounded tool loops
- CLI and JSON API
- Claude Code project memory, permissions, startup scripts, and engineering mission prompt

## Verified lifecycle

The deterministic mock lifecycle was run end-to-end:

1. Master Character born
2. Seed children created
3. Master command accepted
4. Mission planned
5. Mission-specific agents created
6. Research task completed
7. Build task completed
8. Evaluation task completed
9. Internal capability research completed
10. Trainer proposed a mutation
11. Mutation was evaluated and staged
12. One approval request was created for Ryan

## Verification

```text
python -m compileall -q src tests
pytest -q
```

Result:

```text
7 passed
```

## Not live-tested

No live Anthropic request was made because no API key was provided. The Anthropic adapter is implemented behind configuration and should be verified by Claude Code against the current SDK/API behavior before production use.

## Claude Code handoff

Claude Code should load `CLAUDE.md` automatically. Paste the full contents of:

```text
docs/CLAUDE_CODE_START_PROMPT.md
```

The first Claude Code mission focuses on runtime integrity, real research adapters, evolution benchmarking, model-gateway resilience, tests, and observability.
