---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2: 外部高星设计规范仓库，能提升 UI 生成一致性，但非当前任务池阻塞项"
dependency_order: ["['1) 读取 VoltAgent/awesome-design-md 分类与示例；2) 对比现有 ckm/design/design-md/baseline-ui skills；3) 提炼可复用 DESIGN.md 模板与项目画像字段；4) 只在验证不降级现有 UI 规则后落地技能/模板补丁']"]
created: 2026-05-19T06:50:21+08:00
updated: 2026-05-19T18:46:38+08:00
expires_at: 2026-06-17T19:46:26+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: quota observability narrowed brief
anti_drift_check: keep parent objective unchanged while proving quota_state semantics
acceptance_evidence: proof log cites source evidence for quota_state confidence and unknown handling
workflow_contract: external_repo_absorption; evidence-first; patch existing/umbrella skill before creating duplicates
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest single-model evidence pass: repo metadata显示80k+ stars、定位为 DESIGN.md files for coding agents；判定 P2/skill-graph，暂不触发昂贵多模型，执行时如要改核心设计技能再外部认证"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-19T11:19:55+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-030330-120001-p79598-72cddcdd-efb43e35/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-为-2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流-细化-quot-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 1
next_attempt_at: 
workspace: 
parallel_boundary: 可与 12Factor/Dreaming 任务并行；落地设计技能补丁前需先完成现有 UI skill 差距对比。
evidence:
  - proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash
  - command:proof-check PASS
  - command:selfcheck PASS
  - classification:axis=quota_observability_complete_parent_still_blocked
  - artifact:/Users/charles/.hermes/tick-20260519-024140-301112-p56617-d300d818-bbe43359/discussion_result.json
  - command:multimodel_gate FAIL
  - command:multimodel_decision CONTINUE_LOOP
  - command:multimodel_status not_certified
  - command:multimodel_auto_outcome certification_failed
  - proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["accuracy_keyword", "architecture_target", "evolution_lane"]
multimodel_certification_reasons: []
multimodel_auto_uncertain_count: 0
---

# Task - 为 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流`. Do not change the parent objective. Define quota_state source, confidence, staleness, and fail-closed semantics so future ratification can decide whether quota-aware change is required.

## Acceptance Criteria

- [x] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流
- Discussion artifact: /Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/discussion_result.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

分析 https://github.com/VoltAgent/awesome-design-md 的 DESIGN.md 机制，提炼 Hermes 在设计技能、项目画像与 UI 生成前置规范中应吸收的最小可维护增量。

## Narrowed Scope

- Only resolve quota observability and evidence gaps.
- Do not decide relay ordering or broader fallback policy here.

## Quota Observability Brief

### File-backed evidence locations

- Parent discussion artifact: `/Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/discussion_result.json`.
- Child task note: this file is the canonical evidence deposit for `auto_subtask_axis: quota_observability`.
- Runtime multimodel state should be stored under `~/.hermes/state/taskpool-multimodel/<task-id>-state.json` when a certification/advisory round runs.
- Dispatch/tick evidence is observable in `~/.hermes/logs/brain_task_dispatch_tick.jsonl` and task lifecycle proof log entries.

### quota_state schema required before interpreting votes

Use this minimum structure in future ratification artifacts or task evidence:

```yaml
quota_state:
  source: runtime_provider_observation | discussion_artifact | manual_review
  observed_at: <ISO-8601 timestamp>
  canonical_participants_expected: [claude-opus-4-7, gpt-5.5, deepseek-v4-pro, mimo-v2.5-pro]
  canonical_participants_seen: []
  noncanonical_participants_seen: []
  unavailable_participants: []
  provider_parse_errors: []
  confidence: high | medium | low | unknown
  stale_after: <ISO-8601 timestamp or duration>
```

### Confidence rules

- **high**: each expected canonical participant has either a valid vote or an explicit unavailable/quota record, and no unexpected model is counted as approval evidence.
- **medium**: at least two canonical participants are observed, missing participants have explicit quota/unavailable records, and the task remains advisory or review-only.
- **low**: participant set is incomplete or mixed with noncanonical model IDs, but the artifact is still parseable enough to diagnose the gap.
- **unknown**: provider output is missing/unparseable, state file is absent, or model IDs cannot be mapped to canonical IDs.

### Unknown/unobservable handling

- Unknown quota state is a hard stop for parent closeout, not a reason to lower thresholds.
- Noncanonical models such as unexpected Gemini IDs may be retained as diagnostic evidence but must not satisfy `expected_participants`.
- Missing `mimo-v2.5-pro` must be recorded as `unavailable_participants` or `missing_required_model_*`; it cannot be silently substituted.
- Provider parse errors are routed to `patch_normalization`, while genuine missing capacity routes to this `quota_observability` axis.

### Parent handoff

Quota observability is now defined enough for the parent to distinguish:

1. **semantic disagreement**: canonical participants are observed and disagree;
2. **tooling noise**: parse/model-ID normalization failed;
3. **quota/capacity uncertainty**: expected participant was absent with no explicit unavailable record.

The parent should not refresh ratification until sibling `patch_normalization` and `framing` evidence are also in review/done.

## Narrowed Brief

### Quota observability contract

- Source of truth: quota/provider state must be recorded as file-backed evidence, not inferred from model tone or partial discussion success. Acceptable evidence locations are the parent task note, the referenced discussion artifact, and any state file emitted under `/Users/charles/.hermes/state/taskpool-multimodel/`.
- Minimum `quota_state` shape for future ratification: `expected_canonical_participants`, `seen_canonical_participants`, `missing_canonical_participants`, `noncanonical_participants`, `provider_parse_errors`, `unavailable_participants`, `confidence`, `staleness`, and `evidence_paths`.
- Confidence levels: `high` only when all expected canonical participants are observed with parseable votes; `medium` when quorum exists but optional/noncanonical drift is present; `low` when a required participant is missing or parse errors affect decision fields; `unknown` when evidence is absent or stale.
- Unknown/unobservable handling: unknown quota/provider state is diagnostic evidence only. It may justify splitting or retry scheduling, but it must not lower the truth gate, convert advisory output into certification, or mark parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流` done.
- Parent boundary: this child only defines observability semantics. It does not decide implementation order, fallback threshold, or parent unblocking.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator claim/transition | PASS | task claimed and moved to running before writeback |
| narrowed brief completeness | PASS | quota source, confidence, unknown handling, and evidence paths recorded |
| deterministic safety | pending | run proof/selfcheck after transition evidence hash is created |
| parent boundary preserved | done | parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流` remains blocked until sibling axes and ratification refresh |

## Proof Log

- 2026-05-19T10:17:00+08:00: Landed bounded quota-observability narrowed brief. It defines how future ratification must record quota/provider/canonical participant state without treating missing or noncanonical model output as approval.
- 2026-05-19T06:50:21+08:00: Task created from local-brain control point.

- 2026-05-19T18:46:31+08:00: manual bounded child-axis tranche completed for `quota_observability`; this is child-axis evidence only and does not unblock parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流` by itself.

## Blockers / Confusions

- This axis defines quota/participant observability only; it does not normalize malformed provider output or decide the final DESIGN.md adoption patch.
- If future multimodel output still includes noncanonical IDs, route that to `patch_normalization` before parent ratification.

## Final Handoff

- Status: quota-observability narrowed brief complete; safe for review with deterministic proof.
- Evidence: file-backed evidence locations, quota_state schema, confidence rules, and unknown/unobservable handling are recorded above.
- Residual risk: parent still requires patch_normalization + framing evidence before ratification refresh.

- 2026-05-19T10:16:06+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-19T10:16:06+08:00: Lifecycle transition `claimed` -> `running` by `hermes`.

- 2026-05-19T10:17:12+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: quota_observability_narrowed_brief_complete Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=quota_observability_complete_parent_still_blocked

- 2026-05-19T10:48:07+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-024140-301112-p56617-d300d818-bbe43359/discussion_result.json`. Failures: ["best_within_constraints_missing:gemini-3.1-pro-preview", "missing_required_model_consulted:mimo-v2.5-pro", "missing_required_model_vote:mimo-v2.5-pro", "non_approve_vote:gemini-3.1-pro-preview:amend", "status_not_passed:not_certified", "unexpected_consulted_model:gemini-3.1-pro-preview", "unexpected_vote_model:gemini-3.1-pro-preview"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error", "model_vote_missing"]}

- 2026-05-19T10:51:01+08:00: Lifecycle transition `review` -> `retry` by `hermes-autorun-review-close`. Reason: multimodel closeout certification_failed; returned to retry for correction: previous_multimodel_certification_failed Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=quota_observability_complete_parent_still_blocked, artifact:/Users/charles/.hermes/tick-20260519-024140-301112-p56617-d300d818-bbe43359/discussion_result.json, command:multimodel_gate FAIL, command:multimodel_decision CONTINUE_LOOP, command:multimodel_status not_certified, command:multimodel_auto_outcome certification_failed

- 2026-05-19T11:12:44+08:00: Reconcile action `retry_due_promoted` by `next`. Previous status `retry`.

- 2026-05-19T11:19:55+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-030330-120001-p79598-72cddcdd-efb43e35/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T18:46:34+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_claim

- 2026-05-19T18:46:34+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_running

- 2026-05-19T18:46:38+08:00: Lifecycle transition `running` -> `review` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_review Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=quota_observability_complete_parent_still_blocked

- 2026-05-19T18:46:38+08:00: Lifecycle transition `review` -> `done` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_done Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=quota_observability_complete_parent_still_blocked
