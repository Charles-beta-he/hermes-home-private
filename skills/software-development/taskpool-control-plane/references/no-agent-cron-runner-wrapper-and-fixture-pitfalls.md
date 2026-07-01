# No-agent cron runner wrapper and taskpool fixture pitfalls

Applicability: Hermes/local-brain taskpool cron jobs where the scheduled no-agent script has a short scheduler timeout, but the governed taskpool runner legitimately needs several minutes to finish. Also applies to taskpool control-plane tests that import `brain_task_dispatch_tick.py` and monkeypatch subprocess seams.

Anti-conditions: Do not use this pattern to bypass eligibility, proof, lifecycle, multimodel, or selfcheck gates. Do not mark tasks done, force-claim, or hide claim denials. The wrapper may only decouple cron liveness from a long-running governed runner and must leave the runner's own pid lock/state/log readback authoritative.

## Pattern: short cron wrapper, long governed runner

When a no-agent cron job fails with scheduler-level `Script timed out after 120s` but the underlying runner succeeds when invoked directly:

1. Keep the original runner governed and stateful; do not weaken its gates.
2. Add a small cron wrapper that:
   - checks the runner pid lock and returns silent OK if a live runner already exists;
   - removes stale locks only after liveness readback;
   - launches the real runner with `subprocess.Popen(..., start_new_session=True)`;
   - scopes environment such as `HERMES_LOCAL_BRAIN_AUTORUN=1` and runner-specific timeout env vars;
   - redirects stdout/stderr to bounded log files;
   - waits only briefly for immediate exec failure, then exits 0 silently.
3. Update only the exact local no-agent cron script target to the wrapper.
4. Verify in two layers:
   - cron readback: `cronjob run <job_id>` returns `execution_success=true` quickly;
   - runner readback: the runner state/log later shows `last_summary.status=OK`, `error_count=0`, and any autorun denial is explicit/fail-closed.

Completion claim boundary: cron success only proves scheduling/liveness. If autorun returns `claimed=false` / `advanced=false` (for example `claim_denied`), report runtime healthy but governed advancement blocked; do not call the taskpool drained or productive.

## Safety gate relocation

If eligibility spends time on heavyweight selfcheck before policy can deny, it is safe to move selfcheck later only when all of these hold:

- eligibility/policy can fail closed without claim;
- selfcheck still runs immediately before claim/handoff;
- claim/handoff accepts an explicit prechecked flag such as `--skip-selfcheck` only from that prechecked path;
- tests prove policy-denied paths do not call selfcheck or claim, and policy-allowed paths call selfcheck before claim.

## Fixture pitfalls for dispatch tick tests

- Event hooks can mutate fixture tasks. In tests that exercise lifecycle transitions without wanting multimodel side effects, set `HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1` in the fixture environment.
- Do not assert old `pending -> review` shortcuts; current lifecycle requires claim/running gates before review unless a test intentionally verifies denial.
- Evolution/review closeout can be correctly blocked by multimodel certification mismatch. Tests should assert `certification_triggered_skip` and status remains `review` rather than expecting auto-done.
- `brain_task_dispatch_tick.py` uses multiple subprocess seams. If a test monkeypatches `run_json`, also patch `run_orchestrator_json` or `run_cmd_json` for paths such as `evidence-spine`; otherwise the test may accidentally call the real orchestrator or fail on an unexpected command.
- When mocking `run_cmd_json` for agent-team worker commands, explicitly allow orchestrator `evidence-spine` calls if the tick mode still runs proof/evidence observability.

## Verification checklist

- py_compile the changed scripts and tests.
- Run focused taskpool tests, including autorun-step, dispatch-tick, guardian, silent guardian, and cron-wrapper tests when present.
- `git diff --check` on touched files.
- `cronjob run` exact affected cron IDs.
- Read back runner state/log after the asynchronous process exits.
- Check residual target processes are zero after any manual cleanup.
- Commit only scoped code/test/script changes; treat `cron/jobs.json` and `config.yaml` according to repo tracking/runtime-state policy.
