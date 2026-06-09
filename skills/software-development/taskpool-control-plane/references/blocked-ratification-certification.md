# Blocked-resolve / ratification / certification convergence

Use this reference when local-brain taskpool has active tasks but `next=null` or no in-progress work because parent tasks are `blocked` with `multimodel_status: not_certified`.

## Goal-freeze rule

Before attempting unblock/certification, freeze the original parent objective. Capture at least:
- `title`
- `capability_delta`
- `acceptance_evidence`
- `anti_drift_check`
- `exit_criteria`
- `child_tasks`

Write the snapshot to a state artifact such as:

```bash
/Users/charles/.hermes/state/taskpool_blocked_resolution_frozen_objectives.json
```

Blocked-resolve, ratification, and certification must not shrink or rewrite the original goal. They may only add evidence, child tasks, ratification artifacts, or structured proof needed to demonstrate the frozen objective.

## Diagnostic sequence

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py eligibility-check --task "$TASK" --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py evidence-spine --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --include-active --json
```

Interpretation:
- `blocked` + `eligibility=false` + `reasons=["task_not_dispatchable"]` means do not claim directly.
- `next=null` with active blocked tasks means no dispatchable task exists until a child/gate path is created.
- `evidence-spine: PASS` can coexist with parent `not_certified`; proof/gate details still matter.

## Safe convergence sequence

1. Run blocked-resolve as dry-run first:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step \
  --task "$TASK" --actor hermes --authority dry-run --json
```

2. If unresolved and multimodel already triggered, check intervention state:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-dry-run --task "$TASK" --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-step --task "$TASK" --json
```

`action: no_intervention_needed` does not mean the task is certified. It usually means discussion was already triggered and the remaining work is evidence/child-axis convergence.

3. Try subtask sync before creating more work:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-subtask-sync --task "$TASK" --actor hermes --json
```

4. If the task is blocked by non-convergence, split missing axes:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-split-non-convergence --task "$TASK" --json
```

This can create new pending convergence subtasks, which should then be claimed normally.

5. Claim only newly dispatchable tasks:

```bash
NEXT=$(python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json | python3 -c 'import sys,json; print((json.load(sys.stdin).get("next") or {}).get("id", ""))')
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-claim-and-handoff --task "$NEXT" --actor hermes --json
```

6. Refresh and verify:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py evidence-spine --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
```

## Common blockers

- `multimodel_status: not_certified`: parent cannot be released until certification/rating evidence passes.
- `multimodel_gate: FAIL`, `CONTINUE_LOOP`, `certification_failed`, `certification_inconclusive`: requires further convergence, not direct state edit.
- `child-axis:unknown`: child task evidence is not structured enough for the parent gate.
- `child-task evidence` failures: child may be `done` but not `certified`; do not treat `done` or `advisory_completed` as certification.
- Missing historical `discussion_result.json`: automatic split may fail. Do not fabricate certification; either recover/rebuild the artifact or create explicit convergence subtasks with frozen-objective traceability.

## Pitfalls

- Do not manually change `not_certified` to `certified` to unblock a parent.
- Do not use `auto-claim-and-handoff` on blocked parents; claim only dispatchable child tasks.
- Do not change title/acceptance/capability fields to make gates pass. If the original task was too broad, preserve it and create child convergence work.
- If commands produce very large JSON, redirect to `/tmp/*.json` or use Python to summarize counters/status/gate fields.
