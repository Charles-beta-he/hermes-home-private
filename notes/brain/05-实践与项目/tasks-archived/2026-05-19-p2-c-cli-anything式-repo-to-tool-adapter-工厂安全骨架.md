---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1 detect repo surfaces; 2 generate dry-run adapter spec; 3 permission schema; 4 smoke test wrappers"]
created: 2026-05-19T13:40:37+08:00
updated: 2026-05-19T22:50:36+08:00
expires_at: 2026-06-18T13:40:37+08:00
project: local-brain
architecture_target: local-brain
capability_delta: Hermes can turn external repos into governed dry-run CLI/tool adapter specs instead of ad hoc shell calls.
anti_drift_check: Do not generate unrestricted shell passthrough; generated wrappers default read-only/dry-run and require explicit permission for writes.
acceptance_evidence: repo_to_tool_adapter emits safe spec for a local repo and refuses dangerous passthrough mode.
workflow_contract: "[08-模板/task-workflow-contract-template]"
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
multimodel_triage_result: "P2/evolution: high leverage but must wait for proof/telemetry substrate; no immediate multimodel certification needed for scaffold."
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: /Users/charles/.hermes
parallel_boundary: Parallelizable after P1-A/P1-B skeletons; no Workspace credentials involved.
evidence:
  - proof:next_reconcile_selected_dispatchable_p2_evolution_repo_to_tool_adapter
  - proof:starting_safe_scaffold_implementation_for_repo_to_tool_adapter
  - artifact:/Users/charles/.hermes/scripts/repo_to_tool_adapter.py
  - proof:repo_to_tool_adapter_emits_dry_run_spec_for_hermes_agent_repo
  - proof:dangerous_passthrough_refused_with_status_REFUSED_exit_2
  - proof:sha256:21045044b7819e991986cb02b2b1f3b6b7eef3b7b43ca383ef50bef3c0c73a8d
concepts: ["task", "hermes", "autonomous-workflow-execution"]
---

# Task - P2-C CLI Anything式 repo-to-tool adapter 工厂安全骨架

## Objective

Implement CLI Anything-style safe repo-to-tool adapter scaffold.

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `next --reconcile --json` | PASS | selected this task as highest priority dispatchable evolution item. |
| `python3 ~/.hermes/scripts/repo_to_tool_adapter.py --repo /Users/charles/.hermes/hermes-agent --name hermes_agent_local` | PASS | emitted `/tmp/repo_to_tool_adapter_spec.json` with `status=OK`, `mode=dry-run-spec`, read-only permissions, `shell_passthrough=refused`, repo surface, and generated dry-run operations. |
| `python3 ~/.hermes/scripts/repo_to_tool_adapter.py --repo /Users/charles/.hermes/hermes-agent --passthrough` | PASS | refused dangerous passthrough with JSON `status=REFUSED`, `code=dangerous_passthrough_refused`, exit code 2. |
| `python3 -m py_compile ~/.hermes/scripts/repo_to_tool_adapter.py` | PASS | syntax guard only; not used as sole delivery evidence. |

## Proof Log

- 2026-05-19T13:40:37+08:00: Task created from local-brain control point.
- 2026-05-19T22:09:00+08:00: Implemented `/Users/charles/.hermes/scripts/repo_to_tool_adapter.py`, a dry-run JSON spec generator that inspects local repo readmes/manifests/directories, reports but does not read secret-like top-level names, emits read-only permissions by default, and hard-refuses unrestricted shell/passthrough flags before parsing normal arguments.
- 2026-05-19T22:09:00+08:00: Real-link validation ran against `/Users/charles/.hermes/hermes-agent`; read-back assertions verified `status=OK`, `mode=dry-run-spec`, read-only policy, `shell_passthrough=refused`, repo name, and generated operations. Dangerous passthrough validation returned `status=REFUSED`, `code=dangerous_passthrough_refused`, exit code 2.

## Blockers / Confusions

- None for scaffold review. Remaining downstream work: review before registering any executable Hermes tool wrapper; no wrapper has been auto-registered.

## Final Handoff

- Status: ready for review, not auto-done.
- Evidence: `/Users/charles/.hermes/scripts/repo_to_tool_adapter.py`; `/tmp/repo_to_tool_adapter_spec.json`; `/tmp/repo_to_tool_adapter_refusal.json`; smoke assertions above.
- Residual risk: scaffold only emits specs; future executable wrapper registration still needs explicit review/permission gating.

- 2026-05-19T22:08:13+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-follow-through`. Reason: follow_through_selected_highest_priority_dispatchable Evidence: proof:next_reconcile_selected_dispatchable_p2_evolution_repo_to_tool_adapter

- 2026-05-19T22:08:13+08:00: Lifecycle transition `claimed` -> `running` by `hermes-follow-through`. Reason: bounded_evidence_tranche_start Evidence: proof:starting_safe_scaffold_implementation_for_repo_to_tool_adapter

- 2026-05-19T22:09:45+08:00: Lifecycle transition `running` -> `review` by `hermes-follow-through`. Reason: bounded_scaffold_evidence_ready_for_review_not_auto_done Evidence: artifact:/Users/charles/.hermes/scripts/repo_to_tool_adapter.py, proof:repo_to_tool_adapter_emits_dry_run_spec_for_hermes_agent_repo, proof:dangerous_passthrough_refused_with_status_REFUSED_exit_2

- 2026-05-19T22:50:36+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:21045044b7819e991986cb02b2b1f3b6b7eef3b7b43ca383ef50bef3c0c73a8d, proof:next_reconcile_selected_dispatchable_p2_evolution_repo_to_tool_adapter, proof:starting_safe_scaffold_implementation_for_repo_to_tool_adapter, artifact:/Users/charles/.hermes/scripts/repo_to_tool_adapter.py, proof:repo_to_tool_adapter_emits_dry_run_spec_for_hermes_agent_repo, proof:dangerous_passthrough_refused_with_status_REFUSED_exit_2
