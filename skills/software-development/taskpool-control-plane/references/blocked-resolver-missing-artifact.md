# Blocked resolver over-blocking on missing historical discussion artifacts

Use this when:
- `brain_task_dispatch_tick.py --summary --autorun-step --no-state` returns `ERROR`
- proof debt is already downgraded to tolerated warnings
- but `blocked-resolve-step` still fails the tick

## Symptom pattern

Observed runtime shape:
- `proof_check` = `FAIL` only because of historical done-task evidence debt
- `evidence_spine.gate_status` = `WARN`
- tick still returns `ERROR`
- direct `blocked-resolve-step --json` fails with:
  - `discussion artifact missing: /Users/.../.hermes/tick-*/discussion_result.json`

## Root cause

`command_blocked_resolve_step()` enriches blocked-task results with multimodel failure taxonomy.
That helper calls `load_discussion_artifact()`.

`load_discussion_artifact()` raises `SystemExit` when the path in
`multimodel_last_discussion_artifact` no longer exists.

Because the taxonomy helper originally only caught `Exception`, the `SystemExit`
escaped and aborted the entire blocked-resolve run, which in turn made the
dispatch tick fail closed even though the missing artifact was only historical
and diagnostic.

## Correct fix

Inside the taxonomy helper used by `command_blocked_resolve_step()`:
- catch `SystemExit` from `load_discussion_artifact()`
- continue with `{}` as discussion payload
- expose the message as `taxonomy_warning`

This preserves:
- blocked-task diagnosis
- fail-closed task certification semantics
- scheduler liveness for unrelated dispatchable work

## Expected post-fix behavior

- `blocked-resolve-step --json` returns `OK`
- blocked tasks remain blocked when certification is still not PASS
- missing historical artifact appears as `taxonomy_warning`
- dispatch tick returns `OK` and keeps advancing other eligible tasks

## Follow-up checks

1. `python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --max-tasks 5 --json`
2. `HERMES_LOCAL_BRAIN_AUTORUN=1 python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --autorun-step --no-state`
3. `python3 ~/.hermes/scripts/brain_task_orchestrator.py reconcile --write --promote-due-retry --json`
4. `python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json`

If step 2 is `OK` and step 4 resumes selecting the next task, the control-plane stall is fixed.
