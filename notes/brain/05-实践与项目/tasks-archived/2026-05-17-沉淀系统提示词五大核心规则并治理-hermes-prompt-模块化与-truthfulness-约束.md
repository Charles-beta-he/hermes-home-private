---
type: task
lane: evolution
layer: L3
status: done
priority: P1
created: 2026-05-17T00:13:26+08:00
updated: 2026-05-19T21:09:18+08:00
expires_at: 2026-06-16T00:13:26+08:00
project: hermes-agent
architecture_target: provider-quota
capability_delta: 将系统提示词从经验堆叠提升为可治理的操作系统：静态/动态分段提升缓存命中；模糊代码要求改为可执行规则；风险判断从硬编码升级为可逆性×影响范围框架；安全段落纳入责任人/审批治理；建立双向防说谎约束。
anti_drift_check: 禁止只写理念总结不落到 Hermes prompt builder/系统提示词结构/治理流程；禁止把用户特有动态信息继续混入静态前缀；禁止只要求测试失败直说而放任把成功说成失败；禁止把高风险规则写成无人维护的孤儿段落。
acceptance_evidence: 产出可执行的五规则映射：1) 静态段/动态段分层规范与 Hermes 落点；2) 可执行代码指令样例库；3) 可逆性×影响范围风险判定准则；4) 安全关键段责任人与审批机制；5) 双向防说谎 wording 与验证方式；并给出需要修改的 prompt builder/文档/自检清单。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T00:49:51+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-164812-754872-p92772-3cbe5b7a-0e8a5aa7/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-沉淀系统提示词五大核心规则并治理-hermes-prompt-模块化与-truthfulness-约束-state.json
multimodel_last_failures: ["best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:gpt-5.5:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]
multimodel_failure_taxonomy: ["criteria_missing", "provider_parse_error", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "patch_normalization", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'patch_normalization': ['provider_parse_error'], 'framing': ['vote_reject', 'provider_parse_error']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先完成规则抽象与段落分层规范，再评估提示词治理落点；测试口径与审批流程设计可并行，但正式改造需在统一规范后进行。
evidence:
  - proof:sha256:f37eda2f88f396991aae8d5bcf4dce2395494d1219985b905540fa4619d0e017
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:7932f3da1c2b45a178d8212bd0c49a00d1a15a2a515959e29e7d3f00a6fa4af7
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:6379a42f6725d14b187b62bb91e9c0b8ac4610b938e78aec0573a547a1e4f777
  - proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json
  - proof:sha256:e00a7cc1cf7a21fe086f73f26dd2b31b186f5f214a64abe56c76a6725dab2105
  - proof:sha256:fab10aac11bc0f08289d54e1313c8a0f23e9f1bddb731c803835a8e1ef6ddb52
concepts: ["system-prompt", "prompt-governance", "cache-segmentation", "risk-framework", "safety", "truthfulness"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 沉淀系统提示词五大核心规则并治理 Hermes prompt 模块化与 truthfulness 约束

## Objective

把“系统提示词的五大核心规则”沉淀为 Hermes 自身可执行的提示词治理任务：围绕静态段与动态段分离、代码指令具体化、行动风险双维度评估、安全指令专人维护、双向防说谎机制五条原则，梳理当前 Hermes system prompt / persona / skills / 动态上下文注入链路的落点，形成模块化改造方案与验证清单，确保每条规则都能映射到真实生产问题、缓存命中、风险治理和 truthfulness 约束，而不是停留在抽象宣言。

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

- 2026-05-17T00:13:26+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T00:48:12+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T00:48:12+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T00:48:12+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:7932f3da1c2b45a178d8212bd0c49a00d1a15a2a515959e29e7d3f00a6fa4af7, command:py_compile_taskpool PASS

- 2026-05-17T00:48:12+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:6379a42f6725d14b187b62bb91e9c0b8ac4610b938e78aec0573a547a1e4f777, proof:sha256:7932f3da1c2b45a178d8212bd0c49a00d1a15a2a515959e29e7d3f00a6fa4af7, command:py_compile_taskpool PASS

- 2026-05-17T00:49:11+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-164812-575652-p92763-295ecf98-7f93444f/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T00:49:49+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-164812-890658-p92781-833cac04-6db8a42a/discussion_result.json`. Failures: ["best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:gpt-5.5:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}

- 2026-05-17T00:49:51+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-164812-754872-p92772-3cbe5b7a-0e8a5aa7/discussion_result.json`. Failures: ["best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:gpt-5.5:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}

- 2026-05-19T11:11:14+08:00: Lifecycle transition `done` -> `pending` by `hermes-closeout-audit`. Force: true. Reason: new closeout rule audit: done evidence is py_compile/hash/multimodel-only or lacks task-type-specific real-chain acceptance; reopening for honest completion Evidence: proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json

- 2026-05-19T20:50:48+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T20:50:49+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T20:50:49+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:e00a7cc1cf7a21fe086f73f26dd2b31b186f5f214a64abe56c76a6725dab2105, command:py_compile_taskpool PASS

- 2026-05-19T21:09:18+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:fab10aac11bc0f08289d54e1313c8a0f23e9f1bddb731c803835a8e1ef6ddb52, proof:sha256:f37eda2f88f396991aae8d5bcf4dce2395494d1219985b905540fa4619d0e017, classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task, classification:legacy_autorun_proof_hash=sha256:7932f3da1c2b45a178d8212bd0c49a00d1a15a2a515959e29e7d3f00a6fa4af7, command:py_compile_taskpool PASS, classification:legacy_autorun_proof_hash=sha256:6379a42f6725d14b187b62bb91e9c0b8ac4610b938e78aec0573a547a1e4f777, proof:manual_done_closeout_audit_2026-05-19; file:/tmp/taskpool_done_closeout_audit.json, proof:sha256:e00a7cc1cf7a21fe086f73f26dd2b31b186f5f214a64abe56c76a6725dab2105
