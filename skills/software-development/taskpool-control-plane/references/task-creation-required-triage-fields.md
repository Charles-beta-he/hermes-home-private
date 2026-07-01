# Taskpool add required triage fields

When adding tasks through `brain_task_orchestrator.py add`, do not hand-write Markdown if the CLI rejects the payload. The add path is the governance boundary and may require explicit metadata.

## Pitfall

If the command returns:

```text
task creation requires explicit priority/dependency/triage metadata; missing=['priority_layer', 'dependency_order', 'multimodel_triage_result']
```

retry with the missing fields instead of bypassing the CLI.

## Minimal retry fields

- `--priority-layer <P0|P1|P2|P3>`: mirror the intended priority unless there is a reason to separate scheduling layer from priority.
- `--dependency-order '<ordering / predecessor / boundary statement>'`: say what must happen before the task and what must not happen until after it.
- `--multimodel-triage-result '<triage note>'`: record whether multimodel review is required now, deferred, or unnecessary until promotion.

## Social/advisory intake example

For a single social post that is evidence/inspiration rather than implementation proof:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py add \
  --priority P2 \
  --priority-layer P2 \
  --dependency-order 'after evidence capture; before any dashboard write-action implementation' \
  --multimodel-triage-result 'single-source inspiration intake; no multimodel required until prototype design review or implementation promotion' \
  --lane advisory \
  --architecture-target taskpool \
  --truth-gate 'social-post-is-inspiration-not-proof; verify against Hermes current taskpool model before implementation' \
  ...
```

## Batch external-source intake

When creating many advisory/evidence tasks from one parsed feed, PH backfill, social/media intake, or repo-candidate list:

- Use one shared evidence artifact as `--evidence-bundle`, but give every task a unique `--parallel-boundary` that includes the source/task slug. Reusing the same free-text boundary across the batch can trigger `parallel_boundary_conflict` in selfcheck even when the tasks are independent.
- Keep these tasks advisory unless explicitly promoted: `--lane advisory`, `--workflow-stage evidence`, `--completion-boundary taskpool_candidate`.
- Acceptance should require repo/source readback, capability mapping, risk/low-coupling check, and a prune-or-promote decision.
- Verify after batch add with `brain_task_orchestrator.py list --json` and `brain_task_orchestrator.py selfcheck --json`; do not claim done until `boundary.invalid_count == 0` and no newly introduced boundary warnings remain.
- Detailed checklist: `references/batch-external-source-intake-parallel-boundaries.md`.

## Anti-conditions

- Do not promote a social post directly into production code changes.
- Do not weaken lifecycle, permission, or evidence gates to make a task dispatchable.
- Do not store one-off URLs or session status in global memory; keep source facts in scoped evidence notes or task metadata.
