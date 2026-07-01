# Project-Level Authorization Drain Loop

Scope: Hermes/self-architecture or local workflow-control-plane work where the user gives broad project-level authorization after earlier per-slice gates, e.g. “项目级别授权，推进无未授权、未执行项”.

Applicability: local, reversible, auditable project actions: runtime/readback receipts, dry-run scheduler receipts, taskpool import/readback, projection regeneration, tests, stage reports, scoped commits, and exact-target local executor steps.

Anti-conditions: do not use this to bypass credential entry, destructive cleanup, payment, production deploy, push/publish, external dispatch, third-party mutation, service restart, or ambiguous multi-target execution. These still require exact target/adapter/rollback/verification authority or must be blocked with evidence.

## Procedure

1. Re-read prior authorization packets and classify each remaining item by authority class:
   - local readback/API/ledger/projection
   - dry-run scheduler receipt
   - taskpool write-through/idempotent readback
   - claim/worker/runtime executor
   - model call
   - adapter/local outbox
   - external dispatch/publish/destructive
2. Drain every local/reversible class without asking again. Do not stop at progress summaries or “next suggestions” while safe project items remain.
3. For each drained item, produce real readback evidence:
   - receipt/ledger line
   - projection artifact
   - live snapshot/API readback
   - test output
   - scoped commit
4. If a script refuses due exact-target ambiguity, do not guess. Capture the refusal as evidence and land the smallest enabling fix, usually an exact task-id/target selector with TDD.
5. Applicability: local governed workflow chains whose state is represented by multiple same-group records and downstream receipts. Extend every downstream local gate that keys by a broad chain/group identifier with the same exact selector, not just the first failing executor. Typical classes: claim/execution gates, model-call gates, adapter-write gates, and local outbox/apply gates. Exact selectors must fail closed when the selected record does not match the expected chain.
6. If an existing task/candidate is already `archived`, `done`, `review`, `running`, or `blocked`, treat safe replay as closed/idempotent readback rather than failing the whole drain loop or creating duplicates. For terminal `done` records, prefer a readback packet that preserves historical IDs and does not rerun model calls, overwrite adapter records, or mutate status.
7. Anti-condition: idempotent replay must not degrade historical proof artifacts. If a replay path cannot reconstruct the original rich prompt/response/outbox artifacts, do not overwrite the old packet with null/empty placeholders; either write a separate readback receipt or leave the original artifact untouched and record the readback in stage-report/projection.
8. Keep neighboring gates explicit. A project-level grant can cover local project actions, but external/publish/destructive/credential gates still need exact adapter/target/rollback/readback data.
9. Stage-report progress only as durable evidence, then continue the next safe item. A stage report is not a stop point; when the user says to proceed normally without interruption, keep draining safe reversible work and summarize only at completion or at a real boundary.
10. Terminal no-unexecuted closeout: before declaring the drain empty, inspect staged/unstaged/untracked project artifacts and classify each one. Safe local artifacts (schemas, dry-run validators, public-source reports, read-only benchmark dossiers, terminal indexes) should be tested, executed/read back if applicable, staged, and committed. External/publish/destructive/credential actions are not "unexecuted local work"; record them as terminal gates with exact-target authority requirements instead of silently executing or repeatedly suggesting them.
11. Refresh the terminal observability stack after the last local drain: remaining-gates index, candidate-only/backlog projections, fail-closed posture, Control Tower/live snapshot or equivalent. If runtime readiness is degraded only because old read-only probe/gate artifacts are stale, it can still satisfy fail-closed posture when forbidden side-effect observations are all false and tests cover that interpretation.
12. Scoped replay/readback addendum. Scope: local agent-control-plane projects that use prior-session records only as shadow-routing or policy-quality samples. Applicability: after a user gives project-level authorization but the next safe slice reads historical conversation records. Anti-condition: do not use this for full transcript export, durable memory extraction, model training data, or real execution. Treat broad project authorization as insufficient until the user has also authorized this specific prior-record readback class. Once authorized, keep the replay read-only, cap the sample size, truncate previews, redact credential-like/email/payment-like material, assert `would_execute_anything=false`, and test the redaction path with a fixture.
13. Default-off prompt/advisory addendum. Scope: local runtime-adjacent advisory surfaces that only expose readback or shadow analysis. Applicability: safe local drain may include code for a default-off, config-gated advisory prompt plus tests proving the default is off. Anti-condition: do not silently flip the live user config, connect real routing, invoke tools, or open scheduler/worker/lifecycle gates; record those as remaining gates with exact config key, rollback, and readback commands.
14. Commit scoped changes, leaving unrelated dirty files untouched. If the user asked to proceed without interruption, do not summarize between safe slices; report only when local drain is complete or a real boundary remains.

## Verification checklist

- Project-level grant was recorded in a receipt/ledger, not just chat.
- All safe local actions were either executed or produced a concrete blocker with evidence.
- Ambiguous target selection was not guessed; if duplicates exist, an exact selector was added/tested and reused across downstream local gates.
- Idempotent/closed existing records did not create duplicates or overwrite richer historical proof artifacts with weaker replay placeholders.
- External/publish/destructive/credential effects were not smuggled in under broad wording.
- Prior-session replay/readback, when used, is separately authorized, capped, redacted/truncated, read-only, tested, and explicitly reports no execution.
- Default-off advisory prompt work, when landed, proves the default remains disabled and records live config enablement as a separate gate.
- Final readback includes tests, projection/live snapshot or equivalent, stage report, git status, and commit hash.
