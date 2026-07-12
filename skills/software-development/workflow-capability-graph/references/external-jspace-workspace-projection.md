# External J-space Workspace Projection Pattern

## Scope

Use when translating interpretability / J-space / global-workspace insights into Hermes, AgentOS, taskpool, or workflow-control-plane design.

Applicability:
- User asks to land J-space, internal workspace, model-thought auditing, completion-claim gates, or evidence-governed agent workflow ideas.
- You need a safe external equivalent for closed/API models where hidden activations are not accessible.
- You are building local projection surfaces, evidence DAGs, reflection readbacks, or task lifecycle projections.

Anti-conditions:
- Do not claim direct hidden-state, Anthropic J-space, consciousness, or complete CoT access for closed/API models.
- Do not treat model judgment, reflection text, or multi-model agreement as objective evidence.
- Do not mutate taskpool/Kanban/Mission lifecycle, dispatch externally, publish/deploy/push, delete resources, or write memory/skills from this pattern without a separate exact authority/evidence gate.

## Core translation

```text
Anthropic J-space / global workspace insight
-> External Workspace Projection
-> Evidence DAG
-> Reflection Readback
-> Authority Gate
-> Surface Model Review
-> Completion Claim Gate
-> Task Lifecycle SSOT projection
```

The engineering target is an **external equivalent**, not a mechanistic interpretability implementation.

## Capability graph nodes

```yaml
nodes:
  - id: workspace_projection_builder
    kind: composite_module
    responsibility: Convert goal, constraints, authority, risks, and missing evidence into structured state.
    side_effects: local_write

  - id: evidence_dag_builder
    kind: composite_module
    responsibility: Bind claims to objective evidence and separate model judgment from fact authority.
    side_effects: local_write

  - id: reflection_readback_gate
    kind: gate
    responsibility: Read back external workspace state before review/done/external actions.
    outcomes:
      pass: continue
      fail: require_more_evidence_or_reflection
      blocked: authority_gate

  - id: completion_claim_gate
    kind: gate
    responsibility: Downgrade or block final completion claims lacking objective evidence.
    outcomes:
      verified_local: scoped_completion_claim_allowed
      advisory_only: downgrade_final_claim
      blocked_missing_evidence: stop_or_collect_evidence

  - id: task_event_projection_bridge
    kind: adapter
    responsibility: Map taskpool lifecycle events into workspace states without mutating canonical lifecycle.
    side_effects: local_write

  - id: learning_candidate_projection
    kind: artifact_template
    responsibility: Emit candidate-only reusable learning records requiring review before skill/memory/runtime promotion.
    side_effects: local_write
```

## Minimal data contracts

### WorkspaceProjection

```json
{
  "schema": "workspace_projection_v0_1",
  "id": "...",
  "goal": "...",
  "non_goals": [],
  "constraints": [],
  "authority_boundary": {
    "allowed": [],
    "requires_auth": [],
    "forbidden": []
  },
  "workspace_state": "objective_model|executing|reflective|gated|closed",
  "missing_evidence": [],
  "next_action_contract": {"action": "...", "expected_evidence": []}
}
```

### EvidenceDAG

```json
{
  "claims": [{"id": "C-001", "criticality": "completion_critical", "status": "unverified"}],
  "evidence": [{"id": "E-001", "authority": "objective|model_judgment|user_statement", "supports": ["C-001"], "status": "verified|advisory|failed|blocked"}]
}
```

### CompletionClaimPacket

```json
{
  "claim": "...",
  "scope": "local_projection_only_no_runtime_mutation",
  "evidence_refs": [],
  "missing_evidence": [],
  "negative_evidence": ["no_hidden_state_access", "no_external_dispatch"],
  "excluded_claims": ["not_full_multimodel_certified", "not_taskpool_real_lifecycle_write"],
  "status": "verified_local|advisory_only|blocked_missing_evidence"
}
```

## Evidence authority ladder

```text
L0 single model judgment                  -> advisory only
L1 independent model agreement            -> advisory only
L2 local readback evidence                 -> supports static facts
L3 executable verification evidence        -> supports functional facts
L4 external system readback                -> supports external state
L5 exact human authority for high-risk effect -> required for send/publish/delete/payment/etc.
```

Model judgment can route, criticize, request evidence, or downgrade confidence. It cannot close completion-critical claims without objective evidence.

## Recommended slices

### P0 — local projection skeleton

Implement local commands or artifacts equivalent to:

```text
init -> status -> add-evidence -> gate-check -> reflect -> closure-packet
```

Verification:
- unit tests for schema/gate behavior;
- live smoke workspace;
- closure packet explicitly records negative evidence such as `no_hidden_state_access` and `no_external_dispatch`.

### P1 — projection-only task event bridge

Add:

```text
attach-task -> on-event -> event_ledger.jsonl -> lifecycle-name to workspace-state projection
```

Example mapping:

```yaml
running: executing
review: reflective
blocked: gated
done: closed
reopened: contested
```

Boundary: task events are projected locally; canonical taskpool/Kanban/Mission lifecycle is not mutated.

### P1 — learning candidate projection

Emit `learning_candidate.json` as candidate-only:

```json
{
  "requires_human_review": true,
  "auto_apply_executed": false,
  "global_memory_write_executed": false,
  "skill_patch_executed": false
}
```

Boundary: no skill patch, memory write, or runtime promotion without a separate review gate.

### P2 — read-only dashboard/control-room data

Emit a read-only summary:

```json
{
  "active_jspaces": [],
  "blocked_gates": [],
  "evidence_health": {"verified": 0, "advisory": 0, "failed": 0, "blocked": 0},
  "learning_candidates": [],
  "aggregate_effects": {"runtime_mutation": false, "external_side_effects_executed": false},
  "current_workspace_effects": {"workspace_id": "...", "taskpool_lifecycle_write_executed": false, "external_side_effects_executed": false}
}
```

Boundary: dashboard data is a projection surface, not a UI executor or lifecycle owner. Claims must bind to `current_workspace_effects` when a workspace id is supplied; aggregate history is context only.

## Exact target / payload / rollback / readback matrix

| Boundary | Exact target | Payload | Rollback | Readback |
|---|---|---|---|---|
| Projection validator | One packet file path | WorkspaceProjection/EvidenceDAG/CompletionClaimPacket JSON | No mutation; reject packet | Gate JSON `status=PASS` or errors |
| Event ledger | One workspace id + one task id | Event JSON with source/type/from/to/evidence | Append corrective event | `event_ledger.jsonl`, workspace state, closure packet |
| Taskpool write-through | One canonical task id | One transition + actor/reason/command evidence | Reopen/transition same task only | Task file frontmatter, lifecycle log, selfcheck |
| Disposable destructive canary | Generated canary path under workspace artifacts | Canary content + `.bak` | Restore from `.bak` | SHA equality + `production_resource_touched=false` |
| External dispatch | Exact platform/channel/user | Message + idempotency key | Recall/correction path | Send receipt + post-send fetch |
| Publish/deploy/push | Exact repo/remote/env/branch | Ref/artifact/version | Revert/deploy rollback command | Remote/deploy/API readback |
| Credential/payment | Human UI/provider flow | Redacted receipt schema only | Human cancel/stop path | Redacted human receipt |
| Broad fan-out | Finite channel set | Message + idempotency key | Per-channel recall/correction | Receipt/readback per channel |
| Worker/runtime router | Worker id/command/workspace/budget | Worker packet + timeout/authority | Kill/disable route | PID/log/route/task readback |

If any cell is missing for a high-risk class, keep that class as a blocked projection only; do not infer real targets.

## Verification checklist

- [ ] The design says external projection/readback, not hidden-state access.
- [ ] Every completion-critical claim has objective evidence or is downgraded.
- [ ] Model votes are stored as `model_judgment` and never as objective evidence.
- [ ] Task lifecycle projection does not mutate canonical taskpool/Kanban/Mission state.
- [ ] Learning candidates require review and do not patch skills/memory automatically.
- [ ] Closure packet lists negative evidence and excluded claims.
- [ ] Runtime/external/destructive/publish/credential/payment gates remain closed unless exact authority, rollback, and readback are present.

## Common pitfalls

1. **Hidden-state overclaim** — saying the system reads J-space for closed/API models. Say `external projection` instead.
2. **Plan-as-proof** — treating a nice workspace or reflection as implementation evidence. Require executable/readback evidence.
3. **Model-consensus-as-fact** — multiple models agreeing still remains advisory without objective evidence.
4. **Projection-write-through confusion** — an event bridge can project task state while leaving taskpool lifecycle unchanged; make this explicit in closure packets.
5. **Learning pollution** — reusable lessons should first become candidate records; skill/memory updates need separate review and landing-zone classification.
