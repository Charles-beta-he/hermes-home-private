# PRD — Embodied Workflow Core P1/P2

Generated: 2026-07-02T18:58:00+08:00
Boundary: implementation-ready local contract package, not UI/hardware.

## Problem

Hermes has a strong brain/CLI layer but lacks stable outer-tool contracts. Without contracts, each new entry point (Web, PWA, glasses, embedded, robot) will tend to duplicate workflow logic and bypass evidence/safety gates.

## Goal

Deliver a minimal, tested contract-only package that proves adapters can register capabilities, submit observations, request actions, and replay evidence without Core depending on platform code.

## Non-goals

- No real hardware.
- No robot execution.
- No Web product UI.
- No external dispatch.
- No model-direct action execution.
- No NAS hot runtime.

## Users / actors

- Human operator: asks, confirms, performs manual actions.
- Hermes planner: proposes ActionIntent but does not execute directly.
- Adapter implementer: adds Web/PWA/glasses/embedded/robot support.
- Supervisor: audits evidence, gates, and workflow state.
- Future robot actor: consumes safe ActionIntent subset.

## Requirements

### R1 Capability manifests

System accepts manifests for CLI, Web mock, glasses mock, embedded mock, robot mock.

Acceptance:
- manifest with missing `risk_class` fails;
- executable/physical capability without `readback_required`, `audit_required`, and gates fails;
- observation-only capability may register with lower gate requirements;
- registry output is queryable by required observation/action.

### R2 Observation normalization

All input sources submit `Observation` with evidence refs and derived facts.

Acceptance:
- Web image upload and glasses image mock share same schema;
- voice transcript and text question share intent path;
- adapter cannot direct-write WorldState.

### R3 ActionIntent envelope

All proposed actions use `ActionIntent`.

Acceptance:
- human guidance, robot dry-run, embedded light/buzzer dry-run share same envelope;
- no external/physical action executes without SafetyGate + ExternalControlGate status;
- idempotency key required for executable actions.

### R4 Evidence ledger and replay

All material events append to EvidenceLedger; WorldState is derived.

Acceptance:
- append-only ledger entries have checksum/hash;
- replay reconstructs WorldState from ledger;
- completion claim without verification/evidence is rejected.

### R5 Entry recommendation

System can recommend best entry based on needed capabilities.

Acceptance:
- first-person visual need recommends glasses/mobile camera;
- long fixed observation recommends embedded/fixed camera;
- complex editing recommends Web/PC Workbench;
- high-risk physical action recommends onsite human confirmation or blocks.

## Metrics

- Contract validation coverage: every required contract has positive and negative fixtures.
- Adapter neutrality: adding mock adapter requires zero Core code changes.
- Safety fail-closed: unsafe executable capability fixtures fail.
- Replay determinism: replayed WorldState matches snapshot fixture.

## P1/P2 completion boundary

`validated-slice` only when tests and fixture replay pass. No production/runtime/hardware claims.
