---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T11:43:19+08:00
updated: 2026-05-19T17:32:39+08:00
expires_at: 2026-06-12T21:36:05+08:00
project: hermes-agent-cache-optimization
architecture_target: provider-quota
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
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T15:04:05+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-065029-148395-p90132-41e73860-f1666e2f/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-relay-o-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "quota_unobservable", "vote_reject"]
multimodel_recommended_axes: ["quota_observability", "fallback_threshold", "relay_ordering", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['quota_unobservable'], 'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'framing': ['vote_reject']}"
auto_subtask_parent: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: relay_ordering
auto_subtask_trigger: auto_subtask_on_non_convergence:relay_ordering
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - proof:sha256:24c53a61a99096e03d2ea93df2a9cf3ebde5b3f0231f45c73a35dfc8765d3170
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:5ba57e2a305d225a97b8d65be97854d87aebba845544496f0c602e261c37b295
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:e2dae51d63eeef9018b0bf9ceb5290255308ba3e0bc041d0d600d616b8255caf
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
  - proof:sha256:c27aac5f9b19aa5c25bf004522cefbdb3295fc06a428160219619c7ea4eba85f
  - proof:sha256:b5c6bd22d595ea4a718bd4bcd70944e318609b6650412e1171f14579f96c6f5c
concepts: ["task", "auto-subtask", "non-convergence", "relay-ordering"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 为 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移 细化 relay ordering 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移`. Do not change the parent objective. Define continuation packet / relay ordering after quota and threshold semantics are known, without reopening the parent mission objective.

## Acceptance Criteria

- [ ] Produce a narrowed brief covering continuation packet timing, relay ordering, and parent handoff integration points.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] Execute the smallest verifiable slice.
- [ ] Record proof and update status.

## Parent Link

- Parent task: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
- Discussion artifact: /Users/charles/.hermes/tick-20260517-032949-818144-p62294-184515cc-2e5ac21f/discussion_result.json
- Trigger axis: relay_ordering
- Issue IDs: none tagged

## Parent Objective Snapshot

基于用户提出的核心理念落地优化：Agent 能跑起来的关键不是模型多强，而是缓存命中率多高。按全局层/项目层/会话层/消息层分层，修复时间戳进 system prompt、工具序列化顺序漂移、子 agent 参数微调三大陷阱；实践信息更新走 message 不改 prompt，切模型用子 agent 独立运行，工具状态靠调用切换而非删减，压缩操作作为父对话延伸。

## Narrowed Scope

- Only resolve relay ordering and continuation packet timing.
- Assume quota/threshold semantics are separate prerequisites.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-17T11:43:19+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T12:22:53+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-041448-319806-p73598-5464af82-2566e873/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T14:50:28+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T14:50:28+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T14:50:29+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:5ba57e2a305d225a97b8d65be97854d87aebba845544496f0c602e261c37b295, command:py_compile_taskpool PASS

- 2026-05-17T14:50:29+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:e2dae51d63eeef9018b0bf9ceb5290255308ba3e0bc041d0d600d616b8255caf, proof:sha256:5ba57e2a305d225a97b8d65be97854d87aebba845544496f0c602e261c37b295, command:py_compile_taskpool PASS

- 2026-05-17T14:59:21+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-065029-279202-p90141-24378c92-2c295ec1/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-17T15:04:05+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-065029-148395-p90132-41e73860-f1666e2f/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]. Recommended axes: ["quota_observability", "fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-19T11:11:13+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T17:32:38+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T17:32:39+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T17:32:39+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:c27aac5f9b19aa5c25bf004522cefbdb3295fc06a428160219619c7ea4eba85f, command:py_compile_taskpool PASS

- 2026-05-19T17:32:39+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:b5c6bd22d595ea4a718bd4bcd70944e318609b6650412e1171f14579f96c6f5c, proof:sha256:24c53a61a99096e03d2ea93df2a9cf3ebde5b3f0231f45c73a35dfc8765d3170, classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task, classification:legacy_autorun_proof_hash=sha256:5ba57e2a305d225a97b8d65be97854d87aebba845544496f0c602e261c37b295, command:py_compile_taskpool PASS, classification:legacy_autorun_proof_hash=sha256:e2dae51d63eeef9018b0bf9ceb5290255308ba3e0bc041d0d600d616b8255caf, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, proof:sha256:c27aac5f9b19aa5c25bf004522cefbdb3295fc06a428160219619c7ea4eba85f
