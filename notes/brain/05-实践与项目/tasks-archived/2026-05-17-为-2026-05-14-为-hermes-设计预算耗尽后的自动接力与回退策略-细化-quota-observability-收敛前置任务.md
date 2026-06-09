---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T10:54:07+08:00
updated: 2026-05-17T11:07:31+08:00
expires_at: 2026-06-13T01:37:20+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: quota observability narrowed brief
anti_drift_check: keep parent objective unchanged while proving quota_state semantics
acceptance_evidence: proof log cites source evidence for quota_state confidence and unknown handling
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260517-030733-875365-p50594-4f153a09-33e49765/discussion_result.json
multimodel_last_checked_at: 2026-05-17T11:10:46+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-030733-875365-p50594-4f153a09-33e49765/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-quota-observability-收敛前置任务-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
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
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略`. Do not change the parent objective. Pin down quota-state evidence, confidence, and unknown-handling so the parent no longer debates whether budget exhaustion is observable enough for safe relay.

## Acceptance Criteria

- [x] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.

## Narrowed Brief — Quota Observability

- **Source:** `agent/budget_meter.py:45-145` 是当前唯一一等 quota source；`run_agent.py` 的预算检查与 loop 退出依赖它。
- **Confidence:** token / max-cost 估算即时且新鲜，但当 provider 不返回可靠 usage、或 model pricing 走 default 分支时，成本信号只有中等置信度。
- **Unknown handling:** 预算未知不能被当作“预算足够”；若 usage 缺失或 model pricing fallback 触发，未来 parent 设计必须把状态显式标成 `quota_unobservable` / degraded。
- **Evidence contract:** parent ratification 至少要能回答 budget source、freshness、unknown 行为、以及 relay 何时可相信该值；否则 continuation 决策仍属不完备。

## Parent Link

- Parent task: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
- Discussion artifact: /Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

设计预算耗尽后的自动 continuation handoff 与回退策略，形成从耗尽检测到续跑恢复的完整闭环。

## Narrowed Scope

- Only resolve quota-state evidence semantics.
- Do not redesign the full handoff workflow here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| budget_meter source audit | PASS | quota_state source/confidence/unknown handling captured |

## Proof Log

- 2026-05-17T10:54:07+08:00: Task created from local-brain control point.
- 2026-05-17T11:03:00+08:00: Rebound quota-observability semantics to the latest budget-handoff loop and froze the missing `unknown quota` contract as an explicit parent prerequisite.
- 2026-05-17T11:00:41+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: manual blocked-parent convergence execution
- 2026-05-17T11:00:41+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: record narrowed convergence brief

## Blockers / Confusions

- None.

## Final Handoff

- Status: ready_for_review
- Evidence: latest discussion artifact + BudgetMeter implementation
- Residual risk: current implementation still lacks an explicit `quota_observable` flag; this slice only records the contract debt.

- 2026-05-17T11:07:30+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: narrowed brief recorded Evidence: proof:sha256:5088c4ad7ac0e1906f5205e3c28476e576351f0f0114c42314ff98e4708c63fb, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json

- 2026-05-17T11:07:31+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: narrowed brief accepted as convergence evidence Evidence: proof:sha256:5088c4ad7ac0e1906f5205e3c28476e576351f0f0114c42314ff98e4708c63fb, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-160734-931025-p77261-fc00029d-3510cf2e/discussion_result.json

- 2026-05-17T11:09:29+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-030043-897234-p41944-0b8fd578-7988d54c/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:deepseek-v4-pro", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-17T11:10:32+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-030042-325330-p41827-6a0c8eab-0ab8a184/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T11:10:46+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-030733-875365-p50594-4f153a09-33e49765/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
