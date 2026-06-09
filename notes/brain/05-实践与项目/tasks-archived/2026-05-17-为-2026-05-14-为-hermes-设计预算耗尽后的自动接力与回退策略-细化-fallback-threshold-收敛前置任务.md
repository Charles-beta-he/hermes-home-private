---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T10:54:07+08:00
updated: 2026-05-17T11:07:30+08:00
expires_at: 2026-06-13T01:37:20+08:00
project: hermes-agent
architecture_target: local-brain
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
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260517-030731-772728-p50508-adaf4800-1ec01e52/discussion_result.json
multimodel_last_checked_at: 2026-05-17T11:10:48+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-030731-772728-p50508-adaf4800-1ec01e52/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-fallback-threshold-收敛前置任务-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: auto_subtask_on_non_convergence:fallback_threshold
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - proof: manual convergence closeout by hermes; narrowed brief written, artifact recorded, and py_compile_narrowed_briefs PASS
  - command:py_compile_narrowed_briefs PASS
  - artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json
concepts: ["task", "auto-subtask", "non-convergence", "fallback-thresholds"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 细化 fallback threshold 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略`. Do not change the parent objective. Define fallback thresholds, downgrade policy, and the minimum evidence required to justify noop vs change on budget exhaustion behavior.

## Acceptance Criteria

- [x] Produce a narrowed brief covering trigger thresholds, allowed fallback actions, and explicit noop-vs-change decision criteria.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.

## Narrowed Brief — Fallback Threshold

- **Trigger threshold:** 以 `agent/budget_meter.py:74-109` 的 `can_afford()` 为硬门：下一次 API 调用只要会击穿 `per_call_limit` / `per_turn_limit` / `daily_limit` 任一上限，就必须退出本轮主执行链，进入 continuation/handoff 评估。
- **Allowed fallback actions:** 先压缩上下文与消息体；若仍超限，再切换更低成本模型；若预算仍不足，生成 continuation packet 并停止当前主链。
- **Noop vs change criteria:** 只有当现有预算门已经足以阻止超额调用、且 continuation 证据链已经完整时，才允许 noop；若 budget gate 对“未知 usage / 低置信度成本”是隐式放行，则必须定义 change。
- **Rebind to latest round:** 本子任务沿用 2026-05-15 已形成的阈值语义，但把其重新绑定到本轮 agreement_low / vote_reject 语境，避免 parent 在新一轮里回退成“是否需要阈值”的争论。

## Parent Link

- Parent task: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
- Discussion artifact: /Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json
- Trigger axis: fallback_threshold
- Issue IDs: none tagged

## Parent Objective Snapshot

设计预算耗尽后的自动 continuation handoff 与回退策略，形成从耗尽检测到续跑恢复的完整闭环。

## Narrowed Scope

- Only resolve threshold semantics and noop-vs-change decision criteria.
- Do not redesign the full handoff workflow here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| BudgetMeter can_afford | PASS | threshold semantics rebound to latest budget-handoff round |

## Proof Log

- 2026-05-17T10:54:07+08:00: Task created from local-brain control point.
- 2026-05-17T11:03:00+08:00: Reconfirmed fallback-threshold semantics against the latest budget-exhaustion discussion round and preserved the earlier threshold decision as still-valid narrowing evidence.
- 2026-05-17T11:00:39+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: manual blocked-parent convergence execution
- 2026-05-17T11:00:39+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: record narrowed convergence brief

## Blockers / Confusions

- None.

## Final Handoff

- Status: ready_for_review
- Evidence: latest discussion artifact + BudgetMeter gate lines
- Residual risk: unknown provider usage still weakens confidence; relay ordering remains a separate prerequisite.

- 2026-05-17T11:07:29+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: narrowed brief recorded Evidence: proof:sha256:7dbdc7e5f7a1036351580e7374212bfd1d33ab820e5d938f94eccb9f5a7950ee, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json

- 2026-05-17T11:07:30+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: narrowed brief accepted as convergence evidence Evidence: proof:sha256:7dbdc7e5f7a1036351580e7374212bfd1d33ab820e5d938f94eccb9f5a7950ee, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json

- 2026-05-17T11:07:51+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-030039-404864-p41711-f57b0bc6-2c64e81f/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T11:10:48+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-030731-772728-p50508-adaf4800-1ec01e52/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
