# Hermes Event-Governed Agent Control Plane

Scope: this reference applies only to Hermes Agent self-architecture work: Hermes core agents/workers, taskpool/brain lifecycle control, gateway/cron ingress, Control Tower Ledger, multi-model certification, and memory/skill self-improvement paths.

Applicability: use when designing, modifying, or auditing Hermes-owned automation that can affect lifecycle state, persistent learning surfaces, external side effects, or worker permissions.

Anti-conditions: do not apply this heavy control-plane flow to ordinary user Q&A, read-only file inspection, simple calculations, or unrelated application projects unless those projects explicitly adopt the same control-plane architecture.

Canonical SSOT for the local default profile: `/Users/charles/.hermes/docs/private/hermes-event-governed-agent-control-plane-20260608.md`.

## Core architecture

Do not build a universal autonomous super-agent. Use a narrow-permission, event-governed control plane:

```text
User / CLI / Gateway / Cron / Webhook
        ↓
Event Router / Collector
        ↓
Control Tower / Orchestrator
        ↓
Policy / Danger Gate ── Human Gate
        ↓
Bounded Worker / Tools
        ↓
Evidence Packet
        ↓
Verifier / Multimodel Certifier
        ↓
Ledger API / SSOT Guard
        ↓
Taskpool / Brain / Memory / Skills / Session / Cron Registry
        ↓
Projection Builder / Dashboard / Gateway Report
```

## Non-negotiable invariants

1. Workers submit evidence/proposals; they do not directly mark tasks done/archive/reopen.
2. Model consensus is advisory and never a fact substitute.
3. Gateway, dashboard, reports, and projections do not directly mutate lifecycle.
4. Memory and skill writes default to proposal-only unless explicitly approved.
5. Cron/webhook/untrusted ingress must not inherit high-trust CLI permission.
6. Dangerous actions need policy/danger gate, explicit confirmation, action preview, audit event, and rollback/escape path.
7. SSOT beats projection; projections must be disposable and replayable.

## Implementation surfaces

- Repo module: `hermes_cli/event_governed_agents.py`
- Contract tests: `tests/hermes_cli/test_event_governed_agents.py`
- Existing Control Tower ledger: `hermes_cli/control_tower.py`

The `event_governed_agents` module is report-only and deterministic. It classifies action paths and generates a JSON contract report; it does not execute tools or mutate lifecycle.

## Fast / Standard / Guarded

- Fast: read-only, no persistence, no side effects.
- Standard: scoped work plus evidence packet and verifier verdict.
- Guarded: task lifecycle changes, memory/skill/cron/provider changes, external send/write/deploy/delete; requires policy/human gate.

## Evidence levels

- E0: claim only; never enough for done.
- E1: static evidence.
- E2: execution evidence.
- E3: external receipt or human acceptance.
- E4: sustained operational evidence.

Default done requires E2. External side effects require E3. Long-running automation maturity requires E4.

## Usage guidance

Before adding any new Hermes-owned agent/worker/hook:

1. Identify the SSOT fact domain.
2. Define the event envelope and dedupe key.
3. Classify the path as fast/standard/guarded.
4. Define role permissions and forbidden actions.
5. Define evidence level required to advance state.
6. Keep first landing report-only/proposal-only unless the user explicitly approves a bounded write path.
7. Add tests proving worker outputs cannot bypass the gate.

Falsifier/demotion rule: if a future Hermes implementation proves a narrower deterministic gate already enforces these invariants at runtime, keep this reference as background and prefer the runtime gate/test suite as the operational authority.
