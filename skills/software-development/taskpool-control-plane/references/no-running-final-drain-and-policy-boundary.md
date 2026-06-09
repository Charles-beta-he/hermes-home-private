# No-running final drain and policy boundary

Use this when the user asks why the taskpool has no `running` work, or asks to fully advance the pool until there is no stall.

## Session pattern captured

A healthy terminal state can be:
- active tasks remain, but every active task is `blocked` / non-dispatchable;
- `dispatchable=0`, `claimed=0`, `running=0`, `stale_claim=0`;
- `next` returns `null` / `no_dispatchable_task`;
- selfcheck and proof-check pass, or only bounded warnings remain;
- the remaining blocked item is pause-gated or requires human targeted evidence rather than another autorun loop.

Do not report this as a scheduler failure just because `running=0`. The correct interpretation is: no runnable work exists.

## Distinguish policy failure from safe terminal emptiness

1. First baseline the pool:
   - active count and status distribution
   - `next --json`
   - `dispatch-dry-run` / eligibility
   - `claimed` and `stale_claim`
   - selfcheck / proof-check
2. If dispatchable tasks exist but autorun denies with `allowlist_miss`, `autorun_disabled`, or lane policy mismatch, that is a policy boundary, not a broken cron.
3. If those tasks are low-priority advisory / reference tasks and the current autorun policy is deliberately evolution-first, do not broaden policy just to make `running` non-zero.
4. Instead, manually process a bounded evidence tranche for each advisory task and close it only when the evidence supports closure.
5. Re-run the tick and baseline. If dispatchable becomes zero and the only remaining active task is blocked / pause-gated, the no-running state is healthy.

## Advisory drain pattern

For each advisory task blocked by policy:
1. Claim or otherwise mark an explicit actor/path for the manual intervention.
2. Collect enough evidence to classify the advisory value: P2 reference, P3 learning/reference, candidate for a future umbrella skill, or no immediate execution.
3. Write a concise evidence artifact under the relevant project evidence directory.
4. Add machine-readable task evidence, e.g. `artifact:<abs-path>` and `proof:<short-closeout-summary>`.
5. Transition to `done` only if the advisory item has no immediate mainline action left.
   - Prefer normal review/done lifecycle.
   - Use force close only when the task is already evidence-complete and the goal is to clear a false congestion source; record the proof marker clearly.
6. Do not treat force-close warnings as fatal if proof-check has no failures and the warnings are explained by forced closeout mechanics.

## Blocked evolution parent boundary

If the remaining active item is a P1 evolution parent with `loop_non_convergence`, `gate=FAIL`, `decision=CONTINUE_LOOP`, or a multimodel economy gate pause:
- do not fake `PASS`;
- do not repeatedly burn multimodel rounds without targeted evidence;
- prefer `multimodel-intervention-step`, `auto-split-non-convergence`, and `auto-subtask-sync` first;
- if it remains pause-gated, leave it `blocked` and document that it requires human review or targeted evidence repair.

This is not a taskpool stall when `dispatchable=0`.

## Final verification checklist

Before saying the pool is no longer stuck, verify:
- `active_count` and status distribution are known;
- `dispatchable=0` or the only dispatchable items have been deliberately handled;
- `claimed=0`, `running=0`, and `stale_claim=0`;
- `next` is `null` or reports `no_dispatchable_task`;
- dispatch tick returns OK/WARN as expected;
- no stray runner / multimodel / consult process is still active;
- remaining blocked tasks are named with their blocker and why they are not eligible for autorun.

## Pitfalls

- Do not loosen an evolution-first autorun policy just to run advisory tasks. That converts governance boundaries into accidental execution.
- Do not call cron broken when it fail-closes on `allowlist_miss`; this can be the intended protection.
- Do not call `running=0` a failure after the drain if `dispatchable=0` and only blocked/pause-gated work remains.
- Do not close a blocked P1 evolution parent as done unless certification genuinely passes or the user explicitly accepts a manual governance override.