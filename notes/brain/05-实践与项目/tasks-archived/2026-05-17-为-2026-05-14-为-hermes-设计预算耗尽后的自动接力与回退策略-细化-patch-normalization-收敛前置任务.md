---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-17T19:51:22+08:00
updated: 2026-05-17T19:56:45+08:00
expires_at: 2026-06-13T01:37:20+08:00
project: hermes-agent
architecture_target: local-brain
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
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T20:03:41+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-115645-515331-p54003-a936098e-497071b3/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-patch-normalization-收敛前置任务-state.json
multimodel_last_failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]
multimodel_failure_taxonomy: ["criteria_missing", "quota_unobservable", "vote_reject"]
multimodel_recommended_axes: ["quota_observability", "fallback_threshold", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['quota_unobservable'], 'fallback_threshold': ['criteria_missing'], 'framing': ['vote_reject']}"
auto_subtask_parent: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260517-032103-273581-p59581-ce922050-1bd8027a/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - "command: py_compile brain_task_orchestrator.py PASS; command: selfcheck PASS; command: proof-check PASS; artifact: child proof log patch normalization narrowed brief appended"
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略`. Do not change the parent objective. Normalize surfaced minority patches into a certifiable minimum patch set that preserves the parent objective and removes noop-vs-change ambiguity.

## Acceptance Criteria

- [ ] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
- Discussion artifact: /Users/charles/.hermes/tick-20260517-032103-273581-p59581-ce922050-1bd8027a/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

设计预算耗尽后的自动 continuation handoff 与回退策略，形成从耗尽检测到续跑恢复的完整闭环。

## Narrowed Scope

- Only normalize surfaced patch candidates and their inclusion criteria.
- Do not expand into end-to-end implementation here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-17T19:51:22+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T19:55:06+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: execute non-convergence narrowing: patch normalization


### 2026-05-17 Hermes execution proof — patch normalization narrowed brief

Decision: include only the smallest deterministic patch set required to make non-convergence splitting certifiable after the new fail-closed creation governance.

Included patch:
- `scripts/brain_task_orchestrator.py`: `command_auto_split_non_convergence()` now passes `dependency_order=[str(parent.fm.get("dependency_order") or "1")]` to generated child tasks instead of `list_value(parent.fm.get("dependency_order"))`.

Why included:
- The parent was blocked with `loop_non_convergence` and resolver reported axes requiring split/narrowing.
- Running `auto-split-non-convergence` failed before child creation with `task creation requires explicit priority/dependency/triage metadata; missing=['dependency_order']`.
- Root cause: parent `dependency_order` is a scalar frontmatter value in current tasks; `list_value(...)` normalizes scalar strings to an empty list in this path, causing the generated Namespace to omit dependency_order despite the parent having enough ordering information.
- The minimum durable fix is to preserve/create a one-item dependency order list for generated subtasks and keep triage inherited/fallback bounded to `P2`.

Excluded/deferred candidates:
- End-to-end budget relay implementation changes: deferred; this child is explicitly narrowed to patch normalization only.
- Changing parent objective/status directly: deferred; parent remains blocked until child evidence and certification/blocked-resolver gates are satisfied.
- Broad changes to `list_value`: excluded; too high blast radius for a narrow unblock.

Validation evidence:
- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py auto-split-non-convergence --task 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 --json` returned `status: OK` and created this pending child task.
- `python3 -m py_compile /Users/charles/.hermes/scripts/brain_task_orchestrator.py` is required before closing.

Next handoff:
- Close this child after py_compile/proof-check pass.
- Re-run `blocked-resolve-step` on the parent; if still blocked, continue with the next surfaced axis rather than reopening broad parent scope.

- 2026-05-17T19:56:45+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: execute narrowed patch normalization

- 2026-05-17T19:56:45+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: patch normalization implemented and awaiting closure proof Evidence: command: py_compile brain_task_orchestrator.py PASS; command: selfcheck PASS; command: proof-check PASS; artifact: child proof log patch normalization narrowed brief appended

- 2026-05-17T19:56:45+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: patch normalization narrowed and validated Evidence: command: py_compile brain_task_orchestrator.py PASS; command: selfcheck PASS; command: proof-check PASS; artifact: child proof log patch normalization narrowed brief appended

- 2026-05-17T19:59:11+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-115506-714473-p53491-87364e86-0b35139e/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T20:02:42+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-115645-603570-p54008-75fa8daa-8eac6763/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}

- 2026-05-17T20:03:41+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-115645-515331-p54003-a936098e-497071b3/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}
