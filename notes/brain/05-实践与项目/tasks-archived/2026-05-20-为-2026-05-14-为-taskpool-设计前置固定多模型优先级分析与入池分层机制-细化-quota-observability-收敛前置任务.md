---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-20T21:03:29+08:00
updated: 2026-05-21T00:14:39+08:00
expires_at: 2026-06-13T00:56:42+08:00
project: hermes-agent
architecture_target: taskpool
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
multimodel_triage_result: not_certified
auto_subtask_parent: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence: []
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
---

# Task - 为 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制`. Do not change the parent objective. Define quota_state source, confidence, staleness, and fail-closed semantics so future ratification can decide whether quota-aware change is required.

## Acceptance Criteria

- [x] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Narrowed Brief

### 1. quota_state source of truth

- Runtime quota state is read from `~/.hermes/scripts/model_quota.py` and materialized through `snapshot_models(...)` plus `gate_models(...)`.
- Parent ratification loop records this state through `~/.hermes/scripts/brain_task_multimodel_loop_runner.py` `collect_model_quota_probe(...)`, then carries the snapshot into `discussion_result.json` as `quota_snapshot` / `quota_confidence`.
- The current blocked parent artifact already shows that path end-to-end: `/Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json` contains `planner_patch_summary`, `quota_confidence`, `quota_snapshot`, and the unresolved issue ledger in one packet.

### 2. Confidence semantics

- `default_snapshot(...)` is intentionally pessimistic:
  - subscription providers (`openai-codex`) default to `status=unobservable`, `quota_type=subscription_cap`, `confidence=0.2`.
  - non-subscription providers default to `status=unknown`, `quota_type=unknown`, `confidence=0.1`.
- `snapshot_from_headers(...)` only becomes high-confidence when real rate-limit headers exist; otherwise the snapshot remains low-confidence even if a call succeeded.
- `snapshot_unobservable_success(...)` is explicitly availability evidence, not budget evidence, and caps confidence below `0.49` with policy scope `low_risk_routing_only; not_budget_handoff_certification`.
- `quota_observability_summary(...)` / `quota_observability_evidence(...)` treat `unknown` and `unobservable` as degraded-confidence states, not healthy budget proof.

### 3. Current observed state for this parent problem

- Parent discussion artifact snapshot (`2026-05-19` round): `exact_count=0`, `estimated_count=0`, `unknown_count=4`, `unobservable_count=1`, `has_low_confidence_quota=true`.
- Current local confidence gate (`python3 ~/.hermes/scripts/model_quota.py confidence-gate --json`) still fails closed for the T3 working set:
  - `claude-opus-4-7`: `unknown`, confidence `0.1`
  - `deepseek-v4-pro`: `unknown`, confidence `0.1`
  - `gpt-5.5`: `unobservable`, confidence `0.2`, `quota_type=subscription_cap`
  - `mimo-v2.5-pro`: `unknown`, confidence `0.1`
- This means the control plane can keep these snapshots for routing visibility, but none of them are sufficient as budget-handoff certification evidence.

### 4. Unknown / unobservable handling

- `gate_models(...)` only hard-blocks explicit exhaustion / rate-limit / malformed / unavailable states. Unknown or unobservable snapshots may still be routed for low-risk execution.
- `confidence-gate` and `quota_observability_evidence(...)` are the stricter layer: they fail closed for `unknown`, `unobservable`, `low`, `exhausted`, `rate_limited`, `malformed`, and `unavailable` when the workflow needs budget-handoff/autonomy-grade proof.
- Therefore the durable rule for the parent task is:
  - low-risk triage/routing may proceed with unknown or unobservable quota state,
  - but any budget-aware ratification or autonomy claim must attach explicit quota observability evidence and must fail closed when only unknown/unobservable snapshots exist.

### 5. Staleness semantics

- All default / unobservable snapshots carry `stale_after_seconds=300`.
- Freshness alone is not enough: a fresh `unknown` or fresh `unobservable` snapshot is still low-confidence and still not sufficient for budget handoff.
- So parent ratification should read staleness as a second-order condition:
  1. stale snapshots are definitely insufficient,
  2. fresh exact / high-confidence snapshots may support budget claims,
  3. fresh unknown / unobservable snapshots remain routing-only evidence.

### 6. Evidence locations and refresh actions

- Core code semantics:
  - `~/.hermes/scripts/model_quota.py`
  - `~/.hermes/scripts/consult_models.py`
  - `~/.hermes/scripts/brain_task_multimodel_loop_runner.py`
- Parent blocked artifact with embedded quota packet:
  - `/Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json`
- Current local quota state file:
  - `/Users/charles/.hermes/state/model_quota_state.json`
- Current fail-closed readiness check:
  - `python3 /Users/charles/.hermes/scripts/model_quota.py confidence-gate --json`
- Refresh actions already implied by the confidence gate:
  - DeepSeek -> `probe_deepseek_balance`
  - Anthropic / Xiaomi -> record provider response headers
  - OpenAI Codex subscription path -> manual budget confirmation or lower-risk tier; do not pretend it is exact quota telemetry

## Parent Link

- Parent task: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
- Discussion artifact: /Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

将外部仓库/文章等任务在创建入池前先经过固定多模型分析，直接产出 P1/P2/P3 与优先级依据，使任务池更独立、更可解释、更稳定。

## Narrowed Scope

- Only resolve quota observability and evidence gaps.
- Do not decide relay ordering or broader fallback policy here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| parent discussion artifact quota packet | PASS | `/Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json` shows `quota_confidence`=`unknown_count 4` / `unobservable_count 1` and embeds `quota_snapshot` for the parent ratification round |
| `python3 /Users/charles/.hermes/scripts/model_quota.py confidence-gate --json` | PASS (expected fail-closed evidence) | returns `status=FAIL_CLOSED`, `usable=0`, refresh actions `probe_deepseek_balance`, `record_provider_response_headers`, `manual_budget_confirmation_or_lower_risk_tier` |
| current quota state readback | PASS | `/Users/charles/.hermes/state/model_quota_state.json` confirms T3 models remain `unknown` / `unobservable` with confidence `0.1` / `0.2` and no exact quota evidence |

## Proof Log

- 2026-05-20T21:03:29+08:00: Task created from local-brain control point.
- 2026-05-21T00:14:39+08:00: Completed quota observability narrowed brief. Traced quota_state from `model_quota.py` -> `brain_task_multimodel_loop_runner.py` -> parent `discussion_result.json`, confirmed current T3 evidence remains `unknown/unobservable`, and documented the fail-closed split between low-risk routing and budget-handoff certification.

## Blockers / Confusions

- None for this narrowed brief. Residual work belongs to parent ratification refresh, not to quota semantics discovery.

## Final Handoff

- Status: narrowed brief complete; quota_state semantics are now explicit enough for parent ratification to treat quota evidence as a first-class gate instead of implicit background state.
- Evidence: `~/.hermes/scripts/model_quota.py`, `~/.hermes/scripts/consult_models.py`, `~/.hermes/scripts/brain_task_multimodel_loop_runner.py`, parent artifact `/Users/charles/.hermes/tick-20260519-141151-420713-p52970-87805ecb-ab00cbaa/discussion_result.json`, current state `/Users/charles/.hermes/state/model_quota_state.json`, and local `model_quota.py confidence-gate --json` output.
- Residual risk: parent task is still blocked on broader noop-vs-change / relay / framing convergence; quota observability is now bounded, but the current model fleet still lacks budget-handoff-grade exact quota proof.
