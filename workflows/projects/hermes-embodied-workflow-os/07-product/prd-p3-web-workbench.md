# PRD P3 — Web Workbench (Non-Authoritative Operator Surface)

Status: spec-only, no UI runtime implementation.
Updated: 2026-07-02T19:34:00+08:00

## Objective

Build the first Web-facing surface as a Workbench: a debugging, observation, simulation, and approval console for the stable HEWOS core. The Web Workbench is not the product's authoritative state source and must not bypass ActionIntent, SafetyGate, ExternalControlGate, Verification, or EvidenceLedger.

## Non-goals

- No Web state as source of truth.
- No direct device/robot/hardware execution from UI handlers.
- No `if platform == web` logic inside Core.
- No external dispatch, gateway send, taskpool lifecycle write, deploy, or push from the Workbench.
- No credential/API-key entry or storage.
- No production authentication design in P3; auth is a later gate.

## Users

1. Operator: wants to inspect a task graph, observations, action intents, gates, and evidence.
2. Developer: wants to simulate adapter inputs and verify reducers/gates.
3. Approver: wants to approve/reject a pending medium-risk ActionIntent after reading evidence.

## Product shape

The Workbench has four read-heavy pages and one simulation panel.

### 1. Dashboard

Purpose: current system overview.

Required panels:
- active task graphs count
- recent observations
- pending ActionIntents by risk level
- SafetyGate / ExternalControlGate status summary
- EvidenceLedger append rate and latest entries
- adapter health projection from capability manifests

Authority:
- read-only
- no direct action execution

### 2. TaskGraph Inspector

Purpose: inspect canonical task graph and derived WorldState.

Required panels:
- task graph nodes/edges
- node state derived from EvidenceLedger replay
- observations linked to nodes
- completed/blocked steps
- missing evidence checklist

Authority:
- may create simulation-only observations
- must not mutate canonical task graph directly

### 3. ActionIntent Review

Purpose: review pending intents.

Required panels:
- action preview
- risk level
- required gates
- evidence refs
- readback requirements
- rollback/stop strategy
- approval/rejection controls

Authority:
- P3: dry-run approve/reject only
- P4+: approval may generate a new ledger entry; still no direct adapter execution
- physical/high-risk intent must show onsite human gate and remain blocked unless exact authority packet exists

### 4. EvidenceLedger Browser

Purpose: browse append-only evidence.

Required panels:
- ledger entries by time
- subject_id filters
- evidence refs and hashes
- payload preview with redaction
- replay button for local derived state

Authority:
- read-only
- replay is deterministic local computation

### 5. Adapter Simulation Panel

Purpose: feed mock adapter observations into the local core.

Supported P3 mock inputs:
- CLI text observation
- Web form observation
- glasses first-person image metadata placeholder (no image upload in P3)
- embedded sensor text/json placeholder
- dry-run robot capability manifest only

Authority:
- writes only simulation-local EvidenceLedger entries in dev/test harness
- cannot call external adapter code

## Contract projection API

P3 Web must speak only projection APIs backed by core contracts.

Required read/projection endpoints or equivalent local module functions:

```text
GET /projection/capabilities
GET /projection/task-graphs
GET /projection/task-graphs/{id}/world-state
GET /projection/action-intents
GET /projection/evidence-ledger
POST /simulation/observations
POST /simulation/action-intents/{id}/dry-run-review
```

Rules:
- `GET` endpoints are projections from ledger/registry, not direct DB truth.
- `POST /simulation/*` writes only simulation-local entries.
- There is no `/execute` endpoint in P3.
- There is no device/robot/external adapter credential path in P3.

## State model

```text
Core contracts + EvidenceLedger
  -> reducer/replay
  -> projection DTOs
  -> Web Workbench UI state
```

Forbidden:

```text
Web UI state -> Core truth
Web button -> Adapter execute
Web component -> if platform in Core
```

## Acceptance tests before implementation

P3 implementation must include tests proving:

1. Workbench can render projection fixtures without importing hardware/device modules.
2. Dashboard data comes from projection DTOs, not mutable global UI state.
3. ActionIntent Review blocks physical/high-risk execution without both gates and onsite authority.
4. Simulation creates ledger entries and replay derives WorldState.
5. No `execute`, `send`, `deploy`, `push`, `taskpool lifecycle`, or external gateway call exists in P3 code path.
6. Web UI can be removed without breaking Core tests.

## Security and privacy

- Evidence payload preview must redact secrets and credentials.
- Images/video are out of P3 unless represented by metadata fixture only.
- No production user auth; avoid false security claims.
- Workbench must display when data is simulated vs live.

## Exit criteria

P3 spec is complete when:
- this PRD exists and is linked from project profile;
- P1/P2 tests still pass;
- Workbench implementation tasks can be derived without changing Core contracts;
- no UI/runtime code has been written in the spec-only slice.

P3 implementation can start only after a separate local implementation gate.