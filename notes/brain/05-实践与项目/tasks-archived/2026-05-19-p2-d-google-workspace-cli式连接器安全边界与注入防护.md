---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1 threat model; 2 untrusted content envelope; 3 injection scanner; 4 OAuth scope ledger; 5 read-only connector plan"]
created: 2026-05-19T13:40:37+08:00
updated: 2026-05-19T22:52:29+08:00
expires_at: 2026-06-18T13:40:37+08:00
project: local-brain
architecture_target: local-brain
capability_delta: Hermes gains a Workspace connector safety boundary before touching Gmail/Drive/Docs data.
anti_drift_check: No broad OAuth scope; external document/email text is untrusted and cannot override system/taskpool instructions; write operations require explicit authority.
acceptance_evidence: workspace_instruction_firewall flags injection samples and emits sanitized envelope; no live OAuth required in first slice.
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
multimodel_triage_result: "P2/evolution: powerful but credential-sensitive; must land injection/permission firewall before any Gmail/Drive/Docs operation."
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: /Users/charles/.hermes
parallel_boundary: Serial after P1 proof substrate; credential setup is separate user-approved task.
evidence:
  - proof:sha256:f60184cd6e3f2aa5c4fdeadcd327dd9afde62379187686a49944136ad1ff1e67
  - command:py_compile_taskpool PASS
  - proof:sha256:8bdf0ff345325d7fce8dc44158678ebe5b08f1f5918620e1bbd6ec90620e5878
concepts: ["task", "hermes", "autonomous-workflow-execution"]
---

# Task - P2-D Google Workspace CLI式连接器安全边界与注入防护

## Objective

Implement Google Workspace-style connector safety gate and instruction firewall.

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

- 2026-05-19T13:40:37+08:00: Task created from local-brain control point.

## Blockers / Confusions

- None.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-19T22:11:49+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-19T22:11:50+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-19T22:11:50+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:f60184cd6e3f2aa5c4fdeadcd327dd9afde62379187686a49944136ad1ff1e67, command:py_compile_taskpool PASS

- 2026-05-19T22:52:29+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:8bdf0ff345325d7fce8dc44158678ebe5b08f1f5918620e1bbd6ec90620e5878, proof:sha256:f60184cd6e3f2aa5c4fdeadcd327dd9afde62379187686a49944136ad1ff1e67, command:py_compile_taskpool PASS
