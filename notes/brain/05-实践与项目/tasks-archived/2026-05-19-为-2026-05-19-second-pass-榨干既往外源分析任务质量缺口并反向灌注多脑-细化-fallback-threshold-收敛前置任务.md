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
capability_delta: fallback threshold narrowed brief
anti_drift_check: separate threshold policy from relay implementation so the parent scope does not drift
acceptance_evidence: proof log states threshold semantics and the evidence gate for noop-vs-change
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
auto_subtask_axis: fallback_threshold
auto_subtask_trigger: auto_subtask_on_non_convergence:fallback_threshold
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
  - proof:follow_through_brief_completed_fallback_threshold_2026-05-19
  - proof:source_readback_brain_task_orchestrator_and_discussion_artifact
concepts: ["task", "auto-subtask", "non-convergence", "fallback-thresholds"]
---

# Task - 为 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑 细化 fallback threshold 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑`. Do not change the parent objective.

## Acceptance Criteria

- [x] Produce a narrowed brief covering trigger thresholds, allowed fallback actions, and explicit noop-vs-change decision criteria.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Narrowed Brief — Fallback Threshold Follow-through 2026-05-19

Read-back inputs:
- `brain_task_orchestrator.py:2552-2553` requests the `fallback_threshold` axis whenever issue text implies threshold/downgrade/fallback semantics or when `planner_patch_summary.certification_intent == unresolved_noop_vs_change`.
- The current discussion artifact sets `final_design.planner_patch_summary.certification_intent = unresolved_noop_vs_change`, `concrete_patch_count = 1`, and `noop_only_model_count = 3`; therefore the threshold problem here is not runtime retry tuning but the evidence threshold for accepting a concrete patch against a noop majority.
- Issue ledger rows `I-001` / `I-002` / `I-003` all describe the same threshold boundary: do not upgrade a minority patch into implementation unless it clears an explicit evidence override against the noop majority.

Threshold policy table:

| Situation | Threshold | Allowed fallback action | Not allowed |
|---|---|---|---|
| One concrete patch vs 3 noop votes with no E-* override evidence | Fail threshold | Downgrade to advisory/noop and carry the disagreement in the ledger | Treat as implementation-ready change |
| Minority patch supplies direct evidence tied to verified claim C-001/C-002/C-003 | Pass threshold | Keep the patch in the certifiable minimum set and re-run ratification | Silently drop the patch without ledger resolution |
| Quota snapshot is low-confidence/unknown/unobservable | Fail threshold for policy change | Record observability debt only | Infer budget-exhaustion behavior change from stale quota data |
| Parent objective is already satisfied by bounded child tasks | Pass threshold for no-action certification | Ratify the evidence packet / child task chain | Re-open repo summarization or broad redesign |

Explicit noop-vs-change criteria:
1. A concrete patch may survive only if it cites file-backed evidence that overrides the noop majority and ties directly to one verified claim.
2. If patch evidence is absent, stale, or only quota-ambiguous, the safe fallback is `advisory/noop + keep ledger explicit`.
3. Empty `current_best_summary.patches` is acceptable only after the ledger explicitly records why the minority patch was downgraded; empty output without that explanation remains below threshold.
4. Threshold semantics belong to ratification, not to transport. Relay/continuation mechanics stay deferred to the relay-ordering axis.

Closeout boundary: this tranche defines when a minority patch is allowed to cross the line from advisory disagreement to actionable change. It does not pick the relay mechanism and does not modify provider retry logic.

## Parent Link

- Parent task: 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑
- Discussion artifact: /Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json
- Trigger axis: fallback_threshold
- Issue IDs: none tagged

## Parent Objective Snapshot

Consume the quality audit report, triage the 25 non-absorbed candidates, and close the loop by either updating existing tasks, creating bounded child tasks, or backfilling brain/skill/tool tests with verifiable evidence.

## Narrowed Scope

- Only resolve threshold semantics and noop-vs-change decision criteria.
- Do not redesign the full handoff workflow here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| discussion artifact read-back | PASS | `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json` contains the authoritative issue ledger / quota snapshot / patch summary for this axis |
| source taxonomy read-back | PASS | `brain_task_orchestrator.py:1626-1668`, `2408-2477`, `2589-2718` define the axis mapping and blocked-parent refresh contract |
| note/artifact write | PASS | this note plus `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` |

## Proof Log

- 2026-05-19T14:08:52+08:00: Task created from local-brain control point.
- 2026-05-19T15:13:26+08:00: Completed the narrowed fallback_threshold brief by reading the parent task note, the failed multimodel discussion artifact, and the relevant `brain_task_orchestrator.py` axis / refresh code paths. Wrote the consolidated artifact `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` and marked this child ready for parent targeted refresh.

## Blockers / Confusions

- None.

## Final Handoff

- Status: done; narrowed brief completed and ready to feed the parent blocked-targeted-refresh packet.
- Evidence: this note; `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json`; `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json`.
- Residual risk: parent ratification still has to consume the completed child notes and rerun targeted refresh before the parent can move out of blocked/not_certified.
