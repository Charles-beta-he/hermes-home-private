# Stale claimed task + finished convergence subtasks

## Scenario

A real taskpool stall case had three layers:

1. One active task was stuck in `claimed` (`claimed_by: hermes-autorun`) even though no useful forward progress was occurring.
2. `eligibility-check --json` and `autorun-runner --json` returned `eligible=false` with reasons:
   - `autorun_disabled`
   - `no_dispatchable_task`
3. After clearing the stale claim and re-running a real dispatch tick, that task completed normally, and the pool collapsed to only two genuinely blocked multimodel parent tasks.

## Recovery recipe

1. Read the claimed task note and inspect:
   - `status`
   - `claimed_by`
   - `claim_expires_at`
   - recent lifecycle transitions in the body
2. Compare live time to `claim_expires_at`.
3. Search logs for the task id to determine whether the claim came from autorun, guardian cleanup, or multimodel worker activity.
4. If stale/wedged, requeue it:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition <task-id> \
  --to pending \
  --actor hermes \
  --authority budget-handoff \
  --reason manual_claim_cleanup_for_autorun_step_requeue \
  --force --json
```

5. Then run a real autorun tick:

```bash
HERMES_LOCAL_BRAIN_AUTORUN=1 \
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --autorun-step --no-state
```

## What success looked like

- The requeued task moved through `running -> review -> done`
- `auto_close_review` closed it successfully
- `post_autorun_dispatch` then reported no dispatchable local-brain tasks
- Remaining active work was only `blocked` multimodel tasks

## Important interpretation

`no_dispatchable_task` is not always proof that the pool is empty. It can mean the only candidate is wedged in `claimed` and needs stale-claim cleanup first.

## Parent/child insight from the same session

The two remaining blocked multimodel parents already had convergence subtasks.

For each parent, searching `auto_subtask_parent: <parent-id>` found three `done` subtasks:
- `quota_observability`
- `fallback_threshold`
- `relay_ordering`

Implication:
- If the parent is still `blocked`, do not create more narrowing subtasks by default.
- The real next step is usually parent-level evidence integration, targeted ratification repair, or human adjudication.
