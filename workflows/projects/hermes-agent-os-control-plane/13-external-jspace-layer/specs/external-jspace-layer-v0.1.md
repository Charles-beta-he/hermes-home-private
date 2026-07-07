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
