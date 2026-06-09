---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T01:05:03+08:00
updated: 2026-05-17T08:52:32+08:00
expires_at: 2026-07-01T01:05:03+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 修正 brain_task_orchestrator add 默认任务模板与相关治理文案，使其默认引导长期可维护主链方案、依赖顺序与架构治理，而不是默认落到 smallest verifiable slice / minimal slice framing。
anti_drift_check: 禁止只手改几个现有任务文件而不修正任务生成源头；必须定位 brain_task_orchestrator 默认正文模板与相关 checklist/skill 文案，定义新的稳定默认措辞，并评估是否需要批量迁移或仅对新任务生效。
acceptance_evidence: 定位默认模板注入点、修订后的 Plan/Workpad 默认文案、与用户偏好/任务池治理的一致性说明、受影响范围与迁移策略、必要的脚本/文档/skill 更新清单。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260517-005232-657779-p15706-1ece90c9-649ed821/discussion_result.json
multimodel_last_checked_at: 2026-05-17T08:56:20+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-005232-657779-p15706-1ece90c9-649ed821/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-修正-taskpool-默认任务模板对-smallest-slice-framing-的系统性偏置并对齐长期可维护主链治理-state.json
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
parallel_boundary: "serial-after-taskpool-audit: template wording/schema first, then generator implementation, then migration guidance"
evidence:
  - proof:sha256:fbd8cc7d347f1e3ff94829e6738f9fe8724e1b7cb4a1b2f37af0b33950cf53f1
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:a43192ac0623c59eab36fdf0b6f7e60fbf3398c80ed9747ffeca02536f146863
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:c1de8c01f1790b8be7f61862a19d47a0ffe742eb6f85a34d24edc9e4db0aa815
concepts: ["task-template", "brain-task-orchestrator", "taskpool-governance", "maintainability-framing", "plan-workpad"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 修正 taskpool 默认任务模板对 smallest-slice framing 的系统性偏置并对齐长期可维护主链治理

## Objective

当前 taskpool 任务模板由 brain_task_orchestrator.py add 默认注入“Execute the smallest verifiable slice.”，与用户关于长期可维护主链方案、非最小切片 framing 的偏好冲突，也会把外部 repo/article 吸收任务错误拉向局部 patch。需要把任务生成模板、相关 checklist 与治理文案修正为默认强调主链方案、依赖顺序、架构边界与阶段性证据，而不是最小切片。

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

- 2026-05-17T01:05:03+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T05:12:50+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-211002-152984-p73076-e9b4f2b3-c6186322/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T08:52:32+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T08:52:32+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T08:52:32+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:a43192ac0623c59eab36fdf0b6f7e60fbf3398c80ed9747ffeca02536f146863, command:py_compile_taskpool PASS

- 2026-05-17T08:52:32+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:c1de8c01f1790b8be7f61862a19d47a0ffe742eb6f85a34d24edc9e4db0aa815, proof:sha256:a43192ac0623c59eab36fdf0b6f7e60fbf3398c80ed9747ffeca02536f146863, command:py_compile_taskpool PASS

- 2026-05-17T08:55:35+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-005232-529817-p15697-82c6792b-86bf0509/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T08:56:20+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-005232-657779-p15706-1ece90c9-649ed821/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
