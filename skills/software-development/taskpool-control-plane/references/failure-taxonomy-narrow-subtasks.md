# Failure taxonomy → narrow subtask drain pattern

Applicability: use when taskpool drain stalls on retry/blocked tasks whose `multimodel_last_gate_status` is `FAIL` or `PASS_ADVISORY_ONLY` with `CONTINUE_LOOP`, especially when repeated `blocked-resolve-step` only releases the same parent tasks back to retry.

Anti-conditions:
- Do not use this to bypass certification, proof, or lifecycle gates.
- Do not keep blindly rerunning resolver/claim loops once failures clearly say `missing_required_model_*`, `status_not_passed:*`, `agreement_below_threshold:*`, `final_design_*_missing`, or similar taxonomy signals.
- Do not force done or fabricate autorun proof hashes.

Procedure:
1. Read current active state with `brain_task_orchestrator.py list --json` and group retry/blocked tasks by `multimodel_last_failures`, `multimodel_failure_taxonomy`, and `multimodel_recommended_axes`.
2. For retry tasks with concrete failure lists, run `brain_task_orchestrator.py auto-split-non-convergence --task <task-id> --json` to create narrower repair subtasks. Skip tasks that are only `PASS_ADVISORY_ONLY` and have no actionable failure list.
3. Expect child axes such as `framing`, `quota_observability`, `patch_normalization`, `fallback_threshold`, or `relay_ordering`; verify the created child count, not just command exit.
4. Reconcile and bind children back to parents:
   - `brain_task_orchestrator.py reconcile --write --actor <actor> --promote-due-retry --json`
   - `brain_task_orchestrator.py auto-subtask-sync --write --actor <actor> --json`
   - `brain_task_orchestrator.py blocked-resolve-step --actor <actor> --max-tasks <n> --authority dispatch-hint --json`
   - `brain_task_orchestrator.py auto-close-review --actor <actor> --json`
5. Verify with `selfcheck --json`, `proof-check --json`, `taskpool_watch_report.py --json`, and scoped git status for Hermes code files.

Pitfalls:
- `parallel-claim-and-handoff` followed by `consume-claimed` may be blocked by Human escape. If so, the controller should release claims back to retry; treat that as safe no-progress, not failure to force through.
- Command-level `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1` can generate discussion artifacts for bounded intervention, but `PASS_ADVISORY_ONLY` still cannot authorize `done`; it only supplies evidence for the next split/repair loop.
- A successful split can increase total task count and pending count while reducing retry/blocked. That is expected progress: the parent loop has been converted into narrower dispatchable repair slices.

Evidence shape to report:
- parents split and child count;
- example child ids/axes;
- before/after counts for `retry`, `pending`, `blocked`, `claimed`, `running`;
- selfcheck/proof status and proof warning count;
- whether Human escape or autorun disabled prevented worker execution.
