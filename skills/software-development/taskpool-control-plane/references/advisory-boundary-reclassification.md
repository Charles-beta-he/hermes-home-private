# Advisory boundary reclassification governance

Use when advisory-lane 8 readiness is blocked by `boundary_warnings_present` / `parallel_boundary_conflicts_limit_selection` and quota, handoff backlog, stale claims, and hard blockers are already cleared.

## Objective

Increase advisory dispatch diversity without weakening lifecycle/proof gates or pretending task completion. This is only a dispatch-boundary governance slice.

## Safe command sequence

1. Baseline:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 8 --lane advisory --json
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --print-always --no-state --archive-handoffs
```

2. Generate read-only proposals:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-reclassify-step --lane advisory --max-tasks 20 --json
```

3. Apply only if proposals are safety-classified advisory read-only/parent-gap repair:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-reclassify-step --lane advisory --max-tasks 20 --write --json
```

4. Verify:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 8 --lane advisory --json
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --print-always --no-state --archive-handoffs
```

## Safety rules

- Reclassify only `pending`/`retry` `advisory` tasks.
- Refuse tasks with a concrete `workspace` or existing `workspace_isolation`.
- Parent repair tasks are grouped by `parent + gap` so two children that may mutate the same parent evidence record still conflict.
- Store rollback fields on every applied task:
  - `boundary_governance_original_parallel_boundary`
  - `boundary_governance_reason`
  - `boundary_governance_applied_at`
- This does not close tasks, does not lower proof requirements, and does not change status.

## Acceptance evidence

A successful slice should show:

- `boundary-check status=PASS`, invalid_count=0.
- Advisory `parallel-dispatch-dry-run` selected_count improves and boundary status moves to PASS or has fewer exact blockers.
- Dispatch tick no longer has `boundary_warnings_present` for advisory-8; remaining blockers, if any, are outside boundary governance such as quality slots/resource ceiling.
