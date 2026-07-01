# Human-escape to bounded parallel progress

Use when taskpool is blocked by post-ack terminal envelopes or appears idle after recovery, but the user/operator has asked to inspect and assist progress.

## Applicability

- `taskpool_escape_guard.py --json` shows `human_escape_triggered=true` or post-ack terminal rows requiring review.
- Fresh canonical task list has no active `claimed`/`running` owner, or active owners are separately accounted for.
- `agent_team_controller.py worker-jobs --json` and `brain_task_orchestrator.py multimodel-intervention-jobs --json` show no live owner for the rows being released.
- Operator intent is bounded recovery/progress, not completion bypass.

## Anti-conditions

- Do not ack if terminal envelopes have not been reviewed or if a live worker/multimodel job still owns the target task.
- Do not convert FAILED/TIMEOUT envelopes into `done`.
- Do not treat a single idle dynamic-runner tick as proof the pool is empty; read dispatch dry-runs and canonical row counts.
- Do not autonomously advance excluded project lanes the user has scoped out; leave them pending unless explicitly authorized.

## Bounded sequence

1. Read breaker state:

```bash
python3 ~/.hermes/scripts/taskpool_escape_guard.py --json
```

2. Prove no live owner for the reviewed terminal rows:

```bash
python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
```

3. If reviewed and no live owner remains, ack with a reason that records the evidence shape, then immediately read back:

```bash
python3 ~/.hermes/scripts/taskpool_escape_guard.py --ack-reviewed --reason '<review receipt: rows reviewed, timeouts_now=0, worker alive=0, no active claimed/running; preserve proof/lifecycle/multimodel gates>' --json
python3 ~/.hermes/scripts/taskpool_escape_guard.py --json
```

Expected readback: `human_escape_triggered=false`, `post_ack_terminal_rows=[]`, and `since_ack.failures=0`/`blocks=0`.

4. Run deterministic cleanup before new dispatch:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py reconcile --write --promote-due-retry --actor hermes-cli-taskpool-progress --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --max-tasks 50 --authority autonomous-execution --actor hermes-cli-taskpool-progress --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-subtask-sync --write --actor hermes-cli-taskpool-progress --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --max-tasks 50 --authority autonomous-execution --actor hermes-cli-taskpool-progress --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-reclassify-step --lane all --max-tasks 100 --write --json
```

5. If the normal/single dynamic runner reports no dispatchable task, compare with explicit dry-runs before stopping:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 4 --json
```

If `dispatch-dry-run` says reconcile is required, run reconcile again. If `parallel-dispatch-dry-run` has `dispatchable=true` and `selected_count>0`, a bounded explicit parallel autorun can claim safe slots:

```bash
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --print-always --parallel-autorun --max-agents 4 --review-close-max-tasks 50 --event-next-tick-depth 1
```

6. Read back instead of claiming completion:

```bash
python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
```

Completion evidence is one of:
- alive worker owns the claimed tasks and canonical rows are `running`/`claimed` with fresh `claim_expires_at`; or
- worker exited and rows moved to `review`/`blocked`/`retry`/`done` under normal lifecycle gates.

## Pitfall: single autorun idle vs parallel dry-run progress

`taskpool_dynamic_runner.py` may use `--autorun-step` when `dispatch_mode=single`. A single-lane tick can return `idle_no_dispatchable_task` while `parallel-dispatch-dry-run` would select boundary-safe tasks. In an operator-authorized recovery session, do not stop at the single-lane idle result; run explicit parallel dry-run and, if safe slots exist, the explicit `--parallel-autorun` command above.
