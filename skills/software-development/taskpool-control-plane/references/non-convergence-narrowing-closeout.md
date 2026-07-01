# Non-convergence narrowing child closeout

Use when the taskpool has auto-generated `non_convergence_narrowing` children for a blocked parent, especially axes like `framing`, `patch_normalization`, or `quota_observability`.

## Landing-zone classification

Reusable procedure / verification checklist, not project status. Keep project-specific paths only as examples; future runs must substitute the current task IDs and artifacts.

## Procedure

1. Inspect the child task note first.
   - Confirm `auto_subtask_kind: non_convergence_narrowing`.
   - Confirm the axis (`auto_subtask_axis`) and parent artifact (`auto_subtask_parent_artifact`).
   - Confirm the child is documentation/governance-only before treating UI/API proof as not applicable.

2. Read the source discussion artifact.
   - For framing: verify `status=certified`, `truth_status=grounded`, `evidence_coverage=1.0`, and `unresolved_issue_ids=[]`.
   - For patch normalization: verify `final_design.patches=[]`, `planner_patch_summary.concrete_patch_count=0`, and the no-op/no-action certification fields before declaring an empty minimum patch set.
   - For quota observability: verify `quota_confidence`, `quota_snapshot`, `has_low_confidence_quota`, `unknown_count`, `unobservable_count`, `exhausted_count`, and `stale_after_seconds`; distinguish `unobservable` from `exhausted`.

3. Write a narrow evidence artifact under the project evidence area.
   - Include source artifact path, extracted facts, minimum conclusion, inclusion/exclusion criteria, and rollback boundary.
   - Record sha256 of the evidence artifact.
   - Append only a concise summary to the project ledger when such a ledger exists.

4. Patch the child task proof log.
   - Declare file access boundary.
   - Record validation checks and the artifact sha.
   - State that the child does not close the parent by itself.

5. Close through governed lifecycle, not by force.
   - Transition `pending -> claimed -> running -> review -> done`.
   - If a previous advisory-only multimodel sidecar set `PASS_ADVISORY_ONLY`, it cannot authorize `done` by itself. Supply fresh implementation-shaped verification evidence for the lifecycle gate, e.g.:
     - `command: python3 project evidence verification test PASS ...`
     - `artifact:/path/to/evidence.md project evidence verification test sha256:...`
     - `proof:ui_surface_not_applicable_governance_only ...` only when truly documentation/governance-only.
     - `proof:api_readback_not_applicable_governance_only ...` only when readback is the discussion/artifact verification, not a real API feature.
   - Do not claim UI/API completion from these not-applicable proofs; they only satisfy a governance-only child closeout.

6. Event-hook pitfall.
   - Review transitions can spawn advisory multimodel sidecars that duplicate work or hang the turn. If the child has already been independently verified and you are closing a documentation/governance-only child, it is acceptable to set `HERMES_TASKPOOL_EVENT_HOOK_DISABLED=1` for the lifecycle transitions, but do not use this to bypass completion evidence. The `done` transition must still pass lifecycle proof gates.

7. Re-check after closure.
   - Run selfcheck and dispatch summary.
   - Confirm `review=0`, `stale_claims=0`, `proof_check=PASS`, `boundary_check=PASS`, `cron_status=OK`.
   - Check handoff backlog. If it crossed threshold after the work, dry-run then apply reversible `handoff-gc.py --archive --keep-newest 50 --apply`.
   - Check agent-team worker jobs for `alive_count=0` if agent-team was involved.

## Anti-conditions

- Do not use this pattern for real implementation/UI/API tasks; they need real test/build/browser/API readback proof.
- Do not mark the blocked parent done just because children closed. Run the parent-specific resolve/closeout logic and accept that `blocked-resolve-step` may return `resolved_count=0` until another gate consumes the child evidence.
- Do not encode one project's artifact paths into global memory; keep them in the project profile or local evidence ledger.
