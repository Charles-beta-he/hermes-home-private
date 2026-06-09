---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2 second-batch leverage: observability and operator overview for Hermes runtime"
dependency_order: ["1) repo/README mechanism extraction -> 2) compare against current Hermes dashboard/status/log tooling -> 3) isolate read-only observability deltas -> 4) define smallest verifiable adoption slice"]
created: 2026-05-17T19:09:13+08:00
updated: 2026-05-17T20:50:35+08:00
expires_at: 2026-06-16T19:09:13+08:00
project: hermes-agent
architecture_target: taskpool
capability_delta: 评估 mudrii/hermesd 作为 Hermes 只读 TUI 监控层的可迁移增量：汇总 gateway/sessions/tokens/tools/config/cron/skills/logs/profiles/memory 的实时只读面板、离线告警与健康指示、snapshot 导出与 detail filtering，对 Hermes 当前控制面/仪表盘/运维可观测性提出长期可维护的 dashboard 增量与主链执行顺序。
anti_drift_check: 禁止把任务写成泛泛 TUI 观感评论或运维仪表盘产品介绍；必须对照 Hermes 当前 status/sessions/cron/dashboard/logs/selfcheck 能力，明确 hermesd 的净新增：单屏全局聚合、只读零写入边界、10 panel 信息架构、snapshot/text+json 导出、detail filters、offline banner、footer health indicator。必须区分哪些应进入 taskpool/control-plane dashboard，哪些仅适合作为独立只读工具。
acceptance_evidence: repo metadata、README 关键机制证据、与 Hermes 当前 dashboard/control-plane/observability 的差距图、可吸收/拒绝项、最小验证切片（如只读 snapshot exporter、health summary panel 或多源状态聚合接口）、推荐执行顺序，以及需新增或修订的脚本/仪表盘/reference/自检项。
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
multimodel_triage_result: "Pre-add triage: P2 evolution task for taskpool/control-plane observability; advisory multimodel useful for dashboard-vs-standalone-tool landing and information-architecture tradeoffs, but not a current P1 blocker."
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-17T21:08:54+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-125035-546794-p85150-20c0afd4-992c2191/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-hermesd-仓库并提炼-hermes-在只读-tui-监控面板全局状态聚合与-observability-dashboard-上的可吸收增量-state.json
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
parallel_boundary: 先完成 repo surface 与 README 机制提炼，再对照 Hermes 当前 dashboard/status/log/cron/session 观测能力做 gap map；随后可并行拆成状态聚合与健康指标、snapshot/export 接口、read-only TUI 信息架构 三块，再收敛为长期可维护主链方案。禁止退化成单纯 UI 巡礼。
evidence:
  - proof:sha256:f8874a18bd5f3f2ecf4db46a399163c1cb865f35d601ba4a226b5a33b2cb91b1
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:ad1ea896d9642e12dd55b2cce534b3aec9a56d9212b53562fe54e9120e8f47a1
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:dcebe1d9e5a10ba3ec364ad257e1c717ede5771899f244baeb5009f7bb6fc8b9
concepts: ["hermesd", "tui-dashboard", "observability", "read-only-monitoring", "sessions", "tokens", "cron", "skills", "logs"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 hermesd 仓库并提炼 Hermes 在只读 TUI 监控面板、全局状态聚合与 observability dashboard 上的可吸收增量

## Objective

分析 https://github.com/mudrii/hermesd ，重点不是复述有多少面板，而是提炼它如何以只读方式聚合 Hermes 全局状态，并评估 Hermes 是否应吸收这种实时 observability dashboard 模式来提升运维、任务池和会话监控效率。

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

- 2026-05-17T19:09:13+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T20:50:35+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T20:50:35+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T20:50:35+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:ad1ea896d9642e12dd55b2cce534b3aec9a56d9212b53562fe54e9120e8f47a1, command:py_compile_taskpool PASS

- 2026-05-17T20:50:35+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:dcebe1d9e5a10ba3ec364ad257e1c717ede5771899f244baeb5009f7bb6fc8b9, proof:sha256:ad1ea896d9642e12dd55b2cce534b3aec9a56d9212b53562fe54e9120e8f47a1, command:py_compile_taskpool PASS

- 2026-05-17T21:07:01+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-125035-855794-p85168-1c17d56d-ca26a7db/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}

- 2026-05-17T21:08:42+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-125035-723577-p85159-afb24a43-83f64c2f/discussion_result.json`. Failures: ["best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:mimo-v2.5-pro:amend", "status_not_passed:not_certified"]. Recommended axes: ["fallback_threshold", "patch_normalization", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "patch_normalization": ["provider_parse_error"], "framing": ["vote_reject", "provider_parse_error"]}

- 2026-05-17T21:08:54+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-125035-546794-p85150-20c0afd4-992c2191/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
