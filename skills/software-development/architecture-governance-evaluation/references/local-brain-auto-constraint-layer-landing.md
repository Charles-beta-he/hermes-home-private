# Local Brain Auto-Constraint Layer Landing Pattern

Applicability: Hermes/local-brain architecture work where the user approves a final long-term stable plan and asks to fully land it, especially when the plan governs knowledge selection, multi-model routing, taskpool/completion gates, or local brain preflight.

Anti-conditions:
- Do not treat this as authorization for runtime hard gates, scheduler/worker/lifecycle mutation, external dispatch, publish/deploy/push, destructive actions, payment, credential entry, or broad fanout.
- Do not create a standalone side-plan as the final artifact when the user asked to improve the canonical main plan. Side reviews and auxiliary capabilities must fold back into the main SSOT.
- Do not claim multi-model certification from a degraded/single-model/advisory result.

## Procedure

1. Re-anchor on the canonical main SSOT.
   - Identify the document/profile/ledger that is the target of the stable plan.
   - If an auxiliary review document or sub-plan exists, treat it as supporting evidence and fold its durable objects back into the main SSOT.

2. Split the landing boundary.
   - P0: stable document/schema/contract.
   - P1: local dry-run CLI/schema with no external or lifecycle side effects.
   - P2: workflow/taskpool/completion-claim consumer wiring, still advisory/block-local.
   - P3+: runtime hard gate only after explicit authority, rollback, metrics, and readback.

3. Use TDD for the first executable slice.
   - Write RED tests for multi-vault retrieval, stale-vs-current filtering, RouteReviewRecord/BrainConstraintRecord output, T2/T3 degraded behavior, and side-effect flags staying false.
   - Watch the tests fail before implementation.
   - Implement the smallest local dry-run CLI that passes.

4. Preserve evidence and role boundaries.
   - Model review is advisory unless claim-linked non-model evidence and quorum are present.
   - Producer/self-report cannot certify completion-critical claims.
   - not_certified/degraded_not_certified can guide repair but cannot mark taskpool done or release runtime gates.

5. Verify the live local boundary.
   - `py_compile` the script and tests.
   - Run focused unit tests and the adjacent existing suite.
   - Run the architecture/ratchet gate if the plan touches architecture propagation.
   - Run a real CLI smoke with `--json`; assert parseable BrainConstraintRecord and RouteReviewRecord plus explicit side-effect flags false.
   - Reindex/search the local brain and confirm the canonical plan is accepted, not filtered.

## Pitfalls

- Brain/search summaries may include verbs such as “强化/完善/修改” that canonical notes do not contain. Use recall-oriented query expansion over stable nouns/surfaces/filenames instead of a single AND-style full-summary query.
- Canonical policy documents may mention stale/weak markers as filtering criteria. If frontmatter says `active-stable` or `stability_class: long_term_canonical_plan`, do not demote the policy itself merely because it mentions `without tests`, `no proof`, or similar markers.
- Updating a side review only is the wrong direction when the user’s target is the main all-constraint-layer plan.

## Verification checklist

- [ ] Main SSOT updated, not only a side document.
- [ ] First executable slice is local dry-run and side-effect flags are false.
- [ ] RED/GREEN evidence exists for retrieval, filtering, route review, and degraded gates.
- [ ] Canonical active-stable policy is searchable and accepted.
- [ ] Ratchet/selfcheck still passes.
- [ ] Commit is scoped to implementation, tests, and canonical documentation.
