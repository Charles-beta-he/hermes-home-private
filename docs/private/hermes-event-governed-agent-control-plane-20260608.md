# Hermes Event-Governed Agent Control Plane

**Goal:** Land a stable long-term Hermes Agents architecture as governed contracts, report-only gates, and implementation backlog.
**Status:** in_progress
**Created:** 2026-06-08

## Scope

Implement the safe foundation now:
- architecture SSOT;
- event/evidence/policy/ledger contract code;
- report-only validation CLI;
- tests proving worker output is evidence/proposal, not done authority;
- skill reference so future Hermes self-optimization loads this pattern.

Do not implement full autonomous execution or dangerous writes in this tranche.

## Architecture Decision

Hermes should use an event-governed control plane rather than a universal autonomous agent.

Pipeline:

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

## Non-negotiable Invariants

1. A worker must not directly mark a task done.
2. Model consensus is advisory; it is not fact or evidence.
3. Gateway/dashboard/projection surfaces must not directly mutate lifecycle.
4. Memory and skill changes default to proposal-only unless explicitly approved.
5. Cron/webhook/untrusted input must not inherit high-trust CLI permissions.
6. Dangerous actions require explicit confirmation, action preview, audit record, and rollback/escape path.
7. SSOT wins over projection; projection is disposable and replayable.

## Evidence Levels

- E0: claim only; never sufficient for done.
- E1: static evidence such as diff/config/code refs.
- E2: execution evidence such as tests/build/API/browser/CLI output.
- E3: external receipt or human acceptance.
- E4: sustained operational evidence such as repeated health checks/regression replay.

Default done requires at least E2. External side effects require E3. Long-running automation maturity requires E4.

## Fast / Standard / Guarded Paths

- Fast: read-only, no persistence, no external side effects.
- Standard: scoped local writes plus evidence packet and verifier verdict.
- Guarded: state mutation, memory/skill/cron/provider changes, external side effects, task done/archive/reopen; requires policy/human gate.

## Implementation Plan

- [x] SSOT document created.
- [ ] Inspect repo and current tests.
- [ ] Add RED tests for contracts and policy invariants.
- [ ] Implement contract module and report-only CLI.
- [ ] Add Hermes skill reference.
- [ ] Run focused tests and validation.
- [ ] Scoped commit.

## Landing Boundary

This tranche is a safe foundation. It may add report-only validators and docs. It must not silently enable new autonomous writes or external side effects.
