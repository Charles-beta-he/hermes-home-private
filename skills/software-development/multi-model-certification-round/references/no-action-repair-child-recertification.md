# No-action repair-child recertification

Use this when a taskpool repair child or closeout reconciliation task was previously certified/closed, but a later certification run writes it back to blocked or degraded because the packet was framed like a new implementation rather than no-action evidence reconciliation.

## Recognition pattern

- The later round reports `truth_status=grounded` and `evidence_coverage=1.0`.
- The failures are certification/framing issues, not contradicted facts:
  - `planner fan-out below min_quorum`
  - `best_within_constraints_missing` on a noop/no-action packet
  - low agreement caused by whether to treat noop as certification
- A prior certified artifact or parent closeout artifact exists and is hash-verifiable.

## Repair steps

1. Do **not** relabel the degraded artifact as certified and do **not** lower quorum.
2. Compare prior certified artifact vs later degraded artifact: status, fanout certification, truth assessment, issue ledger, remaining risks, votes, and planner patch summary.
3. Search for requested source/fanout diagnostics. If the `source_hash` or failed planner records are absent, record that absence rather than inventing failure causes.
4. Rebuild the state packet with explicit scope:
   - `certification_intent: no_action_certification`
   - `closeout_scope: repair_child_reconciliation_after_parent_done` (or equivalent)
   - non-goals: no new implementation, no quorum changes, no degraded-artifact relabeling
5. Add claim-linked evidence at the top-level evidence array:
   - parent/repair closeout proof;
   - prior certified artifact;
   - later degraded artifact and its exact failure mode;
   - current control-plane verification.
6. Rerun the governed certification command. Only if it returns gate `PASS` and `LOOP_DONE`, let the taskpool lifecycle proceed normally.
7. If it still fails, produce an evidence request or human gate; do not force status.

## Vote guidance

For a no-action recertification packet, empty patch lists are acceptable only when:

- the packet explicitly requests evidence reconciliation rather than implementation;
- claims are verified by linked evidence;
- no unresolved severity >= 3 truth blockers remain;
- the final status is a real certification from the rerun, not a renamed degraded artifact.
