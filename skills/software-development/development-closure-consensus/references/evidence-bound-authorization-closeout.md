# Evidence-bound Authorization Closeout Pattern

Use this reference when a control plane adds human approval or closeout authorization before any real execution/write-through adapter exists.

## Durable pattern

1. Treat approval/authorization as a ledger projection, not as execution authority, until an explicit executor boundary exists.
2. Bind every authorization request to a review identifier and a deterministic evidence digest/state hash.
3. Recompute the current evidence digest at request time and reject stale review IDs.
4. Recompute the current evidence digest again at decision time; evidence can become stale between request and approval.
5. Keep expired authorizations unusable, but allow a fresh request row for the same review/hash after the expired row is marked expired.
6. Keep role requirements risk-based and conservative; high/unknown risk defaults to the strongest role.
7. Even an approved authorization must remain non-executing until a separate executor/adapter contract is implemented and verified.

## Pitfalls caught in review

- Checking evidence freshness only at request time allows an approval to be recorded after later conflicting evidence appears.
- Making `(review_id, evidence_hash)` globally unique can prevent fresh re-approval after an expired row. Prefer lookup rules that ignore/expire stale pending rows, or a uniqueness shape that includes terminal status/epoch.
- Role matrices drift toward convenience; assert high-risk levels explicitly in tests.
- A UI button named "approve" can imply execution. Responses and snapshots should repeat `execution = not_executed`, `closeout_allowed = false`, and `closeout_execution_enabled = false` until the execution boundary is intentionally crossed.

## Minimum verification

- Request succeeds only for satisfied, current, non-conflicting evidence.
- Request from an old satisfied review fails after new/conflicting evidence is added.
- Decision fails if evidence changes after request.
- Expired authorization fails closed and can be replaced by a fresh request.
- Approved authorization leaves task rows/adapters unchanged.
- Static scan finds no command execution, adapter write-through, or task done/closeout mutation in the projection-only slice.
