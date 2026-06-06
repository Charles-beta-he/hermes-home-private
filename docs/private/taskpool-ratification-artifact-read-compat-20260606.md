# Taskpool ratification artifact read-compat SSOT — 2026-06-06

## Problem

A parent task can carry an authoritative multimodel certification packet as a mission-envelope structured ref:

- `ratification_artifact: artifact:/absolute/path/certification-v1.json`

The packet may be an older certified shape:

- `schema: multimodel_certification_packet_v1`
- `status: PASS`
- `decision: LOOP_DONE`
- target-bound to the parent task
- truth/certification-positive (`truth_gate.can_certify_truth` or equivalent certification fields)

Before this fix, `resolve_local_artifact_path()` rejected every `artifact:` ref as opaque. That made `task_multimodel_artifact()` skip the authoritative PASS packet and fall through to a later bare absolute `multimodel_last_discussion_artifact`, which may be a failed/non-converged discussion. The result looked like missing evidence/coverage even when the PASS packet had `evidence_coverage: 1.0`.

## Long-term invariant

1. `artifact:/absolute/local.json` and `file:/absolute/local.json` are structured local artifact references and may resolve to local JSON evidence.
2. Opaque labels and non-file proof refs remain non-resolvable:
   - `proof:...`
   - `command:...`
   - `search:...`
   - `brainctl:...`
   - `url:...`
   - `artifact:opaque-label`
3. A legacy certification packet is read-compatible only when all are true:
   - schema is an accepted legacy certification packet schema;
   - `status=PASS`;
   - `decision` or `loop_status` is `LOOP_DONE`;
   - target binding matches the expected task (or an explicit repair-child parent id);
   - truth/certification fields are positive.
4. `PASS_ADVISORY_ONLY` / `advisory_completed` remains non-authoritative and must not close tasks.
5. This is a parser/binding/read-compatibility fix, not a quorum/threshold relaxation.

## Implementation points

- `brain_task_orchestrator.py::resolve_local_artifact_path()` now strips `artifact:` only to validate the remainder as an absolute local path.
- `task_multimodel_artifact()` can now select the authoritative `ratification_artifact` before falling through to `multimodel_last_discussion_artifact`.
- `command_ratification_gate()` keeps strict gate failures visible, but when a task-bound legacy PASS+LOOP_DONE packet passes the compatibility predicate, CLI output reports:
  - `status: PASS`
  - `decision: LOOP_DONE`
  - `legacy_packet_passed: true`
  - `strict_gate_status: FAIL`
  - `strict_gate_failures: [...]`

## Regression tests

Added to `/Users/charles/.hermes/scripts/test_brain_task_orchestrator.py`:

- `test_artifact_structured_ref_legacy_packet_preempts_failed_discussion_artifact`
- `test_ratification_gate_cli_reports_legacy_packet_read_compat_without_relaxing_strict_gate`
- `test_legacy_packet_does_not_authorize_advisory_only_task_or_mismatched_target`

## Verification target

- focused pytest for the three regression tests;
- `py_compile` for `brain_task_orchestrator.py`;
- live `ratification-gate` against the Harness Starter legacy packet;
- `review-gap-scan` to verify the active missing certification gap is cleared or reduced to a different non-parser blocker.
