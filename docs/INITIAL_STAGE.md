# Initial Stage Plan

## Stage 0: Repository ready

Definition:

- Complete codebase committed to GitHub.
- Claude Code can read the sentinel files.
- No secrets are committed.
- Baseline tests can be installed and executed.

Pass condition:

```text
python -m pytest -q
```

returns seven passing baseline tests before Session Zero changes.

## Stage 1: Provider hardening

Only the live Anthropic adapter and the supporting cost, retry, failure, and smoke-test paths are in scope.

Required result:

- real usage categories are recorded;
- unknown pricing fails closed;
- task budgets stop calls before exposure exceeds the ceiling;
- provider errors are classified;
- retries are bounded;
- failure records are sanitized and persisted;
- one explicit live smoke command exists;
- all deterministic tests pass.

## Stage 2: Live provider proof

Run one minimal structured request.

Constraints:

- no web search;
- no side-effecting tools;
- no external messages;
- no publishing;
- no spending beyond the configured API ceiling;
- API key remains local;
- recorded successful cost must be greater than zero.

## Stage 3: First real general mission

Use the ordinary Master directive interface.

Mission payload:

- produce a verified Siteupfit audit and improvement proposal for one business selected by Ryan;
- do not contact the business;
- do not publish;
- preserve sources, assumptions, artifacts, model usage, tool calls, failures, and decisions.

This proves the architecture remains general while touching real commercial work.

## Stage 4: Evolution from real failures

Build baseline-versus-candidate evaluations from concrete failures observed in Stage 2 and Stage 3.

Do not invent synthetic self-improvement claims when real failure evidence exists.
