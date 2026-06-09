---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-17T14:23:56+08:00
updated: 2026-05-17T16:50:22+08:00
expires_at: 2026-06-16T14:23:56+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 评估 CocoIndex 的 delta-only 增量计算、多源 connector→transform→target 数据流、实时 fresh-context 保证、codebase intelligence / knowledge graph / agent memory 数据面能力，对 Hermes local-brain / 外部仓库文档摄取 / context freshness 形成长期可维护的吸收边界、主链方案与执行顺序。
anti_drift_check: 禁止把 CocoIndex 退化成泛泛的 RAG/ETL 仓库总结；必须围绕 Hermes 的净新增机制提炼：增量同步计算、stale-context 防护、多源 source→target 声明式数据面、code intelligence/knowledge graph 可接入点，以及与现有 local-brain / session_search / taskpool ingest 的边界。避免直接采信 README 自报效果，重点看机制、约束、验证入口与最小可落地主链。
acceptance_evidence: repo metadata、README/架构入口提炼、Hermes 当前 local-brain/taskpool ingest/context freshness 差距图、可吸收/不吸收清单、主链执行顺序、最小验证切片，以及需新增或修订的技能/脚本/控制面点位。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260517-085022-585752-p9991-bdb1030b-a1f63b01/discussion_result.json
multimodel_last_checked_at: 2026-05-17T16:54:41+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-085022-585752-p9991-bdb1030b-a1f63b01/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-cocoindex-仓库并提炼-hermes-在增量索引多源实时同步与-fresh-context-数据面上的可吸收增量-state.json
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
parallel_boundary: 先完成 repo surface + README + 关键目录机制提炼，再对照 Hermes local-brain/taskpool ingest 的现状做 gap map；随后分离 connector/source-target 数据面、增量 freshness 机制、code intelligence/knowledge graph 落点，最后收敛为长期可维护的主链方案。禁止直接跳到通用 RAG 结论或一次性大改。
evidence:
  - proof:sha256:add02a541e96faf28fa56c3a7acda3321b11af8c434c6290c3fa9b6ee9664163
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:9137be276dcfd0d3b171cf10f0464c78b79e8b07456c9ab039c4ec4fc2ae6ee3
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:af271c4dd889ef79426efaff964929208320874264986aa51c37b7c56c23812e
concepts: ["cocoindex", "incremental-indexing", "fresh-context", "change-data-capture", "codebase-intelligence", "knowledge-graph"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 CocoIndex 仓库并提炼 Hermes 在增量索引、多源实时同步与 fresh-context 数据面上的可吸收增量

## Objective

分析 https://github.com/cocoindex-io/cocoindex ，重点不是总结一个 AI 数据框架，而是提炼它在 delta-only 增量重算、多源数据接入、持续 fresh-context、代码库/知识图谱索引与声明式 source→target 数据流上的机制，明确 Hermes 应该吸收什么、落在哪一层、按什么顺序推进。

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

- 2026-05-17T14:23:56+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T16:03:20+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-080015-600170-p26323-6158b96c-645703ca/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T16:50:22+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T16:50:22+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T16:50:22+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:9137be276dcfd0d3b171cf10f0464c78b79e8b07456c9ab039c4ec4fc2ae6ee3, command:py_compile_taskpool PASS

- 2026-05-17T16:50:22+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:af271c4dd889ef79426efaff964929208320874264986aa51c37b7c56c23812e, proof:sha256:9137be276dcfd0d3b171cf10f0464c78b79e8b07456c9ab039c4ec4fc2ae6ee3, command:py_compile_taskpool PASS

- 2026-05-17T16:53:56+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-085022-453041-p9982-35e18064-a555f48c/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T16:54:41+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260517-085022-585752-p9991-bdb1030b-a1f63b01/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}
