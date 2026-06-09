---
type: task
lane: evolution
layer: L3
status: done
priority: P2
created: 2026-05-15T05:33:35+08:00
updated: 2026-05-15T05:37:00+08:00
expires_at: 2026-06-14T05:33:35+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 基于 MemOS memos-local-plugin 源码与 Hermes 本地插件文档，增强 Hermes 在本地持久记忆、任务总结、技能自动进化与多智能体共享上的集成与演进能力。
anti_drift_check: 必须基于 GitHub 源码目录（agent-contract/core/bridge/server/tests/viewer/templates）与 Hermes 本地插件中文文档做实际差距分析；优先复用和 patch 现有 Hermes memory/skill/taskpool/control-plane 能力，避免平行重复建设或引入云依赖假设。
acceptance_evidence: 形成源码/文档分析摘要、与 Hermes 当前 local-brain/记忆/技能体系的差距清单、明确的最小可验证优化切片或接入方案，并在任务池中留下可继续派发的结构化证据。
workflow_contract: "[08-模板/task-workflow-contract-template]"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-15T05:36:29+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260514-213337-105762-p58349-fe999610-201b2f64/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-15-分析-memos-memos-local-plugin-源码与-hermes-本地插件文档并优化-hermes-本地记忆-任务总结-技能进化集成-state.json
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
parallel_boundary: "Recommended order: 1) repo/doc architecture + runtime data-flow analysis -> 2) Hermes local-brain/memory/skill gap mapping -> 3) smallest verifiable integration or optimization slice; can parallelize note extraction with non-overlapping documentation work, but avoid concurrent landing with overlapping local-brain memory/control-plane mutations."
evidence:
  - proof:sha256:f68658858d3359cd9ef90b1e8dff4b8129b88ec04e63017c8690abe917435ff1
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:e788c1263f98ceac9a38832033135df7dec8aec6f9a1b910cce0874f193bf796
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:6fd4f6c839961b64700ed23940c23849ba5c73cc212c3050408c954899dd7139
concepts: ["memos-local-plugin", "hermes-local-plugin", "local-memory", "task-summary", "skill-evolution", "local-brain"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - 分析 MemOS memos-local-plugin 源码与 Hermes 本地插件文档并优化 Hermes 本地记忆/任务总结/技能进化集成

## Objective

分析 https://github.com/MemTensor/MemOS/tree/main/apps/memos-local-plugin 与 https://memos-docs.openmem.net/cn/openclaw/hermes_local_plugin ，提炼可迁移的 Hermes 本地持久记忆、任务总结、技能自动进化与协同共享设计，并映射为 Hermes 自身能力、技能体系或控制面优化。

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

- 2026-05-15T05:33:35+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-15T05:36:29+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260514-213337-105762-p58349-fe999610-201b2f64/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-15T05:36:59+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-15T05:36:59+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-15T05:36:59+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:e788c1263f98ceac9a38832033135df7dec8aec6f9a1b910cce0874f193bf796, command:py_compile_taskpool PASS

- 2026-05-15T05:37:00+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:6fd4f6c839961b64700ed23940c23849ba5c73cc212c3050408c954899dd7139, proof:sha256:e788c1263f98ceac9a38832033135df7dec8aec6f9a1b910cce0874f193bf796, command:py_compile_taskpool PASS
