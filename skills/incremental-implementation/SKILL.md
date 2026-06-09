---
name: incremental-implementation
description: Use when implementing a task in small verifiable slices instead of a single large change.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - implementation
    - slicing
    - testing
    - delivery
    related_skills:
    - test-driven-development
    - source-driven-development
    - writing-plans
---

# incremental-implementation

## Overview


One slice at a time. Each slice: build → test → ship (or stash as done). Never build the whole thing before testing anything.

## When to Use

- Implementing a task in small verifiable slices instead of a single large change
- Don't use for: requests that do not need implementing a task in small verifiable slices instead of a single large change; choose a more specific child skill or a broader routing skill that actually matches the task.
## Slice Rules

1. Each slice is independently verifiable (has its own test)
2. Each slice is < 50 LOC changed (if bigger, split)
3. Each slice touches only one concern (one function, one component)
4. Don't start slice N+1 until slice N passes all tests

## Process

```
FOR each slice:
  1. Build: implement minimal working version
  2. Test: run relevant tests + new test for this slice
  3. Verify: does it work end-to-end for this slice?
  4. Commit: atomic commit with slice description
  5. Next: only proceed if all tests green
```

## Slice Sizing

| Task Type | Ideal Slice Size |
|-----------|-----------------|
| Add endpoint | 1 route → 1 handler → 1 test |
| Add component | 1 component → 1 story → 1 test |
| Refactor | 1 function extracted → 1 test adjusted |
| Bug fix | 1 failing test → 1 fix → test passes |

## Mock-to-Real-API Vertical Slice Pattern

Use this when a prototype or mock-heavy page must be converted to production data without destabilizing the surrounding app.

1. Start with the narrowest end-to-end slice that already has a clear backend truth source.
   - Prefer pages where the backend controller / DTO / domain fields already exist.
   - Avoid starting with the visually biggest page if its data contract is still ambiguous.

2. Land the service-layer contract first.
   - Extend the existing frontend service module instead of inventing page-local fetch code.
   - Normalize backend shapes once in the service layer so multiple pages can reuse them.

3. Wire one page at a time.
   - Replace mock data on a single page.
   - Keep the page layout mostly stable; change the data source before redesigning UI structure.

4. Add backend bridging only when needed.
   - If the raw integration client is not suitable for admin/UI use, add a thin admin-facing controller/facade that preserves permission checks and existing response conventions.
   - Prefer reusing existing config storage / audit / GA flows over introducing new schema or ad hoc endpoints.

5. Adapt real backend shapes at the edge, not deep in the UI.
   - If the page already renders against a prototype/mock type, add one adapter function from API DTO → page contract.
   - Preserve existing table/detail rendering first; migrate field truth sources before redesigning component structure.
   - When a placeholder field is derivable but not explicitly returned (for example purpose/source derived from wallet keys, pair presence, or linked journal IDs), centralize that derivation in the adapter instead of scattering heuristics across the page.
   - Treat empty API responses as real state: explicitly clear lists/totals instead of only updating state on non-empty responses.

6. Extract reusable reference components when replacing placeholders across multiple surfaces.
   - If the same placeholder logic appears in both table rows and detail drawers (for example counterparty resolution), factor it into a reusable reference component/helper instead of duplicating click/match heuristics.
   - Prefer a single matching function that checks multiple durable identifiers (name/code/userId/account/address/external payee id) over fragile substring-only matching.

7. Verify both sides immediately after each vertical slice.
   - Run the frontend build/typecheck for the touched app.
   - Run the narrowest backend compile/test command that exercises the changed module graph.
   - If the repo requires a pinned runtime, invoke the build with the repo-declared runtime rather than assuming the shell default is correct.

8. Only then move to the next page.
   - Typical order: service contract → page A → dashboard/summary consumers → neighboring detail pages.

See also: `references/mock-to-real-api-vertical-slices.md` and `references/admin-prototype-to-real-api-page-conversion.md`.

## Template-variable hydration bugfix slice pattern

Scope: any templated outbound artifact (email, notification, PDF, SMS, in-app message) where delivered output exposes raw placeholder syntax or a field renders in one channel but not another.

Applicability:
- The template is persisted or editable separately from the code that supplies variables.
- The same business event can fan out through multiple renderers or channels.
- Missing-variable behavior may leave placeholders visible instead of failing closed.

Anti-conditions:
- Do not encode one product's exact template codes, branch names, or migration file names in this global skill.
- Do not treat this as a license to weaken template text; preserve user-facing meaning and security intent while adding fallbacks.
- Do not expose PII as a fallback; mask identity fields before adding shared defaults.

Process:

1. Treat the screenshot/UI symptom as a contract bug, not just copy or CSS.
   - Trace the chain: template definition → event/caller vars → dispatcher/enricher → renderer missing-variable behavior → delivered artifact.
   - Compare sibling channels for the same event; one channel may pass the full variable set while another passes only a subset.

2. Fix the narrow caller first.
   - Build an explicit variable map for the affected event containing every variable used by the template.
   - Add null/blank fallbacks before insertion; avoid null-rejecting map factories when any value can be absent.
   - Prefer stable subject/body wording that does not depend on unreliable enrichments such as IP geolocation.

3. Add a shared enrichment layer only for truly common user-context variables.
   - Good defaults include a generic display-name fallback and a masked email fallback when the user object is available.
   - Calling code should still own event-specific fields such as address, location, device, amount, timestamp, or reference id.
   - Caller-provided values must win over dispatcher defaults.

4. Test both levels.
   - Caller test captures the map passed to the dispatcher and asserts template-required event variables plus fallbacks.
   - Dispatcher test captures the map passed to the renderer and asserts shared identity fallbacks/masking.
   - If available, keep or add renderer-level tests that fail when final output still contains raw placeholder syntax.

See also: `references/template-variable-hydration-bugfix.md`.

## Ledger-only executor consumer slice pattern

Scope: domain-level pattern for workflow/control-plane systems that are adding their first bounded executor after a separate eligibility or policy-review projection.

Applicability:
- The executor is intentionally limited to read-only or no-external-side-effect actions.
- A durable ledger stores command, plan, policy-review, run, and audit-event state.
- The next authority boundary would be adapter write-through, lifecycle mutation, shell execution, or closeout.

Anti-conditions:
- Do not use this as permission to execute arbitrary commands or mutate external systems.
- Do not apply exact tuple matching blindly if the reviewed action does not depend on payload/target identity; choose the tuple fields that define the reviewed authority.
- Do not turn project-specific command names into global requirements; keep whitelist names in the local reference or project docs.

Falsifier:
- If later architecture uses cryptographic plan digests or immutable command snapshots, replace exact tuple re-checks with the stronger digest/snapshot contract.

Process:

1. Keep the first consumer ledger-only.
   - It may insert run rows and audit events in the control-plane ledger.
   - It must not write adapters, close tasks, mutate external task lifecycle state, or run arbitrary shell.

2. Gate execution on durable plan + policy state.
   - Require the executor plan to still be planned/not-executed and write-disabled.
   - Require a policy review that is explicitly read-only eligible, allowed, and write-disabled.
   - Require the command to still be in the expected pre-execution ledger state.

3. Treat policy freshness as exact tuple matching, not just class eligibility.
   - Persist the reviewed/generated command tuple in the plan, including the fields that define authority, typically command type, risk level, and payload.
   - Before execution, re-read the current command and require exact tuple equality with the generated plan.
   - Recompute read-only eligibility from the current tuple.
   - Fail closed even if a stale command changed from one allowed low-risk type to another allowed low-risk type.

4. Make idempotency concurrency-safe.
   - Use a unique run key such as `plan_id`.
   - Return an existing run on ordinary retry.
   - Catch unique-constraint races and re-read the existing run before raising.

5. Verify the boundary explicitly.
   - Tests must assert no task rows/lifecycle state and no adapter observations/writes changed.
   - Smoke tests should create command → plan → policy review → read-only run → repeated run, then inspect ledger rows/events.

See also: `references/control-plane-read-only-executor-consumer.md` for the session-specific command whitelist and verification bundle that motivated this pattern.

## Evidence-bound ledger closeout consumer slice pattern

Scope: workflow/control-plane systems that promote a previously non-executing evidence/authorization projection into the first lifecycle-affecting action while keeping external adapters disabled.

Process:

1. Keep the first closeout consumer ledger-local.
   - It may insert closeout run rows, append audit events, and update the control-plane ledger task status.
   - It must not write taskpool/Kanban/external adapters, run arbitrary shell, or enable rollback/reopen in the same slice.

2. Gate execution on authorization and evidence freshness.
   - Require an approved authorization, actor role still satisfying the required role, and unexpired TTL.
   - Recompute the current task evidence hash and require exact match with the authorization-bound hash.
   - Re-read the evidence gate review and require satisfied/non-conflicting status plus the same evidence hash.
   - Require the ledger task row to exist and not already be closed unless an existing execution run makes the retry idempotent.

3. Make closeout idempotent and auditable.
   - Use a unique key such as `closeout_authorization_id` on the execution table.
   - Return the existing run on ordinary retry and on unique-constraint races.
   - Record explicit `adapter_writes=[]` and `external_adapter_write_through_enabled=false` in both run rows and snapshots.

4. Verify the boundary explicitly.
   - Tests must cover unapproved authorization, stale evidence after approval, insufficient role, expired authorization, missing task row, closed-without-run task row, ordinary retry, and no adapter observations/writes.
   - Smoke should create evidence -> satisfied gate -> authorization request -> approval -> ledger closeout -> retry, then inspect task status, run count, adapter rows, and event sequence.

## Agent architecture coverage contract slices before runtime execution

When evolving an agent/control-plane architecture to absorb external executors (Claude Code, Codex, OpenCode, delegate workers), land contract/projection slices before enabling execution authority:

1. Start with a report-only coverage matrix in code, not just prose. Include capability, existing control-plane anchor, external-agent leverage, coverage status, next safe slice, authority boundary, and priority.
2. Validate worker result contracts before dispatch integration. Worker output may be accepted only as evidence/proposal; reject fields that smuggle authority such as lifecycle status, mark-done flags, external writes, memory/skill writes, provider config changes, or outbound messages. Successful results must carry evidence references.
3. Validate fork/join graphs as ledger projections before runtime fanout. Check node IDs, dependencies, duplicate IDs, cycles, join arity, and join evidence requirements. A valid graph still reports runtime dispatch and lifecycle mutation disabled until a separate governed executor slice exists.
4. Validate multi-model certification packets before using consensus. Require quorum, at least two reviewers, truth gate enabled, and claim-linked evidence references. Model consensus remains non-fact and cannot mark done by itself.
5. Keep every slice side-effect free until the next boundary is explicitly authorized: no worker dispatch, lifecycle mutation, external adapter write-through, persistent learning write, or automatic done.
6. Verify with focused unit tests, py_compile, CLI/smoke probes for the contracts, `git diff --check`, then make a scoped commit containing only the contract slice.

## First real runtime start after agent architecture contracts

When agent/control-plane contract slices are complete and the user explicitly authorizes moving to a “real and started” boundary, the next safe slice is a ledger-only runtime start, not external worker invocation.

1. Add a durable run-start consumer that appends a bounded run record to the local ledger (JSONL or table) and returns a structured `started` result.
2. Keep the boundary narrow and explicit: record `runtime_boundary="started_ledger_only"`, `run_status="started"`, deterministic `run_id`, request digest, worker identity, task ref, evidence refs, and timestamp.
3. Make retries idempotent by matching the same request digest and returning the existing run instead of appending a duplicate row.
4. Reject authority smuggling before writing the run: lifecycle fields (`task_status`, `lifecycle_status`, `mark_done`), external writes, persistent learning writes, outbound messages, and provider/config changes must fail closed and leave the ledger untouched.
5. Preserve the safety flags in both return payload and ledger row: external executor invoked=false, canonical lifecycle unchanged=true, lifecycle mutation=false, external adapter write-through=false, persistent learning write=false.
6. Add a CLI smoke path that actually writes a temporary ledger row and read it back. This proves the boundary is real/startable without crossing into worker execution.
7. Update the coverage/SSOT language from pure report-only to “runtime boundary started”, but keep the next boundary explicit: governed worker executor behind policy gate, lease/readback, stop/timeout, artifact capture, and failure taxonomy.
8. Verify with RED tests for started/idempotent/rejected paths, py_compile, focused tests, CLI smoke, diff check, and a scoped commit. Stop before external executor invocation, task lifecycle mutation, or adapter write-through unless a separate gate authorizes that slice.

## Agent runtime executor ratchet after ledger-only start

When an agent/control-plane architecture has already landed contract validations and a ledger-only runtime start, promote runtime capability one authority boundary at a time. Each step must have RED tests, focused smoke, hot-path bounded evidence, and a scoped commit before the next boundary opens.

1. First consume a started run with a governed builtin read-only executor.
   - Re-read the run ledger and require a matching `run_status="started"` row.
   - Allow only named builtin executor/action pairs; reject unknown executors without appending ledger rows.
   - Append a completed run result with `external_executor_invoked=false`, lifecycle mutation disabled, adapter write-through disabled, and evidence refs preserved.

2. Then probe external agent binaries without task prompts.
   - Maintain an executor-type to binary-basename allowlist (for example `claude_code -> claude`, `codex -> codex`, `opencode -> opencode`).
   - Invoke only a fixed benign command such as `--version`; never accept arbitrary command strings.
   - Append a probe receipt to the ledger, but keep `task_prompt_sent=false`, tools disabled, lifecycle unchanged, and adapter write-through disabled.

3. Then allow no-tool/no-write external prompt dry-runs.
   - Require a previously started run, executor allowlist match, non-empty prompt, artifact path, and evidence refs.
   - Force the external agent into constrained/no-write mode (`--permission-mode plan`, empty tools list, no session persistence, structured output where available).
   - Reject prompt requests that smuggle authority fields such as lifecycle status, mark-done, external writes, memory/skill writes, outbound messages, provider config, or tools/write mode flags.
   - Capture full stdout/stderr into an external artifact; the hot ledger stores only `artifact_uri`, sha256, size, bounded summary, and evidence refs.

4. Then allow readonly context artifact packets.
   - Require a previously started run, executor allowlist match, non-empty instruction, `context_artifact_uri`, `context_sha256`, output artifact path, and evidence refs.
   - Pass only the context artifact URI/hash into the agent prompt; reject inline context so large evidence never enters the hot ledger or prompt builder by accident.
   - Recompute and verify the context artifact SHA-256 before invoking the agent.
   - Keep the same no-tool/no-write invocation constraints as prompt dry-run; capture stdout/stderr into an output artifact and append only context/output pointers, hashes, bounded summary, and evidence refs to the ledger.
   - Reject tool/write flags and authority-smuggling keys before process invocation.

5. Then accept external proposal artifacts, not facts.
   - Require a previously started run and a proposal artifact URI/hash; recompute SHA-256 before appending.
   - Accept only review proposals (`proposal_type="worker_review_proposal"`, `lifecycle_target="review_proposed"`) with non-empty summary, failure classification, top-level evidence refs, and claim-level evidence refs.
   - Reject `done`, lifecycle status, mark-done flags, external writes, memory/skill writes, outbound messages, provider/config changes, and any tool/write authority smuggling.
   - Append only proposal artifact pointer/hash/summary/counts to the ledger; preserve `allowed_to_mark_done=false`, lifecycle mutation disabled, adapter write-through disabled, and persistent learning disabled.

6. Then accept multi-model certification promotion packets, still not done.
   - Require a started run plus an already recorded proposal artifact.
   - Require certification artifact URI/hash and verify it binds to the recorded proposal artifact URI/SHA-256.
   - Require at least two reviewers, `quorum >= 2`, `quorum <= reviewer_count`, `truth_gate=true`, reviewer evidence refs, and claim evidence refs.
   - Allow only `lifecycle_target="certification_passed_for_review"`; preserve `model_consensus_is_fact=false`, `allowed_to_mark_done=false`, and lifecycle mutation disabled.
   - Append only certification pointer/hash/summary/reviewer_count/quorum/truth_gate/claim_count to the hot ledger.

7. Keep the next unopened boundary explicit.
   - After certification promotion, the still-closed boundary is human/elevated policy done authorization, lifecycle mutation, external tools, workspace file reads/edits, shell execution, adapter write-through, rollback/reopen, and automatic done.
   - Do not open readonly tools, writes, rollback/reopen, or automatic done in the same slice as proposal or certification promotion.

See also: `references/agent-runtime-boundary-ratchet.md` for the Claude Code/Codex/OpenCode runtime progression and smoke-verification bundle that motivated this pattern.
See also: `references/agent-runtime-proposal-certification-ratchet.md` for proposal artifact intake and multi-model certification promotion packet requirements.

## External adapter write intent before write-through

When the next boundary is an external adapter mutation, add an intermediate intent projection rather than writing the adapter immediately:

1. Create a ledger-only `*_write_intents` table with immutable blocked defaults (`writes_enabled=0`, `external_adapter_write_through_enabled=0`, rollback required, rollback unavailable) and SQLite `CHECK` constraints enforcing those flags.
2. Bind each intent to the completed internal ledger action, target adapter, external ref, canonical mutation payload, and a SHA-256 digest of canonical JSON.
3. Fail closed on missing completed internal action, unsupported adapter, insufficient actor role, task row drift, and external-ref mismatch.
4. Make preparation idempotent with a UNIQUE tuple such as `(closeout_execution_id, adapter_name, external_ref)` plus IntegrityError retry readback.
5. Snapshot and dashboard may display/prepare the intent, but must label it as blocked/projection-only and keep external writes disabled.
6. Verification: recompute digest in tests, assert adapter observations/external state stay unchanged, smoke event chain includes intent-prepared event, and run an independent review before commit.

## External adapter write readiness review before write-through

When an intent exists but real adapter writes/rollback are still unsafe, add a separate readiness review projection:

1. Create a ledger-only review table keyed uniquely by intent id.
2. Bind review rows to the exact intent id, mutation digest, adapter, operation, and adapter contract version.
3. Enforce blocked behavior with DB checks: `review_status='blocked'`, `write_through_allowed=0`, `writes_enabled=0`, `external_adapter_write_through_enabled=0`, and rollback still required.
4. Before insert, recompute the canonical mutation payload digest and fail closed on drift, unsupported actor role, missing source, unknown adapter/operation, or unexpected write flags.
5. Append a reviewed event and return idempotent existing reviews on retry; do not mutate adapter observations or external lifecycle state.
6. Verification: tests cover happy path, retry, digest drift, unsupported actor/missing intent, zero external adapter rows, snapshot blocked counts, and smoke ending in a readiness-reviewed event with write-through disabled.

## External adapter write authorization before write-through

When a readiness review exists but real adapter mutation is still unsafe, add a separate non-executing authorization projection rather than enabling writes:

1. Bind authorization rows to review id, intent id, adapter contract version, and mutation digest.
2. Require admin role (or stronger local policy) for request and decision.
3. Add TTL and revalidate freshness on both request and decision: current canonical payload digest must still match the review-bound and authorization-bound digest.
4. Enforce disabled behavior with DB checks: `writes_enabled=0`, `external_adapter_write_through_enabled=0`, `rollback_available=0`, and `write_through_allowed=0`.
6. If adding external write authorization before real write-through, make it a second ledger-only projection after readiness review: bind authorization to review id + adapter contract version + mutation_digest, require admin role, add TTL, keep `write_through_allowed=false`, `writes_enabled=false`, `external_adapter_write_through_enabled=false`, `rollback_available=false`, and add tests for expired duplicate requests so stale requested rows are not returned after TTL.
7. If adding command execution preflight before real external write-through, persist a canonical command execution payload + digest but keep executor/write-through disabled by DB CHECK (`external_write_executor_enabled=0`, `write_through_allowed=0`, `rollback_available=0`). Runtime gates must re-check all source rows, not just the new table: authorization flags, readiness-review flags, intent flags, TTL/status, and mutation digest. Add a drift test that bypasses DB CHECKs (e.g. SQLite `PRAGMA ignore_check_constraints = ON`) to prove source intent flag drift fails closed.
8. If enabling the first real external write executor, keep it adapter/operation-specific (for example Kanban closeout only), consume an approved preflight by exact `command_execution_digest`, and before mutation compare every digest-bound payload field back to the mutable preflight/run columns (`external_ref`, adapter, operation, ids, contract version, mutation digest). Add an adversarial target-drift test with a second valid adapter target to prove the executor cannot close the wrong target while preserving the old digest. Store rollback snapshots if useful, but keep rollback/reopen disabled until a separate governed slice.
9. If enabling rollback/reopen after a real write-through slice, do it as its own governed consumer slice. Bind rollback to the completed write run and exact command execution digest; require the same or stronger actor role; restrict adapter/operation explicitly; validate rollback snapshot target identity (`adapter_name`, `external_ref`) against the write run before touching the external target; make rollback idempotent with a UNIQUE write-run key; and read back the external target state before reporting success. Update the previous write-run metadata/events/snapshots from “rollback disabled” to “rollback available” in the same slice so ledger/API/UI/docs do not disagree.
10. Verification: focused tests + plugin tests + coverage gate + smoke path. For preflight-only slices prove closeout → intent → readiness review → auth → preflight and `adapter_observations`/external adapter writes stay zero. For first write-through slices prove the narrow adapter target changes, exactly one execution run and adapter observation are recorded, retries are idempotent, and rollback/reopen remains disabled. For rollback slices prove write-through target changes, rollback restores the prior external state, exactly one rollback run/event/observation is recorded, retries are idempotent, target drift fails closed, and no broader adapter/taskpool/evidence override boundary was opened.

See also: `references/control-plane-external-write-rollback.md` for the Phase 14 rollback/reopen verification pattern and metadata-consistency pitfall.

## Anti-patterns
- Building the "framework" first with nothing working
- Waiting to test until "everything is done"
- Slice too large: "Implement user auth" is NOT a slice
- Skipping tests: "I'll add tests later" → never happens

## When a slice fails
1. Revert that slice only (git checkout -- <changed files>)
2. Don't touch other slices
3. Diagnose root cause before retrying

## Verification Checklist
- [ ] Each slice has its own commit
- [ ] git log shows incremental progression (not one mega-commit)
- [ ] All tests pass after every slice
- [ ] No slice touches more than one concern
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.
## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
