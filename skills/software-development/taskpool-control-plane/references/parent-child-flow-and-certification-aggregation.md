# Parent/Child Flow and Certification Aggregation

Use this reference when a parent task is large enough to be split into auto-subtasks and appears stuck after children complete.

## Core diagnosis

Do not assume this is a concurrency deadlock. Classify it into four distinct failure modes:

1. Worker/claim liveness: claimed or running tasks have no live worker, stale leases, or expired claims occupying capacity.
2. Boundary contention: dispatchable work exists, but `parallel_boundary` conflicts or capacity limits throttle selected tasks.
3. Child execution gap: required auto-subtasks are open, missing, or not terminal.
4. Parent evidence-consumption gap: child tasks are done, but the parent resolver/certification path has not consumed child evidence.

Only the first two are concurrency/capacity problems. The fourth is a resolver/certification problem; adding concurrency may increase WIP and stale evidence without unblocking the parent.

## Required resolver behavior

For blocked parents with `auto_subtask_kind: non_convergence_narrowing`:

1. Aggregate child state from `auto_subtask_children` and/or child backlinks (`auto_subtask_parent`).
2. Report `child_count`, `done_count`, `open_children`, `missing_children`, `axis_summary`, and stale child-status proof entries.
3. If all children are done but certification reasons remain (`explicit_requires_multimodel`, `loop_non_convergence`, `truth_gate_contract`, required model/vote missing), keep the parent blocked and emit:
   - `parent_aggregation.action = keep_blocked_certification_required`
   - `suggested_next = parent_ratification_refresh`
4. Do not treat child completion as authority to force `done` or bypass multimodel/proof gates.
5. If children are open/missing, keep blocked with explicit child IDs.
6. If children are done and no certification gate remains, re-enter normal parent ratification/review path; subsequent `done` still uses ordinary completion gates.

## TDD / verification pattern

For taskpool resolver improvements:

1. Write a RED test in the stateful CLI/orchestrator test suite that constructs a blocked parent and done children.
2. Assert the exact JSON contract, not only file text: `kept_blocked`, `parent_aggregation`, `suggested_next`, and no false `resolved_count`.
3. Implement the minimum read-only diagnostic first; preserve lifecycle gates.
4. Run focused regression tests for sibling paths such as missing taxonomy artifact and auto-subtask sync.
5. If a standalone helper is introduced, drive it to 100% statement coverage when feasible and run a live dry-run against an actual task before claiming the control-plane slice is complete.

## Theory anchors

Useful works/arguments for this class of control-plane work:

- Frederick Brooks, `The Mythical Man-Month`: coordination overhead grows nonlinearly with added people/interfaces.
- Eliyahu Goldratt, `The Goal`: optimize the bottleneck, not local activity.
- Goldratt, `Critical Chain`: shared resource contention and hidden buffers delay project flow.
- Donald Reinertsen, `Managing the Design Factory` and `The Principles of Product Development Flow`: limit WIP, small batches, queue economics.
- Eppinger & Browning, `Design Structure Matrix Methods and Applications`: dependency structure predicts iteration/rework loops.
- Moseley & Marks, `Out of the Tar Pit`: separate essential state from accidental control complexity.
- `Team Topologies`, `Site Reliability Engineering`, and `Accelerate`: sustainable flow requires cognitive-load boundaries, explicit SLO/rollback, and fast feedback.

## Anti-conditions

- Do not capture a project-specific parent ID as a global rule; use it only as a fixture/live-readback example.
- Do not make broad scheduler concurrency changes when the evidence shows a parent evidence-consumption gap.
- Do not use advisory multimodel output as completion authority.
- Do not mark parent `done` from child completion alone.
