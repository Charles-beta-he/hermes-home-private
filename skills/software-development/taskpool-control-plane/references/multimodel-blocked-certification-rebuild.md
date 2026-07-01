# Multi-model blocked certification rebuild

Use when a taskpool task remains `blocked` because `multimodel_last_discussion_artifact` is missing or a previous T3 certification loop was pruned, but the user asks to continue the certification path rather than archive/terminal-advisory closeout.

## Applicability

- Active task is `blocked` and `blocked-resolve-step --authority dry-run` reports `discussion artifact missing` or `multimodel certification still not PASS`.
- The user authorizes the certification-rebuild path (not a forced `done`).
- Existing evidence/state files still identify the task and truth claims.

Anti-conditions:

- Do not treat `fanout_quorum_met`, `truth_status=grounded`, or `evidence_coverage=1.0` as enough to unblock if the task requires full ratification.
- Do not bypass required model/participant policy just because other models approve.
- Do not capture credential/auth failures as durable tool limitations; treat them as an external setup/authority boundary.

## Procedure

1. Read the task frontmatter fields:
   - `multimodel_last_state_path`
   - `multimodel_last_discussion_artifact`
   - `requires_multimodel`, `multimodel_last_gate_status`, `multimodel_round_status`, and `multimodel_last_failures`.
2. Check whether the old `tick-*` directory exists. If the tick directory exists but `discussion_result.json` is missing, use `consult_models.py resume-discussion <tick-dir>`. If the whole tick directory is gone, rerun from `multimodel_last_state_path`:
   - `python3 ~/.hermes/scripts/consult_models.py run --tier T3 --discussion --max-rounds 2 --timeout 180 --keep <state.json>`
3. Inspect both artifacts:
   - `<tick>/discussion_result.json`
   - `<tick>/final/certification_manifest.json`
4. Stamp task binding before evaluating/writing back. The ratification gate is fail-closed on missing target binding. Use the orchestrator's `stamp_discussion_task_binding()` semantics or the normal `multimodel-intervention-step` path when available. Binding metadata must include task id, task path, state path, and state hash.
5. Run the gate against the stamped discussion and write the result back to the task note. A FAIL writeback is still useful: it replaces stale/missing artifact references with the fresh artifact and clears the `discussion artifact missing` diagnostic.
6. Re-run:
   - `brain_task_orchestrator.py blocked-resolve-step --task <task> --authority dry-run --json`
   - `brain_task_orchestrator.py selfcheck --json`
   - `brain_task_dispatch_tick.py --summary --print-always --no-state`

## Interpretation

- If full ratification passes (`status=certified` / gate `PASS` / decision `LOOP_DONE`), the blocked resolver may move the task to review; normal auto-close gates still apply.
- If the rebuilt discussion has quorum/truth coverage but a required participant fails authentication or does not sign `best_within_constraints=true`, keep the task blocked. The next boundary is either fixing that participant's setup or running the governed participant-substitution workflow from the multi-model certification skill.
- If non-required/optional reviewers fail, check the current ratification policy before treating them as blockers.

## Evidence shape to report

Report separately:

- fanout quorum status;
- truth grounding / evidence coverage;
- discussion certification status;
- required participant approval coverage;
- current blocked resolver result.

This prevents the common mistake of saying “multi-model passed” when only fanout/truth passed but final ratification did not.
