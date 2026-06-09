---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T10:54:04+08:00
updated: 2026-05-17T11:07:28+08:00
expires_at: 2026-06-12T21:36:05+08:00
project: hermes-agent-cache-optimization
architecture_target: provider-quota
capability_delta: patch normalization narrowed brief
anti_drift_check: keep implementation slicing smaller than the parent mission
acceptance_evidence: proof log explains why each candidate patch is included, excluded, or deferred
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T11:10:50+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-030037-328984-p41580-c507ad48-2e7d5f27/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-patch-n-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "relay_ordering", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'framing': ['vote_reject']}"
auto_subtask_parent: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json
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
  - artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移`. Do not change the parent objective. Normalize the surfaced candidate patches into the smallest certifiable patch set and defer everything else explicitly.

## Acceptance Criteria

- [x] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.

## Narrowed Brief — Patch Normalization

- **Minimum certifiable patch set:** 仅包含 transport/ratification 归一化，不触碰 parent 的缓存层设计：1) 将 `failed_closed` / unparseable model 结果显式降格为 `provider_parse_error` 证据；2) 保留 canonical four-model vote ledger，但把 transport failure 与 semantic amend 分开表达；3) 禁止把缺失 `best_within_constraints` 直接解释成新方案分歧。
- **Include:** `brain_task_orchestrator.py:5644-5709` 的 canonical vote / required-model gate；`consult_models.py:1755-1815` 的 `fanout_certification_status()`，用于区分 `degraded_not_certified` 与真正 multi-model certified。
- **Exclude:** router 调权、prompt 结构改造、额外 handoff 设计——这些超出本子任务。
- **Decision rule:** 如果失败集中在 parser/transport，优先归一化 artifact schema；只有当成功解析模型之间也存在实质 patch 分歧时，才把问题升级回 parent 设计争议。

## Parent Link

- Parent task: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
- Discussion artifact: /Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

基于用户提出的核心理念落地优化：Agent 能跑起来的关键不是模型多强，而是缓存命中率多高。按全局层/项目层/会话层/消息层分层，修复时间戳进 system prompt、工具序列化顺序漂移、子 agent 参数微调三大陷阱；实践信息更新走 message 不改 prompt，切模型用子 agent 独立运行，工具状态靠调用切换而非删减，压缩操作作为父对话延伸。

## Narrowed Scope

- Only normalize the minimum certifiable patch set.
- Do not widen into router or prompt-architecture changes.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | PASS | patch-normalization brief written with canonical include/exclude rules |

## Proof Log

- 2026-05-17T10:54:04+08:00: Task created from local-brain control point.
- 2026-05-17T11:03:00+08:00: Normalized the current disagreement into a minimum transport-focused patch set and explicitly excluded router retuning / broader design drift.
- 2026-05-17T11:00:36+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: manual blocked-parent convergence execution
- 2026-05-17T11:00:36+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: record narrowed convergence brief

## Blockers / Confusions

- None.

## Final Handoff

- Status: ready_for_review
- Evidence: latest discussion artifact + canonical vote gate + fanout certification code
- Residual risk: without a follow-up code patch, future rounds can still fail-closed on parser output; this slice only freezes the admissible patch scope.

- 2026-05-17T11:07:28+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: narrowed brief recorded Evidence: proof:sha256:378ea994fd6ed06885a815cfc301301a4fa64395e6cf357b2b8f9d3c6cf77302, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json

- 2026-05-17T11:07:28+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: narrowed brief accepted as convergence evidence Evidence: proof:sha256:378ea994fd6ed06885a815cfc301301a4fa64395e6cf357b2b8f9d3c6cf77302, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json

- 2026-05-17T11:10:50+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-030729-264021-p50431-e34c3a0b-05be0a4c/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T11:10:50+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-030037-328984-p41580-c507ad48-2e7d5f27/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}
