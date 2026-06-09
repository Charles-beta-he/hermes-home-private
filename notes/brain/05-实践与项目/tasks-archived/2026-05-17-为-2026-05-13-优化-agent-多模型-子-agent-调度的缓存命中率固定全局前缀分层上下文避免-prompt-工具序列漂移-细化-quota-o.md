---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T10:54:04+08:00
updated: 2026-05-17T11:07:29+08:00
expires_at: 2026-06-12T21:36:05+08:00
project: hermes-agent-cache-optimization
architecture_target: provider-quota
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
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T11:17:35+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-030730-260591-p50476-8de77fc8-fad1b748/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-quota-o-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "provider_parse_error", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "relay_ordering", "patch_normalization", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'patch_normalization': ['provider_parse_error'], 'framing': ['vote_reject', 'provider_parse_error']}"
auto_subtask_parent: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
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
  - "proof: manual convergence closeout by hermes; narrowed brief written, artifact recorded, and py_compile_narrowed_briefs PASS"
  - command:py_compile_narrowed_briefs PASS
  - artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移`. Do not change the parent objective. Pin down quota-state evidence, confidence, and unknown-handling so the parent no longer debates whether missing model outputs are observable or semantic.

## Acceptance Criteria

- [x] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [x] Reconcile current state before execution.
- [x] Execute the smallest verifiable slice.
- [x] Record proof and update status.

## Narrowed Brief — Quota Observability

- **Observable quota source:** 对该 parent 而言，真正需要观测的不是纯美元余额，而是 multi-model fanout 的可用性：`discussion_result.json` 中的 `parse_status_by_model`、`prompt_chars_by_model`、`estimated_tokens_saved` 与 `consult_models.py:1755-1815` fanout counters 共同构成 provider-quota state。
- **Confidence / freshness:** artifact 是轮次级即时产物，freshness 高；但当某模型 `failed_closed` 时，只能说明 transport/配额链路不可用，不能反推出其语义 stance。
- **Unknown handling:** 任何 `failed_closed` / missing vote 都必须显示为 degraded，不允许静默当作 noop 共识；这与 `brain_task_orchestrator.py:5664-5719` 的 required-model gate 对齐。
- **Parent implication:** parent 的缓存优化结论只能在“成功模型共识 + 失败模型被明确标成 transport-unobservable”的前提下推进，否则应先补 observability artifact。

## Parent Link

- Parent task: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
- Discussion artifact: /Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

基于用户提出的核心理念落地优化：Agent 能跑起来的关键不是模型多强，而是缓存命中率多高。按全局层/项目层/会话层/消息层分层，修复时间戳进 system prompt、工具序列化顺序漂移、子 agent 参数微调三大陷阱；实践信息更新走 message 不改 prompt，切模型用子 agent 独立运行，工具状态靠调用切换而非删减，压缩操作作为父对话延伸。

## Narrowed Scope

- Only resolve quota-state evidence semantics.
- Do not redesign the parent cache architecture here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| discussion_result parse_status_by_model | PASS | provider-quota observability source and unknown handling captured |

## Proof Log

- 2026-05-17T10:54:04+08:00: Task created from local-brain control point.
- 2026-05-17T11:03:00+08:00: Bound provider-quota observability to per-model parse/fanout evidence instead of inferring semantics from missing votes.
- 2026-05-17T11:00:37+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: manual blocked-parent convergence execution
- 2026-05-17T11:00:37+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: record narrowed convergence brief

## Blockers / Confusions

- None.

## Final Handoff

- Status: ready_for_review
- Evidence: latest discussion artifact + fanout certification code + required-model gate
- Residual risk: the stack still lacks a first-class `provider_parse_observable` field; this slice only freezes the evidence contract.

- 2026-05-17T11:07:28+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: narrowed brief recorded Evidence: proof:sha256:e520b4f06246049ff820201593e14607bb8f9e5240cc7aa523d7573eab173106, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json

- 2026-05-17T11:07:29+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: narrowed brief accepted as convergence evidence Evidence: proof:sha256:e520b4f06246049ff820201593e14607bb8f9e5240cc7aa523d7573eab173106, command:py_compile_narrowed_briefs PASS, artifact:/Users/charles/.hermes/tick-20260516-144747-864197-p63917-ec68a7f0-39e52d66/discussion_result.json

- 2026-05-17T11:10:28+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-030038-545527-p41682-71c32a89-58e2e84a/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["quota_observability", "fallback_threshold", "relay_ordering", "patch_normalization", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}

- 2026-05-17T11:17:35+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-030730-260591-p50476-8de77fc8-fad1b748/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}
