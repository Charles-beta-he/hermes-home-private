---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2: 外部高星设计规范仓库，能提升 UI 生成一致性，但非当前任务池阻塞项"
dependency_order: ["['1) 读取 VoltAgent/awesome-design-md 分类与示例；2) 对比现有 ckm/design/design-md/baseline-ui skills；3) 提炼可复用 DESIGN.md 模板与项目画像字段；4) 只在验证不降级现有 UI 规则后落地技能/模板补丁']"]
created: 2026-05-19T06:50:21+08:00
updated: 2026-05-19T13:34:18+08:00
expires_at: 2026-06-17T19:46:26+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: patch normalization narrowed brief
anti_drift_check: keep implementation slicing smaller than the parent mission
acceptance_evidence: proof log explains why each candidate patch is included, excluded, or deferred
workflow_contract: external_repo_absorption; evidence-first; patch existing/umbrella skill before creating duplicates
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest single-model evidence pass: repo metadata显示80k+ stars、定位为 DESIGN.md files for coding agents；判定 P2/skill-graph，暂不触发昂贵多模型，执行时如要改核心设计技能再外部认证"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-19T08:59:33+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-005115-272504-p14876-b96a187f-5bef09bf/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-为-2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流-细化-patc-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 可与 12Factor/Dreaming 任务并行；落地设计技能补丁前需先完成现有 UI skill 差距对比。
evidence:
  - proof:sha256:508f38e853c153181eb5161ae3719f59cdcd273276963f29967d5cd3b18221e7
  - command:py_compile_taskpool PASS
  - proof:sha256:68a62f9525c0980a85fecefdc650cbf32f1738c632763804509308a34f4e7645
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
multimodel_advisory_only: True
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "evolution_lane"]
multimodel_certification_reasons: ["closeout_ratification"]
---

# Task - 为 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流`. Do not change the parent objective. Normalize surfaced minority patches into a certifiable minimum patch set that preserves the parent objective and removes noop-vs-change ambiguity.

## Acceptance Criteria

- [ ] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-18-吸收-awesome-design-md-的-designmd-代理设计规范机制到-hermes-设计-项目画像工作流
- Discussion artifact: /Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

分析 https://github.com/VoltAgent/awesome-design-md 的 DESIGN.md 机制，提炼 Hermes 在设计技能、项目画像与 UI 生成前置规范中应吸收的最小可维护增量。

## Narrowed Scope

- Only normalize surfaced patch candidates and their inclusion criteria.
- Do not expand into end-to-end implementation here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-19T06:50:21+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

### 2026-05-19 Hermes execution proof — patch normalization narrowed brief

Decision: keep the certifiable minimum patch set empty for this convergence slice; normalize the surfaced minority patch into an explicit no-action brief instead of inventing a new skill/template/code delta.

Included patch set:
- None. `merged_plan.json` reports `planner_patch_summary.certification_intent=no_action_certification`, `concrete_patch_count=0`, and `models_with_noop_only_patches=["deepseek-v4-pro"]`.

Why included:
- The parent evidence tranche already landed the durable DESIGN.md absorption changes that matter for the main objective: `design-md` now contains the awesome-design-md adoption workflow, AGENTS.md/DESIGN.md pairing guidance, project-profile `design_system.design_md` schema, and precedence over `baseline-ui`; the linked absorption reference captures the gap table and minimal Hermes delta; the starter template now includes optional `Responsive Behavior` and `Iteration Guide` sections.
- The only surfaced patch in the certified discussion artifacts is `P-001`, a noop on the parent task note. DeepSeek's plan states all claims in the evidence bundle are already verified and no additional patch is needed.
- Promoting a concrete patch in this child would blur scope and re-open the parent objective despite the discussion artifact carrying no concrete model-backed delta. Normalizing to an explicit empty patch set removes the noop-vs-change ambiguity without weakening the parent acceptance contract.

Excluded/deferred candidates:
- New edits to `design-md`, baseline UI rules, or project-profile schema: excluded here because those deltas are already present in the current skill/reference/template state and were not surfaced as concrete missing patches in the discussion artifact.
- Parent closeout / ratification changes: deferred to the parent and sibling narrowing tasks; this child only resolves whether patch normalization requires a concrete code/content patch.
- Any broad redesign of multimodel quorum or provider handling: excluded; those belong to `quota_observability`, `fallback_threshold`, or `framing`, not this axis.

Validation evidence:
- `/Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/merged_plan.json` shows `minority_patches=["P-001"]`, `patches=[]`, and `planner_patch_summary` with `total_patch_count=1`, `noop_patch_count=1`, `concrete_patch_count=0`, `certification_intent=no_action_certification`.
- `/Users/charles/.hermes/tick-20260518-183738-393915-p95217-7ace76ba-d4feb119/plans/deepseek-v4-pro.json` defines `P-001` as `op=noop` against the parent task note and states no patch is needed because the evidence bundle already grounds C-001/C-002/C-003.
- `creative/design-md/SKILL.md`, `creative/design-md/references/hermes-awesome-design-md-absorption.md`, and `creative/design-md/templates/starter.md` currently contain the parent-facing design absorption deltas (awesome-design-md adoption workflow, profile schema, precedence guidance, optional responsive/iteration sections), so inventing another patch here would be duplicate change.
- `ui-skills/skills/baseline-ui/SKILL.md` still keeps accessibility/interaction/performance red lines authoritative, so leaving this slice as no-action does not weaken existing UI guardrails.

Next handoff:
- Treat patch normalization as resolved to an explicit empty patch set.
- Continue parent convergence via the remaining unresolved axes (`framing`, `quota_observability`, `fallback_threshold`) and then re-run parent ratification instead of reopening new design-skill edits from this child.

## Final Handoff

- Status: done for the narrowed patch-normalization axis; the certifiable minimum patch set is explicitly empty.
- Evidence: merged_plan/deepseek plan prove the only surfaced patch is noop-only, and current `design-md` skill/reference/template state already contains the parent-facing absorption delta while `baseline-ui` still anchors the guardrails.
- Residual risk: parent still cannot close until sibling convergence slices resolve quorum/framing concerns and parent ratification is rerun.

- 2026-05-19T08:51:15+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T08:51:15+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T08:51:15+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:508f38e853c153181eb5161ae3719f59cdcd273276963f29967d5cd3b18221e7, command:py_compile_taskpool PASS

- 2026-05-19T08:57:18+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-005115-686510-p14901-332fae47-856b4dfc/discussion_result.json`. Failures: ["best_within_constraints_missing:gemini-3.1-pro-preview", "missing_required_model_consulted:mimo-v2.5-pro", "missing_required_model_vote:mimo-v2.5-pro", "non_approve_vote:gemini-3.1-pro-preview:amend", "status_not_passed:not_certified", "unexpected_consulted_model:gemini-3.1-pro-preview", "unexpected_vote_model:gemini-3.1-pro-preview"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error", "model_vote_missing"]}

- 2026-05-19T08:57:36+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-005115-532446-p14890-d8d7ec7b-1ed1960f/discussion_result.json`. Failures: ["best_within_constraints_missing:gemini-3.1-pro-preview", "missing_required_model_consulted:mimo-v2.5-pro", "missing_required_model_vote:mimo-v2.5-pro", "non_approve_vote:gemini-3.1-pro-preview:amend", "status_not_passed:not_certified", "unexpected_consulted_model:gemini-3.1-pro-preview", "unexpected_vote_model:gemini-3.1-pro-preview"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error", "model_vote_missing"]}

- 2026-05-19T08:59:33+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-005115-272504-p14876-b96a187f-5bef09bf/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T13:34:18+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:68a62f9525c0980a85fecefdc650cbf32f1738c632763804509308a34f4e7645, proof:sha256:508f38e853c153181eb5161ae3719f59cdcd273276963f29967d5cd3b18221e7, command:py_compile_taskpool PASS
