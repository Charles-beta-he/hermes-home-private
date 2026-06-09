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
capability_delta: quota observability narrowed brief
anti_drift_check: keep parent objective unchanged while proving quota_state semantics
acceptance_evidence: proof log cites source evidence for quota_state confidence and unknown handling
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
auto_subtask_axis: quota_observability
auto_subtask_trigger: auto_subtask_on_non_convergence:quota_observability
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
  - proof:follow_through_brief_completed_quota_observability_2026-05-19
  - proof:source_readback_brain_task_orchestrator_and_discussion_artifact
concepts: ["task", "auto-subtask", "non-convergence", "quota-observability"]
---

# Task - 为 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑 细化 quota observability 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑`. Do not change the parent objective.

## Acceptance Criteria

- [x] Produce a narrowed brief covering quota_state source, confidence, unknown/unobservable handling, and file-backed evidence locations.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Narrowed Brief — Quota Observability Follow-through 2026-05-19

Read-back inputs:
- Parent discussion artifact `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json` carries the authoritative quota snapshot for this non-convergence round: `final_design.quota_snapshot` and `final_design.quota_confidence` are already present, so this slice should normalize how those fields are interpreted rather than inventing a new quota probe.
- `brain_task_orchestrator.py:2515-2541` treats low quota confidence as any provider snapshot whose `confidence <= 0.25` or whose `observability in {unknown, unobservable, missing}`; that condition alone is enough to request the `quota_observability` axis.
- `brain_task_orchestrator.py:1626-1661` also maps textual quota/rate-limit/unobservable failures into the `quota_unobservable` category, which in turn recommends the `quota_observability` + `framing` axes.

Quota-state interpretation table:

| Provider/model | Source | Observability | Confidence | Staleness rule | Operational meaning |
|---|---|---|---|---|---|
| anthropic::claude-opus-4-7 | response_headers | unknown | 0.1 | stale after 300s | Do not infer remaining budget; only record that the provider exposed no reliable quota state. |
| deepseek::deepseek-v4-pro | response_headers | unknown | 0.1 | stale after 300s | Same fail-closed treatment as above. |
| openai-codex::gpt-5.5 | response_headers | unobservable | 0.2 | stale after 300s | Subscription-cap provider; absence of exact counters must stay observational, not a trigger for policy change by itself. |
| xiaomi::mimo-v2.5-pro | response_headers | unknown | 0.1 | stale after 300s | Same fail-closed treatment as above. |

Minimum semantics to carry forward:
1. `quota_state.source` stays file-backed by the discussion artifact snapshot; do not rewrite it from memory or from a later unrelated run.
2. `quota_state.confidence <= 0.25` means “not actionable for policy change”. It may justify a narrowed observability brief, but it cannot justify a concrete fallback rewrite on its own.
3. `observability=unknown` and `observability=unobservable` are distinct but both fail-closed for decision making: `unknown` means the provider exposed no stable schema, while `unobservable` means the provider class cannot expose exact remaining quota in the current integration.
4. `stale_after_seconds=300` is the explicit freshness boundary. Any quota snapshot older than that must be treated as historical evidence only, not as live budget state.
5. File-backed evidence locations for future ratification are `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json` plus `brain_task_orchestrator.py:2515-2541` and `brain_task_orchestrator.py:1626-1661`.

Closeout boundary: this tranche resolves the semantics of quota_state and its evidence locations. It does not authorize new quota-aware implementation work; if a future round wants to change fallback behavior, it must first present fresh, provider-specific quota evidence above this confidence floor.

## Parent Link

- Parent task: 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑
- Discussion artifact: /Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json
- Trigger axis: quota_observability
- Issue IDs: none tagged

## Parent Objective Snapshot

Consume the quality audit report, triage the 25 non-absorbed candidates, and close the loop by either updating existing tasks, creating bounded child tasks, or backfilling brain/skill/tool tests with verifiable evidence.

## Narrowed Scope

- Only resolve quota observability and evidence gaps.
- Do not decide relay ordering or broader fallback policy here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| discussion artifact read-back | PASS | `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json` contains the authoritative issue ledger / quota snapshot / patch summary for this axis |
| source taxonomy read-back | PASS | `brain_task_orchestrator.py:1626-1668`, `2408-2477`, `2589-2718` define the axis mapping and blocked-parent refresh contract |
| note/artifact write | PASS | this note plus `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` |

## Proof Log

- 2026-05-19T14:08:52+08:00: Task created from local-brain control point.
- 2026-05-19T15:13:26+08:00: Completed the narrowed quota_observability brief by reading the parent task note, the failed multimodel discussion artifact, and the relevant `brain_task_orchestrator.py` axis / refresh code paths. Wrote the consolidated artifact `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` and marked this child ready for parent targeted refresh.

## Blockers / Confusions

- None.

## Final Handoff

- Status: done; narrowed brief completed and ready to feed the parent blocked-targeted-refresh packet.
- Evidence: this note; `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json`; `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json`.
- Residual risk: parent ratification still has to consume the completed child notes and rerun targeted refresh before the parent can move out of blocked/not_certified.
