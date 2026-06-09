---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: "P1: 已完成多脑拆分后的质量补齐主链；先处理 open/pending，再补 done 任务证据债，最后反向灌注 brain/skill/test"
dependency_order: ["['1) 不重复创建已有 active 任务：awesome-design-md 与 OmniVoiceStudio 只作为依赖/引用；2) 处理 open_task_continue：GenericAgent、铁板架构 Cron、Sakana conductor、active logs；3) 处理 done 但缺 source/decision/stop 的 P0/P1 历史任务；4) 将高价值机制沉到 design/research/media/mlops/workflow/hermes-core/dev 对应 brain profile、skill reference、route smoke；5) proof-check/evidence-spine/P10 验证']"]
created: 2026-05-19T14:08:52+08:00
updated: 2026-05-19T15:13:26+08:00
expires_at: 2026-06-18T01:59:16+08:00
project: hermes
architecture_target: local-brain
capability_delta: patch normalization narrowed brief
anti_drift_check: keep implementation slicing smaller than the parent mission
acceptance_evidence: proof log explains why each candidate patch is included, excluded, or deferred
workflow_contract: "['[08-模板/task-workflow-contract-template]']"
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: requires_multimodel=true; reason=P1 evolution + cross-brain governance + historical external-analysis absorption quality gate; expected=Claude architecture arbitration + GPT/Codex implementation sanity + DeepSeek review; fail-closed on self-relaxing gates
auto_subtask_parent: 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: Can parallelize by owner brain (design/research/media/mlops/workflow/hermes-core/dev) only when task files and brain/skill surfaces are disjoint; one integration owner reconciles registry/routes/tests.
evidence:
  - artifact:/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json
  - artifact:/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json
  - proof:follow_through_brief_completed_patch_normalization_2026-05-19
  - proof:source_readback_brain_task_orchestrator_and_discussion_artifact
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
---

# Task - 为 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑`. Do not change the parent objective.

## Acceptance Criteria

- [x] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Narrowed Brief — Patch Normalization Follow-through 2026-05-19

Read-back inputs:
- The merged discussion reports `minority_patches = [P-NOOP-RATIFICATION, P-NOOP-LANE-PREEMPTION, P-001-noop-preserve-certified-gates, P-001, P-QUOTA-PROBE, P-NEXT-SLICE, P-CERTIFICATION]` with `concrete_patch_count = 1` and `noop_patch_count = 6`.
- `issue_ledger` plus round reasoning says the concrete patch came from `mimo-v2.5-pro`, but no file-backed evidence override was attached; the disagreement is about certification packaging, not about a missing implementation diff in Hermes itself.
- Because the parent objective is evidence reconciliation for external-analysis tasks, the minimum certifiable patch set should prefer note/packet normalization over broad code changes.

Candidate patch normalization table:

| Candidate | Decision | Reason |
|---|---|---|
| `P-NOOP-RATIFICATION`, `P-NOOP-LANE-PREEMPTION`, `P-001-noop-preserve-certified-gates` | Include only as noop evidence labels | They confirm preserved gating behavior and should stay in the ledger, not become implementation work. |
| `P-001` minority concrete patch | Exclude from implementation-ready set unless explicit E-* override is supplied | Current artifact contains no evidence that beats the 3-model noop majority. |
| `P-QUOTA-PROBE` | Defer to quota-observability brief | It is evidence-shape work, not parent implementation work. |
| `P-NEXT-SLICE`, `P-CERTIFICATION` | Include as ratification-packet requirements, not code patches | They describe how the parent should be re-presented, not what Hermes code should change. |

Minimum certifiable patch set:
1. Keep the parent objective unchanged: no repo re-summary, no new cross-brain implementation work in this slice.
2. Treat the current result as a packet-normalization problem: the certifiable output is a child-brief bundle plus explicit ledger resolution, not a source patch.
3. Allow a concrete implementation patch only if a future rerun adds file-backed evidence that directly ties the change to verified claims and survives the fallback threshold rule.
4. Otherwise, normalize the result into `no_action_certification` with explicit rationale for why each surfaced patch stayed noop/advisory.

Closeout boundary: this tranche resolves which surfaced patch candidates belong in the certifiable minimum set. It does not authorize code edits in Hermes scripts, skills, or profiles from the current artifact alone.

## Parent Link

- Parent task: 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑
- Discussion artifact: /Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

Consume the quality audit report, triage the 25 non-absorbed candidates, and close the loop by either updating existing tasks, creating bounded child tasks, or backfilling brain/skill/tool tests with verifiable evidence.

## Narrowed Scope

- Only normalize surfaced patch candidates and their inclusion criteria.
- Do not expand into end-to-end implementation here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| discussion artifact read-back | PASS | `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json` contains the authoritative issue ledger / quota snapshot / patch summary for this axis |
| source taxonomy read-back | PASS | `brain_task_orchestrator.py:1626-1668`, `2408-2477`, `2589-2718` define the axis mapping and blocked-parent refresh contract |
| note/artifact write | PASS | this note plus `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` |

## Proof Log

- 2026-05-19T14:08:52+08:00: Task created from local-brain control point.
- 2026-05-19T15:13:26+08:00: Completed the narrowed patch_normalization brief by reading the parent task note, the failed multimodel discussion artifact, and the relevant `brain_task_orchestrator.py` axis / refresh code paths. Wrote the consolidated artifact `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` and marked this child ready for parent targeted refresh.

## Blockers / Confusions

- None.

## Final Handoff

- Status: done; narrowed brief completed and ready to feed the parent blocked-targeted-refresh packet.
- Evidence: this note; `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json`; `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json`.
- Residual risk: parent ratification still has to consume the completed child notes and rerun targeted refresh before the parent can move out of blocked/not_certified.
