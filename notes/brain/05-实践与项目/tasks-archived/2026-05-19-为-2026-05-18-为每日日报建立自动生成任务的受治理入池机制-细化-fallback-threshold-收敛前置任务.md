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
capability_delta: fallback threshold narrowed brief
anti_drift_check: separate threshold policy from relay implementation so the parent scope does not drift
acceptance_evidence: proof log states threshold semantics and the evidence gate for noop-vs-change
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
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: auto_subtask_on_non_convergence:fallback_threshold
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
  - "proof: fallback_threshold narrowed brief completed; parent remains blocked until sibling axes and ratification refresh"
  - classification:axis=fallback_threshold_complete_parent_still_blocked
  - artifact:/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报建立自动生成任务的受治理入池机制-细化-fallback-threshold-收敛前置任务.md
  - proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash
  - command:proof-check PASS
  - command:selfcheck PASS
concepts: ["task", "auto-subtask", "non-convergence", "fallback-thresholds"]
---

# Task - 为 2026-05-18-为每日日报建立自动生成任务的受治理入池机制 细化 fallback threshold 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制`. Do not change the parent objective. Define fallback thresholds, downgrade policy, and the minimum evidence required to justify noop vs change on budget exhaustion behavior.

## Acceptance Criteria

- [x] Produce a narrowed brief covering trigger thresholds, allowed fallback actions, and explicit noop-vs-change decision criteria.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-18-为每日日报建立自动生成任务的受治理入池机制
- Discussion artifact: /Users/charles/.hermes/tick-20260519-024139-387815-p56580-48f6cbf7-5b799bd1/discussion_result.json
- Trigger axis: fallback_threshold
- Issue IDs: none tagged

## Parent Objective Snapshot

将“根据每日日报生成任务添加任务”纳入 taskpool 主链，形成带优先级、去重、依赖与证据字段的自动入池机制。

## Narrowed Scope

- Only resolve threshold semantics and noop-vs-change decision criteria.
- Do not redesign the full handoff workflow here.

## Narrowed Brief

### Fallback threshold contract

- GREEN/no-op: governed packet already contains priority layer, dependency order, evidence bundle, truth gate or equivalent boundedness, and duplicate/canonical-task check. The bridge may pass it through without inventing priority semantics.
- AMBER/escalate: packet is high leverage, touches taskpool/control-plane/prompt/memory/provider-quota, or has ambiguous duplicate/canonical status. It must carry explicit multimodel-at-intake semantics before downstream execution.
- RED/fail-closed repair: priority/dependency/evidence/truth fields are missing or ungrounded. Create/route a packet repair step rather than silently downgrading to generic backlog.
- BLACK/reject: source unreadable, evidence absent, invalid contract, or active duplicate already exists. Do not create another task.
- Parent boundary: fallback policy is a child-axis brief only; parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` remains blocked until sibling axes and parent ratification refresh complete.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| canonical child-axis note review | done | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-为每日日报建立自动生成任务的受治理入池机制-细化-fallback-threshold-收敛前置任务.md` |
| parent boundary preserved | done | parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` remains blocked until sibling axes and ratification refresh |

## Proof Log

- 2026-05-19T12:50:29+08:00: Task created from local-brain control point.

- 2026-05-19T18:46:31+08:00: manual bounded child-axis tranche completed for `fallback_threshold`; this is child-axis evidence only and does not unblock parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` by itself.

## Blockers / Confusions

- None.

## Final Handoff

- Status: review-ready / done-ready for child axis `fallback_threshold`.
- Evidence: narrowed brief, checked acceptance/workpad boxes, structured frontmatter evidence, and deterministic gates run after batch update.
- Residual risk: parent `2026-05-18-为每日日报建立自动生成任务的受治理入池机制` remains blocked until every sibling axis is closed and parent-level ratification is refreshed.
- 2026-05-19T18:46:31+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_claim

- 2026-05-19T18:46:31+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_running

- 2026-05-19T18:46:36+08:00: Lifecycle transition `running` -> `review` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_review Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=fallback_threshold_complete_parent_still_blocked

- 2026-05-19T18:46:36+08:00: Lifecycle transition `review` -> `done` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_done Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=fallback_threshold_complete_parent_still_blocked
