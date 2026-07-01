# Taskpool Verification Checks

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Verification

After a fix or manual intervention, verify:
1. A previously dispatchable P1 task moves to `claimed` (or `running` if your flow does that next).
2. The tick payload/log shows either `OK` or `WARN`, not a false `ERROR` caused only by unrelated governance debt.
3. Governance issues remain visible in logs/payloads for later cleanup.
4. Dynamic-runner / cron continues to make forward progress on subsequent ticks.
5. For follow-up work, verify the automation trigger itself exists and has run at least once: deterministic runner output has `summary.status: OK` or a classified safe blocker, LLM follow-through cron has a real `last_run_at` / `last_status`, and `selfcheck` + `proof-check` + dispatch tick still pass. Do not report “后续再做” without an execution trigger.
6. Run `blocked-resolve-step --json` directly once. If it returns `OK` while surfacing artifact-loss detail as a warning field, the resolver is no longer over-blocking dispatch.
7. Run `next --json` after `reconcile --write`; if a parent blocked task had only auto-subtask completion pending, it should reopen to `pending` instead of remaining hidden behind a reconcile-required message.
8. If the parent already exceeded the multimodel economy gate and child evidence was merely backfilled, verify the opposite outcome:
   - status remains `blocked`
   - dispatch / `dispatch-dry-run` shows no false dispatchable work
   - `multimodel-intervention-dry-run --json` reports the task under `paused_plans[]`, not `plans[]`
   - the task note contains `## Auto-subtask Backfill` plus a proof-log explanation that pause prevented reopen.
