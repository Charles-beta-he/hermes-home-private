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
capability_delta: framing narrowed brief
anti_drift_check: parent objective remains canonical
acceptance_evidence: proof log maps each unresolved issue to one narrowed question
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
auto_subtask_axis: framing
auto_subtask_trigger: auto_subtask_on_non_convergence:framing
auto_subtask_issue_ids: ["I-001", "I-002", "I-003"]
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
  - proof:follow_through_brief_completed_framing_2026-05-19
  - proof:source_readback_brain_task_orchestrator_and_discussion_artifact
concepts: ["task", "auto-subtask", "non-convergence", "framing"]
---

# Task - 为 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑 细化 framing 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑`. Do not change the parent objective.

## Acceptance Criteria

- [x] Produce a narrowed brief that maps unresolved issues to one concrete evidence or design question each.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Narrowed Brief — Framing Follow-through 2026-05-19

Read-back inputs:
- The unresolved cluster is already explicit: `I-001`, `I-002`, and `I-003` all revolve around noop-vs-change ambiguity, not around missing parent objective wording.
- `brain_task_orchestrator.py:1658-1668` maps `vote_reject`, `provider_parse_error`, `model_vote_missing`, and evidence-shape failures back into the `framing` axis because framing is responsible for asking the next narrowed question cleanly.
- For this parent, the durable framing target is still the long-term maintainable mainline plan: bounded child tasks, evidence-first reconciliation, and no reopening of already absorbed repo summaries.

Issue-to-question map:

| Issue | Narrowed question | Why this is the framing question |
|---|---|---|
| `I-001` | Is the lone minority concrete patch a real exception to the noop majority, or should the ledger formalize it as noop/advisory? | This is the top-level ambiguity blocking certification. |
| `I-002` | If the minority patch should survive, what exact E-* file evidence ties it to verified claims `C-001/C-002/C-003`? | Without this question, the parent drifts into undocumented implementation. |
| `I-003` | If the patch is downgraded, how should `current_best_summary` and the ratification packet record that resolution so empty patches are not mistaken for silent merge loss? | This keeps the packet fail-closed and human-auditable. |

Framing guardrails:
1. Parent objective remains canonical: reconcile external-analysis quality debt and land bounded backfills.
2. The next ratification round should ask one question set only: resolve noop-vs-change ledger semantics. It should not reopen repo scoring, owner-brain decomposition, or already-created bucket tasks.
3. Any future implementation demand must be phrased as a consequence of answered ledger questions, not as a fresh architectural rewrite.

Closeout boundary: this tranche narrows the conversation to the single highest-leverage blocker cluster and names the exact questions future ratification must answer.

## Parent Link

- Parent task: 2026-05-19-second-pass-榨干既往外源分析任务质量缺口并反向灌注多脑
- Discussion artifact: /Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json
- Trigger axis: framing
- Issue IDs: I-001, I-002, I-003

## Parent Objective Snapshot

Consume the quality audit report, triage the 25 non-absorbed candidates, and close the loop by either updating existing tasks, creating bounded child tasks, or backfilling brain/skill/tool tests with verifiable evidence.

## Narrowed Scope

- Resolve only the highest-leverage unresolved issue cluster first.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| discussion artifact read-back | PASS | `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json` contains the authoritative issue ledger / quota snapshot / patch summary for this axis |
| source taxonomy read-back | PASS | `brain_task_orchestrator.py:1626-1668`, `2408-2477`, `2589-2718` define the axis mapping and blocked-parent refresh contract |
| note/artifact write | PASS | this note plus `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` |

## Proof Log

- 2026-05-19T14:08:52+08:00: Task created from local-brain control point.
- 2026-05-19T15:13:26+08:00: Completed the narrowed framing brief by reading the parent task note, the failed multimodel discussion artifact, and the relevant `brain_task_orchestrator.py` axis / refresh code paths. Wrote the consolidated artifact `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json` and marked this child ready for parent targeted refresh.

## Blockers / Confusions

- None.

## Final Handoff

- Status: done; narrowed brief completed and ready to feed the parent blocked-targeted-refresh packet.
- Evidence: this note; `/Users/charles/.hermes/state/taskpool-follow-through/2026-05-19-second-pass-narrowed-briefs.json`; `/Users/charles/.hermes/tick-20260519-055902-295405-p3880-6cc3319d-26c54ea6/discussion_result.json`.
- Residual risk: parent ratification still has to consume the completed child notes and rerun targeted refresh before the parent can move out of blocked/not_certified.
