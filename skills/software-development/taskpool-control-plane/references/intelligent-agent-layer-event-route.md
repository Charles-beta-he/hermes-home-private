# Scoped reference: intelligent agent-layer event route

Scope: applies only to governed taskpool-control-plane systems that already have a canonical taskpool SSOT and a separately governed worker/agent bridge. This is not a global Hermes runtime rule and is not evidence that any specific live deployment currently has runnable work.

Applicability:
- A taskpool event should be able to wake or expand intelligent agents, not just run a single bounded autorun step.
- The user asks that all semantic entrances into the intelligent agents layer be routed through one expansion decision point.
- The implementation has a worker bridge that can re-check eligibility, claims, allowlists, resource caps, and proof gates before execution.

Anti-conditions:
- Do not place agent expansion policy inside the taskpool core state machine.
- Do not let workers create a competing task store or bypass lifecycle/proof gates.
- Do not use this as authority for external dispatch, deploy, publish, destructive actions, credential entry, broad fanout, or direct completion transitions.
- Do not claim that workers spawned if live taskpool readback shows no dispatchable task.

Layering rule:
1. Taskpool remains SSOT: task identity, status, claim/lease, evidence, proof, lifecycle gates.
2. Smart routing decides whether an event should wake the intelligent agents layer.
3. The intelligent agents layer selects/spawns executors through a governed bridge.
4. Workers produce evidence/readback; taskpool gates decide review/done/retry/blocked.

Reusable implementation pattern:
- Add a route classifier for event-to-agent-layer decisions.
- Cover the complete set of semantic agent-layer entrances, e.g. creation, state transition, ingestion, and explicit dispatch authorization events.
- Keep a hard no-spawn kill switch that overrides force/auto routing.
- In auto mode, require dispatchable statuses and explicit/intended execution signals such as agent-required metadata, explicit dispatch authorization, high-priority execution lanes, or another local safe-route policy.
- When the route is enabled, call the governed parallel agent bridge, not an unrestricted side process.
- Let the downstream dispatch tick re-check eligibility, boundary isolation, allowlists, resource caps, claims, and proof gates immediately before spawning.

Verification checklist:
- Unit test the route classifier independently from worker spawning.
- Unit test that a routed event invokes the parallel agent bridge rather than only a single autorun step.
- Unit test that the no-spawn switch blocks both force and auto modes.
- Run syntax/targeted tests for the orchestrator and event-hook tests.
- Read back live taskpool state after landing; if no task is dispatchable, route availability must not be reported as an actual spawn.

Pitfall:
If you answer “the taskpool automatically adds agents,” you collapsed layers. The durable statement is: taskpool authorizes and records; smart routing selects; the intelligent agents layer expands through a governed worker bridge; lifecycle/proof gates remain authoritative.
