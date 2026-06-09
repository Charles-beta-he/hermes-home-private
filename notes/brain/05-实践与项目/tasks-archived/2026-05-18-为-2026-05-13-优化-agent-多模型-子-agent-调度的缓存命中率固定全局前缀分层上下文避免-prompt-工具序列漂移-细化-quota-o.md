---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-18T11:35:26+08:00
updated: 2026-05-18T12:20:30+08:00
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
multimodel_triage_result: not_certified
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json
multimodel_last_checked_at: 2026-05-18T12:11:33+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-quota-o-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-manual-targeted-evidence-state.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json
  - command:multimodel_gate PASS
  - command:multimodel_decision LOOP_DONE
  - command:multimodel_status certified
  - artifact:/Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json
  - classification:legacy_autorun_proof_hash=sha256:7e0ffdc0228de10281675158b6002b784e760fddca024bfb66dec69a9966a426
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["accuracy_keyword", "architecture_target", "evolution_lane"]
multimodel_certification_reasons: ["closeout_ratification"]
---

# Task - 为 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移`. Do not change the parent objective. Define quota_state source, confidence, staleness, and fail-closed semantics so future ratification can decide whether quota-aware change is required.

## Acceptance Criteria

- [ ] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移
- Discussion artifact: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-manual-targeted-evidence-state.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

基于用户提出的核心理念落地优化：Agent 能跑起来的关键不是模型多强，而是缓存命中率多高。按全局层/项目层/会话层/消息层分层，修复时间戳进 system prompt、工具序列化顺序漂移、子 agent 参数微调三大陷阱；实践信息更新走 message 不改 prompt，切模型用子 agent 独立运行，工具状态靠调用切换而非删减，压缩操作作为父对话延伸。

## Narrowed Scope

- Only resolve quota observability and evidence gaps.
- Do not decide relay ordering or broader fallback policy here.

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

- 2026-05-18T11:59:10+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Reason: auto-claim-and-handoff

- 2026-05-18T12:07:37+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: 推进 non-convergence child into active implementation after handoff

- 2026-05-18T12:08:09+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260518-035910-976275-p76236-6ed485fd-3a5f732a/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T12:11:33+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T12:20:28+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: multimodel PASS/LOOP_DONE achieved; send certified child to review Evidence: artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json, command:multimodel_gate PASS, command:multimodel_decision LOOP_DONE, command:multimodel_status certified

- 2026-05-18T12:20:30+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: close certified quota child after proof-gated review Evidence: artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json, artifact:/Users/charles/.hermes/tick-20260518-040737-655543-p81154-cdaed7da-52d53fce/discussion_result.json, command:multimodel_gate PASS, command:multimodel_decision LOOP_DONE, command:multimodel_status certified, proof:sha256:7e0ffdc0228de10281675158b6002b784e760fddca024bfb66dec69a9966a426
