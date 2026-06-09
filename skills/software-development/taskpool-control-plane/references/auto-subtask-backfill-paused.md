# Auto-subtask backfill while pause-gated

Use when a blocked parent already has finished `auto_subtask_children`, but multimodel non-convergence has already tripped the economy gate.

## Problem shape
- Parent has `auto_subtask_ready_for_parent: true`
- Child notes are `done`
- Prior logic would reopen parent to `pending`
- `multimodel-intervention-dry-run --json` still says `economy_gate.action: pause`

This combination is dangerous: evidence integration is correct, but reopening makes the parent look dispatchable even though policy says human review / targeted evidence fix only.

## Safe pattern
1. Build a parent `## Auto-subtask Backfill` section with one line per child:
   - child link
   - `auto_subtask_axis`
   - child `status`
   - child multimodel gate / status
2. Mirror the relationship into parent `evidence:` entries:
   - `artifact:<child-note-path>`
   - `child-task:<child-id>:status:done`
   - `child-axis:<axis>:<child-id>`
   - child discussion / ratification artifacts when present
3. Re-check the economy gate on the parent before reopening.
4. If gate action is `pause`, keep:
   - parent `status: blocked`
   - `blocked_resolve_last_action: auto_subtask_backfill_paused`
   - `blocked_resolve_reason` aligned to the gate reason
5. Append proof log text that child evidence was backfilled but reopen was intentionally suppressed by the pause gate.

## Verification
- `reconcile --write --json` should either:
  - reopen to `pending` only when gate allows, or
  - emit a paused/backfilled action while leaving the task blocked
- `dispatch-dry-run --json` must not show the paused parent as dispatchable
- `multimodel-intervention-dry-run --json` should place it in `paused_plans[]`
- task note should show `## Auto-subtask Backfill`

## Why this matters
Without this guard, the control plane can regress from a correct fail-closed state into a false-positive pending task, causing repeated useless dispatch attempts on work that policy already paused.