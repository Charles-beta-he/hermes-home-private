---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-20T21:03:29+08:00
updated: 2026-05-21T00:18:51+08:00
expires_at: 2026-06-13T00:56:42+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: relay ordering narrowed brief
anti_drift_check: relay ordering must stay downstream of quota and threshold decisions
acceptance_evidence: proof log names continuation packet timing and parent re-entry points
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: not_certified
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-21T00:20:58+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260520-161614-942675-p98309-55e49aea-347053fa/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-20-为-2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制-细化-relay-ordering-收敛前置任务-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: relay_ordering
auto_subtask_trigger: auto_subtask_on_non_convergence:relay_ordering
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - artifact:/Users/charles/.hermes/kanban/workspaces/t_c8e16526/taskpool-relay-ordering-narrowed-brief.md
  - artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-relay-ordering-policy-brief.md
  - proof:relay_ordering_downstream_of_quota_and_threshold_with_targeted_evidence_reentry_contract
concepts: ["task", "auto-subtask", "non-convergence", "relay-ordering"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#28"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制 细化 relay ordering 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制`. Do not change the parent objective. Define continuation packet / relay ordering after quota and threshold semantics are known, without reopening the parent mission objective.

## Acceptance Criteria

- [x] Produce a narrowed brief covering continuation packet timing, relay ordering, and parent handoff integration points.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
- Discussion artifact: /Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json
- Trigger axis: relay_ordering
- Issue IDs: none tagged

## Parent Objective Snapshot

将外部仓库/文章等任务在创建入池前先经过固定多模型分析，直接产出 P1/P2/P3 与优先级依据，使任务池更独立、更可解释、更稳定。

## Narrowed Scope

- Only resolve relay ordering and continuation packet timing.
- Assume quota/threshold semantics are separate prerequisites.

## Narrowed Brief

### 1. Downstream dependency contract

- `~/.hermes/scripts/brain_task_orchestrator.py` already encodes relay ordering as a downstream axis, not a first-pass classifier:
  - `AUTO_SUBTASK_AXIS_ORDER` orders `quota_observability` then `fallback_threshold` before `relay_ordering`.
  - `build_non_convergence_spec(..., axis="relay_ordering")` states the objective is to define continuation packet / relay ordering only after quota and threshold semantics are known.
- Therefore this child must not redefine quota semantics or noop-vs-change thresholds. It only governs checkpoint -> transition -> handoff ordering once those inputs exist.

### 2. Continuation packet timing

- The accepted policy brief at `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-relay-ordering-policy-brief.md` remains the source-of-truth ordering contract.
- For this taskpool parent, continuation packet is required before:
  - provider/model/session switch under RED/BLACK pressure;
  - creating a child task or other explicit handoff;
  - releasing claim because quota/budget pressure prevents safe continuation;
  - transitioning the parent into `blocked`, `retry`, or review checkpoint states instead of completing acceptance;
  - resuming parent targeted-evidence refresh in a fresh session.
- Continuation packet is optional for AMBER-only conditions when a bounded deterministic verification step can finish first.
- Continuation packet is disallowed/noisy for GREEN/no-risk states where no recoverability risk exists.

### 3. Parent handoff integration points

- Use the six stable re-entry points from the accepted policy brief:
  1. `observe_quota`
  2. `decide_threshold`
  3. `checkpoint`
  4. `transition_task`
  5. `handoff_or_retry`
  6. `resume_from_packet`
- Critical invariant for this parent: relay ordering begins only after `observe_quota` and `decide_threshold` have already resolved the upstream budget state.

### 4. Targeted-evidence refresh integration

- `~/.hermes/scripts/test_brain_task_orchestrator.py:1438-1469` proves the current parent recovery path is `blocked_parent_targeted_evidence`, preserves the frozen parent objective, injects child evidence paths, and binds reratification to explicit axis evidence.
- So the correct relay target is not a generic retry loop. It is a durable checkpoint that feeds the parent targeted-evidence refresh path with:
  - completed child artifact paths,
  - next atomic action,
  - authority boundary,
  - and the already-decided quota/threshold state.

### 5. Control-plane intake alignment

- `~/.hermes/scripts/test_brain_task_orchestrator.py:261-285` proves inbox ingest derives `priority_layer`, `dependency_order`, and `multimodel_triage_result` before task creation when absent.
- `~/.hermes/scripts/daily_report_task_ingest.py:108-157` proves governed ingest always passes those same fields into `brain_task_orchestrator.py add`.
- Therefore relay ordering belongs after pre-add triage metadata is materialized, not inside the ingestion classification step itself.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| accepted relay-ordering policy brief | PASS | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-relay-ordering-policy-brief.md` defines GREEN/AMBER/RED/BLACK ordering, continuation-packet timing, and six stable re-entry points |
| `~/.hermes/scripts/brain_task_orchestrator.py` relay child spec | PASS | `AUTO_SUBTASK_AXIS_ORDER` and `build_non_convergence_spec(..., axis="relay_ordering")` keep relay downstream of quota/threshold semantics |
| `~/.hermes/scripts/test_brain_task_orchestrator.py:1438-1469` | PASS | blocked-parent targeted-evidence refresh preserves frozen parent objective and injects child evidence paths into the reratification build command |
| `~/.hermes/scripts/test_brain_task_orchestrator.py:261-285` + `~/.hermes/scripts/daily_report_task_ingest.py:108-157` | PASS | pre-add ingest/read-back proves triage metadata is materialized before relay ordering needs to act |
| narrowed brief artifact | PASS | `/Users/charles/.hermes/kanban/workspaces/t_c8e16526/taskpool-relay-ordering-narrowed-brief.md` |

## Proof Log

- 2026-05-20T21:03:29+08:00: Task created from local-brain control point.
- 2026-05-21T00:18:51+08:00: Completed relay-ordering narrowed brief. Anchored continuation-packet timing to the accepted relay policy brief, verified current control-plane child spec keeps relay ordering downstream of quota/threshold decisions, and tied parent handoff to the blocked-parent targeted-evidence refresh path instead of a generic retry loop.

## Blockers / Confusions

- None.

## Final Handoff

- Status: narrowed brief complete; relay ordering is now explicitly downstream of quota observability and fallback-threshold decisions, with durable continuation-packet timing and parent targeted-evidence re-entry points.
- Evidence: accepted relay policy brief `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-relay-ordering-policy-brief.md`, control-plane source `~/.hermes/scripts/brain_task_orchestrator.py`, coverage in `~/.hermes/scripts/test_brain_task_orchestrator.py`, governed ingest contract in `~/.hermes/scripts/daily_report_task_ingest.py`, and narrowed brief artifact `/Users/charles/.hermes/kanban/workspaces/t_c8e16526/taskpool-relay-ordering-narrowed-brief.md`.
- Residual risk: parent task remains blocked until auto-subtask sync / targeted evidence refresh backfills this child together with quota, fallback-threshold, and framing evidence; this child does not itself re-run parent ratification.

- 2026-05-21T00:20:58+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260520-161614-942675-p98309-55e49aea-347053fa/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
