# Taskpool cron wrapper and local-brain precommit gate

Applicability: Hermes/local-brain taskpool control-plane changes that touch `brain_task_*`, `taskpool_*`, guardian, dynamic runner, autorun, eligibility, or pre-commit BrainConstraintGate behavior.

Anti-conditions: Do not use this to bypass policy/proof/lifecycle/multimodel gates, force claim/done, or treat advisory model output as completion authority. Do not record session progress here.

## Cron 120s timeout recovery pattern

Symptom: a no-agent cron script times out at the scheduler boundary even though the real taskpool runner can finish if given several minutes.

Preferred recovery:
1. Keep the long-running runner as the owner of its own pid lock, state file, and JSONL log.
2. Replace the cron script with a tiny wrapper that exits quickly:
   - if the runner pid lock is live, return silent OK;
   - otherwise `Popen(..., start_new_session=True)` the real runner with bounded env vars and logs;
   - sleep only briefly to catch immediate exec failure;
   - keep stdout empty on success for no-agent cron silence.
3. Verify both layers separately:
   - wrapper runtime is sub-second, rc=0, stdout empty;
   - `cronjob run <job>` reports `execution_success=true` and `last_status=ok`;
   - runner state/jsonl later shows `last_summary.status=OK`, `error_count=0`, and whether autorun claimed/advanced.
4. If autorun reports `claim_denied`, treat runtime recovery as complete but not task production. Open a separate policy/claim-gate investigation; do not force claim/done.

## Skip-selfcheck fast path without bypassing gates

When eligibility repeatedly spends time in heavyweight selfcheck before policy/allowlist denies the claim, it is safe to add a fast flag only if claim still performs selfcheck before mutation:

1. Add `--skip-selfcheck` to eligibility/read-only preflight paths.
2. In autorun-step, run policy/allowlist first.
3. Only after policy passes and before claim, run `selfcheck --json`.
4. Fail closed on selfcheck failure; no claim, no advance.
5. Call claim with explicit prechecked flags (for example `--no-reconcile --skip-selfcheck`) only after the selfcheck readback passed.
6. Tests must cover: policy denial does not run selfcheck/claim; selfcheck failure prevents claim; claim command carries the fast flags; claim denial remains non-mutating.

## Local-brain precommit gate for taskpool T3 changes

Symptom: `git commit` is blocked by local BrainConstraintGate with missing `task_record`, `proof_log`, or `lifecycle_readback`, or later with `degraded_not_certified`, despite deterministic taskpool tests passing.

Debug order:
1. Let pre-commit fail once and read the emitted `route_review_record.evidence_state`.
2. If evidence is missing, fix the evidence collector, not the gate:
   - detect taskpool/control-plane staged files (`scripts/brain_task_*`, `scripts/taskpool_*`, `scripts/task_pool_guardian*`, `scripts/agent_team_controller.py`);
   - run focused taskpool regression tests;
   - add evidence prefixes: `task_record:`, `proof_log:`, `lifecycle_readback:` plus `tests:`, `py_compile_or_build:`, `deterministic_gate:`, `exact_target:`, `rollback:`, `post_action_readback:`.
3. If evidence coverage is 1.0 but the dry-run gate still reports `degraded_not_certified`, first check whether a real live ratification/multimodel certification command exists. If there is no executable interface and the user authorizes proceeding, use a narrow local-precommit certification state such as `local_deterministic_certified`:
   - require `truth_status=grounded`, coverage=1.0, non-model evidence present;
   - require deterministic pre-commit evidence and taskpool lifecycle/proof/readback evidence;
   - mark `certified=true` but keep `multi_model_certified=false`;
   - keep forbidden actions closed (`external_dispatch`, real lifecycle write-through, publish/deploy, destructive, credential/payment).
4. Add tests for both the blocked no-evidence T3 path and the locally-certified full-evidence path.

## Residual process verification

After cron/manual runs and before claiming closure, check and clear only taskpool-owned residuals such as:
- `taskpool_dynamic_runner.py`
- `brain_task_dispatch_tick.py --summary`
- `brain_task_autorun_step.py`
- `brain_task_orchestrator.py selfcheck/list/eligibility-check/next/reconcile/auto-claim-and-handoff`

Use TERM, wait, then KILL if needed. Re-read process state after any background notification or cron wrapper run; old process lists do not prove final residual state.
