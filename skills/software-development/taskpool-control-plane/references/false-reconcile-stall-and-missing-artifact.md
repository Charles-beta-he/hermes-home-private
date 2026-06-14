# False reconcile stalls and missing historical artifact recovery

Use when the taskpool appears stalled with `next=null`, `eligibility-check` reports `reconcile_required`, or `blocked-resolve-step` exits on a missing `tick-*/discussion_result.json`.

## Failure signatures

1. False reconcile stall:
   - `reconcile --json` returns only `auto_subtask_progress_synced` for a blocked parent.
   - The action has `ready: false`, `missing_children: []`, and non-empty `open_children`.
   - `next --json` / `eligibility-check --json` reports `reconcile_required` even after `reconcile --write`.
   - `selfcheck` and `proof-check` pass, and no stale claims exist.

2. Missing historical artifact in blocked resolver:
   - `blocked-resolve-step --json` exits nonzero with `discussion artifact missing: .../tick-*/discussion_result.json`.
   - The affected task has `loop_non_convergence`, `CONTINUE_LOOP`, and no `auto_subtask_children`.
   - Taxonomy enrichment already catches missing artifacts, but the later auto-split branch re-loads the artifact and can still fatal.

3. Finished multimodel job left visible running state:
   - Task is `running`, `claimed_by: hermes-multimodel`, but `multimodel-intervention-jobs --json` has `alive_count: 0` and matching job `alive: false`.
   - Frontmatter shows failed/non-certified multimodel state (`multimodel_last_gate_status: FAIL`, `multimodel_status: not_certified`).

## Durable fix pattern

- Add a helper that classifies reconcile actions by whether they block dispatch. `auto_subtask_progress_synced` with `ready=false` and no `missing_children` is observability for an open-child blocked parent, not a canonical-write prerequisite. `next` and `eligibility-check` should use this helper instead of raw `action_count`.
- In `blocked-resolve-step`, if taxonomy payload contains a missing-artifact warning, do not enter `command_auto_split_non_convergence()` for that task. Keep it blocked with a structured action such as `keep_blocked_missing_taxonomy_artifact` and include `taxonomy_warning` in JSON output.
- If a multimodel job is no longer alive but the task remains `running` under `hermes-multimodel`, requeue with the owning actor and explicit evidence rather than waiting for the lease to expire:
  `transition <task> --to retry --actor hermes-multimodel --authority claim-and-handoff --reason manual_requeue_no_live_multimodel_job_after_failed_certification --evidence 'command:multimodel-intervention-jobs alive_count=0 matching_task_alive=false' --evidence 'command:multimodel_gate FAIL status_not_certified' --json`

## Regression tests to add

- Fixture where only a benign `auto_subtask_progress_synced` exists and there are no dispatchable tasks: `eligibility-check` should return `no_dispatchable_task`, not `reconcile_required`.
- Fixture where a blocked loop-non-convergence task points at a missing discussion artifact: `blocked-resolve-step` should return `status: OK`, `error_count: 0`, `kept_blocked_count: 1`, and a `taxonomy_warning` containing `discussion artifact missing`.

## Verification

After patching or manual recovery:

1. `python3 -m py_compile ~/.hermes/scripts/brain_task_orchestrator.py ~/.hermes/scripts/test_brain_task_orchestrator.py`
2. `python3 ~/.hermes/scripts/test_brain_task_orchestrator.py`
3. `python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --json` returns `status: OK` and `error_count: 0`.
4. `HERMES_LOCAL_BRAIN_AUTORUN=1 python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --autorun-step --no-state` or a scoped `--parallel-autorun` shows either a real claim/handoff or a clean `no_dispatchable_task`, not a false `reconcile_required` caused only by open-child progress sync.
5. `selfcheck --json` and `proof-check --json` remain `PASS`.
