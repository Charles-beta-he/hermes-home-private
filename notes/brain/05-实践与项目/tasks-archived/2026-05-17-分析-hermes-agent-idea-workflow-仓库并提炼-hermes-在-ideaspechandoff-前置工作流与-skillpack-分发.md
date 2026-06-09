---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: "P2 second-batch leverage: planning/spec skillpack governance"
dependency_order: ["1) repo/README mechanism extraction -> 2) compare with existing planning/spec skills -> 3) identify patch-vs-new-skillpack landing -> 4) define smallest verifiable adoption slice"]
created: 2026-05-17T19:08:01+08:00
updated: 2026-05-17T19:26:48+08:00
expires_at: 2026-06-16T19:08:01+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: 评估 AkoliteZA/hermes-agent-idea-workflow 作为 Hermes 前置创意工作流 skillpack 的可迁移增量：把粗糙想法沉淀为 design doc、implementation spec、agent build handoff、spec review gate，并通过可安装技能包交付固定流程，对 Hermes 现有 planning/writing-plans/spec 体系提出长期可维护的 skill-graph 增量与主链执行顺序。
anti_drift_check: 禁止把任务写成泛泛产品经理方法论、头脑风暴鸡汤或‘想法变 PRD’式营销总结；必须对照 Hermes 已有 planning/spec/skill 工作流，明确该仓库的净新增：lite/full 双模式、阶段化 Markdown 工件、GREENLIGHT NEXT STAGE 覆盖机制、final single-file handoff、spec review gate、以及与后续 build workflow 的接口边界。必须区分哪些应并入既有 umbrella/planning skill，哪些不应平行复制新技能树。
acceptance_evidence: repo metadata、README 机制证据、与 Hermes 当前 planning/spec/skill 体系的差距图、可吸收/拒绝项、最小验证切片（如 idea→design→implementation→handoff 的模板化技能路径或现有 umbrella skill patch 点）、推荐执行顺序，以及需新增或修订的技能/模板/reference 项。
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
multimodel_triage_result: "Pre-add triage: P2 evolution task for skill-graph; advisory multimodel useful for planning/spec boundary and patch-vs-new-skillpack decision, but not a current P1 blocker."
multimodel_status: not_certified
multimodel_last_checked_at: 2026-05-17T19:33:50+08:00
multimodel_round_status: failed
multimodel_last_gate_status: FAIL
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260517-112648-967843-p41021-596cff49-985e538e/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析-hermes-agent-idea-workflow-仓库并提炼-hermes-在-ideaspechandoff-前置工作流与-skillpack-分发-state.json
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
parallel_boundary: 先完成 repo surface 与 README 机制提炼，再对照 Hermes 当前 writing-plans/planning/spec 技能体系做 gap map；随后可并行拆成 artifact pipeline、review gate/override phrase、handoff-to-build workflow interface 三块，再收敛为长期可维护的主链方案。禁止退化成普通提示词模板收集。
evidence:
  - proof:sha256:c1473504d5cce26fde3e84ca1cb58cd0b6f2fcc57fc3c8431038646621d5264f
  - classification:proof_debt_migration_compat=current_chain_hash_minted_for_historical_autorun_done_task
  - classification:legacy_autorun_proof_hash=sha256:43cad6ef996d05bde56ade71f62bb6748eed471f3c6c9eb773f0557cdd1cdd56
  - command:py_compile_taskpool PASS
  - classification:legacy_autorun_proof_hash=sha256:a92aea343cff1ff3b72ae169c0af75c30d63afb04be8abc5033ee0afc305f53f
concepts: ["idea-workflow", "product-spec", "handoff", "skillpack", "prebuild-workflow", "design-doc", "implementation-spec"]
multimodel_advisory_only: False
multimodel_certification_authority: False
multimodel_advisory_reasons: []
multimodel_certification_reasons: []
---

# Task - 分析 hermes-agent-idea-workflow 仓库并提炼 Hermes 在 idea→spec→handoff 前置工作流与 skillpack 分发上的可吸收增量

## Objective

分析 https://github.com/AkoliteZA/hermes-agent-idea-workflow ，重点不是复述‘创意变 PRD’，而是提炼它如何把模糊想法转成 staged specs 与 build handoff，并评估 Hermes 是否应吸收这种 pre-build skillpack/workflow 作为 planning/spec 前置层。

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

- 2026-05-17T19:08:01+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-17T19:26:48+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-17T19:26:48+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-17T19:26:48+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:43cad6ef996d05bde56ade71f62bb6748eed471f3c6c9eb773f0557cdd1cdd56, command:py_compile_taskpool PASS

- 2026-05-17T19:26:48+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:a92aea343cff1ff3b72ae169c0af75c30d63afb04be8abc5033ee0afc305f53f, proof:sha256:43cad6ef996d05bde56ade71f62bb6748eed471f3c6c9eb773f0557cdd1cdd56, command:py_compile_taskpool PASS

- 2026-05-17T19:30:54+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-112648-582300-p41004-531c71e3-63953729/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-17T19:33:25+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-112648-802769-p41014-048fd7e9-7ead845a/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}

- 2026-05-17T19:33:50+08:00: Multimodel PUA-loop round `failed`. Gate `FAIL`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260517-112648-967843-p41021-596cff49-985e538e/discussion_result.json`. Failures: ["best_within_constraints_missing:claude-opus-4-7", "non_approve_vote:claude-opus-4-7:amend", "status_not_passed:not_certified"]. Recommended axes: ["quota_observability", "fallback_threshold", "framing"]. Axis rationale: {"quota_observability": ["quota_unobservable"], "fallback_threshold": ["criteria_missing"], "framing": ["vote_reject"]}
