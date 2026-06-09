---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2 second-batch leverage: command-level token reduction and terminal pipeline efficiency"
dependency_order: ["1) repo/README mechanism extraction -> 2) compare against existing token compression and terminal pipeline -> 3) isolate command-rewrite/plugin deltas -> 4) define smallest verifiable adoption slice"]
created: 2026-05-17T19:08:51+08:00
updated: 2026-05-17T20:02:41+08:00
expires_at: 2026-06-16T19:08:51+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 ogallotti/rtk-hermes 作为 Hermes 终端命令前置改写插件的可迁移增量：在 pre_tool_call 阶段把 shell command 重写为 RTK 低上下文等价命令、以 fail-open 方式集成 token 过滤输出、用环境变量控制 runtime mode，对 Hermes 现有 token compression/result spilling/terminal policy 提出长期可维护的命令级降耗增量与主链执行顺序。
anti_drift_check: 禁止把任务写成泛泛 token 优化宣传或‘省 60%-90%’复读；必须对照 Hermes 已有 token compression/result_spiller/context management 与 token-saver 方向，明确 rtk-hermes 的净新增：pre_tool_call hook、command rewrite contract、RTK 外部规则复用、fail-open 策略、零新增工具/MCP 的轻量插件边界。必须区分哪些值得吸收到 Hermes 核心、哪些只适合作为可选插件，避免重复已有压缩层审计任务。
acceptance_evidence: repo metadata、README 关键机制证据、与 Hermes 当前 token/context/terminal pipeline 的差距图、可吸收/拒绝项、最小验证切片（如 pre_tool_call command rewrite 原型或 RTK-compatible output shaping 接口）、推荐执行顺序，以及需新增或修订的插件/脚本/文档/自检项。
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
multimodel_triage_result: "Pre-add triage: P2 evolution task for local-brain/runtime pipeline; advisory multimodel useful because overlap with existing token-optimization work is high and core-vs-plugin landing must be framed carefully, but not a current P1 blocker."
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T20:09:49+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-120241-914475-p57557-6ddc6a9c-1f0554e4/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-rtk-hermes-仓库并提炼-hermes-在-pre-tool-command-rewritertk-过滤输出与插件化-token-降耗上的可吸收增-state.json
multimodel_last_failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]
multimodel_failure_taxonomy: ["criteria_missing", "quota_unobservable", "vote_reject"]
multimodel_recommended_axes: ["quota_observability", "fallback_threshold", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['quota_unobservable'], 'fallback_threshold': ['criteria_missing'], 'framing': ['vote_reject']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先完成与既有 token/context 优化任务的对照和 Hermes 终端管线 gap map；随后可并行拆成 pre_tool_call rewrite contract、RTK/output shaping integration、plugin fail-open/runtime config 三块，再收敛为长期可维护主链方案。禁止退化成成本口号总结。
evidence:
  - proof:sha256:45590e166fd74b9c2474a907a4eb14f5fc54642d8dfa2ca5695f7e6e7c63f3d2
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:e50d454a8772e98ea089082b12c056eef4527bdc980c96be3a85a1d478875719
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:a16f95a861c14e4fd154f7fe042127d492b2c56d7a768eec5c5abc815f0707fc
concepts: ["rtk-hermes", "token-savings", "command-rewrite", "pre-tool-call", "rtk", "terminal-output-filtering", "plugin"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 rtk-hermes 仓库并提炼 Hermes 在 pre-tool command rewrite、RTK 过滤输出与插件化 token 降耗上的可吸收增量

## Objective

分析 https://github.com/ogallotti/rtk-hermes ，重点不是复述省 token 数字，而是提炼它如何在 Hermes 的 terminal 调用前做 command rewrite 与输出降噪，并评估 Hermes 是否应吸收这种插件化、fail-open、低侵入的 token 降耗模式。

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

- 2026-05-17T19:08:51+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T20:02:41+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T20:02:41+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T20:02:41+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:e50d454a8772e98ea089082b12c056eef4527bdc980c96be3a85a1d478875719, command:py_compile_taskpool PASS

- 2026-05-17T20:02:41+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:a16f95a861c14e4fd154f7fe042127d492b2c56d7a768eec5c5abc815f0707fc, proof:sha256:e50d454a8772e98ea089082b12c056eef4527bdc980c96be3a85a1d478875719, command:py_compile_taskpool PASS

- 2026-05-17T20:08:48+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-120242-064931-p57566-38c92877-3455ebd4/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}

- 2026-05-17T20:09:14+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-120241-732043-p57548-63550912-796d9783/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T20:09:49+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-120241-914475-p57557-6ddc6a9c-1f0554e4/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}
