---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["depends on retrieval bridge and consolidation design -> 1 define selfcheck probes -> 2 implement default-off checks -> 3 verify healthy/unavailable/misconfigured outputs -> 4 integrate post-update or control-plane evidence"]
created: 2026-05-21T20:38:37+08:00
updated: 2026-05-21T22:17:06+08:00
expires_at: 2026-06-20T20:38:37+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 把 AgentMemory 的 privacy/audit/retention/index-health 思路纳入 Hermes 自检：检测 server reachability、localhost/auth/HTTPS、data dir size、retention policy、vector/BM25/index 健康与共享记忆风险。
anti_drift_check: 不得把 README benchmark 数字当健康证据；自检必须区分 optional integration 未启用、启用但健康、启用但降级/危险；默认未启用不能报错。
acceptance_evidence: selfcheck 规则或脚本设计、启用/未启用/不健康三态样例、auth/storage/retention/index 检查输出、proof-check/selfcheck 通过。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P2: AgentMemory source-backed Hermes memory evolution task; high leverage but must remain default-off and evidence-gated before runtime adoption"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-21T20:42:35+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-123845-063807-p25345-0e0796ac-8df3f064/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-add-agentmemory-governance-selfcheck-for-server-auth-storage-retention-and-index-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 按依赖顺序推进：compatibility spike -> policy wrapper -> retrieval bridge/consolidation -> governance selfcheck；禁止未验证前改默认配置或启用外部 shared memory。
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123845-063807-p25345-0e0796ac-8df3f064/discussion_result.json"
  - "command: brain_task_orchestrator transition --to pending after add-time advisory auto-close"
  - proof:sha256:07be6744c6fb9d50b087ebec37349fad42ecce8ab77680fc578bb6276294639a
  - command:py_compile_taskpool PASS
  - proof:sha256:96cbbcac1d4047a4ca98600840b1bb16cee3cfb7eefc337f635f1b3ebf7ed3ca
concepts: ["agentmemory", "selfcheck", "governance", "privacy", "storage", "auth", "retention"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#267"
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane"]
multimodel_certification_reasons: []
manual_review_decided_at: "2026-05-27T16:20:00+08:00"
manual_review_decided_by: "user-approved-multimodel-review"
manual_review_classification: "PARTIAL_STAGE"
manual_review_approval_action: "needs_more_evidence"
manual_review_final_landed: false
manual_review_result_ref: "/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md"
manual_review_reason: "需补 selfcheck 脚本、三态输出、proof-check；暂不按最终完成处理。"
---

# Task - Add AgentMemory governance selfcheck for server auth storage retention and index health

## Objective

把 AgentMemory 源码分析中的 governance/selfcheck 可吸收能力转成 Hermes 可执行进化任务，保持默认关闭、安全优先、证据驱动。

## Acceptance Criteria

- [ ] selfcheck 规则或脚本设计、启用/未启用/不健康三态样例、auth/storage/retention/index 检查输出、proof-check/selfcheck 通过。

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-27T16:20:00+08:00: User approved multimodel manual-review classification PARTIAL_STAGE; action=needs_more_evidence; final_landed=false; ref=/Users/charles/.hermes/docs/private/manual-review-multimodel-result-20260527.md; reason=需补 selfcheck 脚本、三态输出、proof-check；暂不按最终完成处理。

- 2026-05-21T20:38:37+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T20:38:44+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T20:38:44+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T20:42:35+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260521-123845-063807-p25345-0e0796ac-8df3f064/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T20:42:35+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123845-063807-p25345-0e0796ac-8df3f064/discussion_result.json

- 2026-05-21T20:44:08+08:00: Lifecycle transition `review` -> `pending` by `hermes-agent`. Force: true. Reason: User asked to add AgentMemory evolution improvements to taskpool; queued work items are not completed implementation. Evidence: command: brain_task_orchestrator transition --to pending after add-time advisory auto-close

- 2026-05-21T22:17:06+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T22:17:06+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T22:17:06+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:07be6744c6fb9d50b087ebec37349fad42ecce8ab77680fc578bb6276294639a, command:py_compile_taskpool PASS

- 2026-05-21T22:17:06+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:96cbbcac1d4047a4ca98600840b1bb16cee3cfb7eefc337f635f1b3ebf7ed3ca, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260521-123845-063807-p25345-0e0796ac-8df3f064/discussion_result.json, command: brain_task_orchestrator transition --to pending after add-time advisory auto-close, proof:sha256:07be6744c6fb9d50b087ebec37349fad42ecce8ab77680fc578bb6276294639a, command:py_compile_taskpool PASS
