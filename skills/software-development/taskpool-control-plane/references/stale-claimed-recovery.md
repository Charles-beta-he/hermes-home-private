# Stale-Claimed Task Recovery

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Stale-claimed task recovery before declaring the pool blocked

A recurring stall pattern is: the pool shows an active `claimed` task, but `eligibility-check` / `autorun-runner` return `eligible=false` with reasons like `no_dispatchable_task`, while nothing is actually progressing.

Human-escape wedge pattern: `parallel-claim-and-handoff` may claim tasks, then `agent_team_controller.py consume-claimed` sees `human_escape_triggered` and refuses to start workers. The safe controller behavior is to release the just-claimed handoff batch back to `retry` with structured evidence such as `command:agent_team_controller consume-claimed human_escape_release`; never leave them occupying the claim lease with no worker. After patching or recovering, verify `claimed=0`, `agent_team_controller.py status` shows `human_escape_triggered=false` after an explicit ack, and `selfcheck`/`proof-check` still PASS.

If envelope workers actually finished `BLOCKED` but the corresponding brain markdown task remains `status: running`, align the brain task to `blocked` (or `retry` only when safe to rerun immediately) with evidence `command:agent_team_controller event_worker_finished result=blocked` plus a no-live-worker check. If workers finished `FAILED` due provider/rate-limit infrastructure (for example `HTTP 429` / `missing_proof` with no live worker), align the brain task to `retry` with evidence like `command:agent_team_controller_worker_failed_provider_429_no_live_worker`; do not leave false `running` rows occupying active slots. Durable code fix pattern: patch `agent_team_controller.py` so `_detect_infra_failure()` recognizes generic `HTTP 429` / `Too many requests` / `RateLimitError` / quota strings, and so both `_process_worker_result()` and `consume_claimed_batch()._run_one()` transition worker `blocked -> brain blocked`, `timeout/continuation_pending -> retry + SKIPPED envelope`, and `failed/error -> retry + FAILED envelope` instead of reporting `to_status=running`. Add regression tests in `test_agent_team_controller_safety.py` for failed->retry, blocked->blocked, and generic provider 429 detection. Acknowledge envelope escape only after the failed/blocked outcomes are understood and either requeued or blocked; otherwise the same post-ack rows will retrigger escape.

Retry-drain pitfalls observed 2026-05-31: (1) `collect_proof()` must accept multiline/fenced `PROOF_JSON`, not only single-line JSON, because DeepSeek/Gemini often wrap proof objects; invalid parsing creates false `invalid_proof` retries. (2) Automatic `multimodel-intervention-dry-run` candidates must be lifecycle-scoped to `pending`; blocked/review/retry/running/claimed tasks are owned by resolver/review/worker lanes and should only be targeted by explicit `--task`. (3) Async multimodel job liveness must validate the current process command line, not only `os.kill(pid, 0)`, because macOS PID reuse can make stale job files look alive (e.g. old multimodel pid reused by Chrome Renderer). (4) After full provider fallback and repeated timeout/missing-proof on an advisory/plugin analysis item, convert to `blocked` with decomposition/evidence-required reason instead of allowing infinite retry. (5) A late worker timeout/failure must never demote a task that has already progressed to `review`/`done` through deterministic evidence; before requeueing, re-read current task status and only transition to `retry` from `claimed`/`running`. Mark the late envelope `SKIPPED` with `worker_result_ignored_current_status_<status>` instead.

Use this recovery sequence:
1. Inspect the claimed task note directly and confirm `claimed_by`, `claim_expires_at`, and recent lifecycle transitions.
2. Compare the live clock to `claim_expires_at`.
   - If the claim is already stale, do not treat the pool as truly busy.
3. Search runner / cron logs for the task id to see whether the claim came from `hermes-autorun`, guardian cleanup, or a previous intervention worker.
4. If the task is stale or wedged in `claimed` without a live worker, force-transition it back to `pending`.
   - Proven command pattern (use `claim-and-handoff` or `budget-handoff` — see `references/bulk-taskpool-unclog.md` for all valid authority values):
     - `python3 ~/.hermes/scripts/brain_task_orchestrator.py transition <task-id> --to pending --actor hermes --authority claim-and-handoff --reason manual_claim_cleanup_for_autorun_step_requeue --force --json`
5. Immediately run a real dispatch tick with autorun enabled:
   - `HERMES_LOCAL_BRAIN_AUTORUN=1 python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --autorun-step --no-state`
6. Verify whether the task cleanly moves through `running -> review -> done`, or whether the pool now reports only genuine blocked work.

Interpretation rule:
- `no_dispatchable_task` can mean "the only candidate is stuck in `claimed`" rather than "there is no work left".
- Clear the stale claim before concluding that the remaining blocker is business-level multimodel non-convergence.
