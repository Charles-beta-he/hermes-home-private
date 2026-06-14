# Kanban projection-blockage triage and console drift repair

Scope/applicability: use for Hermes local taskpool/Kanban/Control Console operations where Brain task notes are the lifecycle source of truth, Kanban is an execution projection, and a dashboard/console reports blocked work or projection drift. Anti-conditions: do not use for unrelated Kanban products, do not bypass Brain review/done/multimodel/ratification gates, and do not treat this as permission to mutate external systems.

## Root model

- Brain taskpool markdown is the lifecycle SSOT.
- Kanban DB is an execution projection.
- Control Console/Dashboard `projectionHealth` is an operator projection, not a lifecycle authority.
- Do not close Brain review/done gates from Kanban alone; but it is safe to repair Kanban projection rows when Brain canonical state is already terminal and evidence is recorded.

## Triage sequence

1. Establish three independent baselines:
   - Kanban stats/list/running/blocked/dispatch dry-run.
   - Brain canonical list/next/reconcile state.
   - Coverage, worker-jobs, and envelope escape state.
2. Classify each blocked Kanban row:
   - stale projection: Kanban blocked/running but Brain source/note is terminal (`done`, `archived`, etc.).
   - review-required: worker left a structured review handoff with tests/proof; requires review verification before closing Kanban.
   - real gate: Brain says blocked/retry/review for multimodel, ratification, external side effect, missing proof, retry lane cap, or dependency.
   - live running: worker PID/heartbeat exists; wait/read log instead of force-completing.
3. Fix only projection/service blockers:
   - For stale projection where Brain is already terminal, add a Kanban comment naming the evidence and complete the Kanban row with metadata such as `repair=stale_kanban_projection`, `canonical_source=brain_taskpool_markdown`, and `changed_brain_lifecycle=false`.
   - For review-required Kanban rows, rerun the exact handoff verification tests/build/readback first; complete only if verification passes.
   - If verification fails from a missing optional dependency, install/enable the dependency only when it is part of the task acceptance surface and rerun deterministic tests. Otherwise keep blocked with a comment.
   - Do not unblock/complete real Brain gates just to make the board green.
4. Re-run coverage and health after each batch:
   - desired Kanban service end state: blocked=0, running=0, ready/todo=0 unless live work exists.
   - desired coverage: `agent_coverage_v2.state=flow_idle_clean`, `stale_projection_tasks=0`, `projection_drift_tasks=0`, `blocked_tasks_structured=0`.
   - desired worker/envelope state: alive workers are either expected live work or 0; `human_escape_triggered=false`; since-ack failures/blocks are 0.

## Console projectionHealth pitfall

Execution-flow dry-runs can include historical/terminal rows (`done`, `archived`, `cancelled`, `completed`). These should not be compared against the current active taskpool list. If terminal execution-flow rows are treated as active, the console will show false `execution_flow_task_missing_from_list` drift after Kanban has already been cleared.

Fix pattern in snapshot generators:

```python
terminal_flow_statuses = {"done", "archived", "cancelled", "completed"}
flow_task_ids = {
    str(item.get("task_id") or item.get("taskId") or "")
    for item in evaluations
    if isinstance(item, dict)
    and (item.get("task_id") or item.get("taskId"))
    and str(item.get("status") or "").lower() not in terminal_flow_statuses
}
```

Add a regression test: an execution-flow evaluation for a missing task with `status="done"` must keep `projectionHealth.status == "fresh"` and `taskIdMismatches == []`.

## UI acceptance for projection health

Projection health is an operation-safety chip/strip, not a hero panel. First screen should not expose:

- `PROJECTION TRUST`
- `Projection drift detected`
- Status/Drift/Runtime/Mode/Next grids
- snake_case actions such as `refresh_snapshot_and_inspect_drift`
- drift kinds such as `execution_flow_task_missing_from_list`

Use Chinese operator copy instead:

- healthy: `数据投影可信` / `任务池与执行投影一致，可继续查看与操作。`
- degraded: `数据投影需复核` / `发现 N 个投影任务与当前任务池不一致，写入类操作已临时保护。`
- chips: `可操作`, `写入已保护`, `正常`, `需复核`, `只读`, `只记录`.
- put technical fields behind `查看技术详情`.

Browser acceptance should check: no old English/snake_case text on first screen, no horizontal overflow, no console JS errors, main operator content still visible/readable.