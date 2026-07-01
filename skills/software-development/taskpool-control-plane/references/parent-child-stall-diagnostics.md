# Parent/child stall diagnostics

Scope: reusable taskpool-control-plane procedure for systems where parent task notes reference child task notes and completion is guarded by proof/certification gates. This is not tied to any project, repository, task ID, branch, URL, or environment path.

Applicability:
- A parent remains blocked after child work appears complete.
- Resolver output does not explain whether the blocker is child state, stale evidence, claim lifecycle, concurrency boundary, or certification.
- The operator needs a fail-closed diagnosis before any lifecycle mutation.

Anti-conditions:
- Do not force-close parent tasks.
- Do not bypass proof, UI/browser proof, or multimodel gates.
- Do not treat degraded model fanout as certification.
- Do not increase concurrency before classifying parent/child evidence state.

Reusable diagnostic states:
1. Child still open.
2. Child reference missing or unreadable.
3. Parent proof log has stale child-status receipts.
4. Child is done but parent lacks child/axis backfill proof.
5. Direct child is done but a descendant is blocked.
6. Children are structurally ready but parent certification is still required.
7. Derived status views disagree with canonical task notes.
8. Claim slot is stale or workerless.
9. Certification artifact is missing or pruned.
10. Model output is advisory because quorum/noop-vs-change is unresolved.

Preferred resolver behavior:
- First return read-only aggregation fields: readiness, action, suggested next step, child counts, missing/open children, stale evidence count, and safety note.
- If children are ready but certification remains required, keep the parent blocked and suggest parent ratification refresh.
- If children are missing/open, keep the parent blocked and suggest child recovery/completion.
- If stale receipts exist, report them; do not certify from old evidence.
- Lifecycle mutations and evidence backfill must be separate governed commands.

TDD checklist:
- Build a minimal parent + child fixture.
- Assert the resolver/aggregator emits the expected diagnostic fields.
- Assert no parent done/force-close transition occurred.
- Assert the suggested next step is explicit.
- Run focused tests, syntax checks, and coverage for the standalone aggregation slice where practical.

Next detectors worth adding:
- Parent evidence backfill missing.
- Hidden blocked descendant.
- Missing child file.
- Stale claim occupancy.
- False concurrency contention.
- Derived status mismatch.
- Cyclic or too-deep split tree.
- Durable certification artifact receipt.
