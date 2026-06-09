# Follow-through automation for taskpool “后续任务”

Use this when a session leaves follow-up work such as remaining audits, blocked-child completion, daily-report ingestion, or any “后续再做” item. For this user, follow-up must be wired into automation, not only summarized.

## Required pattern

1. Inspect the existing trigger chain before claiming follow-through is covered:
   - `cronjob list` / `~/.hermes/cron/jobs.json` for enabled jobs and last status.
   - `brain_task_dispatch_tick.py --summary --no-state` for `status`, `error_count`, `next_task_id`, `dispatchable`, `evidence_spine.summary.cron_status`, `selfcheck`, and `proof_check`.
   - `brain_task_orchestrator.py selfcheck --json` and `proof-check --json`.
2. Ensure there is at least one durable execution trigger, not only reporting:
   - deterministic no-agent runner, e.g. `local-brain-taskpool-auto-completer` running `taskpool_dynamic_runner.py` on a short interval;
   - LLM follow-through job for tasks that need reasoning, with a self-contained prompt that loads `taskpool-control-plane` and advances the highest-priority task to a verifiable state.
3. Run the trigger once immediately after wiring it:
   - If deterministic: execute the script directly and inspect the JSON `summary`, `autorun`, `auto_close_review`, and `multimodel_dynamic` fields.
   - If LLM cron: `cronjob run <job_id>` after creation/update; then inspect `jobs.json` for `last_run_at` / `last_status`.
4. Verify health after the run:
   - `selfcheck` PASS
   - `proof-check` PASS
   - dispatch tick `status: OK` or an explicitly classified safe status
   - `next_task_id` still exists or the pool has a healthy terminal no-dispatchable state.

## Recursive evidence-spine self-lock pitfall

Failure signature:
- `local-brain-taskpool-auto-completer` last status is `error`.
- `brain_task_dispatch_tick.py --summary --no-state` reports `status: ERROR`, `error_count: 1`.
- `evidence_spine.summary.auto_completer_semantic_status == "error"` and `auto_completer_safe_for_next_tick == false`.
- The auto-completer's `last_error` contains nested `taskpool_dynamic_runner_v1` output, whose nested `tick.stdout` may be truncated from the front by cron error storage.

Durable fix pattern:
- In `auto_completer_recursive_self_lock(...)`, do not require the nested `tick.stdout` to parse from byte 0 when cron has truncated it.
- If parsing yields a partial object or no `brain_task_dispatch_tick_summary_v1` schema, inspect the nested `stdout_tail` / tail text for:
  - `brain_task_dispatch_tick_summary_v1`
  - `"status": "ERROR"`
  - `brain_task_dispatch_tick.py` recovery command
  - root summary `error_count == 1`
- Classify this as `recursive_evidence_spine_self_lock`, with `safe_for_next_tick: true`, rather than leaving the scheduler permanently unsafe.

## Multi-model certification follow-through

For complete automation, keep review-close consume-only and let the multi-model lane own expensive certification:
- `brain_task_dispatch_tick.py --autorun-step` may call `auto-close-review` with `HERMES_AUTO_CLOSE_REVIEW_TRIGGER_CERT=0` to avoid recursive or mismatched certification from a review closer.
- `multimodel_intervention_dynamic_step.py` should start/advance certification workers when `multimodel_intervention_required=true`.
- After a multi-model worker finishes successfully, it should immediately run a non-recursive `auto-close-review` with `HERMES_AUTO_CLOSE_REVIEW_TRIGGER_CERT=0`, then one bounded dispatch tick (`brain_task_dispatch_tick.py --summary --autorun-step --no-state`) so the chain is: certify -> close eligible review -> advance next dispatchable task.
- Verification should inspect the worker log for `worker_summary.tasks_passed`, `post_certification_closeout_summary.closed_count/error_count`, and `post_closeout_dispatch_tick_summary.status/autorun`.

## Guardrails

- Do not convert unknown auto-completer errors into safe states. Only classify the known recursive self-lock shape.
- Do not let `auto-close-review` recursively spawn certification unless deliberately debugging a targeted task; normal automation should use the separate multi-model worker.
- Do not treat `py_compile`, proof hashes, or selfcheck alone as implementation completion evidence; they only prove control-plane health.
- Do not create a cron job with a vague prompt such as “continue later”. The prompt must specify selection, execution, closeout requirements, verification commands, and what to report.
- Do not leave the turn with “后续再做” unless a cron/script/hook exists and has been run or scheduled.
