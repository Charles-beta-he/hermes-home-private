# Tool-loop convergence audit

Use when the user asks whether Hermes/tool-calling logic may regress into non-convergence, repeated retries, stale workers, or cron/taskpool wedges after a health/self-heal pass.

## Goal

Prove whether the current system has bounded execution and no live wedge. Do not rely on a prior green summary; check both code-level convergence boundaries and runtime state.

## Read-only evidence checklist

1. Main agent conversation loop
   - Inspect `agent/conversation_loop.py` for a bounded outer loop: `api_call_count < max_iterations` and `iteration_budget.remaining > 0`.
   - Verify retry/fallback paths are finite: API `max_retries`, fallback chain reset, length continuation cap, truncated tool-call retry cap, and bounded `max_relay_count` for auto-relay.
   - Confirm malformed/orphaned tool messages are repaired before API calls so the loop does not repeatedly send bad role alternation.

2. Tool executor
   - Inspect `agent/tool_executor.py` for concurrent worker limits (`_MAX_TOOL_WORKERS`), interrupt handling, periodic heartbeat during `concurrent.futures.wait`, and tool-result message emission for every tool call.
   - Confirm exceptions are converted into tool result errors rather than leaving missing tool responses.
   - Check whether there is a batch-level wall-clock timeout. If absent, report this as a residual risk, not as current failure.

3. Taskpool worker / agent-team controller
   - Inspect `scripts/agent_team_controller.py` for finite `model_chain` entries, per-provider subprocess timeouts, proof-stub timeout checkpointing, infra-failure fallback, and proof-gated `review -> done` behavior.
   - Confirm workers cannot mark tasks done directly; done remains lifecycle/proof-gated.
   - Check for no-output provider timeout classification. If only generic `TimeoutExpired` exists, report risk of slow retry/requeue, not hard deadlock.

4. Cron and scheduler state
   - Run diagnostics and list active cron errors. A healthy post-fix state should show cron-job-health with `0 error jobs`.
   - Treat `cron/jobs.json` scheduler fields (`repeat.completed`, `next_run_at`, `last_run_at`) as runtime churn. They can dirty git without proving code/config regression.

5. Live worker state
   - Query durable taskpool worker job files and validate PIDs with `ps` on macOS; do not trust old job JSON alone.
   - Check `agent_team_controller.py status --json` for `human_escape_triggered`, `RUNNING`, `timeouts`, `dispatchable_tasks`, `raw_n`, and `applied_n`.
   - Inspect recent `~/.hermes/logs/taskpool-workers/*.jsonl` tails for `worker_result`, `review_transition`, `blocked_transition`, `worker_timeout_checkpoint`, `missing_proof`, and infra fallback events.

## Verdict rubric

Report “currently converged” only when all are true:
- diagnostics pass and cron active errors are empty;
- no live worker PIDs remain unless expected and progressing;
- taskpool status has no stale RUNNING/claimed wedge, `human_escape_triggered=false`, and post-ack failures/blocks are zero;
- recent worker logs terminate in review/blocked/retry/checkpoint paths rather than silent partial logs;
- code-level loops have explicit iteration/retry/fallback caps.

Report residual risks separately from live blockers. Historical residual risks and landed gates:
- concurrent tool batches should have a hard wall-clock cap independent of individual tool timeouts. Current gate: `agent/tool_executor.py` uses `HERMES_CONCURRENT_TOOL_BATCH_TIMEOUT` (default 1800s; <=0 disables for debugging) and returns synthetic `concurrent_tool_batch_timeout` tool results instead of waiting on `ThreadPoolExecutor.__exit__(wait=True)` forever.
- provider hangs with no stdout/stderr should be classified as provider no-output timeout, not task proof debt. Current gate: `scripts/agent_team_controller.py` emits `provider_no_output_timeout`, falls back through the model chain, and returns blocked `provider_no_output_circuit_open` after all providers no-output timeout.
- cron config and runtime state still share `cron/jobs.json`, producing noisy git diffs. Current audit/降噪 gate: `scripts/cron_static_projection.py --compare-git --json` compares canonical static projection against `HEAD:cron/jobs.json`; runtime-only churn should report `git_compare.status == same_static`.

## Output shape

Keep the answer decision-focused:
- Current verdict: converged / not converged.
- Evidence: diagnostics, taskpool state, worker liveness, cron errors, relevant code boundaries.
- Residual risks: bounded list with trigger conditions.
- Next gates: the smallest durable controls to add, such as tool-batch timeout, first-byte/provider watchdog, and cron config/runtime split.

Avoid repeating large JSON payloads. Quote only the fields needed for the decision.
