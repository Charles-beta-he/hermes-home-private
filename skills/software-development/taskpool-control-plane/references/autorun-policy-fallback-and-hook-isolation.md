# Autorun policy fallback and event-hook isolation

Applicability: Hermes/local-brain taskpool autorun stalls where `taskpool_dynamic_runner.py` or `brain_task_autorun_step.py --json` is healthy enough to run but returns `claimed=false`, `policy_lane_miss`, `claim_denied`, or hangs inside a lifecycle transition.

Anti-conditions:
- Do not use this to widen `auto_run_policy.json`, add advisory lanes, force claim, force done, or bypass proof/lifecycle/multimodel gates.
- Do not silently switch targets when the operator passed an explicit `--task`; explicit targets must fail closed if disallowed.
- Do not classify certification failure as implementation success; certification failures remain retry/blocked/review intervention, never automatic done.

## Debugging path

1. Separate human escape from claim failure.
   - Run the escape guard/readback first if the runner reports `human_escape_active_preclaim`.
   - If the user explicitly authorizes resume and rows are reviewed stale terminal envelopes, consume only the ack-reviewed waterline; preserve proof/lifecycle/multimodel gates.

2. Compare selected candidate vs autorun policy.
   - Inspect the default `eligibility-check` / `next` candidate lane and project.
   - Compare with active `auto_run_policy.json` lanes/projects/task ids.
   - If the default candidate is advisory but policy allows only work/evolution, the root cause is candidate selection, not claim authority.

3. Fix selection without widening policy.
   - In default mode (no explicit `--task`), fallback to the first dispatchable task that already passes `validate_policy_for_task()`.
   - Return a clear no-policy-allowed reason if no dispatchable candidate satisfies policy.
   - Preserve explicit `--task` semantics: never swap the target behind the operator's back.

4. Isolate bounded autorun from event-hook recursion.
   - Child orchestrator commands launched by bounded `brain_task_autorun_step.run_json()` should set:
     - `HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1`
     - `HERMES_TASKPOOL_EVENT_HOOK_DISABLED=1`
   - The first flag prevents inline multimodel PUA loops from blocking `transition` / `release`.
   - The second flag prevents transition hooks from recursively launching another `brain_task_dispatch_tick --autorun-step` during the same bounded step.

## Test pattern

Add deterministic unit tests for:
- default advisory candidate is skipped in favor of a policy-allowed work/evolution candidate;
- explicit `--task` is not swapped;
- child subprocess env includes both event-hook isolation flags;
- bounded step remains review-only and does not execute markdown body code.

If the unit fixture uses real `auto-claim-and-handoff`, avoid dependence on current live health by writing a temporary pass fixture and setting `HERMES_AUTONOMY_PRECONDITION_P10_FIXTURE` in the test env. This keeps production precondition gates intact while making the test deterministic.

## Live verification checklist

1. Run focused tests:
   - `python3 -m py_compile scripts/brain_task_autorun_step.py scripts/test_brain_task_autorun_step.py`
   - `python3 scripts/test_brain_task_autorun_step.py`
   - `python3 scripts/test_brain_task_dispatch_tick.py`
2. Run the bounded dynamic runner or its no-agent cron wrapper.
3. Read back `state/taskpool_dynamic_runner.json`; expect `status=OK` and `error_count=0`.
4. Check residual target processes for:
   - `taskpool_dynamic_runner`
   - `brain_task_dispatch_tick.py --summary --autorun-step`
   - `brain_task_autorun_step.py`
5. Check active claims; success means no orphan `claimed_by=hermes-autorun-step`. Independent `hermes-multimodel` claims are a separate certification lane and should not be killed merely because autorun smoke finished.
6. If auto-close sees `multimodel_gate FAIL`, verify it fails closed to retry/blocked/review and does not force `done`.

## Pitfall observed

A clean cron wrapper can mask a blocked underlying runner: the wrapper returns quickly to satisfy cron's timeout, while the real child can still hang on transition hooks. Always verify both the wrapper execution receipt and the underlying runner state/residual process set.
