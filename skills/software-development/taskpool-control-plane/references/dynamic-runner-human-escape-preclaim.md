# Dynamic Runner Human-Escape Preclaim Pitfall

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Dynamic runner human-escape preclaim pitfall

If `taskpool_dynamic_runner.py` reports `human_escape_active_preclaim`, treat it as a successful preclaim no-op: no claim, no autorun, return OK with `claimed=false`, then verify via focused test and live no-op.

Recovery checklist after user/operator review:
1. Run `python3 ~/.hermes/scripts/taskpool_escape_guard.py --json` and inspect `post_ack_terminal_count`, `worker_timeout_count`, and `since_ack` failures/blocks.
2. If the user has explicitly authorized resuming and the rows are reviewed stale terminal envelopes, run `python3 ~/.hermes/scripts/taskpool_escape_guard.py --ack-reviewed --reason '<review receipt>' --json` and confirm `post_ack_readback.human_escape_triggered=false`.
3. Before rerunning dynamic dispatch, compare configured lane with live supply: `~/.hermes/config.yaml` `taskpool.parallel_dispatch_lane` versus `brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents N --json` selected/dispatchable lanes. A stale lane filter such as `advisory` with only `evolution` dispatchables makes autorun report `no tasks to claim` even while all-lane dry-run selects tasks.
4. If the lane filter is the blocker and the user authorized broad taskpool advancement, set `hermes config set taskpool.parallel_dispatch_lane all`, rerun dry-run, then run `taskpool_dynamic_runner.py` or `brain_task_dispatch_tick.py --parallel-autorun` and read back claimed/running worker jobs.
