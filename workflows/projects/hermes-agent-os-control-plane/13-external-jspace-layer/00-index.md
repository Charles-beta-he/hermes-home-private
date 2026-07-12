# External J-space Layer — P0 Design Package

Status: p0-local-projection-skeleton
Project: hermes-agent-os-control-plane
Created: 2026-07-07

## Purpose

Translate Anthropic's J-space / Global Workspace insight into a Hermes-local, auditable external projection layer. This packet does **not** claim access to closed-model hidden states. It defines an external equivalent: workspace projection, evidence DAG, reflection readback, authority gates, and completion-claim downgrades.

## Canonical artifacts

- `specs/external-jspace-layer-v0.1.md` — P0/P1/P2 operating spec.
- `schemas/workspace_projection.schema.json` — minimal workspace projection contract.
- `schemas/evidence_dag.schema.json` — claim/evidence DAG contract.
- `schemas/completion_claim_packet.schema.json` — completion claim gate packet contract.

## Runtime-adjacent P0 implementation

- Script: `/Users/charles/.hermes/scripts/hermes_jspace.py`
- Tests: `/Users/charles/.hermes/scripts/test_hermes_jspace.py`

The default script path is local-file only. It creates workspaces under `~/.hermes/workflows/jspace/`, records evidence, checks P0 gates, emits reflection readbacks, and produces closure packets. It does not dispatch tools, send messages, publish, deploy, touch credentials, operate broad fan-out, or read model hidden states. Exact local taskpool write-through and disposable canary smokes are separate named commands that require exact target/payload/rollback/readback and must record receipts.

## Current boundary

P0/P1/P2 local projection helpers exist as local-file/read-only or exact-smoke surfaces, but they are not a hidden-state monitor and they do not grant broad taskpool lifecycle/external authority.

## 2026-07-08 source recertification

Anthropic's 2026 Global Workspace/J-space research was re-read and absorbed with evidence:

- Evidence bundle: `/Users/charles/.hermes/workflows/intake/2026-07-08-anthropic-global-workspace-evidence.json`
- Analysis/landing doc: `/Users/charles/.hermes/docs/private/anthropic-global-workspace-analysis-and-hermes-landing-2026-07-08.md`
- Local projection workspace: `/Users/charles/.hermes/workflows/jspace/anthropic-global-workspace-analysis-20260708`
- Local gate readback: objective_defined=pass, reflection_readback=pass, closure_packet status=`verified_local` with negative evidence `no_hidden_state_access`, `no_external_dispatch`, `no_taskpool_lifecycle_write`.
- Reusable class-level validator: `/Users/charles/.hermes/scripts/workspace_projection_gate.py`; sample packet: `/Users/charles/.hermes/skills/software-development/workflow-capability-graph/templates/workspace-projection-packet.sample.json`.

Boundary: this recertifies the external workspace projection pattern from the primary Anthropic source and local evidence. It does not claim real Claude hidden-state/J-space access from Hermes.

## P1 local event projection

P1 now includes local projection-only `attach-task` and `on-event` commands in `/Users/charles/.hermes/scripts/hermes_jspace.py`. These commands write `event_ledger.jsonl` and map task lifecycle names to workspace states. They do not mutate the canonical taskpool/Kanban/Mission lifecycle.

## Learning candidate projection

The helper now emits `learning_candidate.json` as a candidate-only project reference. It preserves the boundary that reusable learnings require review before skill, memory, or runtime promotion.

## P2 read-only dashboard data

The helper now exposes `dashboard-data` as a local read-only operator/control-room data packet. It does not serve a UI, invoke capabilities, or mutate taskpool lifecycle.

## Real-open boundary matrix

The helper now emits `real_open_matrix.json` for class-level high-risk coverage. Current safe real smokes are exact taskpool lifecycle write-through, local no-agent cron heartbeat, and disposable destructive canary restore proof. Class-only external/deploy/payment/fanout requests remain exact-target gated.

## Exact target / payload / rollback / readback matrix

| Boundary | Exact target required | Payload required | Rollback / escape hatch | Readback / receipt | Current status |
|---|---|---|---|---|---|
| WorkspaceProjection validation | Packet path such as `/Users/charles/.hermes/skills/software-development/workflow-capability-graph/templates/workspace-projection-packet.sample.json` | JSON packet with `source_boundary`, claims, evidence DAG, authority gate, completion packet | No mutation; discard invalid packet | `workspace_projection_gate.py <packet> --json` with `status=PASS` or fail-closed errors | Opened as local/read-only |
| Current workspace dashboard | Workspace id, e.g. `anthropic-global-workspace-analysis-20260708` | CLI arg `--workspace-id <id>` only | No mutation; rerun without side effects | `hermes_jspace.py dashboard-data --workspace-id <id>`; bind claims to `current_workspace_effects`, not aggregate flags | Opened as read-only |
| Projection-only event ledger | Workspace id + task id | Local event JSON with `source`, `type`, `task_id`, `from`, `to`, and evidence ref | Append-only local ledger; if event is wrong, append corrective event rather than editing history | `event_ledger.jsonl`, `closure-packet`, workspace state readback | Opened as local ledger |
| Exact taskpool lifecycle write-through | One exact task id: `2026-07-08-将global-workspace外部投影门禁接入taskpool事件桥与只读仪表盘` | One deterministic transition with actor, reason, and `command:` proof evidence | Reopen or transition only the same task with recorded reason; no broad task scan/update | Task file status readback, lifecycle receipt lines, `brain_task_orchestrator.py selfcheck --json` | Opened for the one task; completed |
| Disposable destructive canary | Generated canary under the workspace artifact directory only | Canary content + `.bak` backup path | Restore from `.bak`; verify SHA-256 equality; never touch production/user resources | `real-open-matrix --run-destructive-canary` with `hash_match=true` and `production_resource_touched=false` | Opened only for disposable canary |
| External dispatch | Exact platform + channel/user target + payload + idempotency key | Message body and receipt expectation | Delete/recall path if platform supports it, otherwise correction message plan | Platform receipt and post-send readback | Closed: missing exact platform/target/payload |
| Publish/deploy/push | Exact repo/remote/env/branch or deploy target | Artifact/ref to publish and deployment params | Revert SHA/rollback deploy target and readback command | `git ls-remote`, deployment status, URL/API readback | Closed: missing exact target/rollback |
| Credential/payment entry | Human-owned credential/payment UI target | Redacted receipt schema only; agent never types secrets/cards/OTP/API keys | Human cancel/stop path; no agent-side secret entry | Human-side receipt, redacted and scoped | Closed to agent; human gate only |
| Broad fan-out | Exact finite channel set and payload | Message payload, recipients, idempotency key | Per-channel recall/correction plan | Receipt per channel + readback | Closed: missing exact channel set/payload |
| Worker spawn/runtime router | Exact worker id, command, workspace, budget, kill/readback path | Worker packet with target task, authority, evidence, timeout | Kill process / disable route / rollback status | process id/log, route status, task readback | Closed: missing exact worker packet |
