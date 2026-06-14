# Unified execution-flow dispatch gate

Scope: taskpool dispatch planning when the unified Hermes/workflow/taskpool/harness framework is being connected to real scheduling surfaces.

Use when:
- `brain_task_orchestrator.py dispatch-dry-run` or equivalent scheduling code starts consuming an execution-flow/evidence gate.
- A task has missing harness/browser/API/build proof but is still pre-closeout and safe to execute.
- A task is at a human/permission/writeback/destructive boundary and dispatch artifacts must be suppressed.

## Contract

Taskpool remains the single source of truth. Workflow/evaluator output is a projection consumed by taskpool, not a second lifecycle store.

`dispatch-dry-run` may include an `execution_flow` packet and an `execution_flow_dispatch_decision`, but it must remain read-only:

- no claim
- no transition
- no done/closeout
- no adapter write
- no external side effect

## Decision rules

1. Missing evidence on pending / pre-closeout tasks is not a stop-work signal.
   - Treat missing `browser_or_ui_surface_proof`, API/curl proof, build/test proof, etc. as execution/harness requirements.
   - Keep dispatch allowed when the only blocker is pre-closeout evidence debt.
   - Put the gate packet into the execution prompt so the worker knows what proof must be produced.

2. Hard authority boundaries block dispatch in dry-run.
   - Examples: `permission`, `external_side_effect`, `destructive`, `credential`, `value_judgement`, `safety_legal`.
   - `workflow_stage: human_gate` blocks unconditionally, even if `boundary_class` is blank or `none`.
   - Review/writeback/done stages with a boundary also block dispatch.

3. Blocked dispatch responses must not contain actionable execution artifacts.
   - Suppress `claim_command`.
   - Suppress `execution_prompt`.
   - Suppress nested intervention plans such as `multimodel_intervention`; better, do not construct them on blocked paths.
   - Return only safe inspection/remediation fields such as `blocked_actions`, `safe_actions`, `execution_flow`, and `execution_flow_dispatch_decision`.

4. Normalize gate fields before comparing.
   - Strip whitespace and lowercase `workflow_stage`, `boundary_class`, and other enum-like status values before decision checks.
   - Add regression tests for mixed case and whitespace variants.

## TDD pattern

Add tests at the scheduling boundary, not only the evaluator helper.

Recommended RED cases:

- `dispatch-dry-run` returns `execution_flow` and `execution_flow_dispatch_decision` for the selected task.
- Pre-closeout missing proof remains `dispatchable=true` and the prompt includes execution-flow requirements.
- `workflow_stage: human_gate` returns `dispatchable=false` and omits `claim_command`, `execution_prompt`, and nested intervention plans.
- Hard boundaries are normalized and blocked: e.g. `boundary_class: " External_Side_Effect "`.
- Review/writeback/done stages with evidence/permission boundaries are blocked.

## Claim/handoff consumption rule

Scope: taskpool autorun claim/handoff, after eligibility selection and before any claim/handoff/proof-log mutation.
Applicability: use when `auto-claim-and-handoff` is about to mutate task state or create handoff artifacts.
Anti-condition: do not use this rule to block safe pre-closeout execution gaps; those remain dispatchable and become worker proof requirements.

`auto-claim-and-handoff` must run the execution-flow dispatch decision before write guard and before claim mutation:

- If `allowed_to_dispatch=false`, return `FAIL_CLOSED` with `claimed=false`.
- If the execution-flow dry-run/evaluator is unavailable or raises before a decision, fail closed with a structured no-mutation response; never fall through to claim/handoff just because the gate could not be computed.
- Do not call claim, do not create handoff files, and do not append autorun proof events.
- Return `execution_flow` and `execution_flow_dispatch_decision` when available so the operator can resolve the boundary.
- If allowed, preserve existing write-guard, claim, read-back, handoff, and proof-log gates.
- Regression tests for hard-boundary claim/handoff must assert all no-mutation evidence directly: `claimed=false`, task note unchanged, no `handoff` field in the payload, no autorun proof log, and no handoff markdown files under the autorun handoff directory.

## Closeout consumption rule

Scope: taskpool lifecycle closeout after the dispatch gate has allowed execution.
Applicability: use when a task is already in `review` and a caller attempts `review -> done`.
Anti-condition: do not use this rule to block initial `pending` dispatch or safe execution; before closeout, missing proof is a harness requirement, not a stop-work signal.

`lifecycle_gate(..., to_status="done")` must consume the same execution-flow proof semantics:

- Missing command/browser/API/read-back proof blocks closeout with `execution_flow_closeout_blocked:<missing_evidence>`.
- The failure must happen before task note mutation.
- Supplying the required structured proof allows the normal existing completion gate to continue.
- Closeout proof matching must trust only proposed `--evidence` and frontmatter evidence, not arbitrary task body placeholders or acceptance examples that merely contain `command:` / `proof:` strings.
- This gate is additive: it does not replace lane completion gates, multimodel certification gates, manual-review final-landed gates, autorun proof hash gates, or review-state requirements.

## Verification bundle

Before commit:

```bash
python3 -m py_compile ~/.hermes/scripts/brain_task_orchestrator.py ~/.hermes/scripts/test_brain_task_orchestrator.py
python3 -m pytest ~/.hermes/scripts/test_brain_task_orchestrator.py::test_execution_flow_dry_run_cli_projects_enterprise_gate_without_mutating_task \
  ~/.hermes/scripts/test_brain_task_orchestrator.py::test_dispatch_dry_run_consumes_execution_flow_without_stopping_safe_execution \
  ~/.hermes/scripts/test_brain_task_orchestrator.py::test_dispatch_dry_run_hard_execution_flow_boundary_has_no_actionable_prompt \
  ~/.hermes/scripts/test_brain_task_orchestrator.py::test_execution_flow_dispatch_decision_normalizes_hard_boundaries \
  ~/.hermes/scripts/test_brain_task_orchestrator.py::test_execution_flow_dispatch_decision_blocks_review_writeback_and_done_boundaries -q
python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
```

Run an independent final review after any post-review hardening, because reviewer suggestions change the certified diff.

## Pitfalls

- Do not treat missing harness proof as a reason to stop safe implementation work. It should stop closeout, not initial execution.
- Do not leave `claim_command` or executable prompts in blocked dry-run payloads. Some callers key off presence of those fields rather than `dispatchable`.
- Do not build nested multimodel/intervention plans after a dispatch-blocking decision; even hidden command strings can confuse downstream consumers.
- Do not broaden this into lifecycle mutation without a separate digest-bound authorization and read-back gate.
