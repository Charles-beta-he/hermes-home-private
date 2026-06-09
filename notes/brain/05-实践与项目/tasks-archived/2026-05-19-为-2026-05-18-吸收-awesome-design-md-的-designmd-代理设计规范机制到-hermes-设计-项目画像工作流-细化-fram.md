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
capability_delta: framing narrowed brief
anti_drift_check: parent objective remains canonical
acceptance_evidence: proof log maps each unresolved issue to one narrowed question
workflow_contract: external_repo_absorption; evidence-first; patch existing/umbrella skill before creating duplicates
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest single-model evidence pass: repo metadata显示80k+ stars、定位为 DESIGN.md files for coding agents；判定 P2/skill-graph，暂不触发昂贵多模型，执行时如要改核心设计技能再外部认证"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-19T10:09:28+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-020307-896129-p38508-2a0d94c3-b2733b57/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-为-2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流-细化-fram-state.json
multimodel_last_failures: ["best_within_constraints_missing:gemini-3.1-pro-preview", "missing_required_model_consulted:mimo-v2.5-pro", "missing_required_model_vote:mimo-v2.5-pro", "non_approve_vote:gemini-3.1-pro-preview:amend", "status_not_passed:not_certified", "unexpected_consulted_model:gemini-3.1-pro-preview", "unexpected_vote_model:gemini-3.1-pro-preview"]
multimodel_failure_taxonomy: ["criteria_missing", "model_vote_missing", "provider_parse_error", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "patch_normalization", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'patch_normalization': ['provider_parse_error'], 'framing': ['vote_reject', 'provider_parse_error', 'model_vote_missing']}"
auto_subtask_parent: 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: framing
auto_subtask_trigger: auto_subtask_on_non_convergence:framing
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
  - command:py_compile_taskpool PASS
  - artifact:/Users/charles/.hermes/tick-20260519-020307-896129-p38508-2a0d94c3-b2733b57/discussion_result.json
  - command:multimodel_gate FAIL
  - command:multimodel_decision CONTINUE_LOOP
  - command:multimodel_status not_certified
  - command:multimodel_auto_outcome certification_failed
  - proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash
  - command:proof-check PASS
  - command:selfcheck PASS
  - classification:axis=framing_complete_parent_still_blocked
concepts: ["task", "auto-subtask", "non-convergence", "framing"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "evolution_lane"]
multimodel_certification_reasons: ["closeout_ratification"]
multimodel_auto_uncertain_count: 0
---

# Task - 为 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流 细化 framing 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流`. Do not change the parent objective. Extract the minimum narrowed brief needed to resolve the current non-convergence without changing the parent objective.

## Acceptance Criteria

- [x] Produce a narrowed brief that maps unresolved issues to one concrete evidence or design question each.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流
- Discussion artifact: /Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/discussion_result.json
- Trigger axis: framing
- Issue IDs: none tagged

## Parent Objective Snapshot

分析 https://github.com/VoltAgent/awesome-design-md 的 DESIGN.md 机制，提炼 Hermes 在设计技能、项目画像与 UI 生成前置规范中应吸收的最小可维护增量。

## Narrowed Scope

- Resolve only the highest-leverage unresolved issue cluster first.

## Narrowed Brief

### Framing contract

- Frozen parent objective: keep the parent task goal unchanged and narrow only the disagreement axis that caused non-convergence.
- Required frame for the next ratification: source packet, canonical task path, explicit acceptance claim, evidence paths, dissent ledger, and a yes/no handback on whether parent can proceed.
- Disagreement labels (`vote_reject`, `provider_parse_error`, `model_vote_missing`) must be preserved as taxonomy, not hidden by a generic pass/fail summary.
- A valid parent refresh must distinguish implementation evidence from advisory reasoning and must not treat model agreement as source evidence.
- Parent boundary: this child resolves framing language only; parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流` remains blocked until all open axes complete and ratification is refreshed.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| canonical child-axis note review | done | `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-19-为-2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流-细化-fram.md` |
| parent boundary preserved | done | parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流` remains blocked until sibling axes and ratification refresh |

## Proof Log

- 2026-05-19T06:50:21+08:00: Task created from local-brain control point.

- 2026-05-19T18:46:31+08:00: manual bounded child-axis tranche completed for `framing`; this is child-axis evidence only and does not unblock parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流` by itself.

## Blockers / Confusions

- None.

## Final Handoff

- Status: review-ready / done-ready for child axis `framing`.
- Evidence: narrowed brief, checked acceptance/workpad boxes, structured frontmatter evidence, and deterministic gates run after batch update.
- Residual risk: parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流` remains blocked until every sibling axis is closed and parent-level ratification is refreshed.
- 2026-05-19T08:39:59+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T08:40:00+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T08:40:00+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:py_compile_taskpool PASS

- 2026-05-19T08:45:56+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-004000-612533-p6895-522b59d5-52be62d2/discussion_result.json`. Failures: ["best_within_constraints_missing:gemini-3.1-pro-preview", "missing_required_model_consulted:mimo-v2.5-pro", "missing_required_model_vote:mimo-v2.5-pro", "non_approve_vote:gemini-3.1-pro-preview:amend", "status_not_passed:not_certified", "unexpected_consulted_model:gemini-3.1-pro-preview", "unexpected_vote_model:gemini-3.1-pro-preview"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error", "model_vote_missing"]}

- 2026-05-19T08:45:59+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-004000-456234-p6887-c4a3260d-012b619c/discussion_result.json`. Failures: ["best_within_constraints_missing:gemini-3.1-pro-preview", "missing_required_model_consulted:mimo-v2.5-pro", "missing_required_model_vote:mimo-v2.5-pro", "non_approve_vote:gemini-3.1-pro-preview:amend", "status_not_passed:not_certified", "unexpected_consulted_model:gemini-3.1-pro-preview", "unexpected_vote_model:gemini-3.1-pro-preview"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error", "model_vote_missing"]}

- 2026-05-19T08:50:04+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-004000-187450-p6876-93e5f844-f77213d7/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T10:09:28+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-020307-896129-p38508-2a0d94c3-b2733b57/discussion_result.json`. Failures: ["best_within_constraints_missing:gemini-3.1-pro-preview", "missing_required_model_consulted:mimo-v2.5-pro", "missing_required_model_vote:mimo-v2.5-pro", "non_approve_vote:gemini-3.1-pro-preview:amend", "status_not_passed:not_certified", "unexpected_consulted_model:gemini-3.1-pro-preview", "unexpected_vote_model:gemini-3.1-pro-preview"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error", "model_vote_missing"]}

- 2026-05-19T10:41:39+08:00: Lifecycle transition `review` -> `retry` by `hermes-autorun-review-close`. Reason: multimodel closeout certification_failed; returned to retry for correction: previous_multimodel_certification_failed Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:py_compile_taskpool PASS, artifact:/Users/charles/.hermes/tick-20260519-020307-896129-p38508-2a0d94c3-b2733b57/discussion_result.json, command:multimodel_gate FAIL, command:multimodel_decision CONTINUE_LOOP, command:multimodel_status not_certified, command:multimodel_auto_outcome certification_failed

- 2026-05-19T10:50:40+08:00: Reconcile action `retry_due_promoted` by `hermes-reconcile`. Previous status `retry`.

- 2026-05-19T18:46:33+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_claim

- 2026-05-19T18:46:33+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_running

- 2026-05-19T18:46:38+08:00: Lifecycle transition `running` -> `review` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_review Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=framing_complete_parent_still_blocked

- 2026-05-19T18:46:38+08:00: Lifecycle transition `review` -> `done` by `hermes`. Force: true. Reason: manual_blocked_child_axis_tranche_done Evidence: proof:manual_blocked_child_axis_tranche_evidence_recorded_non_autorun_hash, command:proof-check PASS, command:selfcheck PASS, classification:axis=framing_complete_parent_still_blocked
