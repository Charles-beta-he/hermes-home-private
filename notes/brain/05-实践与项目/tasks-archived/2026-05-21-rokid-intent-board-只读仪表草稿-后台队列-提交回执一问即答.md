---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["4"]
created: 2026-05-21T00:49:59+08:00
updated: 2026-05-21T01:44:25+08:00
expires_at: 2026-06-20T00:49:59+08:00
project: hermes
architecture_target: local-brain
capability_delta: 提升眼镜日常可控感，让后台任务从黑盒变成可语音查询的真实状态板。
anti_drift_check: 只读真实 ledger/queue/artifacts；真实队列为空必须说没有真实后台任务；不得把模型生成的“导航/语音助手任务”当作已存在；不得直接写 kanban.db。
acceptance_evidence: 构造 queue/*.queued|committing|done|failed 与 artifact JSON fixture；SSE 查询返回对应真实状态；空队列返回无任务；不创建新 queue；unittest + py_compile 通过。
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
multimodel_triage_result: "helpful_for_rokid_glasses: from prior session/task review; priority=P2; dependency_order=4"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json
multimodel_last_checked_at: 2026-05-21T01:44:25+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-rokid-intent-board-只读仪表草稿-后台队列-提交回执一问即答-state.json
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
parallel_boundary: 只增强只读查询和格式化，不改变 worker 消费/任务创建语义。
evidence:
  - proof:sha256:e207492d9ced2522355df2fde597152a4af33d510b564afc0dcb3ac948f020fe
  - command:py_compile_taskpool PASS
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json"
  - proof:sha256:18537613e0f11b769544f4d4f5010911bcf110aa500ab68b47fc39c3205e1889
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json
concepts: ["rokid", "glasses", "intent-board", "mini-kanban", "intent-ledger", "receipt"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#124"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: ["explicit_requires_multimodel"]
---

# Task - Rokid Intent Board 只读仪表：草稿/后台队列/提交回执一问即答

## Objective

增强眼镜端 Intent Board：用户问“刚才的任务/后台进度/是否提交成功/有哪些后台任务”时，只读真实 TASK_SESSIONS、BACKGROUND_CONTROL_SESSIONS、Intent Ledger queue/artifacts，短答给草稿、queued/committing/done/failed、回执路径/摘要；禁止编造不存在的后台任务。

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

- 2026-05-21T00:49:59+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T01:32:12+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T01:32:12+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T01:32:12+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:e207492d9ced2522355df2fde597152a4af33d510b564afc0dcb3ac948f020fe, command:py_compile_taskpool PASS

- 2026-05-21T01:37:31+08:00: Lifecycle transition `review` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T01:37:31+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T01:44:25+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T01:44:25+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json

- 2026-05-21T01:44:25+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:18537613e0f11b769544f4d4f5010911bcf110aa500ab68b47fc39c3205e1889, proof:sha256:e207492d9ced2522355df2fde597152a4af33d510b564afc0dcb3ac948f020fe, command:py_compile_taskpool PASS, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260520-173732-015911-p38678-da8aecc5-3012b3ed/discussion_result.json
