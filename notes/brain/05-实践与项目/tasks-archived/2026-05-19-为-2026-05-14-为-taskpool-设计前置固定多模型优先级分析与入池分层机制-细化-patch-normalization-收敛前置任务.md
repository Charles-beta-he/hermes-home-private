---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["1"]
created: 2026-05-19T11:41:36+08:00
updated: 2026-05-19T18:26:17+08:00
expires_at: 2026-06-13T00:56:42+08:00
project: hermes-agent
architecture_target: taskpool
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
multimodel_triage_result: not_certified
multimodel_status: advisory_completed
multimodel_last_checked_at: 2026-05-19T18:25:56+08:00
multimodel_round_status: advisory_passed
multimodel_last_gate_status: PASS_ADVISORY_ONLY
multimodel_last_decision: CONTINUE_LOOP
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-102141-109482-p21121-235d4778-532b0753/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-为-2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制-细化-patch-normalization-收敛前置任务-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
auto_subtask_parent: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
auto_subtask_kind: non_convergence_narrowing
auto_subtask_axis: patch_normalization
auto_subtask_trigger: auto_subtask_on_non_convergence:patch_normalization
auto_subtask_issue_ids: []
auto_subtask_parent_artifact: /Users/charles/.hermes/tick-20260519-033213-033607-p97711-eed21c74-be8dd337/discussion_result.json
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - "command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-102141-109482-p21121-235d4778-532b0753/discussion_result.json"
  - proof:sha256:933dafcde85ddd7f89cf5b504280eba1b119a84b9e61cfcd12e41f971c341c8b
concepts: ["task", "auto-subtask", "non-convergence", "patch-normalization"]
multimodel_advisory_only: True
multimodel_certification_authority: False
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evolution_lane"]
multimodel_certification_reasons: []
---

# Task - 为 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制 细化 patch normalization 收敛前置任务

## Objective

Auto-generated convergence slice for parent `2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制`. Do not change the parent objective. Normalize surfaced minority patches into a certifiable minimum patch set that preserves the parent objective and removes noop-vs-change ambiguity.

## Acceptance Criteria

- [ ] Produce a narrowed brief that maps surfaced patch candidates to one certifiable minimum patch set with clear inclusion/exclusion criteria.

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Parent Link

- Parent task: 2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制
- Discussion artifact: /Users/charles/.hermes/tick-20260519-033213-033607-p97711-eed21c74-be8dd337/discussion_result.json
- Trigger axis: patch_normalization
- Issue IDs: none tagged

## Parent Objective Snapshot

将外部仓库/文章等任务在创建入池前先经过固定多模型分析，直接产出 P1/P2/P3 与优先级依据，使任务池更独立、更可解释、更稳定。

## Narrowed Scope

- Only normalize surfaced patch candidates and their inclusion criteria.
- Do not expand into end-to-end implementation here.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator list | pending | |

## Proof Log

- 2026-05-19T11:41:36+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

### 2026-05-19 brain-mirror execution proof — patch normalization narrowed brief

Decision: normalize the surfaced planner output into one certifiable minimum patch set centered on ratification participant normalization, not another parent taskpool feature patch.

Included patch candidate:
- Certification participant normalization on the multimodel ratification packet path: required participants must stay aligned to the canonical required set `[claude-opus-4-7, gpt-5.5, deepseek-v4-pro, mimo-v2.5-pro]`, while `gemini-3.1-pro-preview` remains optional and must never replace a required participant in plan files, vote expectations, or manifest counts.
- Why included: `quorum.yaml` and `brain_task_orchestrator.py` already define that required/optional split, while the failed certification artifact shows participant mismatch rather than a missing parent capability patch: the manifest reports missing expected approvals, the parent records `missing_required_model_consulted:mimo-v2.5-pro` plus unexpected Gemini participation, and the three successful planner outputs all classify the state as `no_action` with only `noop` patches.

Excluded/deferred candidates:
- Parent taskpool intake / P1-P2-P3 / dependency-order feature changes: excluded; current evidence already grounds the parent decomposition, one-shot landing gate, and lane-preservation behavior.
- Gate relaxation, threshold lowering, or verifier shortcuts that would certify with missing required participants: excluded; they hide the packet mismatch instead of normalizing it.
- Treating planner noop entries as substantive implementation deltas: excluded; they are evidence that no additional parent-scope patch is justified from this packet.
- Mimo availability debugging beyond participant normalization: deferred to fallback-threshold or quota-observability if a rerun still cannot collect a required Mimo vote.
- Gemini transport support under Codex ChatGPT: deferred; it is optional for parent certification once required participants are normalized.

Validation evidence:
- `~/.hermes/config/quorum.yaml` defines required ratification models as `claude-opus-4-7`, `gpt-5.5`, `deepseek-v4-pro`, `mimo-v2.5-pro`, with Gemini optional.
- `~/.hermes/scripts/brain_task_orchestrator.py` mirrors the same defaults in `DEFAULT_REQUIRED_RATIFICATION_MODELS` / `DEFAULT_OPTIONAL_RATIFICATION_MODELS`.
- `/Users/charles/.hermes/tick-20260519-033213-033607-p97711-eed21c74-be8dd337/final/certification_manifest.json` fails on participant/signature mismatch, not feature-patch absence.
- `/Users/charles/.hermes/tick-20260519-033213-033607-p97711-eed21c74-be8dd337/plans/{claude-opus-4-7,gpt-5.5,deepseek-v4-pro}.json` all emit `noop` patches; Gemini plan is only a failed adapter placeholder.
- Narrowed brief artifact written to `/Users/charles/.hermes/kanban/workspaces/t_419a3e8e/patch-normalization-narrowed-brief.md`.

Next handoff:
- Repair participant-source normalization / manifest accounting on the ratification packet path.
- Re-run parent certification with the canonical required participant set.
- If required-participant collection still fails, continue with fallback-threshold or quota-observability follow-up instead of reopening the parent feature scope.

- 2026-05-19T18:21:23+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun`. Reason: auto-claim-and-handoff

- 2026-05-19T18:21:40+08:00: Lifecycle transition `claimed` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-19T18:21:40+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-19T18:25:56+08:00: Multimodel PUA-loop round `advisory_passed`. Gate `PASS_ADVISORY_ONLY`, decision `CONTINUE_LOOP`. Discussion `/Users/charles/.hermes/tick-20260519-102141-109482-p21121-235d4778-532b0753/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T18:25:56+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-102141-109482-p21121-235d4778-532b0753/discussion_result.json

- 2026-05-19T18:26:17+08:00: Lifecycle transition `review` -> `done` by `hermes`. Reason: manual_blocked_triage_review_close_after_structured_evidence_and_advisory_gate Evidence: proof:sha256:933dafcde85ddd7f89cf5b504280eba1b119a84b9e61cfcd12e41f971c341c8b, command: multimodel-intervention-step gate=PASS_ADVISORY_ONLY decision=continue_loop artifact=/Users/charles/.hermes/tick-20260519-102141-109482-p21121-235d4778-532b0753/discussion_result.json
