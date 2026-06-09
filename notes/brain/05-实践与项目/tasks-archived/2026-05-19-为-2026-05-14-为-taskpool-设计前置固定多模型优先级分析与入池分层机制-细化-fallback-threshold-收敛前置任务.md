---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-19T11:41:36+08:00
updated: 2026-05-19T17:08:43+08:00
expires_at: 2026-06-13T00:56:42+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: fallback threshold narrowed brief
anti_drift_check: separate threshold policy from relay implementation so the parent scope does not drift
acceptance_evidence: proof log states threshold semantics and the evidence gate for noop-vs-change
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: not_certified
auto_subtask_parent: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: auto_subtask_on_non_convergence:fallback_threshold
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-033213-033607-p97711-eed21c74-be8dd337/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - "proof: narrowed fallback-threshold brief completed; threshold bands GREEN/AMBER/RED/BLACK and noop-vs-change criteria documented in task body"
  - "artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制.md"
  - "artifact:/Users/charles/.hermes/scripts/daily_report_task_ingest.py"
  - "artifact:/Users/charles/.hermes/scripts/test_daily_report_task_ingest.py"
  - "artifact:/Users/charles/.hermes/scripts/brain_task_orchestrator.py"
concepts: ["task", "auto-subtask", "non-convergence", "fallback-thresholds"]
---

# Task - 为 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制 细化 fallback threshold 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制`. Do not change the parent objective. Define the fallback thresholds for pre-ingest taskpool triage: when an intake packet is already governed enough to pass through the existing add path, when it must escalate to explicit multimodel-at-intake, and when it must fail closed instead of inventing priority semantics later.

## Acceptance Criteria

- [x] Produce a narrowed brief covering trigger thresholds, allowed fallback actions, and explicit noop-vs-change decision criteria.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
- Discussion artifact: /Users/charles/.hermes/tick-20260519-033213-033607-p97711-eed21c74-be8dd337/discussion_result.json
- Trigger axis: fallback_threshold
- Issue IDs: none tagged

## Parent Objective Snapshot

将外部仓库/文章等任务在创建入池前先经过固定多模型分析，直接产出 P1/P2/P3 与优先级依据，使任务池更独立、更可解释、更稳定。

## Narrowed Scope

- Only resolve threshold semantics and noop-vs-change decision criteria.
- Do not redesign the full handoff workflow here.

## Narrowed Brief

### Threshold bands

- GREEN: the producer already emits a fully governed packet (`priority_layer`, `dependency_order`, `multimodel_triage_result`, evidence/truth fields present), scope is bounded, and no explicit multimodel escalation is needed. In this band the ingest bridge may transport the packet without inventing new priority semantics.
- AMBER: governance fields are present, but the intake is leverage-sensitive (`P1`, control-plane/taskpool/prompt/memory/provider-quota surfaces, or duplicate/canonical-task ambiguity). In this band the task must carry explicit multimodel-at-intake semantics (`requires_multimodel` and/or `multimodel_reason`) at creation time; do not defer the judgment to later ad hoc review.
- RED: contract shape is incomplete or the claimed triage result is not grounded enough to justify task creation (missing `priority_layer`, `dependency_order`, `multimodel_triage_result`, `evidence_bundle`, or equivalent boundedness/evidence). In this band fail closed to a packet/triage repair step rather than silently downgrading to generic backlog.
- BLACK: source unreadable, evidence absent, invalid contract, or active duplicate already exists. In this band do not create a task.

### Noop-vs-change rule

- Noop is acceptable only when the producer has already emitted a governed packet whose priority semantics are explicit enough that the ingest bridge is merely transporting them.
- Change is required when a producer can create or imply a high-leverage task without explicit P1/P2/P3 rationale, dependency order, evidence bundle, truth gate, or a clear yes/no answer on whether multimodel is required at intake.

### Grounded implementation boundary

- `daily_report_task_ingest.py` already enforces fail-closed required governance fields and duplicate suppression.
- `brain_task_orchestrator.py` already has explicit strong multimodel triggers (`requires_multimodel`, retry>=2, stale claim, P0+evolution).
- Therefore the missing decision boundary was not a new routing system; it was the threshold for when governed intake may stay pass-through vs must escalate or reject.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| canonical parent note review | done | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制.md` |
| governed ingest contract review | done | `/Users/charles/.hermes/scripts/daily_report_task_ingest.py` |
| external sidecar acceptance test | done | `/Users/charles/.hermes/scripts/test_daily_report_task_ingest.py` |
| multimodel trigger boundary review | done | `/Users/charles/.hermes/scripts/brain_task_orchestrator.py` |

## Proof Log

- 2026-05-19T11:41:36+08:00: Task created from local-brain control point.
- 2026-05-19T17:08:43+08:00: Verified that the parent objective is already landed as a durable pre-ingest triage rule and that the remaining disagreement is specifically the fallback threshold between pass-through governed intake, explicit multimodel-at-intake escalation, and fail-closed rejection.
- 2026-05-19T17:08:43+08:00: Grounded the threshold bands against live implementation surfaces: `daily_report_task_ingest.py` fail-closed contract checks, `test_daily_report_task_ingest.py` external AIHOT sidecar acceptance, and `brain_task_orchestrator.py` strong multimodel trigger rules.

## Blockers / Confusions

- None.

## Final Handoff

- Status: done. The narrowed fallback-threshold brief is now explicit in the canonical child note and mirrored in `/Users/charles/.hermes/kanban/workspaces/t_fe78d7c2/fallback-threshold-status.md`.
- Evidence: parent task objective, live governed ingest bridge, external AIHOT sidecar test, and orchestrator multimodel-trigger logic all align on the same threshold boundary.
- Residual risk: producers can still emit a `multimodel_triage_result` label without semantic validation by the ingest bridge itself, so follow-through may still be needed on producer-side triage discipline.
