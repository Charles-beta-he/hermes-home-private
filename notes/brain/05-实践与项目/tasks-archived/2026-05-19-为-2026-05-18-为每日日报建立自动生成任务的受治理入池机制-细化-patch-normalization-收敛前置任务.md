---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: daily-report:p1:report-to-task-ingest
dependency_order: ["['recommended-order: ingestion-contract -> prioritization-and-dedup -> task-creation-hook-or-runner -> verification-and-fallback']"]
created: 2026-05-19T12:50:29+08:00
updated: 2026-05-19T18:46:36+08:00
expires_at: 2026-06-17T01:34:04+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: patch normalization narrowed brief
anti_drift_check: keep implementation slicing smaller than the parent mission
acceptance_evidence: proof log explains why each candidate patch is included, excluded, or deferred
workflow_contract: "[08-模板/task-workflow-contract-template]"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest triage: P1 evolution candidate; strong leverage on taskpool autonomy and evidence-governed dispatch because it upgrades report-to-task conversion into a first-class workflow"
auto_subtask_parent: 2026-05-18-为每日日报建立自动生成任务的受治理入池机制
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-024139-387815-p56580-48f6cbf7-5b799bd1/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先定义日报到任务池的治理契约，再实现提取与去重，最后接入自动创建与验证；禁止跳过 schema 直接自动化。
evidence:
  - "proof: patch_normalization narrowed brief completed; parent remains blocked until sibling axes and ratification refresh"
  - classification:axis=patch_normalization_complete_parent_still_blocked
  - artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报建立自动生成任务的受治理入池机制-细化-patch-normalization-收敛前置任务.md
  - proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash
  - command:proof-check PASS
  - command:selfcheck PASS
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
---

# Task - 为 2026-05-18-为每日日报建立自动生成任务的受治理入池机制 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制`. Do not change the parent objective. Normalize surfaced minority patches into a certifiable minimum patch set that preserves the parent objective and removes noop-vs-change ambiguity.

## Acceptance Criteria

- [x] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-18-为每日日报建立自动生成任务的受治理入池机制
- Discussion artifact: /Users/charles/.hermes/tick-20260519-024139-387815-p56580-48f6cbf7-5b799bd1/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

将“根据每日日报生成任务添加任务”纳入 taskpool 主链，形成带优先级、去重、依赖与证据字段的自动入池机制。

## Narrowed Scope

- Only normalize surfaced patch candidates and their inclusion criteria.
- Do not expand into end-to-end implementation here.

## Narrowed Brief

### Patch normalization contract

- Normalize proposed changes into one of: `noop_transport`, `schema_fill`, `producer_contract_patch`, `dedupe_policy_patch`, `ratification_route_patch`, or `reject_as_unbounded`.
- A patch candidate must name the exact producer/consumer boundary, fields added or preserved, rollback condition, and deterministic verification command.
- Provider/model parse errors are not patch evidence. They are taxonomy signals that the packet lacks stable machine-readable decision fields.
- Noncanonical participant output may inform diagnosis but cannot satisfy canonical approval or done evidence.
- Parent boundary: this child completes only the patch-classification axis; parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` still needs sibling completion and target-bound ratification before unblock.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| canonical child-axis note review | done | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报建立自动生成任务的受治理入池机制-细化-patch-normalization-收敛前置任务.md` |
| parent boundary preserved | done | parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` remains blocked until sibling axes and ratification refresh |

## Proof Log

- 2026-05-19T12:50:29+08:00: Task created from local-brain control point.

- 2026-05-19T18:46:31+08:00: manual bounded child-axis tranche completed for `patch_normalization`; this is child-axis evidence only and does not unblock parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` by itself.

## Blockers / Confusions

- None.

## Final Handoff

- Status: review-ready / done-ready for child axis `patch_normalization`.
- Evidence: narrowed brief, checked acceptance/workpad boxes, structured frontmatter evidence, and deterministic gates run after batch update.
- Residual risk: parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` remains blocked until every sibling axis is closed and parent-level ratification is refreshed.
- 2026-05-19T18:46:32+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_claim

- 2026-05-19T18:46:32+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_running

- 2026-05-19T18:46:36+08:00: Lifecycle transition `running` -> `review` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_review Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=patch_normalization_complete_parent_still_blocked

- 2026-05-19T18:46:36+08:00: Lifecycle transition `review` -> `done` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_done Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=patch_normalization_complete_parent_still_blocked
