---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2 second-batch leverage: open prompt/skill asset registry with MCP/plugin/self-host distribution, valuable for Hermes prompt-surface governance but not an immediate P1 blocker"
dependency_order: ["1) repo/README mechanism extraction -> 2) compare against Hermes current system-prompt/skills/prompt-governance surfaces -> 3) isolate prompt-registry and cross-tool distribution deltas vs existing prompt tasks -> 4) define long-term maintainable adoption boundary and execution order"]
created: 2026-05-18T01:20:00+08:00
updated: 2026-05-18T01:22:39+08:00
expires_at: 2026-06-17T01:20:00+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: 评估 f/prompts.chat 作为开放 prompt 资产注册表的可迁移增量：社区维护的 prompt library、PROMPTS.md/CSV/HuggingFace dataset 多格式导出、Claude Code plugin 与 MCP server 双分发、自托管私有 prompt library、以及品牌/鉴权/主题配置，对 Hermes 现有 system prompt 治理、skills、prompt 模板沉淀与跨工具分发提出长期可维护的 prompt-asset/skill-graph 架构增量与主链执行顺序。
anti_drift_check: 禁止把任务写成“收集一些好 prompt”或 prompt engineering 入门综述；必须对照 Hermes 现有 system prompt 治理、skills、meta-meta-prompting、Claude Code/Codex 插件任务，明确 prompts.chat 的净新增：prompt 资产库与版本化导出、多格式同步、Claude Code plugin + MCP server 的跨工具分发、自托管私有 prompt library 与鉴权/品牌化。必须区分哪些应进入 Hermes 的 skill-graph/prompt registry，哪些仅适合作为外部参考库，哪些不应吸收进核心。
acceptance_evidence: repo metadata、README/目录结构关键机制证据、与 Hermes 当前 system prompt/skills/skill files/MCP/plugin surfaces 的差距图、可吸收/拒绝项、长期可维护主链方案与执行顺序、以及需新增或修订的 skill/plugin/script/doc/self-check 项。
workflow_contract: "[08-模板/task-workflow-contract-template]"
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
multimodel_triage_result: "Pre-add triage: P2 evolution task for skill-graph/prompt-governance. Same mechanism class as existing prompt-governance and skill tasks, so external multimodel advisory is useful to avoid turning this into a generic prompt-library survey and to decide whether the main delta belongs in prompt registry, MCP distribution, or optional self-host packaging; not a current P1 blocker."
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-18T01:35:12+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-172238-857850-p60666-e99fc84b-f9cea469/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-分析-promptschat-仓库并提炼-hermes-在开放-prompt-资产注册表mcp-claude-code-插件分发与自托管私有-prompt-li-state.json
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
parallel_boundary: "Serial first: evidence extraction and Hermes current-state contrast must happen before any proposal for prompt registry or plugin/MCP packaging; optional self-host or export-format prototypes can branch only after the architecture boundary is fixed."
evidence:
  - proof:sha256:82dd3fa4c332f1ee078c60908128e9393f1939ad65d3115c7ab7aecdd19872dc
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:a165f56bd6ac2cf4a9410a04aca1d8815a3df9e6076409be93fd381d410370c2
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:0c64f52e21add7774a67e5779a299e4cfaaccea31655f58e17b1cc344e092b88
concepts: ["prompts.chat", "prompt-library", "prompt-registry", "mcp", "claude-code-plugin", "skill-graph", "self-hosting", "prompt-assets"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 prompts.chat 仓库并提炼 Hermes 在开放 prompt 资产注册表、MCP/Claude Code 插件分发与自托管私有 prompt library 上的可吸收增量

## Objective

分析 prompts.chat 仓库并提炼 Hermes 在开放 prompt 资产注册表、MCP/Claude Code 插件分发与自托管私有 prompt library 上的可吸收增量

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

- 2026-05-18T01:20:00+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-18T01:22:38+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-18T01:22:38+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-18T01:22:38+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:a165f56bd6ac2cf4a9410a04aca1d8815a3df9e6076409be93fd381d410370c2, command:py_compile_taskpool PASS

- 2026-05-18T01:22:39+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:0c64f52e21add7774a67e5779a299e4cfaaccea31655f58e17b1cc344e092b88, proof:sha256:a165f56bd6ac2cf4a9410a04aca1d8815a3df9e6076409be93fd381d410370c2, command:py_compile_taskpool PASS

- 2026-05-18T01:34:36+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-172239-364473-p60693-dfe57a55-59478ee3/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T01:34:48+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-172239-126882-p60678-9da3a77e-4c10da23/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T01:35:12+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-172238-857850-p60666-e99fc84b-f9cea469/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
