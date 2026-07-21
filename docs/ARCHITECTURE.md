# Master Character v2 Architecture

## The main body

`MasterCharacter` is the deterministic body. It owns lifecycle and state transitions.

It coordinates:

- `BirthSequence`: creates identity and initial child lineage.
- `MissionArchitect`: turns a Master directive into a typed plan.
- `AgentFactory`: compiles child-agent specifications.
- `TaskExecutor`: runs one child against bounded tools and records evidence.
- `DriveEngine`: schedules internal research and improvement when external missions are idle.
- `ResearchEngine`: manages bounded source-backed research jobs.
- `EvolutionEngine`: creates, evaluates, stages, and promotes controlled mutations.
- `ApprovalService`: pauses consequential actions for Ryan.
- `EventStore`: persists history and recoverable state.
- `CognitionProvider`: replaceable reasoning organ.

## Deterministic versus cognitive

Deterministic code owns:

- IDs and correlation;
- budgets;
- permissions;
- leases and retries;
- state transitions;
- dependency readiness;
- approvals;
- event history;
- cost shutdown;
- promotion policy;
- rollback metadata.

Models own:

- planning proposals;
- research synthesis;
- agent role design;
- artifact creation;
- criticism;
- mutation proposals;
- explanation.

## Growth

Growth is not unrestricted replication.

It is a closed engineering loop:

```text
observe weakness
 -> define capability gap
 -> research
 -> propose mutation
 -> stage candidate
 -> benchmark against baseline
 -> policy review
 -> founder approval where required
 -> promote or reject
 -> record outcome
```

## Interface boundary

The operator interface can submit commands, inspect state, and resolve approvals. It does not contain business logic.
