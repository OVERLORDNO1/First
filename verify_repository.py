# Master Character: Project Context

## The project

Master Character is a persistent, founder-aligned artificial worker and creator system.

It is not a normal chatbot and it is not one hardcoded business workflow.

Ryan gives Master Character an objective. The system should then:

1. Understand the intended outcome and constraints.
2. Build a mission plan.
3. Select or compile specialist child agents.
4. Give each child a purpose, tools, permissions, budget, outputs, evaluations, and stop conditions.
5. Execute dependency-based work.
6. Preserve state across restarts.
7. Research missing knowledge through bounded tools.
8. Evaluate real outcomes.
9. Propose controlled improvements to agents, prompts, workflows, tools, memory, routing, and code.
10. Keep Ryan as final authority for consequential actions.

Siteupfit is the first commercial mission payload. It is not the identity of the architecture.

## Fixed vision

The system should behave like a virtual worker that begins operating when it is booted, asks its Master what outcome is required, and then works continuously within explicit limits.

The ambition must not be reduced into:

- a dashboard around one model;
- a static workflow;
- a Siteupfit-only application;
- a collection of cute demo agents;
- an architecture document with no executable lifecycle;
- an uncontrolled self-replicating system;
- a system that calls prompt edits "model training."

## Current engineering reality

The repository has a working deterministic mock lifecycle and seven baseline tests.

The live Anthropic provider has not yet been proven. Its current cost accounting is incomplete, so the first engineering session must harden the provider and make the budget real before a live smoke test.

## Current sequence

1. Put this complete codebase in one GitHub repository.
2. Let Claude Code select that repository.
3. Run Session Zero: live provider hardening.
4. Run one minimal live cognition smoke test with a hard cap.
5. Run the first general mission using Siteupfit as the payload.
6. Use actual mission failures to build the first meaningful evolution benchmarks.
