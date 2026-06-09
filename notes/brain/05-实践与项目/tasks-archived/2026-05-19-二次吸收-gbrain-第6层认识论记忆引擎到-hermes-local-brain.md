---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1-core-memory-epistemology
dependency_order: ["after canonical GBrain repo analysis; before broad memory/retrieval follow-ups; may run in parallel with UI/dashboard-only work but blocks local-brain memory-governance design"]
created: 2026-05-19T14:29:52+08:00
updated: 2026-05-19T14:33:38+08:00
expires_at: 2026-06-18T14:29:52+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 把 GBrain 的第6层认识论层转成 Hermes local-brain 的可执行设计：原子事实管理、时间版本控制、来源置信度、知识图谱关系判断、梦境循环/夜间 consolidation 的长期记忆进化闭环。
anti_drift_check: 禁止重复完成“分析 GBrain 仓库”泛化摘要；必须只处理相对既有 done 任务的增量：第6层认识论机制如何落到 Hermes。不得退化为前3层 chunk/embed/index 检索优化，也不得只写概念文。
acceptance_evidence: 产出一份 GBrain layer-6 -> Hermes local-brain gap map；给出最小可落地 schema/control-plane patch 或明确任务拆分；验证原子事实、时间版本、来源置信度至少有一个可执行 proof；更新相关 brain/taskpool/skill 记录。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: "High-leverage Hermes memory architecture change: atomic fact management + temporal version control + source confidence affect truth, graph reasoning, and long-term memory evolution."
expected_participants: ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"]
truth_gate: Must distinguish repo-evidenced GBrain mechanisms from user-supplied interpretation; any implementation must preserve current Hermes memory/taskpool behavior and add measurable proof gates.
evidence_bundle: "Existing task: /Users/charles/Documents/brain/05-实践与项目/tasks/2026-05-13-分析-gbrain-仓库并优化-hermes-自身认知控制面与知识系统.md ; user supplement 2026-05-19: GBrain 8-layer architecture, layers 1-3 retrieval, 4-5 memory evolution, layer 6 epistemology via atomic facts / temporal versioning / source confidence; repo metadata: TypeScript, https://github.com/garrytan/gbrain, README positions GBrain as production AI long-term memory with self-wiring knowledge graph and overnight consolidation."
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P1: user supplied a net-new mechanism slice missing from the completed GBrain task: the layer-6 epistemology moat beyond chunk/embed/index retrieval. Landing zone is local-brain memory governance, not generic repo summary."
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json
multimodel_last_checked_at: 2026-05-19T14:33:36+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-二次吸收-gbrain-第6层认识论记忆引擎到-hermes-local-brain-state.json
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
parallel_boundary: Serial with other local-brain memory schema/governance changes; parallel with unrelated repo-analysis/advisory tasks.
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json"
  - proof:sha256:e681209f78e2d4702291314dbcecbc1605e35442d589bf980ec21881ded000a4
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json
concepts: ["gbrain", "epistemology-layer", "atomic-facts", "temporal-versioning", "source-confidence", "knowledge-graph", "dream-loop", "long-term-memory"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: ["explicit_requires_multimodel"]
---

# Task - 二次吸收 GBrain 第6层认识论记忆引擎到 Hermes local-brain

## Objective

基于用户补充和 GBrain 仓库二次核验，聚焦第6层认识论层，而非基础检索层：设计 Hermes 如何管理原子事实、时间版本与来源置信度，让知识图谱与梦境循环支持长期记忆进化。

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

- 2026-05-19T14:29:52+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-19T14:29:57+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-19T14:29:57+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-19T14:33:36+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T14:33:36+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json

- 2026-05-19T14:33:38+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:e681209f78e2d4702291314dbcecbc1605e35442d589bf980ec21881ded000a4, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260519-062957-310606-p20228-157471af-b0f03a0b/discussion_result.json
