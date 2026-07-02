# HEWOS High-Risk Boundary Coverage — 2026-07-03

Status: governance coverage complete for authorized `taskpool/external/hardware/deploy/auth` classes.

Scope:
- Local high-risk boundary catalog and simulation-only ledger receipts.
- Intent-only authorization records for exact local simulation targets.
- No live taskpool write, external send, hardware/robot action, deploy/push, credential entry, token read, or secret persistence.

## Objective model

The user authorized the high-risk classes, but exact live targets and secrets were not supplied. Therefore the correct next rung is not arbitrary execution; it is a local/fail-closed control plane with:

1. one boundary record per requested class;
2. exact-target requirement for later live execution;
3. idempotent simulation ledger receipt for each boundary;
4. rollback/readback plan per receipt;
5. tests proving unscoped live execution is blocked.

## Boundary coverage

Coverage artifact: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/06-verification/high-risk-boundary-coverage-20260703.json`

- Requested boundaries: taskpool_lifecycle, external_dispatch, hardware_execution, deploy_publish, auth_credential
- Governance coverage: 100%
- Live execution enabled: False
- Production resource touched: False

## Simulation ledger

Ledger artifact: `/Users/charles/.hermes/workflows/projects/hermes-embodied-workflow-os/artifacts/simulation-ledger-20260703.jsonl`

Receipts:

- `simreceipt:0e9322f2712e9d5f` — `taskpool_lifecycle` — `local-simulation:taskpool_lifecycle:intent-only` — execution_enabled=False
- `simreceipt:9de8395420cb58ee` — `external_dispatch` — `local-simulation:external_dispatch:intent-only` — execution_enabled=False
- `simreceipt:e4df753bc9b3ddec` — `hardware_execution` — `local-simulation:hardware_execution:intent-only` — execution_enabled=False
- `simreceipt:674365bd7e355d28` — `deploy_publish` — `local-simulation:deploy_publish:intent-only` — execution_enabled=False
- `simreceipt:ac84695ee9a8d1fe` — `auth_credential` — `local-simulation:auth_credential:intent-only` — execution_enabled=False

## Verification claims

- Unscoped `execute` requests for every requested boundary return `blocked` with `execution_enabled=false`.
- Exact local simulation requests return `authorized_intent_only`, not live execution.
- Auth/credential boundary has `agent_may_type_secret=false` and `token_read_allowed=false`.
- Simulation ledger append is idempotent.
- Simulation ledger receipts are rollbackable by exact receipt id.

## Next executable packet requirements

For a later real adapter boundary, each class must supply a fresh exact packet:

- taskpool: exact task id, intended status/action, evidence refs, idempotency key, rollback/readback command.
- external dispatch: exact platform/channel/target, payload hash, allowlist proof, delivery dry-run, post-send readback.
- hardware: exact device id, telemetry freshness, command preview, SafetyGate + ExternalControlGate, audit path, onsite gate when physical risk exists.
- deploy/push: exact repo/env/branch/target, rollback path, build/test receipt, post-deploy readback.
- auth/credential: human enters secrets outside Hermes; Hermes may record only non-secret gate receipts.
