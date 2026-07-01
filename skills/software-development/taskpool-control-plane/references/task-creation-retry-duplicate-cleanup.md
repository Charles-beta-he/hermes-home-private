# Task Creation Retry / Duplicate Cleanup

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Task creation retry / duplicate cleanup

Applicability: local-brain/taskpool task creation retries where the `add` command succeeds but an event hook reports a non-zero return code, times out, or a later retry creates a duplicate task. Anti-condition: do not use this to delete real work or override another active worker's legitimate claim; first identify the canonical task and the duplicate.

Procedure:
1. Treat `add` output with `status: OK` and a created path as a successful task creation even if `event_hook.status` is `ERROR`; inspect the task file/selfcheck before retrying.
2. Before re-running a failed-looking `add`, search/list existing task files for the title or mission title to avoid duplicate creation.
3. If a retry already produced a duplicate, keep the earliest/canonical task unless the duplicate has newer unique evidence.
4. If the duplicate is claimed/running by an automated route but contains no unique work, release it with the orchestrator `release` command to `archived`, using `--force` only after confirming the canonical task path and reason.
5. Run taskpool selfcheck after cleanup and record any remaining warnings (parallel-boundary conflicts, stale edge nodes, handoff buildup) as non-blocking unless `invalid_count` or active gate failures are nonzero.
