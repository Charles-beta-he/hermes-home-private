---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: daily-report:p1:github-trending-source
dependency_order: ["['recommended-order: source-verification -> field-schema -> daily-report-integration -> validation-and-fallback']"]
created: 2026-05-19T14:12:28+08:00
updated: 2026-05-19T18:46:37+08:00
expires_at: 2026-06-17T01:34:34+08:00
project: hermes-agent
architecture_target: local-brain
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
multimodel_triage_result: "pre-ingest triage: P1 evolution candidate; strengthens daily-report evidence quality and upstream signal quality for downstream task creation"
auto_subtask_parent: 2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-045114-221956-p46067-c446de14-117e7db1/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先确认官方 Trending 数据源与字段，再实现日报补充逻辑，最后验证与“日报生成任务”链路衔接。
evidence:
  - "proof: patch_normalization narrowed brief completed; parent remains blocked until sibling axes and ratification refresh"
  - classification:axis=patch_normalization_complete_parent_still_blocked
  - artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总-细化-patch-normalization-收敛前.md
  - proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash
  - command:proof-check PASS
  - command:selfcheck PASS
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
---

# Task - 为 2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总`. Do not change the parent objective. Normalize surfaced minority patches into a certifiable minimum patch set that preserves the parent objective and removes noop-vs-change ambiguity.

## Acceptance Criteria

- [x] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总
- Discussion artifact: /Users/charles/.hermes/tick-20260519-045114-221956-p46067-c446de14-117e7db1/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

将 GitHub 官方 Trending 数据源排名补充到每日日报，形成证据化趋势来源，并服务后续日报→任务入池机制。

## Narrowed Scope

- Only normalize surfaced patch candidates and their inclusion criteria.
- Do not expand into end-to-end implementation here.

## Narrowed Brief

### Patch normalization contract

- Normalize proposed changes into one of: `noop_transport`, `schema_fill`, `producer_contract_patch`, `dedupe_policy_patch`, `ratification_route_patch`, or `reject_as_unbounded`.
- A patch candidate must name the exact producer/consumer boundary, fields added or preserved, rollback condition, and deterministic verification command.
- Provider/model parse errors are not patch evidence. They are taxonomy signals that the packet lacks stable machine-readable decision fields.
- Noncanonical participant output may inform diagnosis but cannot satisfy canonical approval or done evidence.
- Parent boundary: this child completes only the patch-classification axis; parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` still needs sibling completion and target-bound ratification before unblock.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| canonical child-axis note review | done | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总-细化-patch-normalization-收敛前.md` |
| parent boundary preserved | done | parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` remains blocked until sibling axes and ratification refresh |

## Proof Log

- 2026-05-19T14:12:28+08:00: Task created from local-brain control point.

- 2026-05-19T18:46:31+08:00: manual bounded child-axis tranche completed for `patch_normalization`; this is child-axis evidence only and does not unblock parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` by itself.

## Blockers / Confusions

- None.

## Final Handoff

- Status: review-ready / done-ready for child axis `patch_normalization`.
- Evidence: narrowed brief, checked acceptance/workpad boxes, structured frontmatter evidence, and deterministic gates run after batch update.
- Residual risk: parent `2026-05-18-为每日日报补充-github-官方-trending-排名数据源并纳入证据化汇总` remains blocked until every sibling axis is closed and parent-level ratification is refreshed.
- 2026-05-19T18:46:33+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_claim

- 2026-05-19T18:46:33+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_running

- 2026-05-19T18:46:37+08:00: Lifecycle transition `running` -> `review` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_review Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=patch_normalization_complete_parent_still_blocked

- 2026-05-19T18:46:37+08:00: Lifecycle transition `review` -> `done` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_done Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=patch_normalization_complete_parent_still_blocked
