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
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260517-030728-825276-p50401-372dd38d-7270ebc5/discussion_result.json
multimodel_last_checked_at: 2026-05-17T11:10:52+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-030728-825276-p50401-372dd38d-7270ebc5/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-fallbac-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: auto_subtask_on_non_convergence:fallback_threshold
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
concepts: ["task", "auto-subtask", "non-convergence", "fallback-thresholds"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移 细化 fallback threshold 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移`. Do not change the parent objective. Define fallback thresholds, downgrade policy, and the minimum evidence required to justify noop vs change on budget exhaustion behavior.

## Acceptance Criteria

- [x] Produce a narrowed brief covering trigger thresholds, allowed fallback actions, and explicit noop-vs-change decision criteria.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.

## Narrowed Brief — Fallback Threshold

- **Trigger threshold:** 当 `brain_task_orchestrator.py` 的 ratification 检查仅剩 `best_within_constraints_missing:*` / `non_approve_vote:*:amend` 且根因落在 `provider_parse_error` 时，不应立刻改动 parent 设计；先把该轮判定为 **transport-degraded**，只允许在子任务层补充阈值与证据。
- **Allowed fallback actions:** 1) 保持 `run_agent.py` 的 `stable_parts` / `context_parts` 分层不变，避免为了救某一模型的 parse 而污染共享前缀；2) 对失败模型重试一次同构 `manifest_delta` 包；3) 若仍 `failed_closed`，保留成功模型共识，记录 transport 失败，不在 parent 层引入新 patch。
- **Noop vs change criteria:** 只有当 3 个成功解析模型都 approve 且 `discussion_result.json` 中不存在未解决 issue 时，noop 才可接受；若同一模型连续多轮 `failed_closed`，或成功解析模型出现真实语义 amend/reject，才升级为 change。
- **Evidence anchors:** `run_agent.py:5795-5901` 已把 `stable_parts` 与 `context_parts` 分层；`brain_task_orchestrator.py:5621-5719` 明确把 `best_within_constraints_missing` / agreement 阈值视为 hard gate；本轮 artifact 显示唯一持续失败源是 `gpt-5.5` parse failure，而非其余模型的语义反对。

## Parent Link

- Parent task: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
- Discussion artifact: /Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json
- Trigger axis: fallback_threshold
- Issue IDs: none tagged

## Parent Objective Snapshot

基于用户提出的核心理念落地优化：Agent 能跑起来的关键不是模型多强，而是缓存命中率多高。按全局层/项目层/会话层/消息层分层，修复时间戳进 system prompt、工具序列化顺序漂移、子 agent 参数微调三大陷阱；实践信息更新走 message 不改 prompt，切模型用子 agent 独立运行，工具状态靠调用切换而非删减，压缩操作作为父对话延伸。

## Narrowed Scope

- Only resolve threshold semantics and noop-vs-change decision criteria.
- Do not redesign the full handoff workflow here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator next | PASS | child task claimed and narrowed brief recorded |

## Proof Log

- 2026-05-17T10:54:04+08:00: Task created from local-brain control point.
- 2026-05-17T11:03:00+08:00: Recorded fallback-threshold narrowed brief for the latest loop_non_convergence round; kept stable/context cache layering unchanged and bound noop-vs-change to transport-vs-semantic distinction.
- 2026-05-17T11:00:35+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: manual blocked-parent convergence execution
- 2026-05-17T11:00:35+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: record narrowed convergence brief

## Blockers / Confusions

- None.

## Final Handoff

- Status: ready_for_review
- Evidence: latest discussion artifact + ratification gate lines + prompt layering lines
- Residual risk: provider parse instability on `gpt-5.5` still requires later transport normalization; this slice only freezes threshold semantics.

- 2026-05-17T11:07:28+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: narrowed brief recorded Evidence: proof:sha256:1bf8d5e675c31412f3d9e15994fc56bfd4f3ca11f4ed8b29818038a2f0b585dd, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json

- 2026-05-17T11:07:28+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: narrowed brief accepted as convergence evidence Evidence: proof:sha256:1bf8d5e675c31412f3d9e15994fc56bfd4f3ca11f4ed8b29818038a2f0b585dd, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json

- 2026-05-17T11:10:52+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-030728-825276-p50401-372dd38d-7270ebc5/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
