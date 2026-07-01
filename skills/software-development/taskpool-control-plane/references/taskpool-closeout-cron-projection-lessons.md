# Taskpool closeout, cron, and projection repair lessons

Applicability: Hermes/local-brain taskpool maintenance when review/blocked tasks have already received implementation evidence but lifecycle closeout, cron health, or Kanban projection still disagree. Anti-conditions: do not use these steps to bypass credential entry, missing multimodel certification, destructive cleanup, or external publishing gates.

## Execution-flow closeout proof can be non-browser UI

The `execution_flow_closeout_blocked:browser_or_ui_surface_proof` gate is a UI-surface requirement, not literally always a browser requirement. For TUI/Desktop/voice work, valid evidence can be `proof:ui_surface`, `proof:ui`, `tui`, or `desktop` readback when backed by a real command/test/artifact. Do not force fake `proof:browser` strings for non-browser features.

Verification pattern:

1. Generate deterministic backend/API readback, e.g. status/profile/config report with blockers and providers.
2. Generate UI-surface readback, e.g. TUI gateway status response, desktop UI status, screenshot, or browser route as appropriate.
3. Store both in an artifact under `~/.hermes/evidence/` with a sha256.
4. Close review only through normal lifecycle transition and attach `command:*`, `proof:api_readback*`, and `proof:ui_surface*` evidence.

## Repair child tasks after parent closeout

When a repair child exists only to gather missing evidence for a parent review task:

- If the parent closes successfully with deterministic proof, that does not automatically make the repair child certified.
- If the repair child itself requires multimodel/T3 certification and the gate returns `FAIL/CONTINUE_LOOP`, do not force `done` just because the parent is done.
- Treat unresolved planner fan-out/quorum failures as a real certification boundary. Either find and rerun the failed planner/fanout evidence, or explicitly downgrade/isolate the child as advisory/uncertified with human authority.

Useful diagnostics:

- Read the child `multimodel_last_discussion_artifact` and inspect final-round votes, unresolved issues, and requested evidence.
- Search for cited `source_hash`/fanout failure records before deciding rerun vs downgrade.
- Keep the child `blocked` if the certifier says quorum is unmet and source failure records are unavailable.

## ContextCard no-agent cron stability

No-agent cron jobs are killed by the scheduler timeout (often ~120s). If a wrapper invokes a slow nested refresh:

- Keep nested timeout below scheduler timeout so the wrapper can emit/record structured JSON instead of being killed.
- Bound batch size for opportunistic refreshes; keep manual backfill override via env var.
- For opportunistic session-end refresh, preserve failure details in a log but fail-soft when authoritative production/fallback refresh jobs remain healthy.
- Avoid `set -e` around captured command substitution unless you intentionally want to skip logging on child failure; capture child exit code explicitly.

Example shell pattern:

```bash
set +e
OUTPUT="$(python3 watcher.py --refresh-timeout-seconds 105 --json)"
WATCHER_EXIT=$?
set -e
printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$OUTPUT" >> "$LOG_FILE"
STATUS="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("status","unknown"))' <<< "$OUTPUT")"
case "$STATUS" in
  error) printf '%s\n' "$OUTPUT"; exit "$WATCHER_EXIT" ;;
  refresh_failed) ;;  # fail-soft only for opportunistic refresh
esac
exit 0
```

## Kanban projection drift after task closeout

When source task notes transition to `done` but Kanban mirrors stay `blocked`, repair projection with `hermes kanban complete`. The CLI does not accept `--reason`; use `--result`, and if using `--summary`/`--metadata`, complete one task at a time.

Pattern:

```bash
hermes kanban complete <task_id> \
  --result 'source task is done; projection drift repair after governed taskpool closeout' \
  --metadata '{"repair":"blocked_projection_for_done_source","source_status":"done","task_id":"<task_id>"}'
```

Verify with `v_state.py --json`: `stale_projection_tasks=0`, `projection_drift_tasks=0`, and `kanban=1.0`.

## Final verification bundle

Before reporting closure, always read back:

- `brain_task_orchestrator.py selfcheck --json`
- `brain_task_orchestrator.py proof-check --json`
- `brain_task_orchestrator.py boundary-check --json`
- `brain_task_orchestrator.py list --json`
- `v_state.py --json`
- scoped `git status` and commit hash for code/evidence changes
