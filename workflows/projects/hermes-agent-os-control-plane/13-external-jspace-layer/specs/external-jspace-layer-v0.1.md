# External J-space Layer v0.1

## Objective

Provide a Hermes-local external equivalent of a model workspace: a structured, auditable layer for goal, constraints, authority, intermediate beliefs, risks, evidence, reflection readback, and completion claim gating.

## Non-goals

- No claim of direct hidden-state or true Anthropic J-space access.
- No automatic taskpool lifecycle mutation in P0.
- No external dispatch, publish/deploy/push, destructive action, credential entry, payment, or broad fan-out.
- No model vote may certify a completion-critical claim without objective evidence.

## P0 capability nodes

```yaml
nodes:
  - id: workspace_projection_builder
    kind: composite_module
    produces: [workspace_projection]
    side_effects: local_write
  - id: evidence_dag_builder
    kind: composite_module
    produces: [evidence_dag]
    side_effects: local_write
  - id: reflection_readback
    kind: gate
    produces: [reflection_packet]
    side_effects: local_write
  - id: completion_claim_gate
    kind: gate
    produces: [completion_claim_packet]
    side_effects: none
```

## Evidence authority ladder

| Level | Authority | Examples | Completion-critical use |
|---|---|---|---|
| L0 | model_judgment | single model review | advisory only |
| L1 | independent_model_agreement | multiple model votes | advisory only |
| L2 | local_readback | file/config/git diff | static facts |
| L3 | executable_verification | tests/build/API smoke | functional facts |
| L4 | external_system_readback | browser/CI/remote API | external state |
| L5 | explicit_human_authority | send/publish/delete/payment authorization | required for high-risk effects |

## Gate semantics

- `objective_defined`: requires goal, non-goals, constraints, and authority boundary.
- `evidence_dag_exists`: requires an initialized evidence DAG with root evidence.
- `reflection_readback`: requires a current reflection packet based only on external workspace state.
- `completion_claim`: blocks or downgrades claims whose completion-critical evidence is missing or only model judgment.

## P0 workflow

```text
init -> status/readback -> add-evidence -> gate-check -> reflect -> closure-packet
```

## Status vocabulary

```text
certified
verified_local
truth_grounded_but_not_certified
advisory_only
degraded_not_certified
blocked_missing_evidence
blocked_missing_authority
blocked_provider_unavailable
blocked_policy_violation
```

## P1/P2 backlog

- P1: projection-only task/event bridge, event ledger, before_review/before_done gate checks (implemented locally); learning candidates remain future work.
- P2: read-only control room, CapabilityGraph projection, surface model router, advisory multi-model review, dry-run learning promotion.

## Exact boundary contract

Every boundary-opening slice must name all four fields before execution:

```yaml
exact_target: one file/workspace/task/channel/repo/resource id only
payload: minimal JSON/event/message/ref that will be sent or written
rollback: exact undo/restore/disable command or human escape hatch
readback: command/file/API receipt that proves target, effect, and negative side effects
```

If any field is missing, the slice may still project a blocker into the workspace/taskpool, but it must not execute the side effect.

## P1 event bridge slice

P1 adds a local projection-only task/event bridge to the P0 helper:

```text
attach-task -> on-event -> workspace_state projection -> before_review/before_done gates -> closure packet event count
```

Supported commands:

```bash
hermes_jspace.py attach-task <workspace_id> --task-id <task_id>
hermes_jspace.py on-event <workspace_id> --event-json '{"source":"taskpool","type":"task.status_changed","from":"running","to":"review"}'
hermes_jspace.py gate-check <workspace_id> --gate before_review
hermes_jspace.py gate-check <workspace_id> --gate before_done
hermes_jspace.py learning-candidates <workspace_id>
```

Boundary: this is not real taskpool lifecycle write-through. It records task references and projected lifecycle events in `event_ledger.jsonl` only.

## Learning candidate boundary

`learning-candidates` writes `learning_candidate.json` as a project-ref proposal only. It does not patch skills, write global memory, alter taskpool lifecycle, or promote runtime behavior.

## P2 read-only dashboard data slice

`dashboard-data` summarizes active workspaces, blocked gate results, evidence health, and learning candidate records from the local J-space root. It is read-only and sets all runtime/taskpool/external side-effect flags false.

## Real-open boundary matrix

`real-open-matrix` reports governance/readback coverage across high-risk side-effect classes. It may execute only scoped safe smokes: exact local taskpool lifecycle write-through, local no-agent cron heartbeat readback, and disposable destructive canary delete/restore. External dispatch, publish/deploy/push, credential/payment entry, broad fan-out, and worker spawn remain blocked until exact target/payload/rollback/readback packets exist.

## Boundary packet examples

### Exact taskpool lifecycle write-through packet

```yaml
exact_target:
  task_id: 2026-07-08-将global-workspace外部投影门禁接入taskpool事件桥与只读仪表盘
  workspace_id: anthropic-global-workspace-analysis-20260708
payload:
  transitions: [pending->claimed, claimed->running, running->review, review->done]
  evidence: command:brain_task_orchestrator-selfcheck-PASS-and-workspace_projection-hermes_jspace-tests-PASS
rollback:
  command: brain_task_orchestrator.py transition <same-task> --to reopened --reason <reason>
  scope: same task only; no broad task scan/update
readback:
  - task file frontmatter status
  - event_ledger.jsonl receipt ids
  - hermes_jspace.py closure-packet <workspace_id>
  - brain_task_orchestrator.py selfcheck --json
```

### Disposable destructive canary packet

```yaml
exact_target:
  path: <workspace>/artifacts/destructive-canary/canary.txt
payload:
  generated canary text plus .bak backup
rollback:
  restore canary.restored.txt from .bak
readback:
  before_sha256 == restored_sha256
  hash_match: true
  production_resource_touched: false
```

### Closed high-risk packet skeleton

```yaml
external_dispatch:
  exact_target: missing platform + channel/user id
  payload: missing message body + idempotency key
  rollback: missing recall/correction path
  readback: missing send receipt + post-send fetch
  status: blocked_missing_platform_target_payload
publish_deploy_push:
  exact_target: missing repo/remote/env/branch or deploy target
  payload: missing ref/artifact/version
  rollback: missing revert/rollback command
  readback: missing remote/deploy status command
  status: blocked_missing_exact_target_rollback
credential_payment:
  exact_target: human UI or provider flow only
  payload: redacted receipt schema; no secret/card/OTP/API key may be typed by agent
  rollback: human cancel/stop path
  readback: redacted human-side receipt
  status: human_secret_gate_only
broad_fanout:
  exact_target: missing finite channel set
  payload: missing message + idempotency key
  rollback: missing per-channel recall/correction plan
  readback: missing receipt per channel
  status: blocked_missing_exact_channel_set_payload
worker_spawn_runtime_router:
  exact_target: missing worker id/command/workspace
  payload: missing worker packet with budget/timeout/authority
  rollback: missing kill/disable route command
  readback: missing process/log/route/task readback
  status: blocked_missing_worker_packet
```
