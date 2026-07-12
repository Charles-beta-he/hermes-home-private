# Verifier clean-window retry pattern

Use this when an autonomous local safe-slice queue dispatches independent verifiers while additional local slices may continue in the same repo.

## Problem pattern

A verifier returns AMEND even though target code/evidence are valid because its fresh readback sees later WIP in the same file, or because `local-h5-loop-latest.json` now points to a newer slice. This is an environmental/verifier-brief problem, not automatically a product blocker.

## Classifier

Classify as `stale-environment-amend-not-product-blocker` only when all are true:

1. Target commit is contained in current HEAD:
   - `git merge-base --is-ancestor <target_commit> HEAD` succeeds.
2. Target commit scope is bounded and expected:
   - `git show --name-only --stat <target_commit>` touches only the slice files.
3. Target evidence JSON is still valid and reports negative gates:
   - `ok: true`
   - forbidden requests empty
   - no credential/session read
   - no real order/payment/funds mutation
4. The verifier's blocker is cleanliness or latest-pointer identity only:
   - dirty tree caused by later local WIP, or
   - `local-h5-loop-latest.json` points to a newer slice while a timestamped target loop report exists.

If the verifier reports a product/evidence defect, do not use this classifier; fix the defect first.

## Required receipt

Write a receipt under `ssot_root/receipts/` containing:

- source delegation id
- target slice and target commit
- verifier verdict and exact objective blocker
- fresh `git status --short --branch` and current HEAD
- target-contained-in-HEAD result
- target evidence path
- timestamped target loop report path when available
- classification
- action: re-dispatch fresh verifier; do not upgrade to L3 from stale AMEND
- closed gates: push/deploy/device/auth/production/real funds/order

## Retry verifier brief

Do not require fixed HEAD or fixed ahead count. Use this shape:

- target commit `<sha>` must be contained in current clean HEAD
- `git status --short --branch` must have no staged/unstaged/untracked file rows at verifier read time
- branch may be further ahead due later committed safe slices
- use the timestamped target loop report as identity proof
- `local-h5-loop-latest.json` is only a convenience pointer and may point to a newer slice

## Concurrency guard

If the same file repeatedly causes stale AMENDs:

1. Commit or discard all current WIP.
2. Pause new WIP in that file until the clean-window retry returns.
3. Continue only non-conflicting files/surfaces, or wait.
4. If continuing on a non-conflicting route/surface, run an auth-free preflight before editing or committing. A local smoke that redirects to `/Login` (or otherwise crosses an auth gate) means the candidate is outside the current anonymous safe lane; rollback any WIP and record the gate rather than forcing certification.
5. After APPROVE, write the L3 verdict, resolve stale AMEND ids in ledger/profile, and then resume same-file safe slices.

When a verifier AMEND is caused only by later uncommitted same-file WIP, treat the WIP commit/clean readback as the environmental fix, not a product fix. Write the stale-AMEND receipt, re-dispatch a clean-window verifier, and avoid starting more same-file WIP until that retry has had a clean read window.

## L3 promotion after retry APPROVE

Before writing L3:

- re-read current clean status and HEAD
- verify target commit is still contained in HEAD
- bind verdict to target evidence and timestamped loop report
- explicitly state bounded scope and still-closed gates

Do not treat stale AMEND receipts themselves as approval evidence; only an APPROVE verifier vote can upgrade to L3.