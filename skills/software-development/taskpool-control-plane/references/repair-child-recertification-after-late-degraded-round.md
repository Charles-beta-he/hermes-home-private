# Repair-child recertification after a late degraded round

Use this when a taskpool repair child was already certified or even closed, then a later autorun/multimodel review-close round writes it back to `blocked` with `degraded_not_certified`.

## Class of failure

A later certification round can be semantically narrower or differently framed than the original closeout. Common shape:

- Earlier artifact: `status=certified`, `fanout_certification.certified=true`, all/most votes approve.
- Later artifact: `status=degraded_not_certified`, but `truth_assessment.truth_status=grounded` and `evidence_coverage=1.0`.
- Later blockers are not contradictory implementation evidence, but certification framing issues such as:
  - `planner fan-out below min_quorum`
  - no-action/noop patch list counted as sub-quorum
  - missing `best_within_constraints` signatures because the packet was framed as a new implementation rather than evidence reconciliation.

Do not force-close the task and do not relabel the degraded artifact as certified.

## Recovery workflow

1. Reconstruct the timeline from the canonical task note:
   - earlier PASS/certified artifact;
   - lifecycle transitions into `review`/`done`;
   - later degraded artifact and its writeback reason.
2. Inspect both artifacts:
   - Compare `status`, `fanout_certification`, `truth_assessment`, `agreement_matrix`, `issue_ledger`, `remaining_risks`, and `planner_patch_summary`.
   - If the later artifact has `truth_status=grounded` and `evidence_coverage=1.0`, classify the remaining issue as a certification/framing blocker, not a missing-proof blocker.
3. Search for requested fanout/source diagnostics (e.g. `source_hash`, failed planner records). If absent, record that search result; do not invent planner failure causes.
4. If the task objective is already satisfied by a parent closeout, rebuild the state packet as a **no-action evidence-reconciliation packet**:
   - Explicitly state scope: repair-child reconciliation after parent done.
   - Include claim-linked evidence for parent closeout, prior certified artifact, later degraded artifact, and current control-plane health.
   - State non-goals: no new implementation, no quorum-threshold changes, no degraded-artifact relabeling.
   - Back up the previous state file before writing the new packet.
5. Rerun the governed certification path (`multimodel-intervention-step`) rather than editing task status by hand.
6. Only after gate `PASS` and decision `LOOP_DONE`, transition `review -> done` through normal lifecycle with evidence referencing the new artifact and the underlying parent proof.
7. Reconcile Kanban projections afterwards. A stale blocked mirror for a source-done note should be completed as projection repair, with metadata explaining `blocked_projection_for_done_source`.
8. Final verification: active list, `selfcheck`, `proof-check`, `boundary-check`, `v_state`, and scoped git status.

## Anti-conditions

Do not use this pattern when:

- the later degraded artifact has unsupported or contradicted high-severity factual claims;
- parent/task closeout proof is missing;
- the repair child still has real implementation work to do;
- the only available evidence is model agreement without linked artifacts;
- a credential, permission, or production-write boundary is involved.

In those cases produce a human gate or taskpool intervention packet instead.
