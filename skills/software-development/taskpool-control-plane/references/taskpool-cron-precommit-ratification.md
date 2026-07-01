# Taskpool cron recovery and pre-commit ratification boundary

Use this reference when repairing Hermes/local-brain taskpool cron, dynamic runner, autorun, or pre-commit gates.

## Applicability

- `local-brain-taskpool-auto-completer` or similar cron jobs time out around the scheduler script timeout.
- `taskpool_dynamic_runner.py` can eventually finish but is too slow for no-agent cron.
- `brain_task_autorun_step.py` / `brain_task_orchestrator.py` changes are blocked by local BrainConstraintGate pre-commit.
- Guardian cron or selfcheck/list subprocesses leave orphaned taskpool processes.

## Anti-conditions

- Do not use this to force claim/done, bypass eligibility, bypass policy, or mark tasks complete.
- Do not downgrade T3/taskpool/lifecycle-write `degraded_not_certified` to pass silently.
- Do not use `git commit --no-verify` for governed taskpool/control-plane commits.
- Do not treat a cron wrapper returning OK as proof that a task was claimed or advanced; it only proves scheduler-level trigger health.

## Recovery pattern

1. Separate scheduler health from task execution health.
   - Cron wrapper success proves no-agent scheduler no longer hits its script timeout.
   - Runner state/jsonl proves the dynamic runner actually completed.
   - Autorun payload proves whether any task was claimed/advanced.

2. For slow dynamic runners, use a short cron wrapper.
   - If a live pid lock exists, exit silent OK.
   - Else `Popen(..., start_new_session=True)` the real runner and return quickly.
   - Preserve stdout/stderr logs and runner-owned pid/state files.
   - Verify wrapper unit tests plus cron manual run.

3. Preserve gates when reducing latency.
   - Eligibility can use a fast flag such as `--skip-selfcheck` only if the caller runs selfcheck before claim/execution.
   - Claim path should remain fail-closed and still call the orchestrator gate.
   - Policy denied, selfcheck failed, and claim denied are successful safe no-ops, not runtime crashes.

4. Process cleanup.
   - Before and after cron/manual runs, read back taskpool-related processes.
   - Clean orphaned `taskpool_dynamic_runner.py`, `brain_task_dispatch_tick.py --summary`, `brain_task_autorun_step.py`, and `brain_task_orchestrator.py selfcheck/list/eligibility-check/...` with TERM then KILL.
   - After cleanup, require `residual_count=0` before claiming the environment is quiet.

5. Guardian cron verification.
   - Run the guardian cron explicitly.
   - Inspect execution_success/last_status.
   - If the guardian returns error after an earlier OK, suspect concurrent selfcheck/list/runner residue before changing guardian logic.

## Pre-commit BrainConstraintGate pitfall

For taskpool/control-plane Python changes, the local pre-commit hook may be the failing component, not the implementation. Root cause pattern:

- Focused tests and py_compile pass.
- `git commit` fails with `missing_required_evidence` for taskpool evidence (`task_record`, `proof_log`, `lifecycle_readback`).
- The hook collected only generic local-brain evidence or marked tests as not applicable.

Correct repair:

- Teach the hook to classify taskpool/control-plane files and run the relevant focused tests.
- Add evidence strings with these prefixes when the focused checks pass:
  - `task_record:` exact staged taskpool files and rollback target.
  - `proof_log:` concrete py_compile/test evidence.
  - `lifecycle_readback:` fail-closed lifecycle behavior covered by tests.
- Add a regression test for hook evidence collection.

Boundary after evidence repair:

- If `missing_evidence=[]`, `evidence_coverage=1.0`, and `truth_status=grounded` but pre-commit still blocks on `degraded_not_certified`, stop at the ratification/multimodel gate.
- Do not change the T3 ratification policy to pass without explicit authority or a real certification path.
- Return a DecisionPacket/ContinuationPacket with the staged files, test evidence, rollback path, cron states, and requested authority.

## Verification checklist

- `python3 -m py_compile` for touched scripts and tests.
- Focused tests for autorun step, dispatch tick, guardian, guardian silent wrapper, dynamic runner cron wrapper, and pre-commit hook if touched.
- `git diff --check`.
- `cronjob run <auto-completer>` returns `execution_success=true` and job script points at the wrapper.
- `cronjob run <guardian>` returns `execution_success=true`.
- Runner state/jsonl has fresh `last_summary.status=OK` and `error_count=0` if claiming runner completion.
- Autorun claim/advance status is reported honestly; `claim_denied` is a governance result, not a crash.
- Final residual taskpool process count is 0, unless intentionally leaving a live runner and labeling it.
