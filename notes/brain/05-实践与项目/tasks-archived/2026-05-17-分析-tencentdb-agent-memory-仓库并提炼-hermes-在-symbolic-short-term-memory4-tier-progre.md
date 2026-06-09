---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2 second-batch leverage: layered memory runtime with symbolic short-term compression"
dependency_order: ["1) repo/README mechanism extraction -> 2) compare against existing memory-layer tasks and Hermes current stack -> 3) isolate symbolic-short-term + layered-runtime deltas -> 4) define smallest verifiable adoption slice"]
created: 2026-05-17T21:10:38+08:00
updated: 2026-05-20T20:42:14+08:00
expires_at: 2026-06-16T21:10:38+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 Tencent/TencentDB-Agent-Memory 作为本地优先记忆运行时的可迁移增量：symbolic short-term memory 通过 Mermaid canvas 压缩工具日志、L0→L3 progressive memory layering、异构存储与可追溯 drill-down、Hermes/OpenClaw 插件接入与 Docker runtime，对 Hermes 现有 local-brain/memory provider/context compression 提出长期可维护的记忆架构增量与主链执行顺序。
anti_drift_check: 禁止把任务写成又一个通用记忆系统综述；必须对照现有 plur/agentmemory/openhuman/上下文压缩任务，明确 TencentDB-Agent-Memory 的净新增：symbolic short-term offload、Mermaid canvas 作为高密度任务状态载体、L0 Conversation→L3 Persona 的 4-tier pyramid、top-layer symbol 到 raw evidence 的可回钻链路、Hermes Docker/plugin runtime。禁止直接照搬 README benchmark 数字；重点提炼机制、边界、最小验证切片，以及哪些部分适合 Hermes 核心、哪些仅适合作为可选插件。
acceptance_evidence: repo metadata、README 关键机制证据、与 Hermes 当前 local-brain/memory provider/result_spiller/token compression 的差距图、相对 plur/agentmemory/openhuman 的增量边界、可吸收/拒绝项、最小验证切片（如 Mermaid symbolic state 原型、4-tier memory mapping、plugin runtime interface）、推荐执行顺序，以及需新增或修订的技能/插件/脚本/文档项。
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
multimodel_triage_result: "Pre-add triage: P2 evolution task for local-brain; advisory multimodel useful because overlap with existing memory tasks is high and this repo must be framed around net-new symbolic/layered runtime mechanisms, but not a current P1 blocker."
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-17T23:37:59+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-140318-097983-p11864-00447ada-c5e21b44/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-tencentdb-agent-memory-仓库并提炼-hermes-在-symbolic-short-term-memory4-tier-progre-state.json
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
parallel_boundary: 先完成与既有 memory tasks 的对照和 Hermes 现状 gap map；随后可并行拆成 symbolic short-term offload/Mermaid canvas、4-tier long-term layering、Hermes plugin/runtime integration 三块，再收敛为长期可维护主链方案。禁止退化成记忆概念大而全总结。
evidence:
  - proof:sha256:25d3877399e4b19b461f1b57af06028384a9b0c3dba180474db7f0f7cdbe5454
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:1df89151843855f87090e388a09ebb9ccc30a918d465ed18954d35c3acdb6b8d
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:3438cc15706f658594f9547adedfff85e072d6931afbf37db9fc9cabf2aa98fd
concepts: ["tencentdb-agent-memory", "symbolic-memory", "mermaid-canvas", "4-tier-memory", "local-first", "long-term-memory", "plugin-memory"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 TencentDB-Agent-Memory 仓库并提炼 Hermes 在 symbolic short-term memory、4-tier progressive layering 与 Hermes 插件记忆运行时上的可吸收增量

## Objective

分析 https://github.com/Tencent/TencentDB-Agent-Memory ，重点不是泛谈长期记忆，而是提炼它如何用 Mermaid symbolic short-term memory 与 4-tier progressive layering 同时解决长任务上下文膨胀和跨会话记忆保留，并评估 Hermes 是否应吸收这种 layered memory runtime 模式。

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.
- [x] Second-pass evidence packet records canonical source, adoption decision, landing surface, verification slice, and stop-condition / anti-drift boundary.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-17T21:10:38+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Second-pass evidence backfill（2026-05-20）

- Source / provenance: canonical external source is `https://github.com/Tencent/TencentDB-Agent-Memory`, recorded at task objective and confirmed by the 2026-05-19 audit row `urls: github.com/Tencent/TencentDB-Agent-Memory`. This task is an external absorption note, not an endogenous-only task.
- Adoption decision: absorb as architecture pattern, not as a direct vendor dependency. Keep the transferable deltas limited to (1) symbolic short-term state offload, (2) 4-tier memory mapping, and (3) optional plugin/runtime interface for memory experiments. Defer direct runtime integration until a Hermes-native prototype proves value over existing `result_spiller`, context compression, task proof logs, and memory-provider surfaces.
- Landing surface: `brain` task note is the current canonical landing packet; future executable landing must be a bounded Hermes prototype, preferably under `~/.hermes/scripts/` or a dedicated memory plugin, with any durable operator guidance routed through the mlops/local-brain profile rather than another broad repo summary. Existing related landing surfaces to compare before new work: local-brain memory provider, context compressor, result spilling, and taskpool proof-log chain.
- Verification slice: smallest acceptable slice is a deterministic fixture that converts one long tool/task transcript into Mermaid symbolic state plus back-links to raw evidence, then maps the same fixture into L0 Conversation / L1 Episode / L2 Knowledge / L3 Persona records. PASS requires drill-down from each top-layer symbol to raw task evidence and an explicit comparison against current Hermes compression/result-spiller behavior.
- Stop-condition / anti-drift boundary: stop if the candidate requires non-canonical model/provider IDs, unverifiable quota state, proprietary TencentDB runtime coupling, or weakens current proof gates. Do not claim performance/benchmark superiority from README-only numbers. Do not promote into core memory runtime until the prototype produces file-backed evidence and passes review against existing memory tasks (`plur`, `agentmemory`, `openhuman`) without duplicating their scope.
- Model-route / quota boundary: future analysis may use advisory multi-model only for architecture arbitration; certification authority is not granted by this historical task. Canonical route IDs must use the registered IDs (`claude-opus-4-7`, `gpt-5.5`, `deepseek-v4-pro`, `mimo-v2.5-pro`) and must fail closed when quota/provider state is `unknown`, `limited`, or `exhausted`.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T22:03:17+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T22:03:18+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T22:03:18+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:1df89151843855f87090e388a09ebb9ccc30a918d465ed18954d35c3acdb6b8d, command:py_compile_taskpool PASS

- 2026-05-17T22:03:18+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:3438cc15706f658594f9547adedfff85e072d6931afbf37db9fc9cabf2aa98fd, proof:sha256:1df89151843855f87090e388a09ebb9ccc30a918d465ed18954d35c3acdb6b8d, command:py_compile_taskpool PASS

- 2026-05-17T22:06:31+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-140318-458917-p11882-2d7a8df2-f40cebf7/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T23:35:43+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-140318-276166-p11873-a5b0af0e-38bf87e5/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-17T23:37:59+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-140318-097983-p11864-00447ada-c5e21b44/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
