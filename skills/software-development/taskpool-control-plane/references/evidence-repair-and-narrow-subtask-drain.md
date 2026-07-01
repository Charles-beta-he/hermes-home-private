# Evidence repair and narrow-subtask drain pattern

Use when taskpool automation is stuck in retry/blocked loops after the user authorizes continued progress, especially when worker execution is blocked by human-escape, autorun allowlists, or multimodel certification gates.

## Trigger signals

- `consume-claimed` returns `Human escape` and releases claimed handoffs to retry.
- `auto-close-review` skips with `autorun_multimodel_disabled`, `allowlist_miss`, `certification_inconclusive`, or `certification_task_mismatch`.
- `proof-check` is PASS but has historical warning debt; `selfcheck` is PASS; taskpool still shows retry/blocked due to evidence/certification gaps.
- User says “证据补齐” or asks to continue without bypassing gates.

## Safe operating model

1. Do not force `done`, do not fabricate proof, and do not bypass allowlists.
2. Use AgentOS route/status only as advisory readback unless separately authorized for an exact write surface.
3. Prefer deterministic evidence binding and lifecycle-safe transitions over worker execution when human-escape is active.
4. If certification remains blocked by allowlist, report the exact gate and leave the task in retry/review according to lifecycle rules.

## Procedure

1. Read the next task and its parent/repair contract:
   - `brain_task_orchestrator.py next --reconcile --json`
   - inspect `acceptance_criteria`, `review_gap_parent`, `review_gap_required_evidence`, `ratification_artifact`, `evidence_refs`, and `multimodel_last_failures`.
2. Verify evidence deterministically before binding it:
   - check artifact exists;
   - validate parent task id and repair child id;
   - verify `certification_result=PASS`, `loop_done=true`, `certification_status=certified`, `vote=approve`, `no_red_line_violations=true`;
   - verify all acceptance criteria are covered;
   - compute and record SHA-256.
3. Bind evidence through legal lifecycle transitions only:
   - `pending -> claimed -> running -> review` with `--authority budget-handoff` and evidence text;
   - never jump `pending -> review` directly; it is illegal and will fail.
4. Run closeout gates:
   - `auto-close-review --json`;
   - if needed and explicitly authorized, one command may set `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1` for closeout certification, but do not persist config changes.
5. If closeout still fails due to `allowlist_miss` or `certification_task_mismatch`, stop escalation and report the gate. Do not loop the same evidence repair.
6. Run recovery/readback:
   - `blocked-resolve-step --authority dispatch-hint --json` to avoid review/blocked wedges;
   - `selfcheck --json`, `proof-check --json`, `taskpool_watch_report.py --json`, and scoped git status.

## Narrow-subtask generation pattern

When retries have concrete `multimodel_last_failures`:

1. Skip retry tasks with no failure list or only `PASS_ADVISORY_ONLY` unless there is a specific missing artifact.
2. Run `auto-split-non-convergence --task <id> --json` for each retry task with concrete failures.
3. Reconcile and sync:
   - `reconcile --write --promote-due-retry --json`
   - `auto-subtask-sync --write --json`
   - `blocked-resolve-step --authority dispatch-hint --json`
4. Verify that task count increased by the created subtask count and that `selfcheck`/`proof-check` remain PASS.

## Pitfalls

- `auto-close-review` may ignore an already verified ratification artifact if the task is not in the multimodel intervention allowlist. Treat this as a real gate, not an evidence failure.
- A repair child can have evidence showing the parent gap is resolved, but closeout can still fail with `certification_task_mismatch`. Report the mismatch and leave the normal gate intact.
- Claiming tasks while human-escape is active creates no progress; `consume-claimed` should release them to retry to prevent claimed-without-progress wedges.
- Historical autorun proof warning debt should not be erased unless the append-only proof/readback chain validates it.

## Report format

Always include:

- what was verified and the artifact SHA;
- which lifecycle transitions succeeded;
- whether `auto-close-review` closed or skipped, with exact failure strings;
- final `selfcheck`, `proof-check`, `watch`, and scoped git status;
- explicit boundary: what was not bypassed or forced.
