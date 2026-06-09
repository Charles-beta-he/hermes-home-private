---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-20T21:03:29+08:00
updated: 2026-05-20T21:06:07+08:00
expires_at: 2026-06-13T00:56:42+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: patch normalization narrowed brief
anti_drift_check: keep implementation slicing smaller than the parent mission
acceptance_evidence: proof log explains why each candidate patch is included, excluded, or deferred
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
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
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
  - proof:sha256:4027da24b070a19140708e070112a382d99735d6436c6229568f5439bbff8ee0
  - command:py_compile_taskpool PASS
  - proof:sha256:5905b4f8f50ce754b4b4afa3a92b8f1f99828cfa2fe98654774321fff5187999
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#17"
---

# Task - 为 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制`. Do not change the parent objective. Normalize surfaced minority patches into a certifiable minimum patch set that preserves the parent objective and removes noop-vs-change ambiguity.

## Acceptance Criteria

- [ ] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
- Discussion artifact: /Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

将外部仓库/文章等任务在创建入池前先经过固定多模型分析，直接产出 P1/P2/P3 与优先级依据，使任务池更独立、更可解释、更稳定。

## Narrowed Scope

- Only normalize surfaced patch candidates and their inclusion criteria.
- Do not expand into end-to-end implementation here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-20T21:03:29+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-20T21:06:07+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-20T21:06:07+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-20T21:06:07+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:4027da24b070a19140708e070112a382d99735d6436c6229568f5439bbff8ee0, command:py_compile_taskpool PASS

- 2026-05-20T21:06:07+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:5905b4f8f50ce754b4b4afa3a92b8f1f99828cfa2fe98654774321fff5187999, proof:sha256:4027da24b070a19140708e070112a382d99735d6436c6229568f5439bbff8ee0, command:py_compile_taskpool PASS
