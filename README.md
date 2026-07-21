# Initial-stage handoff

Start with `SETUP_WINDOWS.md` or `SETUP_UNIX.md`. Claude Code should receive `CLAUDE_CODE_WEB_START.md` after the repository passes `python scripts/verify_repository.py`.

# MASTER CHARACTER v2

Master Character is the main body of **Under My Enterprise**.

It is not a chatbot wrapper and not a decorative dashboard. It is a persistent, founder-aligned meta-agent kernel designed to:

- receive a high-level command from Ryan;
- understand the desired outcome, constraints, and success test;
- create the specialist agents required for the mission;
- build and execute a dependency-aware task graph;
- maintain memory, state, cost, approvals, and evidence;
- run bounded research when idle;
- detect capability gaps;
- ask its Trainer to propose mutations;
- evaluate and version improvements;
- preserve its identity independently of any model provider.

The model is an organ. Master Character owns the identity, memory, objectives, agent registry, evaluation history, and operating loop.

## Birth sequence

1. Load the Charter and immutable rules.
2. Restore persistent identity and state.
3. Create Trainer as the first child.
4. Trainer creates Researcher and Evaluator.
5. Create Mission Architect and Operator.
6. Queue the first bounded self-research mission.
7. Ask: **Master, what do you want me to accomplish?**

## Main operating loop

```text
Master command
  -> Mission Architect
  -> Agent Factory
  -> Task graph
  -> Child-agent execution
  -> Evidence and artifacts
  -> Evaluation
  -> Result to Master
  -> Memory and outcome update
  -> Trainer proposes improvement
  -> Evaluation / approval / promotion
  -> repeat
```

## Quick start

### Windows PowerShell

```powershell
cd master-character-v2
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
master-character birth
master-character command "Build a working research engine for Master Character"
master-character step --until-idle
master-character status
```

### Start the operator API

```powershell
master-character serve
```

Open `http://127.0.0.1:8765`.

### Live Anthropic mode

Put your key in `.env` and set:

```env
MASTER_PROVIDER=anthropic
```

The live adapter uses the Anthropic Messages API with a forced structured-result tool, bounded tool loops, prompt caching for stable Charter context, usage logging, and task budgets.

## Claude Code handoff

The repository contains:

- `CLAUDE.md`, automatically loaded by Claude Code as project instructions.
- `docs/CLAUDE_CODE_START_PROMPT.md`, the exact first mission to paste into Claude Code.
- `.claude/settings.json`, conservative project permissions.

Run Claude Code from the repository root, then paste the prompt:

```powershell
claude --permission-mode acceptEdits
```

Do not use `--dangerously-skip-permissions`.

## Current scope

Implemented now:

- persistent identity;
- append-only event log;
- master directives;
- mission planning;
- child-agent specifications and versioning;
- dependency-aware tasks with leases and retries;
- bounded model routing;
- safe workspace tools;
- approval queue;
- background research scheduling;
- mutation proposals and prompt-version promotion;
- CLI and JSON API;
- mock and Anthropic cognition providers;
- test suite.

Next build for Claude Code:

- real source-backed research adapters;
- benchmark arena for candidate code branches;
- richer outcome-learning;
- MCP connector runtime;
- robust recovery and concurrency tests;
- provider gateway for cheap Chinese models.

## Claude Code workflow

The permanent Claude Code instructions are in `CLAUDE.md`. The only active workstream is defined in `docs/CURRENT_MISSION.md`. Start each session by pasting `docs/CLAUDE_CODE_START_HERE.md` into Claude Code.
