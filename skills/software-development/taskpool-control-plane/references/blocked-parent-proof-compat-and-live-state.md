# Blocked Parent Proof Compatibility and Live-State Repair

Use this when a blocked evolution parent is structurally healthy, but the control plane still misreports why it is blocked or `proof-check` fails on legacy evidence shapes.

## Failure signatures

1. `proof-check --json` fails on legacy child evidence entries such as:
   - `child-task:<id>:status:<status>`
   - `child-axis:<axis>:<id>`
2. Manual / human closeout gets forced through autorun proof-hash validation just because the task contains a historical `proof:sha256:...` entry.
3. `blocked-resolve-step --json` reports taxonomy reasons like `no_claims` even though the relevant convergence child is already `claimed` / `running` / `done`.
4. Parent or child notes point `multimodel_last_discussion_artifact` / `auto_subtask_parent_artifact` at a pruned `~/.hermes/tick-*/discussion_result.json` path.

## Durable repair pattern

### 1. Fix source-side evidence generation, not just historical tasks
When auto-subtask backfill writes parent evidence, prefer structured entries:
- `artifact:<child-note-path>`
- `proof:child-task:<id>:status:<status>`
- `proof:child-axis:<axis>:<id>`
- `classification:child_multimodel_gate=<status>` when needed

Do not keep generating bare `child-task:` / `child-axis:` items and then rely on debt cleanup later.

### 2. Keep proof-check compatible with legacy task debt
If historical tasks already contain bare `child-task:` / `child-axis:` evidence:
- accept them as legacy-compatible during `proof-check`
- emit warnings, not failures
- continue to prefer the new structured form for future writes

This preserves fail-closed behavior for real proof faults while preventing old shorthand from freezing the pool.

### 3. Narrow autorun audit detection
Do not infer "this task was auto-closed by autorun" merely because `evidence:` contains `proof:sha256:...`.

Safer rule:
- treat autorun proof-hash validation as mandatory only when the task has the explicit lifecycle marker
  - `Lifecycle transition `review` -> `done` by `hermes-autorun-review-close``

This avoids misclassifying manual/human closeout tasks that reused a proof hash as general evidence.

### 4. Repair stale artifact pointers before ratification triage
If the parent or children reference a missing `tick-*/discussion_result.json`:
- rebind the pointer to a real existing artifact or state file that is actually present
- update both the parent’s `multimodel_last_discussion_artifact` and any child `auto_subtask_parent_artifact` references that still point to the dead path

Goal: reduce the blocked state to the true remaining blocker (`open_children`, ratification debt, economy gate), not a dead filesystem pointer.

### 5. Overlay live child status onto taxonomy output
When `blocked-resolve-step` produces `axis_rationale`, merge in the current subtask state:
- remove stale `no_claims` for an axis that already has a child in `claimed` / `running` / `review` / `done`
- add status hints such as:
  - `child_status:pending`
  - `child_status:running`
  - `child_status:done`

This makes resolver output operationally truthful: the parent may still be blocked, but the reason becomes "waiting on real child convergence" rather than a stale multimodel taxonomy artifact.

## Interpretation rule

After these repairs, a blocked parent that still reports:
- `action = await_auto_subtasks`
- non-empty `open_children`
- no missing artifact warning

is a healthy fail-closed state, not a control-plane malfunction.

## Verification

1. `python3 -m py_compile ~/.hermes/scripts/brain_task_orchestrator.py`
2. `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
   - should PASS or downgrade legacy child shorthand to warnings
3. `python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --json`
   - should report real `open_children`
   - should no longer rely on missing tick-artifact paths
   - `axis_rationale` should reflect live child states instead of stale `no_claims`
4. `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - should remain PASS after the compatibility patch
