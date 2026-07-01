# Parent/child evidence aggregation for blocked taskpool parents

Use when a large parent task has been split into auto-subtasks and the pool looks stuck even though children are completing.

## Core diagnosis

Do not assume this is a worker-concurrency deadlock. Distinguish four states:

1. Execution starvation: dispatchable work exists, but `running/claimed` and worker liveness do not advance.
2. Boundary contention: many children share a coarse `parallel_boundary`, causing `parallel_boundary_conflict` / `capacity_exceeded` without stale claims.
3. Stale claim: tasks remain `claimed` past TTL while no live worker owns them.
4. Parent evidence-consumption gap: children are `done`, but parent remains `blocked` because the resolver/certification gate has not consumed child evidence.

The fourth state is common for oversized parents. Adding concurrency does not fix it; it usually increases WIP and stale proof. The bottleneck is the parent evidence aggregator / certification gate.

## Diagnostic checklist

1. Read current pool health: selfcheck, dispatch tick summary, worker-jobs, handoff backlog.
2. For the suspected parent, collect:
   - `auto_subtask_children`
   - child task `status`
   - child `auto_subtask_axis`
   - parent `blocked_resolve_reasons`
   - parent `multimodel_last_gate_status`
   - stale `proof:child-task:<id>:status:<old>` evidence entries.
3. Classify:
   - any missing child -> keep parent blocked with `missing_children`.
   - any non-terminal child -> keep parent blocked with `open_children`.
   - all children done and certification reasons remain -> keep parent blocked; run parent ratification refresh, do not force close.
   - all children done and no certification blocker -> parent may reopen to pending/review through the governed resolver path.
4. Emit a read-only aggregation artifact before any lifecycle mutation.

## Local tool pattern from session

A safe first slice is a read-only CLI, not a direct mutation of `brain_task_orchestrator.py`:

- Input: `--task <parent_id>`, `--tasks-dir <task_dir>`.
- Discover children from both parent `auto_subtask_children` and child backlinks `auto_subtask_parent`.
- Output JSON schema with: `ready_for_parent`, `action`, `child_count`, `done_count`, `axis_summary`, `open_children`, `missing_children`, `stale_evidence`, `remaining_gate_reasons`, `safety`.
- Recommended actions:
  - `no_children_found`
  - `keep_blocked_children_open`
  - `keep_blocked_certification_required`
  - `reopen_for_parent_ratification`
  - `aggregate_only`

For taskpool Markdown, include a fallback frontmatter parser: real task files may contain malformed YAML-like values with unquoted colons. A diagnostic aggregator should skip or fallback-parse those files instead of crashing before it reaches the target parent.

## TDD / coverage bar

For this class of resolver/aggregator work:

- Write RED subprocess/CLI tests first.
- Cover done children + remaining certification, missing child, backlink discovery, stale child-status evidence, malformed frontmatter fallback, missing parent, and CLI JSON output.
- Use coverage on the new slice and require 100% statement coverage before claiming the slice complete.
- Then run a live dry-run against an actual blocked parent and save the JSON report as evidence.

## Theory anchors

Use these as conceptual backing when designing policy:

- Brooks, `The Mythical Man-Month`: coordination overhead grows nonlinearly with interfaces.
- Goldratt, `The Goal` / `Critical Chain`: optimize the system bottleneck; shared resources and hidden buffers delay flow.
- Reinertsen, `Managing the Design Factory` / `The Principles of Product Development Flow`: limit WIP, use small batches, expose queues.
- Eppinger & Browning, `Design Structure Matrix Methods and Applications`: dependency structure predicts iteration, rework, and coordination loops.
- Moseley & Marks, `Out of the Tar Pit`: separate essential state/complexity from accidental control complexity.
- Skelton & Pais, `Team Topologies`: cognitive load and boundary design constrain sustainable flow.
- Beyer et al., `Site Reliability Engineering`: automation needs explicit SLOs, receipts, and rollback.
- Forsgren/Humble/Kim, `Accelerate`: fast flow depends on safety, feedback, and recovery.

## Anti-conditions

- Do not force-close a parent merely because all children are done.
- Do not treat advisory multimodel output as completion authority.
- Do not add more parallelism until stale claims, worker liveness, and parent evidence consumption have been ruled out.
- Do not save one parent/task id as a global rule; keep project-specific IDs in evidence artifacts or project profiles.
