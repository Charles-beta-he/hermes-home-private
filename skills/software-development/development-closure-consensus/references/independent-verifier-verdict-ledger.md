# Independent Verifier Verdict Ledger

## Scope

Use this pattern when closure depends on one or more asynchronous, independent reviews of immutable implementation slices. It applies to code, UI behavior, lifecycle fixes, contract parity, and evidence packets where a local pass is not sufficient for the requested certification level.

Anti-conditions:

- Do not use it for a single synchronous reviewer whose verdict is already present and scoped.
- Do not turn model agreement into production/device certification without corresponding runtime evidence.
- Do not let a broad batch result override a newer, narrower review of a later remediation commit.

## Canonical Per-Slice State

Track each slice independently:

```text
slice_id
immutable_target: commit or content hash
local_evidence: RED/GREEN, lint, typecheck, build, runtime, readback
review_request: delegation id + exact scope
review_result: APPROVE | AMEND | NO_VERDICT_CONNECTION_FAILURE | NO_VERDICT_TIMEOUT
remediation: optional later immutable commit/hash
replacement_review: optional delegation id
certification: L2 local | bounded L3 | gated
boundaries: device, backend traffic, auth, production, external side effects
```

A batch is transport, not a certification unit. Certification attaches to an immutable slice or remediation chain, never to “batch complete.”

## Verdict Rules

1. **APPROVE**
   - Promote only the reviewed immutable slice and evidence surfaces explicitly covered.
   - Record negative evidence and unverified boundaries.
   - Do not promote device, production, authenticated, external, or full-project claims from source/browser/local evidence.

2. **AMEND**
   - Keep the target unapproved.
   - Convert each material finding into a deterministic RED where feasible.
   - Implement the smallest safe remediation as a new immutable commit; do not rewrite the old verdict.
   - Re-run local evidence, commit/readback, then request a replacement review of the full chain.
   - Preserve wording such as “base commit AMEND; base+remediation APPROVE” when the replacement passes.

3. **NO_VERDICT_CONNECTION_FAILURE / NO_VERDICT_TIMEOUT**
   - A completed async job with only transport failure, timeout, or no summary is not AMEND and not APPROVE.
   - Record the failure as no-verdict; it changes no certification state.
   - Re-dispatch only unresolved slices, not items already covered by newer explicit verdicts.
   - Narrow replacement reviews to one coherent slice to reduce timeout and context risk.

## Async Completion and Turn Boundaries

An asynchronous verifier is an evidence dependency, not a reason to busy-wait inside one agent turn.

1. Dispatch one coherent replacement review with the exact immutable chain, prior AMEND findings, evidence paths, verdict schema, and certification boundaries.
2. Continue all independent local work: fresh tests/build/runtime, Git readback, SSOT reconciliation, and owned-process cleanup after any live-review need has ended.
3. Do not burn tool iterations on repeated `sleep`, status probes, or duplicate review dispatches merely to keep the turn open. A second reviewer is justified only for real dissent, an explicit no-verdict result, or a deliberately different review dimension—not because the first background result has not yet re-entered the conversation.
4. If every safe local slice is drained and the explicit verdict is still unavailable, persist `PENDING <delegation-id>` plus the immutable target and evidence packet, close as `waiting_acceptance`/evidence-bound continuation, and reconcile the eventual result in the next turn.
5. A provider/auth/setup failure from an alternate reviewer is `NO_VERDICT_*`; record it only in the scoped verdict ledger when it materially explains the fallback path. Never convert it into a durable claim that the reviewer tool is unavailable.
6. On resume, consume the newest explicit verdict first, update profile/evidence/ledger atomically, then run the final Converge readback. Do not redispatch while a valid pending review still covers the unchanged hash.

This async boundary is compatible with continuation discipline: unavailable required evidence after dispatch and drained safe work is a concrete evidence boundary, not a roadmap-phase excuse.

## Precedence and Drift

Use this order when reviews overlap:

1. Explicit verdict on the newest immutable remediation chain.
2. Explicit verdict on an older immutable slice, bounded to that slice.
3. Local verifier evidence (L2 only when independent review is required).
4. Timeout/connection/no-summary result (no verdict; no state change).

A later batch timestamp does not outrank a more specific valid verdict if it produced no decision. Concurrent HEAD movement is acceptable only when the reviewer proves the target commit is immutable and the relevant current source hash still matches, or clearly scopes the verdict to the historical object.

A review request becomes stale immediately when any covered file changes after dispatch—even if the patch is a reviewer-inspired test, redaction fix, or process-cleanup hardening. Recompute the binary-safe hash, rerun every evidence command affected by that change, and dispatch a replacement review of the complete latest slice. The older reviewer may still return useful findings about its historical hash, but it can never approve the newer patch. Record the replacement relation explicitly rather than treating “review is still running” as coverage.

For a dirty multi-repository closeout, stage/review only one root slice at a time when later slices share the same index. Independently hash nested repositories; verify generated lockfiles remain unstaged. After a nested-repository commit, expect the parent repository’s submodule pointer to become dirty and prove that a later path-scoped root commit does not accidentally include it.

## Evidence Reconciliation Checklist

- [ ] Each material finding maps to code/test/runtime/readback evidence.
- [ ] Old AMEND is preserved rather than rewritten as if it never occurred.
- [ ] Replacement commit and reviewer scope are explicit.
- [ ] Baseline lint failures are attributed with immutable blame/diff evidence, not called PASS.
- [ ] Batch transport status is separated from item verdict status.
- [ ] Per-item certification is updated only after an explicit verdict.
- [ ] Evidence JSON, project profile, and progress ledger agree on commit, verdict, level, and boundary.
- [ ] Stale pending delegation IDs are replaced by final status (`APPROVE`, `AMEND`, or `NO_VERDICT_*`).
- [ ] Local preview/test processes remain available only while a live review needs them, then are terminated by exact PID/ownership and ports are read back closed.

## Small UI State-Slice Review Matrix

**Applicability:** narrow frontend changes that add or alter loading, empty, error, fallback, or non-empty content states and require an independent `APPROVE`/`AMEND` verdict.

**Anti-conditions:** skip the runtime branch matrix for prose-only changes or components with no stateful/data-backed rendering. This is a class-level verification pattern; keep project paths, commit IDs, ports, endpoint names, and payload examples in project evidence rather than this skill.

For an applicable UI state change, do not approve from a source-string harness alone. Review the immutable implementation slice against both state branches and the current checkout:

1. **Bind the target** — record the implementation commit, any documentation-only successor commit, and prove ancestry. If HEAD moved, compare the current rendered source blob/hash with the target commit's blob; matching content permits a verdict scoped to that immutable slice, while any mismatch requires a replacement review.
2. **Inspect ownership** — trace the UI value back through its hook/service normalization and request failure behavior. Verify that missing values, rejection, whitespace-only payloads, and cached values cannot bypass the intended state contract.
3. **Run negative runtime evidence** — deterministically block or fail the relevant request and assert the fallback text, visibility/semantics, selected state, and absence of leaked missing-value text.
4. **Run positive runtime evidence** — intercept the same request with a unique cache key/entity and a contract-correct non-empty payload; assert the loading state was observable, the original renderer consumed the payload, and the fallback did not remain visible. Match the real API envelope instead of guessing a fixture shape.
5. **Run structural gates** — whitespace/diff check, typecheck, and production build. Treat pre-existing build warnings as non-blocking only when the reviewed slice does not introduce or worsen them.
6. **Read back cleanliness** — verify no tracked files changed. Note that production builds may refresh ignored output directories; “read-only review” means no source/tracked/evidence mutation, not that build tools perform zero filesystem writes.

Approval is bounded to the exercised local state contract. It does not certify remote content safety, live backend availability, authenticated behavior, device parity, CI, publishing, deployment, or production.

### Pitfalls

- A blocked-request test proves the failure fallback but not the non-empty renderer; require a positive intercepted response too.
- A static check for the renderer proves syntax presence, not that the real response envelope reaches it.
- Reusing the same entity/cache key after a failed or successful probe can produce false evidence; use a unique key or clear the relevant cache.
- Do not stop preview/debug processes merely because they exist. Establish ownership first; preserve pre-existing reviewer infrastructure and only terminate processes started by the current run.

## Reporting Shape

```text
Reviewed slice: <immutable target or chain>
Verdict: <APPROVE|AMEND|NO_VERDICT_*>
Evidence: <fresh commands/runtime facts>
Certification: <L2|bounded L3|gated>
Supersedes: <older pending/AMEND review, if any>
Still unverified: <device/backend/auth/production/etc.>
```

Never report “all reviewers finished” as closure. Report item-level verdicts, unresolved replacements, and exact remaining gates.
