---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T00:39:51+08:00
updated: 2026-05-17T06:51:32+08:00
expires_at: 2026-06-16T00:39:51+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 agentmemory 的持久记忆引擎、hooks 自动捕获、BM25+vector+graph 混合检索、4-tier consolidation 与 MCP/provider 接入，对 Hermes local-brain / memory provider / context injection 提出长期可维护的记忆架构增量与主链执行顺序。
anti_drift_check: 先对照已存在的 claude-mem 记忆任务，禁止把 agentmemory 写成重复的“再研究一遍通用记忆层”；必须明确其相对 claude-mem 的净新增：shared MCP server、多 agent 共享、4-tier consolidation、hook capture、knowledge graph、graceful fallback。避免直接采用 README 自报 benchmark 结论为事实，重点提炼机制与验证入口。
acceptance_evidence: repo metadata、README 机制提炼、与 Hermes 现有 MEMORY/USER/session_search/local-brain/memory provider 的差距清单、吸收/拒绝项、长期可维护主链方案、执行顺序，以及需要新增或修订的技能/脚本/文档/自检项。
workflow_contract: "[08-模板/task-workflow-contract-template]"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T06:58:32+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260516-225132-404900-p91455-811a0478-1aec1919/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-agentmemory-仓库并提炼-hermes-在-hybrid-retrieval-shared-memory-server-与-hook-drive-state.json
multimodel_last_failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]
multimodel_failure_taxonomy: ["agreement_low", "criteria_missing", "vote_reject"]
multimodel_recommended_axes: ["fallback_threshold", "relay_ordering", "framing"]
multimodel_axis_rationale: "{'fallback_threshold': ['criteria_missing'], 'relay_ordering': ['agreement_low'], 'framing': ['vote_reject']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 先完成与 claude-mem 结果的对照和 Hermes 现状差距图；然后分别评估 shared memory server / memory provider 边界、hybrid retrieval 与 graph 索引、hook-driven capture 与 consolidation 状态机；最后再收敛为长期可维护的主链改造方案与执行顺序，禁止退化成单点 recall patch。
evidence:
  - proof:sha256:911d84e3a1a9132e4f29e16dee50c66249649a9c3e6abb08bf63633b8d316c2f
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:6c4cf5c0f8d48ecd360aa1a61f0164335814ce6ae303814bccd040c7a21f707d
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:913feae52eb7646ca80139cf1cc50c3dcb215651ecb1807767b0849c6f3d1b4c
concepts: ["agentmemory", "persistent-memory", "hybrid-search", "knowledge-graph", "4-tier-consolidation", "mcp-memory-provider", "hook-capture"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 agentmemory 仓库并提炼 Hermes 在 hybrid retrieval shared memory server 与 hook-driven consolidation 上的可吸收增量

## Objective

分析 https://github.com/rohitg00/agentmemory ，重点不是泛泛“做记忆层”，而是提炼它在跨 agent 共享记忆服务器、自动 hook 捕获、BM25+vector+graph 混合检索、4-tier consolidation、privacy filter、MCP + provider 双接入上的机制，对照 Hermes 当前 memory/session_search/local-brain/control-plane 设计，形成可执行的吸收边界、长期可维护主链改造方案与执行顺序。

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

- 2026-05-17T00:39:51+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T04:12:19+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-200927-160591-p57765-cc6cbe36-95ebc015/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T06:51:32+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T06:51:32+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T06:51:32+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:6c4cf5c0f8d48ecd360aa1a61f0164335814ce6ae303814bccd040c7a21f707d, command:py_compile_taskpool PASS

- 2026-05-17T06:51:32+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:913feae52eb7646ca80139cf1cc50c3dcb215651ecb1807767b0849c6f3d1b4c, proof:sha256:6c4cf5c0f8d48ecd360aa1a61f0164335814ce6ae303814bccd040c7a21f707d, command:py_compile_taskpool PASS

- 2026-05-17T06:53:54+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260516-225132-535110-p91465-31b2c9a9-f60f3c94/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T06:58:32+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260516-225132-404900-p91455-811a0478-1aec1919/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-21T18:05:36+08:00: User supplied verified source URL `https://github.com/rohitg00/agentmemory`. Cloned successfully to `/tmp/agentmemory` at commit `bc641077913c0ac043e702a8f6519189e89b1721`; GitHub API canonical `rohitg00/agentmemory`, Apache-2.0, package `@agentmemory/agentmemory` v0.9.21. Source-backed analysis written to `/Users/charles/.hermes/hermes-agent/docs/private/agentmemory-gap-analysis.md`. Key verified surfaces: `integrations/hermes/README.md`, `integrations/hermes/plugin.yaml`, `src/functions/remember.ts`, `src/functions/search.ts`.
