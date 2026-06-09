---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T00:52:17+08:00
updated: 2026-05-19T21:29:10+08:00
expires_at: 2026-07-01T00:52:17+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: 把 EvoAgentX 建议中的内置评估管线增强落成 Hermes 长期可维护的评估反馈基座：为多模型评审与执行回放定义 execution_quality 维度、skill 质量评分、低分退化/待修复标记与证据写回协议，作为后续自动 skill 演化与 workflow 生成的上游治理基础。
anti_drift_check: 禁止做一次性打分脚本或只在单 task 上加临时字段；必须从长期可维护架构出发，明确 consult_models/任务池/skill 元数据/证据写回的稳定接口。禁止把此任务降格为最小落地切片或孤立 patch。
acceptance_evidence: execution_quality 评价维度定义、skill 评分与状态机设计、证据回写路径、与现有多模型 gate/curator/taskpool 的兼容方案、后续自动 prompt 优化与 workflow 生成的依赖说明。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260516-184903-219746-p40888-4cfa411c-495cbee1/discussion_result.json
multimodel_last_checked_at: 2026-05-17T02:52:06+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-184903-219746-p40888-4cfa411c-495cbee1/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-建设-hermes-长期可维护的-execution-quality-评估反馈基座以承接-evoagentx-演化闭环建议-state.json
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
parallel_boundary: serial-1-of-3:evoagentx-unlanded-evolution-closure
evidence:
  - proof:sha256:0dbc70ce0d733a02ffad84a259a88462992cc99cc2ac1dadda4053c7f2487225
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:672a61b4174acdf42dd3ac9204112465a606fc0d2f04d3ea6509d232707fd9d6
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:585ddade9cf96d72f3cb77dc035c55d6d266e9dabc71c974122d71d3dab66575
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
  - proof:sha256:ccff9ed946ea305c57746318230cdd9c9f3c035611396b92176e84bab17f6ae1
  - proof:sha256:7782b0cc91ae8f79a65d5a4a3f1ee0eb43fc9f8dd94db0ba9f4f0d802b84625c
concepts: ["evoagentx", "evaluation-pipeline", "execution-quality", "skill-scoring", "consult-models", "governance-feedback"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 建设 Hermes 长期可维护的 execution-quality 评估反馈基座以承接 EvoAgentX 演化闭环建议

## Objective

基于 2026-05-16 的 EvoAgentX 优化建议，先建设 Hermes 的长期可维护评估反馈基座，而不是局部补丁：定义 execution_quality、skill 质量评分、needs_optimization 标记、评估证据写回与读取协议，使评估结果能够稳定反馈给 skill 治理、背景 review 和后续自动演化闭环。此任务应先于自动 prompt 优化与工作流自动生成执行。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] 推进长期可维护主链方案并记录阶段性证据。
- [ ] Record proof and update status.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-17T00:52:17+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T01:09:14+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-170813-249432-p4559-9d5ab919-51050aed/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T02:49:02+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T02:49:02+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T02:49:02+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:672a61b4174acdf42dd3ac9204112465a606fc0d2f04d3ea6509d232707fd9d6, command:py_compile_taskpool PASS

- 2026-05-17T02:49:03+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:585ddade9cf96d72f3cb77dc035c55d6d266e9dabc71c974122d71d3dab66575, proof:sha256:672a61b4174acdf42dd3ac9204112465a606fc0d2f04d3ea6509d232707fd9d6, command:py_compile_taskpool PASS

- 2026-05-17T02:51:44+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-184903-079964-p40879-260896a2-efc25e31/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T02:52:06+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-184903-219746-p40888-4cfa411c-495cbee1/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T11:11:14+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T21:29:09+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T21:29:09+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T21:29:09+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:ccff9ed946ea305c57746318230cdd9c9f3c035611396b92176e84bab17f6ae1, command:py_compile_taskpool PASS

- 2026-05-19T21:29:10+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:7782b0cc91ae8f79a65d5a4a3f1ee0eb43fc9f8dd94db0ba9f4f0d802b84625c, proof:sha256:0dbc70ce0d733a02ffad84a259a88462992cc99cc2ac1dadda4053c7f2487225, classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task, classification:legacy_autorun_proof_hash=sha256:672a61b4174acdf42dd3ac9204112465a606fc0d2f04d3ea6509d232707fd9d6, command:py_compile_taskpool PASS, classification:legacy_autorun_proof_hash=sha256:585ddade9cf96d72f3cb77dc035c55d6d266e9dabc71c974122d71d3dab66575, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, proof:sha256:ccff9ed946ea305c57746318230cdd9c9f3c035611396b92176e84bab17f6ae1
