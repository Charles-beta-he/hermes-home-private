---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-18T11:35:26+08:00
updated: 2026-05-18T12:41:19+08:00
expires_at: 2026-06-12T21:36:05+08:00
project: hermes-agent-cache-optimization
architecture_target: provider-quota
capability_delta: framing narrowed brief
anti_drift_check: parent objective remains canonical
acceptance_evidence: proof log maps each unresolved issue to one narrowed question
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: not_certified
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json
multimodel_last_checked_at: 2026-05-18T12:40:54+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-framing-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: framing
auto_subtask_trigger: auto_subtask_on_non_convergence:framing
auto_subtask_issue_ids: ["I-001", "I-002", "I-003", "I-004", "I-005", "I-006", "I-007", "I-008", "I-009", "I-010", "I-011"]
auto_subtask_parent_artifact: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-manual-targeted-evidence-state.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json
  - command:multimodel_gate PASS
  - command:multimodel_decision LOOP_DONE
  - command:multimodel_status certified
  - artifact:/Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json
  - classification:legacy_autorun_proof_hash=sha256:d4afd57baf9fbfba9caf636e8710509175b869dd6c1bb663f6594a236d4eec56
concepts: ["task", "auto-subtask", "non-convergence", "framing"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "evolution_lane"]
multimodel_certification_reasons: ["closeout_ratification"]
---

# Task - 为 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移 细化 framing 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移`. Do not change the parent objective. Extract the minimum narrowed brief needed to resolve the current non-convergence without changing the parent objective.

## Acceptance Criteria

- [ ] Produce a narrowed brief that maps unresolved issues to one concrete evidence or design question each.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
- Discussion artifact: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-manual-targeted-evidence-state.json
- Trigger axis: framing
- Issue IDs: I-001, I-002, I-003, I-004, I-005, I-006, I-007, I-008, I-009, I-010, I-011

## Parent Objective Snapshot

基于用户提出的核心理念落地优化：Agent 能跑起来的关键不是模型多强，而是缓存命中率多高。按全局层/项目层/会话层/消息层分层，修复时间戳进 system prompt、工具序列化顺序漂移、子 agent 参数微调三大陷阱；实践信息更新走 message 不改 prompt，切模型用子 agent 独立运行，工具状态靠调用切换而非删减，压缩操作作为父对话延伸。

## Narrowed Scope

- Resolve only the highest-leverage unresolved issue cluster first.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-18T11:35:26+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-18T11:43:56+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: auto-claim-and-handoff

- 2026-05-18T11:44:08+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: autorun_handoff_promoted_to_running_for_targeted_convergence

- 2026-05-18T11:47:02+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-034356-421337-p66632-d2bd8c6e-e58f5f52/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T11:51:41+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-034408-951313-p66800-7dc2a64c-e64d070a/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-18T12:40:54+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T12:41:18+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: multimodel PASS/LOOP_DONE achieved; send certified framing child to review Evidence: artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json, command:multimodel_gate PASS, command:multimodel_decision LOOP_DONE, command:multimodel_status certified

- 2026-05-18T12:41:19+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: close certified framing child after proof-gated review Evidence: artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json, artifact:/Users/charles/.hermes/tick-20260518-043749-755673-p98558-15d35199-f91835a4/discussion_result.json, command:multimodel_gate PASS, command:multimodel_decision LOOP_DONE, command:multimodel_status certified, classification:legacy_autorun_proof_hash=sha256:d4afd57baf9fbfba9caf636e8710509175b869dd6c1bb663f6594a236d4eec56
- proof:legacy autorun proof hashes preserved as classification because current autorun proof chain no longer validates historical hashes; no new verification fabricated
- classification:legacy_autorun_hash_migrated_due_to_current_chain_mismatch
