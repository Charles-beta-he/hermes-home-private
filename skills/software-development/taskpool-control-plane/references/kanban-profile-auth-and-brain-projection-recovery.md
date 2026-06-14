# Kanban Profile Auth and Brain Projection Recovery

## Scope

Use this when Kanban workers are blocked/crashing while the canonical local-brain taskpool shows no dispatchable work or a different status distribution.

This is a recovery pattern for the Brain ↔ Kanban dual-store architecture:
- Brain markdown task notes are the canonical semantic SSOT for task objective, lifecycle gates, evidence, proof, and multimodel state.
- `~/.hermes/kanban.db` is the execution queue/projection: worker claims, runs, heartbeats, decomposed execution DAG, and runtime logs.
- A healthy Kanban backlog does not prove the Brain taskpool is dispatchable; a clean Brain `next` does not prove Kanban has no in-flight workers.

## Diagnosis sequence

1. Check Kanban runtime state first:
   - `hermes kanban stats`
   - `hermes kanban dispatch --dry-run --json`
   - For suspect tasks: `hermes kanban runs <task>` and `hermes kanban log <task>`.
2. If workers crash before task execution, inspect logs for setup/auth failures, but classify them as runtime setup blockers rather than task-quality failures.
3. Check the worker profile directly, not only the root/default profile:
   - `hermes -p <assignee-profile> doctor`
   - Run a tiny profile-scoped smoke call with the same provider/model the worker uses.
4. If the root profile is healthy but the worker profile is not, repair the profile-scoped credential/config store first. Do not bulk-unblock until the profile smoke passes.
5. Only unblock tasks whose last blocker was infrastructure/crash/protocol violation. Leave `review-required:` tasks blocked for human review.
6. Trigger a real Kanban dispatch pass and verify live PIDs/heartbeats:
   - `hermes kanban dispatch --json`
   - Query `task_runs` or inspect `hermes kanban list --status running --json`.
7. Separately check canonical Brain taskpool state:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py eligibility-check --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 24 --json`

## Interpretation rules

- Kanban `running>0` with live heartbeats means the execution queue is moving, even if Brain `next` says `next: null`.
- Brain `next: null` with open children means the canonical taskpool is not dispatchable yet; it may be waiting for child completion, proof/evidence integration, or parent ratification.
- Kanban `todo` child tasks created by decomposition are execution DAG items. They are not necessarily canonical Brain tasks and may not appear in Brain `list`.
- Do not treat review handoffs as infrastructure backlog. `review-required:` is a human gate.
- Do not call the system healthy solely because Kanban has no `blocked` rows; also verify Brain blocked/review/pending counts and reconcile actions.

## Recovery pattern

1. Repair worker profile setup/auth and prove with a tiny profile-scoped smoke.
2. Add an explicit Kanban comment/unblock reason naming the infrastructure fix.
3. Unblock only crash/protocol-violation tasks, not human review tasks.
4. Dispatch once and verify that workers initialize past the previous failure and emit heartbeats/tool calls.
5. After workers finish or decompose tasks, run Brain reconciliation:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py reconcile --write --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-subtask-sync --write --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json`
6. If children are done but the parent remains blocked, move to parent-level targeted evidence / ratification refresh instead of creating more unrelated children.

## Pitfalls

- Root profile auth can pass while the assignee profile fails. Always check the worker profile named in Kanban.
- Bulk unblocking all `blocked` rows can erase intentional human-review gates. Filter by last run outcome/error and block reason.
- A Kanban task body may contain stale embedded Brain status text (`Status: blocked`) even after Kanban has moved it through triage/todo/running. Trust the database row for Kanban execution state, and the Brain markdown frontmatter for canonical taskpool state.
- Piping large JSON output into a consumer that exits early can cause `BrokenPipeError`; write to a temp file first, then parse it.
