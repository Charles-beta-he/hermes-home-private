# Advisory-lane scoped concurrency upgrade

Use this when taskpool global/work-first dispatch blocks a concurrency raise even though an advisory/evidence lane has safe independent work. This is a taskpool-control-plane pattern, not a general permission to raise all lanes.

## Applicability

Use when:
- `parallel-dispatch-dry-run` global selection is limited by work-first or lane preemption.
- Advisory/evidence tasks are independent enough to run in parallel.
- The target raise is bounded, local, reversible, and has multi-model/readback evidence.

Anti-conditions:
- Do not describe the result as global concurrency readiness.
- Do not use this to raise 6/8 or higher when resource, quality, API, provider-confidence, or projected-active gates are still fail-closed.
- Do not bypass boundary checks, stale-claim checks, or lifecycle proof gates.
- Do not let residual skipped boundary conflicts block a slice when selected/projected slots already satisfy the requested count; keep them as telemetry unless they reduce selected/projected capacity.

## Procedure

1. Establish the exact target:
   - Prefer wording like `advisory lane scoped 4 concurrency`.
   - Keep `work`, `evolution`, 6/8, external dispatch, deploy/push, destructive actions, and broad fan-out outside scope unless separately authorized and certified.
2. Read baseline state:
   - `brain_task_orchestrator.py list --json`
   - `agent_team_controller.py worker-jobs --json`
   - `brain_task_dispatch_tick.py --summary --print-always --no-state`
3. Prove lane-specific capacity without mutation:
   - `brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 4 --lane advisory --json`
   - Check selected lanes are all `advisory` and `boundary_readiness.status == PASS`.
4. Read readiness using projected active slots:
   - Treat `projected_active_count = active_count + selected_count` as the relevant sufficiency signal, not selected count alone.
   - Require `resource_ceiling >= 4`, `quality_slots >= 4`, `api_slots >= 4`, `stale_claim_count == 0`, and scoped boundary blockers empty.
5. If config writes are needed, prefer the official CLI instead of editing `~/.hermes/config.yaml` directly:
   - `hermes config set taskpool.max_parallel_agents 4`
   - `hermes config set taskpool.dynamic_max_parallel_agents 4`
   - `hermes config set taskpool.parallel_dispatch_lane advisory`
6. Verify config readback before real autorun:
   - `brain_task_dispatch_tick.py --summary --print-always --no-state`
   - Confirm `parallel_dispatch.lane_filter == advisory`, 4 readiness PASS, 6 readiness FAIL_CLOSED.
7. Run one bounded autorun only after the read-only gate passes:
   - `brain_task_dispatch_tick.py --summary --parallel-autorun --no-state --max-agents 4`
   - Confirm no subprocess timeout, no errors, and claimed/running tasks remain advisory-scoped.
8. Post-action readback:
   - `brain_task_orchestrator.py list --json`
   - `agent_team_controller.py worker-jobs --json`
   - another summary tick if needed.
   - Verify `claimed == 0`, `running <= 4`, all running lanes are `advisory`, worker jobs are alive or completed normally, and 6 remains fail-closed.

## Pitfalls

- `~/.hermes/config.yaml` may be write-protected by tool guards. Use `hermes config set` for security-sensitive config changes.
- A successful claim may be represented under `autorun.worker_trigger` rather than top-level `event_worker_trigger`; inspect nested fields before concluding no worker started.
- `claimed_tasks` may be summarized/omitted in high-level output; task list readback is the source of truth for `claimed`, `running`, lane, actor, and stale status.
- A PASS for advisory-scoped 4 is not evidence for global 4 or 6/8 readiness.

## Rollback

Use the config CLI:

```bash
hermes config set taskpool.max_parallel_agents 2
hermes config set taskpool.dynamic_max_parallel_agents 4
hermes config set taskpool.parallel_dispatch_lane all
```

Then run a summary tick and task list readback. Only release or transition stale/false-running tasks after proving they are stale; do not interrupt live workers merely because the config was rolled back.
