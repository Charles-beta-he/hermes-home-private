# Control Tower command proposal and workflow-schema reference

## Scope / applicability / anti-condition

Scope: Hermes Agent workflow-control-plane work where the user is designing or extending a Control Tower-style orchestrator, dashboard, taskpool/kanban adapter, command surface, human inbox, or ledger-backed workflow map.

Applicability: use only when a project has, or is explicitly choosing, a single durable workflow ledger and treats UI/task boards/workers as adapters or projections.

Anti-condition: do not apply this to ordinary product feature work, unrelated dashboards, or projects that have not chosen a single canonical workflow fact source. Do not vendor the referenced external project or copy its APIs into Hermes by default; extract only the class-level architecture patterns below.

## Phase 2 pattern: proposal-only command registry

The next safe slice after read-only snapshot is a **proposal-only** command registry, not an executor.

Durable rules:

- The ledger remains the only canonical workflow fact source.
- Dashboard, gateway, kanban, taskpool, CLI, and worker surfaces may propose commands but do not own command truth.
- A proposed command records operator/agent intent; it must not execute lifecycle actions.
- Persist `status=proposed`, idempotency key, actor, target, risk level, payload, source surface, and audit timestamps.
- Emit a `CommandProposed` event for every newly recorded command.
- L0/L1 commands are still `not_executed`; they may be eligible for future low-risk executors but should not execute in this slice.
- L2+ commands should also create a `human_approvals` pending row and emit `HumanApprovalRequested`.
- Idempotency lookup must return the existing command without duplicating events/approvals.
- Snapshot should expose a command registry projection (`proposed_count`, recent proposed commands) and a human inbox projection (`pending_count`, pending approvals).

Stop before:

- approve/reject semantics if not defined,
- executor authority,
- write-through adapters,
- task claim/release/mark-done,
- evidence attach with lifecycle effect,
- arbitrary shell or dashboard-triggered mutation.

Verification shape:

- RED test: missing proposal API/function fails.
- Unit tests: proposed command insert, audit event, idempotency dedupe, L2+ human approval request.
- Plugin/API tests: dashboard proposal endpoint returns `proposed` and `execution=not_executed`.
- Smoke: isolated home/profile, propose an L0 command, assert snapshot command count increments and human inbox remains zero.

## Phase 3A recommended boundary: approval lifecycle, still no execution

Before any executor exists, stabilize approval records:

- approve/reject APIs update only ledger approval state.
- approvals are single-use/idempotent and bound to command identity/hash.
- emit `HumanApprovalGranted` / `HumanApprovalRejected`.
- snapshot shows pending and decided approvals.
- no target command is executed.

This keeps human-gate semantics auditable before granting executor power.

## External reference pattern: OpenSpec-style workflow schema

A review of Fission-AI/OpenSpec produced useful class-level patterns for workflow schema/projection design, but it should be treated as a reference pattern, not as a dependency.

Helpful patterns to adapt:

1. **Schema-defined workflow graph**
   - Define nodes/artifacts, dependencies, and readiness predicates declaratively.
   - Validate duplicate IDs, missing dependencies, and cycles before use.
   - Compute ready/blocked nodes deterministically.

2. **Fluid actions, not rigid phases**
   - A graph should explain what is ready and what is blocked; it should not force a brittle phase machine.
   - Human edits/evidence/approvals can change readiness and trigger recomputation.

3. **Scoped context/rule injection**
   - Project/workflow rules can guide prompts, dashboard explanations, and proposed commands.
   - Store activation/version in the ledger or scoped config; do not promote local rules into global memory or global hard gates without explicit elevation.

4. **Workspace/local view projection**
   - Multi-repo context can be modeled as a private workspace projection over linked repos/folders/task sources.
   - Local path bindings are private/config projection data, not canonical workflow facts.

5. **Adapter registry**
   - Keep command content tool/surface agnostic.
   - Surface adapters format, display, and submit command proposals; they do not own command state.

6. **Verification dimensions**
   - Completeness: tasks/requirements covered.
   - Correctness: tests/proofs/requirements match.
   - Coherence: design/ADR/policy alignment.
   - Store reports as evidence rows/events, not chat-only summaries.

Cautions:

- Do not use filesystem existence as completion truth. Files are evidence artifacts; ledger events and policy decisions are canonical.
- Prompt/artifact orchestration does not replace approval/executor governance.
- Treat external workspace support as conceptual reference unless a stable API is explicitly adopted.
- If experimenting with a third-party CLI locally, check telemetry defaults and set the documented opt-out when needed.

## Suggested schema slice

After approval lifecycle is stable, add a ledger-backed workflow schema projection:

- Define a minimal schema for command lifecycle nodes such as `command_proposed`, `approval_requested`, `approval_decided`, and future disabled `executor_eligible`.
- Validate duplicate node IDs, missing dependencies, and cycles.
- Add snapshot fields: `workflow_map.nodes`, `workflow_map.ready`, `workflow_map.blocked`.
- Keep execution disabled until executor authority/policy is separately approved.
