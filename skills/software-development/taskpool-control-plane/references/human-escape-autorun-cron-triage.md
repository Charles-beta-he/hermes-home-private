# Human-escape and autorun cron triage

Use this when taskpool cron/selfcheck shows active tasks but no running work, or a no-agent autorun wrapper returns an error while `selfcheck` and `proof-check` pass.

## Core lesson

Do not confuse a safe autorun pause with taskpool deadlock. A wrapper that tries `--parallel-autorun` while `human_escape_triggered=true` should emit a classified safe skip/WARN, not a generic cron error.

## Read-only evidence to collect

```bash
python3 ~/.hermes/scripts/agent_team_controller.py status --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --no-reconcile --json
python3 ~/.hermes/scripts/taskpool_dynamic_runner.py --json
python3 ~/.hermes/diagnostics/runner.py --json
```

Inspect:
- `claimed`, `running`, `stale_claim_count`, live worker jobs
- `dispatchable_tasks` and conflict groups
- `human_escape_triggered`, `since_ack.failures`, `since_ack.blocks`
- whether candidates are P0/P1 work or only P2/evolution/advisory
- whether `proof-check` is PASS with historical warnings or FAIL with active blockers

## Interpretation rules

- `human_escape_triggered=true` + `claimed=0` + `running=0` means an autorun preclaim safety pause, not necessarily live work deadlock.
- `dispatchable_tasks>0` behind human escape means manual dispatch may exist but automation is paused.
- P2/evolution-only candidates should not be described as user work blocked.
- Duplicate candidates sharing one `parallel_boundary` should be shown as `DUPLICATE_CANDIDATE` / `boundary_conflict`, not as available concurrency.
- `next --json` and `next --no-reconcile --json` drift indicates selector/reconcile explanation debt; do not immediately mutate state.
- Empty stdout from no-agent watchdog/dynamic runner with exit 0 can be healthy no-op; classify as `NOOP_OK`.

## Durable wrapper behavior

A no-agent autorun summary wrapper should preflight before calling a mutating autorun step:

1. Query agent-team status.
2. If `human_escape_triggered=true`:
   - emit compact JSON with `status: "WARN"` or `status: "SKIP"`, `class: "SAFETY_PAUSE_POST_ACK_FAILURES"`, `blocks_what: "autorun_preclaim"`, live worker count, claimed/running counts, and since-ack failure counts.
   - exit 0 unless the wrapper itself crashed.
   - do not call `--parallel-autorun`.
3. If only P2/evolution candidates exist and no P0/P1 work is blocked, say so.
4. If the wrapper does call autorun and the subprocess returns nonzero with empty stdout/stderr, wrap it as `AUTORUN_STEP_EMPTY_ERROR` with the selected candidate/boundary and preflight context.

## Long-term control-plane fixes

- Make `human_escape` quarantine keyed by lane + boundary + failure_class instead of one global post-ack counter.
- Keep terminal historical envelope failures visible in a debt ledger, but do not let them block unrelated dispatch by default.
- Enforce envelope FSM terminal immutability: terminal states require explicit reopen/retry attempt, not in-place reverse transitions.
- Add CAS/expected_previous_state to lifecycle transitions and keep workers as result/proof producers, not direct state writers.
- Enforce machine-parseable proof at worker output boundary; natural language "evidence verified" is not proof.

## Report shape

For this user, report:
- P0: live user-work blockers, if any.
- P1: safety pause/control-plane issues such as human_escape, wrapper misclassification, duplicate candidates, allowlist/ratification loops.
- P2: historical debts such as terminal proof debt, continuation volume, stale edge-node warnings, old envelope failures.

Avoid saying "taskpool is stuck" unless a concrete P0/P1 task is dispatchable, unclaimed, and not blocked only by an intentional safety pause.
