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
auto_subtask_parent: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: relay_ordering
auto_subtask_trigger: auto_subtask_on_non_convergence:relay_ordering
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
  - artifact:/Users/charles/.hermes/tick-20260513-213742-502936-p80883-2e691a87-ed06220b/discussion_result.json
  - proof: narrowed brief records continuation packet timing, relay ordering, and parent handoff integration points
  - classification:auto_subtask_axis=relay_ordering
concepts: ["task", "auto-subtask", "non-convergence", "relay-ordering"]
---

# Task - 为 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略 细化 relay ordering 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略`. Do not change the parent objective. Define continuation packet / relay ordering after quota and threshold semantics are known, without reopening the parent mission objective.

## Acceptance Criteria

- [x] Produce a narrowed brief covering continuation packet timing, relay ordering, and parent handoff integration points.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.


## Narrowed Brief — Relay Ordering

**Source:** `run_agent.py` AIAgent.run_conversation() main loop + `_budget_grace_call` mechanism.

**Continuation packet timing:**
- Budget exhaustion detected at `iteration_budget.check()` → returns False when `remaining <= 0`.
- **Grace call:** One extra API call allowed after exhaustion (`_budget_grace_call = True`) to let the model produce a final response rather than mid-tool-call cutoff.
- After grace call completes, loop exits. Response is returned to caller (CLI or gateway).
- **No automatic relay** currently exists — when budget hits zero, the conversation simply ends.

**Relay ordering (current):**
1. Agent loop detects `iteration_budget.remaining <= 0`
2. Sets `_budget_grace_call = True` for one final turn
3. Model produces final response (may summarize partial results)
4. `run_conversation()` returns with `final_response`
5. **Dead end:** No mechanism to resume with fresh budget or hand off to successor agent

**Parent handoff integration points:**
- `cli.py` process_command() calls `agent.run_conversation()` — could catch exhausted return and spawn continuation
- `gateway/` session.py could detect incomplete tool chains and queue relay
- `agent/result_spiller.py` already handles overflow → could signal "needs relay" to orchestrator

**Gap analysis:**
- No continuation token / checkpoint mechanism
- No "relay-needed" signal from BudgetMeter to caller
- Grace call is fire-and-forget — no guarantee of useful summary

**Recommendation for parent ratification:** Add `BudgetMeter.exhaustion_signal()` returning a structured `{exhausted: bool, remaining_grace: int, spill_summary: str}`. Callers (cli/gateway/batch) check this signal post-conversation and decide relay strategy: (a) spawn new agent with remaining context, (b) queue for human review, (c) extend budget with user confirmation.

## Parent Link

- Parent task: 2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略
- Discussion artifact: /Users/charles/.hermes/tick-20260513-213742-502936-p80883-2e691a87-ed06220b/discussion_result.json
- Trigger axis: relay_ordering
- Issue IDs: none tagged

## Parent Objective Snapshot

设计预算耗尽后的自动 continuation handoff 与回退策略，形成从耗尽检测到续跑恢复的完整闭环。

## Narrowed Scope

- Only resolve relay ordering and continuation packet timing.
- Assume quota/threshold semantics are separate prerequisites.

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
