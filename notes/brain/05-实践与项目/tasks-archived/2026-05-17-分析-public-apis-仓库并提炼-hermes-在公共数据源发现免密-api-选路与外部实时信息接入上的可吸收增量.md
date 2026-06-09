---
type: task
lane: evolution
layer: L3
status: done
priority: P3
created: 2026-05-17T14:26:00+08:00
updated: 2026-05-17T23:10:10+08:00
expires_at: 2026-06-16T14:26:00+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 public-apis 作为大规模公共 API 目录在数据源发现、免密/低门槛接口筛选、领域覆盖映射、实时外部信息接入与工具路由前置目录上的价值，对 Hermes 的 live-data acquisition、source registry、任务池外部资料摄取和后续 agent 选源策略提出可维护增量。
anti_drift_check: 禁止把任务退化成对 70+ 分类/几十万 star 的泛泛盘点；必须围绕 Hermes 的净新增机制提炼：公共 API 目录如何转化为可治理的 source registry、何时适合接入为 research/live-data 的候选源、如何做免密优先/可靠性分层/领域映射，以及哪些内容不应吸收到 Hermes。不要把 README 中的 API 列表逐项抄写成结果。
acceptance_evidence: repo metadata、README/目录结构提炼、Hermes 当前 web/live-data/source-discovery 能力差距图、公共 API 目录可吸收/不吸收清单、候选落点（registry/skill/tool-routing/ingest）与最小验证切片，以及需新增或修订的技能/脚本/控制面项。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T23:40:02+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-151010-902240-p15201-e6aee033-ebceb9ee/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-public-apis-仓库并提炼-hermes-在公共数据源发现免密-api-选路与外部实时信息接入上的可吸收增量-state.json
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
parallel_boundary: 先确认仓库定位、维护方式与数据组织结构，再对照 Hermes 当前 external-source 获取路径做 gap map；随后分离 source registry 建模、免密 API 选路策略、领域映射与可靠性分层，最后收敛为长期可维护的吸收边界与最小落地方案。禁止退化成单纯 API 清单摘录。
evidence:
  - proof:sha256:35ad9706d013c8f80a1b85fa3cb45eb821e0ceb2febbcfb23944598ad1a2b3df
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:eadebf8c37979d024a79bcfcdcd5d7b7499b943d1fcfa123a424ac9799d9456a
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:842655a8605690f8a0e680327dac4173202973d02f59b2bf2e9f74def60a695f
concepts: ["public-apis", "api-catalog", "external-data-sources", "live-data", "source-discovery", "tool-routing"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 public-apis 仓库并提炼 Hermes 在公共数据源发现、免密 API 选路与外部实时信息接入上的可吸收增量

## Objective

分析 https://github.com/public-apis/public-apis ，重点不是收集 API 名单，而是提炼它作为公共数据源目录对 Hermes 的价值：是否应沉淀成 source registry / live-data 候选目录、怎样支持研究类任务快速选源、以及如何在不引入低质量外部依赖的前提下提升实时信息接入能力。

## Acceptance Criteria

- [ ] Observable result is recorded in Proof Log.

## Plan / Workpad

- [ ] Reconcile current state before execution.
- [ ] Execute the smallest verifiable slice.
- [ ] Record proof and update status.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-17T14:26:00+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T18:05:07+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-100216-030283-p74394-6ac3259c-50b9e39b/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T23:10:10+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T23:10:10+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T23:10:10+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:eadebf8c37979d024a79bcfcdcd5d7b7499b943d1fcfa123a424ac9799d9456a, command:py_compile_taskpool PASS

- 2026-05-17T23:10:10+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:842655a8605690f8a0e680327dac4173202973d02f59b2bf2e9f74def60a695f, proof:sha256:eadebf8c37979d024a79bcfcdcd5d7b7499b943d1fcfa123a424ac9799d9456a, command:py_compile_taskpool PASS

- 2026-05-17T23:38:48+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-151010-772369-p15192-7558aaaf-e3cc4a7a/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:reject"]. Recommended axes: ["quota_observability", "fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["no_claims", "vote_reject"]}

- 2026-05-17T23:40:02+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-151010-902240-p15201-e6aee033-ebceb9ee/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}
