---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2 second-batch leverage: shared memory substrate for multi-agent/multi-tool recall"
dependency_order: ["1) repo/README mechanism extraction -> 2) compare against existing memory tasks and current Hermes memory stack -> 3) isolate net-new engram/shared-memory deltas -> 4) define smallest verifiable adoption slice"]
created: 2026-05-17T19:08:28+08:00
updated: 2026-05-17T19:31:57+08:00
expires_at: 2026-06-16T19:08:28+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 plur-ai/plur 作为本地优先共享记忆层的可迁移增量：Open Engram YAML 存储、跨会话/跨工具/跨机器共享记忆、作用域与极性建模、自动注入与学习提取、Hermes 插件接入，对 Hermes 现有 MEMORY/USER/session_search/local-brain/memory provider 提出长期可维护的 shared-memory 增量与主链执行顺序。
anti_drift_check: 禁止把任务写成‘再研究一个记忆系统’的宽泛综述；必须对照已有 gbrain/agentmemory/openhuman/上下文压缩任务，明确 plur 的净新增：Engram typed assertions、scope/polarity、跨实例共享、Hermes/Claude Code/OpenClaw 多工具统一记忆、MCP + plugin 自动注入。禁止直接照搬 README benchmark 结论；重点提炼机制、边界、最小验证切片，以及哪些部分与 Hermes 现有记忆层重复或不该吸收。
acceptance_evidence: repo metadata、README 关键机制证据、与 Hermes 当前 local-brain/memory provider/session_search/MEMORY-USER 的差距图、可吸收/拒绝项、最小验证切片（如 engram schema 映射、scope/polarity 注入门、共享存储原型）、推荐执行顺序，以及需新增或修订的技能/插件/脚本/文档项。
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
multimodel_triage_result: "Pre-add triage: P2 evolution task for local-brain; advisory multimodel useful because memory-layer overlap with existing tasks is high and needs explicit delta framing, but not a current P1 blocker."
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-17T19:40:46+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-113157-736129-p44474-9f6da26c-54309c81/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-plur-仓库并提炼-hermes-在共享-engram-记忆层跨实例注入与-local-first-mcp-记忆上的可吸收增量-state.json
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
parallel_boundary: 先完成与既有 memory tasks 的对照和 Hermes 现状 gap map；随后可并行拆成 engram schema/scope-polarity、跨实例共享与注入机制、Hermes plugin/MCP 接口三块，再收敛为长期可维护主链方案。禁止退化成通用长期记忆概念整理。
evidence:
  - proof:sha256:1aaea4bee0daac2d6fc8818920936cff373b97a3c568ad1e88b7555cb3cf6ceb
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:e77016974af2e6d7a488d5f5f42a853482f0934f4d8b23ad92db174720f6f6fd
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:5f61e0a3521992e1750fbac13e33fe94274f5800579c181a3154f3bd635c73fe
concepts: ["plur", "shared-memory", "engram", "mcp-memory", "local-first", "yaml-memory", "cross-instance-memory"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 plur 仓库并提炼 Hermes 在共享 Engram 记忆层、跨实例注入与 local-first MCP 记忆上的可吸收增量

## Objective

分析 https://github.com/plur-ai/plur ，重点不是泛谈 agent 记忆，而是提炼它如何用 local-first YAML engrams 构建跨实例共享记忆层，并评估 Hermes 是否应吸收这种 shared-memory + auto-injection 模式来提升多 agent / 多工具协作一致性。

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

- 2026-05-17T19:08:28+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T19:31:57+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T19:31:57+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T19:31:57+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:e77016974af2e6d7a488d5f5f42a853482f0934f4d8b23ad92db174720f6f6fd, command:py_compile_taskpool PASS

- 2026-05-17T19:31:57+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:5f61e0a3521992e1750fbac13e33fe94274f5800579c181a3154f3bd635c73fe, proof:sha256:e77016974af2e6d7a488d5f5f42a853482f0934f4d8b23ad92db174720f6f6fd, command:py_compile_taskpool PASS

- 2026-05-17T19:38:00+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-113157-953715-p44484-c81fe4cd-6411253a/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}

- 2026-05-17T19:40:17+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-113158-125389-p44491-33ebeef3-d45e16d4/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}

- 2026-05-17T19:40:46+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-113157-736129-p44474-9f6da26c-54309c81/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
