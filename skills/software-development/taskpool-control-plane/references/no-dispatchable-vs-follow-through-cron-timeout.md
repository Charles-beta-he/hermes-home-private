# No-dispatchable taskpool vs follow-through cron timeout

## Trigger
Use when checking local-brain/taskpool status and the pool shows `claimed=0` / `running=0`, while one or more cron jobs related to follow-through or taskpool automation have recent `last_status=error`.

## Procedure

1. Treat `brain_task_orchestrator.py` canonical notes as the source of truth.
2. Run/read the primary no-agent path first:
   - `python3 ~/.hermes/scripts/taskpool_dynamic_runner.py --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py next --reconcile --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-check --json`
3. If the no-agent runner exits 0 with empty/silent output, `next=null`, `dispatchable=false`, and selfcheck/proof/boundary pass, classify the pool as **healthy no-dispatchable**, not stuck.
4. Separately inspect taskpool-related cron jobs. If an agent-based follow-through cron timed out during provider/API recovery, classify that as a cron/provider health problem, not as canonical taskpool wedging.
5. Report active `review` and `blocked` tasks with their closeout gates. Do not force a dispatch when `pending=0` and `dispatchable=0`.

## Interpretation rules

- `running=0` is only a problem when a concrete dispatchable task exists.
- A silent no-agent taskpool cron can be healthy: silence often means “nothing to do”.
- `proof-check` warnings about terminal/historical debt do not block unrelated dispatch when current `status=PASS` and boundary says the debt is terminal/unrelated.
- Agent-based follow-through jobs may be useful as advisory execution lanes, but they are not the canonical liveness signal when the no-agent dynamic runner is healthy.

## Anti-conditions

- Do not enable expensive/multimodel autorun just to make the dashboard show running work.
- Do not treat a provider/API timeout in a follow-through cron as evidence that taskpool claims are stale.
- Do not close `review` tasks as `done` unless their task-type-specific closeout evidence is present.
