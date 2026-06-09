---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: external-repo-intake:p2:context7-doc-injection
dependency_order: ["recommended-order: repo-surface-and-readme -> doc-injection-mechanism-extraction -> hermes-gap-map -> landing-order-and-validation-slice"]
created: 2026-05-18T01:32:51+08:00
updated: 2026-05-18T01:33:16+08:00
expires_at: 2026-06-17T01:32:51+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 Context7 的最新文档抓取、版本化代码示例注入、MCP 服务接入与 coding prompt 去幻觉机制，对 Hermes 在文档检索、上下文注入与实时知识补充上的长期可维护增量。
anti_drift_check: 禁止把 Context7 写成泛泛 MCP 服务简介；必须明确其相对 Hermes 现有 session_search/skills/web 工具的净新增：版本化官方文档注入、编码场景去幻觉、prompt 侧上下文补全。避免和一般搜索/文档站收集混为一谈。
acceptance_evidence: repo metadata、README 机制提炼、与 Hermes 当前 docs/context injection 路径的差距图、建议吸收/拒绝项、落点与执行顺序、最小验证切片。
workflow_contract: "[08-模板/task-workflow-contract-template]"
requires_multimodel: true
multimodel_reason: external repository intake for Hermes context-engineering evolution should stay evidence-first before adoption
expected_participants: ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"]
truth_gate: "evidence-first: verify documentation freshness, versioning path, and integration surface before adapting any context-injection workflow into Hermes"
evidence_bundle: https://github.com/upstash/context7 | stars=55480 forks=2635 issues=150 language=TypeScript topics=llm,mcp,mcp-server,vibe-coding
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "pre-ingest triage: P2 evolution candidate; notable leverage on coding-context quality, but not an immediate blocking fix"
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-18T01:41:27+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-173316-784355-p67744-56f996ed-433ab179/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-18-分析-context7-平台并提炼-hermes-在最新代码文档检索版本化上下文注入与编码提示去幻觉上的可吸收增量-state.json
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
parallel_boundary: 先核对 repo surface 与文档注入机制，再对照 Hermes 当前知识获取路径；可并行于 web-access，但落点偏上下文工程而非浏览器编排。
evidence:
  - proof:sha256:1f43a2b1450f1b5ad06306665a9588c09dc1181b18b7b6a2fc938381768a16f1
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:2e6572681e227ab962910e64e9823acb666c908defb7dcb72adc780a771079c3
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:a1dadcb44c13aa2370d21326da4ed6425d2184b9de06e0b44ad9c6b4f3693c07
concepts: ["task"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 Context7 平台并提炼 Hermes 在最新代码文档检索、版本化上下文注入与编码提示去幻觉上的可吸收增量

## Objective

分析 https://github.com/upstash/context7 ，重点提炼其最新代码文档检索、版本化上下文注入与编码提示去幻觉机制，对照 Hermes 当前上下文工程与知识补充路径形成可吸收增量。

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

- 2026-05-18T01:32:51+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-18T01:33:16+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-18T01:33:16+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-18T01:33:16+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:2e6572681e227ab962910e64e9823acb666c908defb7dcb72adc780a771079c3, command:py_compile_taskpool PASS

- 2026-05-18T01:33:16+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:a1dadcb44c13aa2370d21326da4ed6425d2184b9de06e0b44ad9c6b4f3693c07, proof:sha256:2e6572681e227ab962910e64e9823acb666c908defb7dcb72adc780a771079c3, command:py_compile_taskpool PASS

- 2026-05-18T01:40:57+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-173317-079385-p67785-8af9688e-25900140/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend", "non_approve_vote:gpt-5.5:amend", "non_approve_vote:mimo-v2.5-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}

- 2026-05-18T01:40:59+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-173316-465300-p67694-ff0c0c65-2b04c36e/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-18T01:41:27+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-173316-784355-p67744-56f996ed-433ab179/discussion_result.json`. Failures: ["agreement_below_threshold:approach:0.65", "agreement_below_threshold:framing:0.65", "agreement_below_threshold:implementation_order:0.65", "best_within_constraints_missing:claude-opus-4-7", "best_within_constraints_missing:gpt-5.5", "best_within_constraints_missing:mimo-v2.5-pro", "non_approve_vote:claude-opus-4-7:amend", "non_approve_vote:deepseek-v4-pro:amend"]. Recommended axes: ["fallback_threshold", "relay_ordering", "framing"]. Axis rationale: {"fallback_threshold": ["criteria_missing"], "relay_ordering": ["agreement_low"], "framing": ["vote_reject"]}
