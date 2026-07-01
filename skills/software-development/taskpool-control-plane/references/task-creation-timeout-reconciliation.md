# Task Creation Timeout Reconciliation

Use this when `brain_task_orchestrator.py add ...` or `transition ...` times out or the parent tool returns no JSON, especially for tasks with multimodel hooks, mission envelopes, or proof gates.

## Rule

Do not immediately retry the same `add`/`transition` command. Taskpool operations can complete the file write and trigger hooks before the caller times out. A blind retry risks duplicate tasks, duplicate multimodel jobs, or stale lifecycle ownership.

## Reconciliation steps

1. Search the task vault for the expected title or slug.
2. Read the candidate task note frontmatter.
3. Check `status`, `claimed_by`, `run_id`, `claim_expires_at`, `certification_status`, `evidence`, and hook-added proof lines.
4. If multimodel intervention is involved, inspect `brain_task_orchestrator.py multimodel-intervention-jobs --json` before starting another intervention.
5. Treat a created task with hook-updated status as the canonical result, even if the original command timed out.
6. Only repair lifecycle state with a new transition after confirming no live owner/job remains and after attaching evidence for the repair.

## Classification

- Timeout + task file absent: retry may be reasonable after checking logs.
- Timeout + task file present: reconcile; do not duplicate.
- Timeout + task status `running`/`claimed` by a hook: inspect hook job/log and respect ownership.
- Timeout + evidence partially written: update or transition only with explicit evidence and smallest state change.

## Anti-condition

Do not save the specific title, path, run id, or timeout duration as a durable rule. The reusable lesson is the reconciliation pattern, not the one session's task.
