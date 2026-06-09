# Full-pool advance: bounded loop when the user asks to “全盘推进”

Use this when the user is not asking for a read-only health check, but wants the taskpool actively pushed forward.

## Goal

Advance the pool without doing any of these by accident:
- misreporting `dispatchable` as “already executing”
- leaving an advisory task stuck in `claimed`
- forcing `done`/`review` when only a first evidence tranche landed
- blaming proof debt when the real blocker is `autorun_disabled`

## Proven sequence

1. Re-baseline the live pool first.
   - `list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`

2. Run the normal automation path before manual intervention.
   - `autorun-runner --json`
   - `auto-claim-and-handoff --json`
   - multimodel intervention step/dry-run as appropriate

3. Interpret the result correctly.
   - If the pool is still `dispatchable=true` but nothing starts and the payload shows `autorun_enabled=false`, `autorun_disabled`, or `allowlist_miss`, treat that as the primary reason full-pool advancement did not auto-execute.
   - Do not misdiagnose this as “no candidate task” if `next --json` still nominates a real task.

4. Manually advance one highest-value dispatchable task.
   - Prefer the current `next --json` candidate.
   - Claim it explicitly.
   - Read the task note before writing.
   - Land one bounded, real evidence tranche tied to the task’s acceptance shape.

5. For advisory / evidence-deposition tasks, release after bounded progress.
   - If you only landed the first evidence tranche and the task is not truly complete, release it back to `pending` with a precise reason.
   - This is better than leaving the task artificially wedged in `claimed`.
   - Keep the note fail-closed: record residual uncertainty and the exact next boundary still missing.

6. Clean up bounded automation claims before final reporting.
   - If `autorun-runner`, `auto-claim-and-handoff`, or the dynamic auto-completer left tasks in `claimed` but no worker body actually ran, release those tasks back to `pending`.
   - Use an explicit reason such as `bounded_full_pool_advance_handoff_or_evidence_verified_release_no_worker_body`.
   - Use a CLI-accepted transition authority; `brain_task_orchestrator.py transition --authority` is an enum. `claim-and-handoff` and `budget-handoff` are both safe cleanup authorities. Do not invent free-form authority labels like `bounded-full-pool-advance-cleanup` because argparse accepts them silently but the transition does nothing. See `references/bulk-taskpool-unclog.md` for the full authority enum table.
   - Verify `claimed=0`, `stale_claims=0`, and that the task remains honestly dispatchable rather than falsely complete.

7. Re-test the pool.
   - `list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`
   - `proof-check --json`
   - `evidence-spine --json`
   - `python3 ~/.hermes/scripts/post-update-check.py` for Hermes governance drift when the work touched Hermes/taskpool infrastructure
   - For self-evolution/taskpool-governance rounds, run `pua_loop_self_optimize.py p10-check` with explicit `--goal`, `--boundary`, `--evidence`, and `--next-action`; include Tool/Skill/Benchmark wording in evidence when the leverage check should pass.

## Task-type-specific closeout requirements

Do **not** use one generic `proof/selfcheck/py_compile` closeout shape for every task. Before moving any task to `done`, classify what kind of completion it claims and require matching evidence:

- **Feature / implementation tasks**: require a concrete landed implementation artifact plus an end-to-end or realistic smoke proof of the feature path. Examples: script/module path, cron/hook/config wiring, dry-run and real-input run, created task/file/API response, regression test. `py_compile`, `proof-check`, `selfcheck`, or dashboard refresh alone are insufficient.
- **Integration / automation tasks**: require evidence that the automation boundary is actually connected. Examples: cron prompt/script updated, hook invoked, taskpool `add`/`ingest` called in dry-run and write mode, idempotency/dedup checked, fallback behavior observed.
- **Governance / policy tasks**: require the rule to be encoded where the runtime consumes it, plus a failing-before/passing-after test or deterministic selfcheck. A markdown proposal alone is advisory, not done.
- **Research / advisory tasks**: require deposited report/artifact evidence and explicit handoff boundaries. These can close without code only if the task objective is advisory and the final handoff says no implementation was promised.
- **Evidence-only / cleanup tasks**: require proof that the specific debt was migrated/cleaned and current gates pass.

If the task's `acceptance_evidence` says “script/control-plane落点/最小实现/验证步骤”, closeout must include those artifacts. If only a bounded tranche landed, return the task to `pending` or keep it in `review`; do not mark `done`.

## What to write into the task note during bounded advancement

For external-repo / advisory tasks, the first bounded tranche should usually include:
- `capability_delta`
- `anti_drift_check`
- `acceptance_evidence`
- structured `evidence:` entries
- validation rows showing what was actually checked
- proof log explaining why the task is still not ready for closeout
- blockers / confusions that preserve fail-closed interpretation
- final handoff that says whether to keep pending, block, or promote later

## Interpretation rules

- `next` staying the same after manual advancement does **not** mean nothing changed.
  - It may simply mean the same task is still the highest-value pending item, now with better evidence.
- Historical `proof-check FAIL` remains secondary if the immediate reason nothing auto-ran is `autorun_disabled`.
- A bounded advisory advancement counts as real progress when the note now contains durable evidence and sharper execution boundaries.

## Pitfalls

- Do not call it “fully advanced” if you only inspected state.
- Do not leave a partially worked advisory task in `claimed` just because you touched it.
- Do not upgrade README marketing claims into repository facts without boundary checks.
- Do not convert “automation disabled” into a fake governance/proof explanation.
- Do not close an advisory task just because the first evidence artifact exists.

## Good end-state for this pattern

A successful bounded full-pool advance often ends like this:
- automation path was exercised and its blocker identified
- one real dispatchable task received a concrete evidence tranche
- that task was released back to the correct lifecycle state
- post-checks confirm the pool is still healthy, still dispatchable, and not falsely reported as running
