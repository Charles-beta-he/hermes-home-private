# Taskpool drain/reconcile patterns

Applicability: use when a Hermes/local-brain taskpool drain loop stalls with `blocked` remaining, apparent `claimed`/`running` rows, retry backoff, or `human_escape_active_preclaim` during authorized local taskpool advancement.

Anti-conditions:
- Do not use this to mark tasks done.
- Do not bypass proof, lifecycle, browser/UI/API readback, multimodel, or evidence gates.
- Do not reclaim active tasks when a live worker/multimodel job or process still owns the task.
- Do not preserve session progress here; re-read live taskpool state every time.

## Canonical safe drain loop

1. Snapshot first:
   - `brain_task_orchestrator.py list --json`
   - `agent_team_controller.py worker-jobs --json`
   - `brain_task_orchestrator.py multimodel-intervention-jobs --json`
   - summarize counts, `claimed`/`running`/`retry`, and `blocked_resolve_last_action` buckets.
2. If live workers exist, wait for them before reclaiming anything. Poll jobs and task state after the wait.
3. If no live worker/multimodel/process owns a `claimed`/`running` task, reconcile it to retry/over-retry with evidence; never mark done.
4. Run the local gated loop:
   - `auto-close-review --max-tasks ... --authority autonomous-execution --json`
   - `reconcile --write --promote-due-retry --actor <actor> --json`
   - `auto-subtask-sync --write --actor <actor> --json`
   - `blocked-resolve-step --max-tasks ... --authority autonomous-execution --actor <actor> --json`
   - dispatch via `taskpool_dynamic_runner.py` or `brain_task_dispatch_tick.py --summary --parallel-autorun --no-state --max-agents N`
5. Repeat until either blocked decreases, new workers launch, or remaining rows are true evidence/certification gates.
6. Finish with `py_compile`, `selfcheck`, counts/jobs readback, and explicit remaining boundary.

## Orphaned active claim reconciliation

A task in `claimed` or `running` is only orphaned when all owner channels are negative:
- `agent_team_controller.py worker-jobs --json` has no live job containing the task id;
- `brain_task_orchestrator.py multimodel-intervention-jobs --json` has no live job for the task;
- `ps`/process text has no matching task id or run id.

Safe action:
- move to `retry` (or over-retry configured status) with evidence such as `command:reconcile_orphaned_active_claim_no_live_owner`;
- clear `claimed_by`, `claim_expires_at`, and `run_id`;
- never mark done or review solely from missing process ownership.

Pitfall: if a task appears stale in task metadata but worker-jobs or multimodel job registry is alive, do not reclaim. Let the worker finish or time out, then re-read.

## Human escape guard during drain

If dispatch reports `human_escape_active_preclaim`, do not treat it as a task failure. It means the escape guard blocked new claims because post-ack terminal worker envelopes exist.

Safe recovery:
1. Run `taskpool_escape_guard.py --json` and inspect `post_ack_terminal_count`, `worker_timeout_count`, `since_ack`, and the terminal rows.
2. If the operator/user has authorized continued local drain and the rows are stale/failed worker envelopes, acknowledge with `taskpool_escape_guard.py --ack-reviewed --reason '<receipt>' --json`.
3. Confirm readback has `post_ack_readback.human_escape_triggered=false`.
4. Resume dispatch; preserve all proof/lifecycle gates.

Do not ack if rows show unresolved external side effects, credential/payment prompts, or unreviewed destructive actions.

## Interpreting blocked buckets

- `await_auto_subtasks`: parent must wait for child evidence; create/execute targeted repair/narrowing children, not force parent done.
- `keep_blocked_transient_retry_cap`: retry cap is a safety boundary; prefer targeted evidence repair/certification child or human review.
- `keep_blocked`: inspect completion/multimodel failures; if deterministic taxonomy exists, split into child tasks; otherwise report the evidence boundary.
- `missing_taxonomy_artifact`: historical artifacts may be cleaned up; if task frontmatter carries deterministic failure/taxonomy fields, reconstruct axes from those fields instead of freezing forever.
