# Blocked task diagnosis pattern

Use this when the local-brain task dashboard shows no in-progress work or all active tasks are blocked.

## Fast probes

1. Get pool counts and blocked rows:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
```

Inspect `rows[].status`, `priority`, `lane`, `multimodel_status`, `blocked_reason`, `depends_on`, `claimed_by`, and `claim_expires_at`.

2. Confirm whether any task is dispatchable:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
```

If `next=null` and the message says no dispatchable tasks, do not try to claim tasks until the block reason is resolved.

3. Check gate health and dispatchability summary:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py evidence-spine --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --include-active --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
```

## Interpreting common blocked states

- `status=blocked` + `eligibility-check` reason `task_not_dispatchable`: the task is intentionally not claimable; claiming is not the fix.
- `multimodel_status=not_certified`: parent task is waiting for certification/ratification, even if child tasks are already `done`.
- Multiple blocked tasks with **identical model-specific failures** (e.g. all showing `best_within_constraints_missing:gemini-3.1-pro-preview`): suspect a gate validation bug where optional models are treated as required. Check `ratification_gate_result()` — optional model votes should be warnings, not failures. See `references/multimodel-ratification-unblock-patterns.md` for the fix pattern.
- `multimodel_gate:FAIL`, `multimodel_decision:CONTINUE_LOOP`, or `multimodel_auto_outcome:certification_failed|certification_inconclusive`: run the multi-model/ratification convergence path before releasing the block.
- `child-task:*` or `child-axis:*` proof failures: child work exists but proof/axis structure is not accepted. Look for `child-axis:unknown`, missing structured evidence, or child tasks that are `done` but still `not_certified`.
- Dashboard `active_count>0` with `dispatchable=0` means there are active notes, but the control plane is correctly refusing to schedule them.

## Reporting format

For each blocked task, report:

- priority, title, and id
- direct state: `status`, `multimodel_status`, `eligibility` result, and `next`/dispatchability
- concrete gate evidence: proof-check failures, multimodel gate/decision/outcome, child-axis or child-task failures
- child task certification status, distinguishing `done` from `certified`
- conclusion: what must be resolved before it can become dispatchable

## Pitfalls

- Do not equate `done` child tasks with a releasable parent. Parent release depends on structured proof and certification gates.
- Do not hand-claim a blocked task just to create progress; first resolve the proof/certification blocker.
- If shell pipelines with heredocs drop piped JSON, use a temp file or `execute_code` with `hermes_tools.terminal()` instead of assuming the CLI returned invalid JSON.
