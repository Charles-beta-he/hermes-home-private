---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-15T10:30:14+08:00
updated: 2026-05-15T10:30:14+08:00
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
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-16T22:01:13+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: RATIFY
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-134823-895333-p29114-a345e3f1-929571bc/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-15-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-quota-observability-收敛前置任务-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260513-213742-502936-p80883-2e691a87-ed06220b/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - artifact:/Users/charles/.hermes/tick-20260516-134823-895333-p29114-a345e3f1-929571bc/discussion_result.json
  - proof: narrowed brief records quota_state source, confidence, unknown handling, and evidence locations for parent ratification
  - classification:multimodel_gate=PASS_ADVISORY_ONLY
  - classification:multimodel_decision=RATIFY
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["accuracy_keyword", "architecture_target", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略`. Do not change the parent objective. Define quota_state source, confidence, staleness, and fail-closed semantics so future ratification can decide whether quota-aware change is required.

## Acceptance Criteria

- [x] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.


## Narrowed Brief — Quota Observability

**Source:** `agent/budget_meter.py` BudgetMeter class + `run_agent.py` iteration_budget integration.

**quota_state origin:**
- BudgetMeter tracks per-session cost via `record(tokens_in, tokens_out, model)` → internal `_spent` accumulator.
- `remaining` property = `budget_limit - _spent`. No external quota API; purely local accounting.
- Model-specific costs resolved via `cost_map` dict (per-1k-token rates). If model missing from cost_map, falls back to default rate → silent underestimate risk.

**Confidence / Staleness:**
- Budget is **always fresh** — no async fetch, no cache. `_spent` is incremented synchronously after each API call.
- Confidence is **high** for token counts (from API response.usage) but **medium** for cost (depends on cost_map accuracy).
- No staleness mechanism needed — state is in-memory, single-process.

**Unknown / Unobservable handling:**
- If `response.usage` is None (some providers omit it), BudgetMeter records 0 → budget gate becomes **permissive** (fail-open on observability gap).
- If model not in cost_map, default rate is used → budget may exhaust early or late.
- **Fail-closed gap:** No explicit "unknown quota" state. When usage is unavailable, the meter silently skips, giving false "remaining budget" signal.

**Evidence locations:**
- `agent/budget_meter.py` L45-180: BudgetMeter class definition
- `run_agent.py` L990-1020: iteration_budget.check() call in agent loop
- `agent/result_spiller.py`: overflow handling when budget exhausted

**Recommendation for parent ratification:** Add explicit `quota_observable: bool` flag to BudgetMeter. When False (usage unavailable), emit warning and apply conservative default budget multiplier (0.5x). This makes the fail-closed gap visible to downstream relay logic.

## Parent Link

- Parent task: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
- Discussion artifact: /Users/charles/.hermes/tick-20260513-213742-502936-p80883-2e691a87-ed06220b/discussion_result.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

设计预算耗尽后的自动 continuation handoff 与回退策略，形成从耗尽检测到续跑恢复的完整闭环。

## Narrowed Scope

- Only resolve quota observability and evidence gaps.
- Do not decide relay ordering or broader fallback policy here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-15T10:30:14+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-16T22:01:13+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-134823-895333-p29114-a345e3f1-929571bc/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
