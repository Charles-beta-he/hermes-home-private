# Concurrent verifier hygiene

Use this when autonomous safe-slice work continues while read-only verifiers are still running.

## Problem pattern

A verifier can return `AMEND` because it checked the repo while later safe-slice work was still uncommitted. The target slice and SSOT evidence may be correct, but the verifier's clean-tree gate fails because the workspace has moved on.

Do not treat that as a product defect automatically.

## Classify the AMEND

Classify as `stale-environment-amend-not-product-blocker` only when all are true:

1. The verifier explicitly reports the target commit/code/evidence/loop as OK.
2. The only objective blocker is dirty working tree or HEAD/status mismatch caused by later local safe-slice work.
3. A fresh readback now shows the repo clean except expected `ahead` count.
4. Current HEAD contains the target commit (`git merge-base --is-ancestor <target> HEAD`).
5. No verifier-reported blocker points to the target slice behavior, evidence semantics, negative gates, or certification loop.

If any target-slice behavior/evidence blocker exists, treat it as real AMEND and fix it before continuing.

## Handling steps

Use `scripts/verifier_drain_helpers.py` as a copy/import helper when draining many verifier results; it standardizes git readbacks, redaction, stale-AMEND receipt fields, and L3 verdict skeletons. Still keep each slice's semantic assertions explicit.

1. Fresh readback:
   - `git status --short --branch`
   - `git rev-parse --short HEAD`
   - `git merge-base --is-ancestor <target> HEAD && echo contains_<target>=yes`
2. Re-read the target evidence JSON and latest loop report from SSOT.
3. Write an SSOT receipt under `evidence/certification/` recording:
   - source delegation id
   - target slice and commit
   - original verifier verdict
   - original dirty-tree blocker
   - current clean readback
   - classification `stale-environment-amend-not-product-blocker`
   - action `fresh verifier redispatch required; do not upgrade to L3 from this AMEND`
4. Update project profile and progress ledger with the stale classification.
5. Re-dispatch a fresh read-only verifier against the current clean repo.
6. Do not promote to L3 until a fresh APPROVE arrives.

## Fresh APPROVE resolution

When the re-dispatched verifier returns `APPROVE`:

1. Re-read current status, HEAD, target ancestry, target evidence JSON, and latest loop report before writing the verdict.
2. Write an L3 verdict that explicitly links the fresh verifier and the stale AMEND it resolves, for example:
   - `verifier.delegationId=<fresh-approve-id>`
   - `verifier.verdict=APPROVE`
   - `verifier.resolvesStaleAmend=<old-amend-id>`
3. Upgrade only the bounded slice/component from stale L2 to `L3-local-certified-packet`; do not broaden to push/device/auth/PWA/production.
4. Update the project profile, backlog/index, and progress ledger with the fresh verdict path and current readback.
5. Keep the stale-AMEND receipt; it is useful audit context but is not itself approval evidence.

## Evidence redaction during verifier handling

Before copying values from evidence JSON into receipts/verdicts or final replies, sanitize quasi-credentials and identifiers in URLs or request payload summaries. Redact token/session/cookie/API key/password/secret values and ID-like trade fields such as `tradeId`, `partnerTradeId`, `partnerId`, and `partnerNo` as `[REDACTED]`.

If an existing SSOT evidence artifact already contains raw quasi-credential query parameters, repair the artifact in-place while preserving the verified structure, then mention the redaction repair in the verdict/ledger. The learning is not that the old evidence invalidates the slice; the learning is to prevent durable evidence and replies from carrying reusable identifiers.

## Verifier brief hygiene

When dispatching verifiers while autonomous work may continue, include:

- target commit under review;
- current HEAD and whether later local commits are allowed;
- expected `git status --short --branch` shape;
- instruction to distinguish current dirty workspace from target-slice evidence defects;
- secret redaction requirements;
- open boundaries that are not blockers (push/deploy/device/auth/PWA/production).

## Preview process notifications

Background preview processes from previous slices may exit with SIGTERM after being intentionally replaced. Before treating a preview-exit notification as a blocker, read current process state and hit the local preview URL. If another tracked preview is running and `curl` returns 200, record it as non-blocking and continue.
