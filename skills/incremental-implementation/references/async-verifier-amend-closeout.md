# Async verifier AMEND closeout

Use when independent review receipts arrive asynchronously or out of order while local implementation continues.

## Receipt classification

1. Bind every receipt to its immutable target commit(s), delegation ID, scope, and dispatch time.
2. Compare that target with the current branch; a stale receipt may still certify or amend its immutable ancestor, but it is not evidence for later commits.
3. Never overwrite a newer pending review with an older batch result. Record verdicts per slice/commit chain.
4. If a receipt identifies the next safe slice rather than reviewing the active slice, treat it as backlog evidence; finish the active closeout gate first unless autonomous continuation explicitly permits another isolated slice.

## AMEND loop

1. Read the full finding, not only the truncated notification.
2. Create a focused RED that reproduces the exact truth-table or lifecycle defect.
3. Make the smallest follow-up commit; do not rewrite the reviewed ancestor.
4. Run focused GREEN, build/typecheck, diff check, commit readback, and the project certification loop.
5. Update evidence with the original AMEND, resolution commit, RED/GREEN facts, and remaining boundaries.
6. Re-dispatch review against the immutable ancestor + follow-up chain. Keep the chain at L2 until explicit APPROVE.

## Baseline-aware lint classification

When changed-file lint fails outside the modified hunk:

- use `git blame` and parent-commit comparison to establish whether the diagnostic predates the slice;
- record `BASELINE_ONLY_FAILURE`, the exact lines/rule/blamed commit, and that changed lines have no diagnostic;
- never rewrite an earlier `scoped lint PASS` claim if fresh lint actually exits nonzero—supersede it explicitly;
- a baseline-only failure does not become a clean lint pass, but it also should not be misattributed as a regression.

## Closure

Promote only the bounded slice covered by the APPROVE. Keep device, production, credentials, remote writes, orders/funds, push/deploy, and full-parity claims separate. Delay process cleanup until all runtime-dependent reviewers finish; then terminate only exact owned listeners and read back closed ports.
