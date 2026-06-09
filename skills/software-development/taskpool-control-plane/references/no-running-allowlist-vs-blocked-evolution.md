# No-running stall: blocked evolution + advisory-only dispatchables + allowlist miss

Use this when the pool shows `active_count > 0` and `dispatchable > 0`, but `claimed=0` and `running=0`.

## Failure signature

Observed pattern:
- `dashboard --json` shows active work, often `pending > 0`, `blocked >= 1`, `running = 0`, `claimed = 0`.
- `next --json` returns a concrete `dispatchable: true` task.
- `eligibility-check --json` and `autorun-runner --json` both deny with `reasons: ["allowlist_miss"]`.
- `auto-claim-and-handoff --json` also denies with `allowlist_miss`.
- `selfcheck --json` passes, `boundary.status` passes, `autorun_enabled=true`, and kill switch is off.
- The highest-priority evolution task is blocked / not dispatchable, often with multimodel `gate=FAIL` and `decision=CONTINUE_LOOP`.
- Remaining dispatchable work is mostly or entirely `advisory` lane.

## Interpretation

This is not a dead scheduler and not an empty pool.

It means:
1. The mainline high-priority evolution task cannot run.
2. The fallback dispatchable tasks exist, but current autorun policy does not permit them.
3. The control plane is healthy; policy and task-state alignment are what prevent `running`.

A common concrete combination is:
- priority mode = `evolution-first`
- autorun policy `lanes = ["evolution"]`
- allowlist excludes the selected advisory task's project
- the only evolution candidate is blocked

Result: repeated fail-closed ticks with no claim.

## What to inspect

1. `next --json`
   - Confirm the nominated task is actually `dispatchable: true`.
   - Record its `lane` and `project`.
2. `eligibility-check --json`
   - Look specifically for `allowlist_miss`.
3. `autorun-runner --json` and/or `auto-claim-and-handoff --json`
   - Confirm the same deny reason repeats in the actual runner path.
4. `~/.hermes/state/auto_run_allowlist.json`
   - Check whether the task's `project:<name>` is present.
5. `~/.hermes/state/auto_run_policy.json`
   - Check whether the task lane is permitted by the active profile.
6. `list --json` / `blocked-resolve-step --json`
   - Verify whether the highest-priority evolution task is blocked and therefore not the real runnable candidate.

## Diagnostic conclusion template

Prefer wording like:
- "The pool is not empty and the scheduler is not down."
- "No running task exists because the only high-priority evolution task is blocked, while the remaining dispatchable advisory tasks are fail-closed by autorun policy / allowlist."
- "`proof-check FAIL` may still exist as historical governance debt, but it is secondary if claim denial is explicitly `allowlist_miss`."

## Recovery options

Choose based on user intent:
1. Fix the blocked evolution task so it becomes dispatchable again.
2. Expand allowlist / policy so the current advisory task class is allowed to autorun.
3. Manually claim one dispatchable advisory task if the user wants immediate movement rather than policy repair.

## Bounded manual advance pattern for "全盘推进"

When the user asks to advance the whole pool rather than only explain the stall, use a bounded manual tranche instead of forcing a fake long-lived `running` state:

1. Reconfirm the baseline with the real runner path.
   - `list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`
   - `autorun-runner --json`
   - `auto-claim-and-handoff --json`
2. If the deny reason is still `allowlist_miss`, manually claim exactly one highest-value dispatchable advisory task.
3. Land one concrete evidence tranche that materially improves the task note (repo surface, package tree, reuse map, architecture boundary, etc.).
4. Update the task note with structured evidence plus a clearer queue recommendation.
5. Release the task back to `pending` unless it is genuinely ready for promotion or closeout.

Why this matters:
- It proves the pool can still make forward progress under manual supervision.
- It avoids leaving advisory research wedged in `claimed` just to create the appearance of activity.
- It preserves the real diagnosis: policy gating and blocked evolution work are still the reasons there is no stable autorun `running` task.

## Interpreting a successful manual tranche

Do not require `running>0` after the manual tranche to call the intervention successful.
A successful pass can still end with `claimed=0` and `running=0` if all of the following are true:
- automation was retried and the deny path was verified,
- the highest-value dispatchable task was manually advanced,
- new structured evidence was landed,
- the task was intentionally released back to its correct lifecycle state,
- the remaining blocker is still accurately described as blocked evolution + autorun allowlist mismatch.

In that state, the right report is "real forward progress happened, but autorun policy/root blockers still prevent a sustained running task" — not "nothing changed".

## Pitfall

Do not misreport this state as `no_dispatchable_task` or `scheduler broken` just because `running=0`.
The important distinction is:
- `dispatchable=true` at task selection time
- but `eligible=false` at autorun policy time

That is a policy gate mismatch, not absence of work.