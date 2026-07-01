# Advisory-8 no-next-step closeout pattern

Use when a user asks to keep pushing the taskpool/advisory lane until there is no safe next step, especially after raising `taskpool.max_parallel_agents` or trying to stabilize 8-way advisory concurrency.

## Objective model

Success is not always `readiness=PASS`. The safe closeout condition is:

- quota gate is current and PASS, or exact blockers are identified;
- handoff backlog gate is below threshold or its archive action has been attempted/read back;
- stale claims are zero, or stale/orphan claims have been reconciled with evidence;
- bounded autorun has been attempted when dry-run shows eligible selected tasks;
- remaining blockers are classified as real supply/boundary/quality constraints, not unexplored execution work.

## Recommended loop

1. Read current state:
   - `python3 scripts/agent_team_controller.py worker-jobs --json`
   - `python3 scripts/brain_task_orchestrator.py list --json`
   - `python3 scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 8 --lane advisory --json`
   - `HERMES_TASKPOOL_API_CACHE=0 python3 scripts/brain_task_dispatch_tick.py --summary --print-always --no-state --archive-handoffs`

2. Refresh quota evidence before treating API blockers as real:
   - exact providers: run the provider probe, e.g. `python3 scripts/model_quota.py probe --deepseek --json`.
   - documented no-header providers: run a live smoke that records successful no-header evidence, e.g. `python3 scripts/multi-model-smoke.py --model gpt-5.5 --timeout 180 --repeat 1 --route taskpool-final-verify`.
   - verify: `python3 scripts/model_quota.py confidence-gate --json --model gpt-5.5 --model claude-opus-4-8 --model deepseek-v4-pro`.

3. Drain only when dry-run shows eligible selected tasks:
   - If `parallel-dispatch-dry-run` or tick shows `selected_count > 0`, run a bounded autorun:
     `python3 scripts/brain_task_dispatch_tick.py --summary --parallel-autorun --no-state --max-agents 8`.
   - Wait briefly, then read `worker-jobs`, `list`, and tick again.
   - Do not blindly repeat autorun when `selected_count=0`; that creates noisy handoffs and no extra work.

4. Reconcile orphan active state carefully:
   - If `worker-jobs alive_count=0` but tasks remain `running`/`claimed`, verify there is no matching live process for the recorded worker/run.
   - Use the lifecycle command, not manual file edits:
     `python3 scripts/brain_task_orchestrator.py release '<task-id>' --actor hermes-final-verify --to-status retry --reason '<evidence-grounded reason>' --force --json`.
   - Re-read the pool immediately after release. Only release tasks that are truly orphaned; do not release live workers just because readiness is failing.

5. Run closeout/resolver gates, but respect fail-closed results:
   - `python3 scripts/brain_task_orchestrator.py auto-close-review --authority autonomous-execution --max-tasks 20 --actor hermes-final-verify`
   - `python3 scripts/brain_task_orchestrator.py blocked-resolve-step --authority autonomous-execution --max-tasks 50 --json`
   - If closeout skips with missing proof classes, report that as a gate, not a failure to force.

## Stop condition / no safe next step

Stop and report a boundary/supply blocker when all are true:

- `worker-jobs alive_count=0` or remaining live jobs are acknowledged as still running;
- `stale_claim_count=0`;
- quota confidence `PASS` and `soft_unknown_count=0`;
- handoff backlog gate count is below threshold;
- dry-run/tick shows `selected_count=0` or only a small bounded selection that has already been consumed;
- remaining readiness blockers are `projected_active_count_below_requested`, `resource_ceiling_below_requested`, `quality_slots_below_requested`, or `boundary_warnings_present` with `capacity_diagnostics.top_limiting_boundaries` pointing at repeated boundaries.

At that point the next step is a separate boundary split/reclassification governance slice, not more autorun. Do not auto-split boundaries: that changes task isolation semantics and can break parallel safety.

## Anti-conditions

- Do not store or report transient stale quota as durable; refresh first.
- Do not continue a claim/autorun loop solely to chase 8 active workers when diagnostics show boundary diversity is the limiting factor.
- Do not mark review tasks done or weaken proof gates to improve readiness.
- Do not directly edit task markdown/status files for lifecycle state; use orchestrator commands and read back.
