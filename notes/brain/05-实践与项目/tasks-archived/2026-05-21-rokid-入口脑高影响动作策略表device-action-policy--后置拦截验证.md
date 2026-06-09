---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["2"]
created: 2026-05-21T00:49:45+08:00
updated: 2026-05-21T01:36:33+08:00
expires_at: 2026-06-20T00:49:45+08:00
project: hermes
architecture_target: local-brain
capability_delta: 降低眼镜端模型幻觉执行/假完成风险，为后续 IoT/导航/消息工具接入提供可审计权限边界。
anti_drift_check: 策略表不能放宽现有确认、幂等、Commit Arbiter、read-after-write、receipt 要求；不得新增真实外部动作调用；没有后端证据时禁止声称已执行。
acceptance_evidence: 测试覆盖 send_message/calendar/navigation/control_device/take_photo/create_task 类输出拦截；模型返回“已发送/已导航/已控制”时 SSE 可见答案必须包含确认/需要证据且不包含成功宣称；现有 42+ unittest 通过。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: Rokid 眼镜端入口脑属于长期个人助理入口与安全边界演进，实施前需真实多模型审查/确认。
expected_participants: ["gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"]
truth_gate: no regression to confirmation/idempotency/evidence/Commit Arbiter/privacy boundaries; all claims backed by tests or smoke artifacts
evidence_bundle: 
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "helpful_for_rokid_glasses: from prior session/task review; priority=P1; dependency_order=2"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json
multimodel_last_checked_at: 2026-05-21T01:36:33+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-rokid-入口脑高影响动作策略表device-action-policy--后置拦截验证-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: /Users/charles/.hermes/hermes-rokid-bridge
parallel_boundary: 只做策略注册表和 guard wiring，不接入真实 Telegram/日历/导航/设备控制工具。
evidence:
  - proof:sha256:ad355b7c3daaedb926d50b0651302740f34698b052bcc7e36dc54d745ffe0386
  - command:py_compile_taskpool PASS
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json"
  - proof:sha256:8d530c248fd89ce53f3813eafc36d944d4e5cac165293ce23b517676b7bcb1f3
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json
concepts: ["rokid", "glasses", "entry-brain", "commit-arbiter", "high-impact-actions", "safety"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#110"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: ["explicit_requires_multimodel"]
---

# Task - Rokid 入口脑高影响动作策略表：DEVICE_ACTION_POLICY + 后置拦截验证

## Objective

把发消息、日程、导航、控制设备、拍照/正式任务提交等高影响动作从提示词约束提取成显式策略表，并在模型输出后用 deterministic guard 拦截“已发送/已创建/已执行”等假完成，统一返回确认草稿+证据要求。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-21T00:49:45+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T01:28:47+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T01:28:47+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T01:28:47+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:ad355b7c3daaedb926d50b0651302740f34698b052bcc7e36dc54d745ffe0386, command:py_compile_taskpool PASS

- 2026-05-21T01:28:48+08:00: Lifecycle transition `review` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T01:28:48+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T01:36:33+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T01:36:33+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json

- 2026-05-21T01:36:33+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:8d530c248fd89ce53f3813eafc36d944d4e5cac165293ce23b517676b7bcb1f3, proof:sha256:ad355b7c3daaedb926d50b0651302740f34698b052bcc7e36dc54d745ffe0386, command:py_compile_taskpool PASS, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260520-172849-099653-p32641-c778845d-7fb21201/discussion_result.json
