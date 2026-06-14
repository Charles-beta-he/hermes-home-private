# Runtime open gate: limited unattended external action

## Scope / applicability

This reference applies to governed taskpool/self-evolution work where the user explicitly authorizes proceeding beyond dry-run toward an opened runtime boundary, and the next boundary may perform a real but narrowly-scoped external action.

It is intentionally class-level: examples below avoid project names, fixed paths, branch names, message IDs, or hashes. Put concrete artifacts in the task note or scoped project evidence, not in the global skill.

## Landing-zone classification

- Reusable procedure / verification checklist → this skill reference.
- Concrete paths, receipt IDs, hashes, branches, and one-session outcomes → task note or scoped project evidence only.
- Concrete follow-up engineering work, such as broader dispatch or scheduler rollout → taskpool candidate/proposal.
- Session progress narrative → no durable write.

## Safe opening sequence

1. Re-baseline the pool first: active list, next candidate, dispatch dry-run, selfcheck, proof-check, and async/advisory jobs.
2. Model the smallest openable boundary. Prefer one target, one purpose, one payload template, one rate limit, one receipt ledger, one explicit compensation path.
3. Require an explicit open manifest with:
   - exact confirmation string or equivalent authority token;
   - readiness checks over prior artifacts;
   - manifest digest / contract packet;
   - target allowlist;
   - kill switch state;
   - idempotency basis;
   - rate limit;
   - receipt ledger path;
   - compensation path.
4. Verify dry-run readiness before executing the external action.
5. Execute exactly one real action through the governed runner when authorized.
6. Immediately re-run the same command to prove duplicate / rate-limit blocking.
7. Record both the positive receipt and negative duplicate proof in the task note.
8. Re-run pool verification: active list, next, dispatch dry-run, selfcheck, proof-check, async/advisory jobs.
9. Commit only scoped files for the open gate and evidence. Do not mix unrelated dirty worktree changes.

## Closeout guard: advisory jobs can re-open lifecycle

When a task is in a self-evolution lane or has architecture/mission-envelope fields, transitions to review may spawn advisory closeout ratification. That background job can temporarily move the task back to running while it owns the lifecycle.

Rules:

- After moving to review, poll the async/advisory job list until no jobs are alive before final done.
- Do not force done while an advisory job is alive unless explicitly repairing a stale lifecycle wedge.
- If a duplicate advisory job is spawned after closeout, inspect its job/log/state evidence. If it has no log progress and exceeds the normal command timeout, terminate it as stale and re-run pool verification.
- Treat the lesson as "wait for/clean up advisory lifecycle ownership", not as a reason to disable advisory ratification globally.

## Evidence bundle

Minimum evidence for a real opened boundary:

- implementation files + hashes;
- manifest artifact + hash;
- receipt ledger + hash;
- real external receipt ID / API response;
- duplicate/rate-limit block proof;
- tests for confirmation mismatch, manifest validation, one-shot execution, duplicate block;
- syntax/type check;
- taskpool selfcheck and proof-check PASS.

## Anti-conditions

Do not use this pattern to silently open broad unattended automation. Stop and create a separate task/gate for:

- more than one target;
- cross-adapter dispatch;
- repeated scheduled real actions;
- arbitrary payload generation;
- credential reads/writes;
- destructive actions;
- missing compensation path;
- missing duplicate/rate-limit proof.
