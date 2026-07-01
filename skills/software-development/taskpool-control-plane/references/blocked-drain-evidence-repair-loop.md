# Blocked-drain evidence repair loop

Applicability: Hermes/local-brain taskpool sessions where the user authorizes safe draining of blocked tasks using pending child execution and targeted evidence repair. This is reusable control-plane procedure, not a record of one task's progress.

## Safe objective model

Blocked=0 is not a license to force completion. Treat each blocked row as one of:

- `await_auto_subtasks`: parent must wait for child evidence/briefs to close and sync.
- `keep_blocked_transient_retry_cap`: retry cap is protecting against infinite churn; create targeted repair evidence or wait for certification, do not reset blindly.
- `keep_blocked_missing_taxonomy_artifact`: historical discussion artifact may be pruned; fallback only to deterministic task-local signals like `multimodel_last_failures`, never invented evidence.
- `keep_blocked`: usually real certification/proof failure; split into targeted child tasks when the parent objective is still valid.
- claimed/running: verify worker ownership before reclaiming.

## Safe loop

1. Snapshot current state:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
   - `python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
2. Classify blocked rows by `blocked_resolve_last_action` and `blocked_resolve_reason`.
3. For `keep_blocked` caused by non-convergence/certification failure, create bounded repair children:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-split-non-convergence --task '<task-id>' --json`
4. Run the reversible drain cycle:
   - `auto-close-review --max-tasks <N> --authority autonomous-execution --json`
   - `auto-subtask-sync --write --actor <actor> --json`
   - `blocked-resolve-step --max-tasks <N> --authority autonomous-execution --actor <actor> --json`
   - `taskpool_dynamic_runner.py` or dispatch tick
   - wait for workers; repeat.
5. If `auto-close-review` skips a row, inspect failure reasons and either create a repair child or leave the task gated. Do not mark done from advisory/model agreement alone.
6. Stop with a DecisionPacket when remaining rows are real gates: active child execution, retry windows, transient retry cap, certification failure, or missing external proof.

## Pitfalls

- Advisory/evidence-intake tasks often mention UI/API/browser/contracts as subject matter. For `advisory-evidence-review-done`, the proof is deposited report/artifact evidence, not live UI/API readback, unless the task contract explicitly requires implementation.
- Auto-generated `non_convergence_narrowing` children are brief/evidence tasks. They should not inherit product implementation proof requirements like build/browser/curl/commit proof unless their own contract says so.
- `PASS_ADVISORY_ONLY` may support advisory closure but cannot authorize work-lane implementation closeout without task-specific implementation evidence.
- Historical discussion artifacts may be pruned. Fallback from `multimodel_last_failures` can classify axes for repair children, but it is not proof of task completion.

## Orphaned active-claim stall check

If dispatch reports `wait_for_running_or_claimed_completion` but progress stalls:

1. Check durable worker jobs: `agent_team_controller.py worker-jobs --json`.
2. Check multimodel jobs: `brain_task_orchestrator.py multimodel-intervention-jobs --json`.
3. Check processes with `ps` for `agent_team_controller.py`, `team-worker`, `hermes -p`, `multimodel_intervention`, or `brain_task_orchestrator.py multimodel`.
4. If no owner is alive and the claim lease is stale, reconcile to `retry`/`pending` with explicit evidence such as `command:ps_worker_jobs_no_alive_process_readback`.
5. If an owner is alive, wait/poll logs; do not steal the claim.

Never use orphan reconciliation to mark a task done. It only frees a stuck active slot for another proof-gated attempt.
