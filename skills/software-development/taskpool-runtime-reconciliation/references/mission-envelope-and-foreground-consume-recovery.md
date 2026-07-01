# Mission-envelope and foreground consume recovery

Session-derived checklist for governed taskpool drain/progress work.

## Dispatch blocked by boundary invalids

If `parallel-dispatch-dry-run` or `boundary-check` fails with `mission_envelope_missing` or `evolution_architecture_alignment_missing`, do not bypass the boundary gate. Repair the task note's structural contract first, then re-run `selfcheck` / `boundary-check`.

Minimum safe repair pattern:
- Add/normalize `architecture_target` to one of the orchestrator's known architecture targets.
- Add `anti_drift_check`, not just `capability_delta` / `acceptance_evidence`.
- Fill mission-envelope fields: `mission_schema_version`, `mission_id`, `mission_title`, `mission_objective`, `mission_constraints`, `evidence_refs`, `acceptance_criteria`, `dag_nodes`, `checkpoint_states`, `permission_gates`, `handoff_artifacts`, `proof_artifacts`, `rollback_signal`, `certification_status`, `ratification_artifact`.
- Structured refs must use the taskpool evidence vocabulary (`proof:...`, `artifact:...`, `file:...`, `command:...`, `url:...`). Plain placeholders like `pending` can still fail as `*:structured_ref`; use explicit placeholders such as `proof:ratification-pending`, `proof:handoff-pending`, and `proof:implementation-proof-pending`.
- Re-run `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`; require `status=PASS` and `boundary.invalid_count=0` before dispatch.

Anti-condition: mission-envelope repair only fixes structural dispatch eligibility; it is not delivery proof and must not be used to mark a task done.

## Foreground consume timeout / orphaned running claim

A manually foregrounded `agent_team_controller.py consume-claimed ...` can outlive the controlling terminal timeout and leave a task in `running` even when the worker registry reports no alive job. Treat it like an orphaned active claim, not as completion.

Before release, prove no live owner:
1. `agent_team_controller.py worker-jobs --json` -> `alive_count=0` or no job containing the task.
2. `brain_task_orchestrator.py multimodel-intervention-jobs --json` -> `alive_count=0` or no job containing the task.
3. Process text has no owner for the task id/run id (`agent_team_controller`, `team-worker`, `hermes -p`, `multimodel_intervention`, `brain_task_orchestrator.py transition`, `parallel-claim-and-handoff`).
4. `taskpool_escape_guard.py --json` has no active human escape / post-ack terminal blocker.

Then release to `retry` only, with explicit evidence in the reason, e.g. `reconcile orphaned running claim: foreground consume-claimed command timed out; worker-jobs alive=0; multimodel alive=0; no process owner; release to retry only, no completion`.

After release: run `reconcile --write --promote-due-retry`, `auto-close-review`, `auto-subtask-sync`, `blocked-resolve-step`, then re-read counts before any new dispatch.
