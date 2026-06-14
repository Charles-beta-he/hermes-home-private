# Multimodel false-running and provider-quota recovery

Use when taskpool shows `status: running` / `claimed_by: hermes-multimodel`, but no actual multimodel worker is alive, or when `multimodel-intervention-step` / `multimodel-intervention-parallel-step` exits without a durable job.

## Failure signature

- `brain_task_orchestrator.py list --json` shows one or more tasks:
  - `status: running`
  - `claimed_by: hermes-multimodel`
  - `run_id: hermes-multimodel-*`
- `brain_task_orchestrator.py multimodel-intervention-jobs --json` shows the matching job:
  - `alive: false`
  - `log_path` exists but `log_size == 0`, or the job is missing from the jobs list
- `ps` has no live `multimodel-intervention-step`, `consult_models`, or matching `brain_task_orchestrator` process.
- Agent-team worker false-running has the analogous signature: `agent_team_controller.py worker-jobs --json` shows `alive_count=0` (or no matching live job for the active `run_id`), while the task remains `running` with `claimed_by: agent-team-controller` / `hermes-parallel`; the worker log may show `subprocess.TimeoutExpired` while transitioning `claimed -> running` before any proof was produced.
- Logs may show provider quota failures such as `HTTP 429` / `Gemini quota exhausted` from `google-gemini-cli`.

## Recovery sequence

1. Re-baseline before mutating:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json
ps aux | grep -E 'multimodel-intervention-step|consult_models|brain_task_orchestrator' | grep -v grep
```

2. For each false-running multimodel task with no live process and empty/missing job log, requeue to `pending` with structured evidence:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "$TASK_ID" \
  --to pending \
  --actor hermes-retry-recovery \
  --authority claim-and-handoff \
  --reason 'no_live_multimodel_worker_for_running_claim; async multimodel job exited with empty/missing log before writing certification; requeue pending instead of leaving false running' \
  --evidence "command:multimodel-intervention-jobs task=$TASK_ID job_id=$JOB_ID alive=false log_size=$LOG_SIZE" \
  --evidence "command:ps no live multimodel process for run_id=$RUN_ID" \
  --force --json
```

3. Run `reconcile --write`, `proof-check --json`, and `selfcheck --json` before re-dispatch. If proof fails because an evidence path is unstructured, fix the task note by keeping only structured evidence prefixes (`artifact:`, `command:`, `proof:`, etc.) before any further dispatch.

3a. For false-running agent-team worker claims, inspect the worker jobs/logs before mutating, then requeue only the affected running task with structured evidence (do not mark done):

```bash
python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "$TASK_ID" \
  --to pending \
  --actor hermes-retry-recovery \
  --authority claim-and-handoff \
  --reason 'no_live_agent_team_worker_for_running_claim; worker exited or timed out before proof; requeue pending instead of leaving false running' \
  --evidence "command:agent_team_controller worker-jobs task=$TASK_ID alive=false log=$LOG_PATH" \
  --evidence "command:ps no live agent_team_controller/hermes worker process for run_id=$RUN_ID" \
  --force --json
```

4. If `multimodel-intervention-parallel-step` or a single `multimodel-intervention-step` immediately exits `-15` and no new durable job/log appears, inspect Hermes logs before retrying. If logs show provider quota exhaustion, do **not** keep spawning multimodel jobs; this will recreate false running claims and noisy empty logs.

4a. Before requeueing a running multimodel task, re-baseline immediately (fresh `list`, fresh `multimodel-intervention-jobs`, and `ps`). Do not requeue from a stale snapshot: a task can have `multimodel-intervention-jobs alive=0` while a live `consult_models.py` process is still running or a new event hook just spawned another worker. If the process is genuinely orphaned or not registered, stop the orphan first, then transition with event-hook multimodel spawning disabled:

```bash
pkill -f 'consult_models.py run .*taskpool-multimodel'  # only after matching the affected task/run_id
pkill -f 'brain_task_orchestrator.py multimodel-intervention-step'
HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1 \
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "$TASK_ID" \
  --to pending \
  --actor hermes-retry-recovery \
  --authority claim-and-handoff \
  --reason 'stopped_orphaned_or_false_running_worker; event-hook multimodel spawn disabled for recovery; requeue pending for later gated retry' \
  --evidence 'command:stopped orphan processes and disabled event hook multimodel spawn for transition' \
  --force --json
```

4b. If a task repeatedly re-enters false-running/autospawn after pending requeue and there is still no trusted registered worker/log, stop the loop by transitioning it to `blocked` with an explicit infra blocker instead of continuing to dispatch. This preserves fail-closed lifecycle and prevents a runaway event-hook loop:

```bash
HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1 \
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "$TASK_ID" \
  --to blocked \
  --actor hermes-retry-recovery \
  --authority claim-and-handoff \
  --reason 'infra_blocked: repeated false-running multimodel/autospawn loop with no live registered job; stop dispatch loop and require deterministic evidence/manual recovery before retry' \
  --evidence 'command:worker-jobs alive_count=0; multimodel-intervention-jobs alive_count=0; ps no live multimodel/consult process' \
  --force --json
```

5. If the task is advisory/evidence-intake and deterministic acceptance evidence already exists, it may be safer to move it to `review` with explicit quota-blocker evidence and then let `auto-close-review` decide through normal lifecycle gates:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition "$TASK_ID" \
  --to review \
  --actor hermes-deterministic-evidence \
  --authority budget-handoff \
  --reason 'bounded_intake_artifact_complete; multimodel advisory provider quota exhausted, so close to review with deterministic evidence rather than leaving false running' \
  --evidence 'artifact:/absolute/path/to/intake-or-proof.md' \
  --evidence 'command:proof-check PASS checked_count=N failures=0' \
  --evidence 'command:selfcheck PASS task_count=N failures=0 warnings=N' \
  --evidence 'command:multimodel-intervention-step provider_quota_blocked google-gemini-cli gemini-3.1-pro-preview HTTP_429' \
  --force --json

python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --json
```

Use this only when the task objective is evidence/design intake and no implementation, external write, or production deploy was promised. For certification-required implementation tasks, keep them `pending`/`blocked` until the provider/quorum issue is resolved.

## Interpretation rules

- `alive=false + log_size=0` is not a completed multimodel result; it is a false-running claim unless another artifact proves completion.
- A stale registry snapshot is not enough to mutate lifecycle: always cross-check fresh `ps` and fresh job state immediately before recovery transitions.
- Provider quota exhaustion is an infrastructure blocker, not evidence that the task failed substantively.
- Do not mark implementation tasks `done` using only proof/selfcheck/provider-quota evidence. Deterministic closeout is appropriate only for advisory tasks whose requested artifact already exists and is referenced.
- After cleanup, a healthy state may be `running=0` with `dispatchable>0`; if multimodel quota is exhausted, report that as the active blocker instead of repeatedly spawning jobs.
