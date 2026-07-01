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

For autonomous/self-advance chains, checkpoint summaries are continuation points, not terminal completion, while safe local next slices remain. Close each slice with verification, ledger/SSOT update, scoped commit, clean-tree readback, then continue; stop only at a real authority/safety boundary. See `references/autonomous-continuation-checkpoints.md`.

### Sequential tracks are not a decision gate

When the user has already approved multiple tracks (for example “A、B、C 可以并行/顺序推进”), do not reframe them as a mutually exclusive implementation decision or stop for human selection. Treat them as an ordered backlog:

1. choose the safest dependency order;
2. execute the first independently verifiable slice;
3. verify and commit/prove it;
4. proceed to the next slice unless there is a real authority boundary, destructive side effect, permission/credential gap, or same-implementation mutually exclusive choice.

Stage reports may mention the current ordering, but they are not permission prompts unless one of those gates is actually present.

## Slice Sizing

| Task Type | Ideal Slice Size |
|-----------|-----------------|
| Add endpoint | 1 route → 1 handler → 1 test |
| Add component | 1 component → 1 story → 1 test |
| Refactor | 1 function extracted → 1 test adjusted |
| Bug fix | 1 failing test → 1 fix → test passes |

## Operator status projection vertical slice

When a local operator/mobile/status UI must surface real lifecycle state without opening executor or external adapter writes, use `references/operator-status-projection-slice.md`: test-first read-only source contract, project lifecycle counts/blocked cards, prioritize blocked items over warning noise, keep oversized control-plane lists behind bounded summary helpers instead of raw UI-service reads, live-smoke the endpoint with real headers and low process buffers, and verify no residual process before committing.

## Mock-to-Real-API Vertical Slice Pattern

Detailed `Mock-to-Real-API Vertical Slice Pattern` guidance moved to `references/mock-to-real-api-vertical-slice-pattern.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Mobile keyboard-stable input shell slice

When a mobile H5/PWA/RN-web input page must keep its FlowNav/header/branding stable while the soft keyboard opens, do not fix only the observed page. Scan sibling input/search/composer routes, add them to an explicit route-level preserve-header classifier, wrap each stable route in `data-keyboard-preserve-header="true"`, pin the header, and move content into an inner scroller. Verify with classifier + component shell tests and TypeScript/build; visual/A+ claims still require real browser/device screenshot evidence. See `references/mobile-keyboard-stable-input-shell.md`.

## Mobile keyboard-stable input propagation slice pattern

Use when fixing a soft-keyboard / viewport stability issue on one mobile-web or PWA input page and the user asks to propagate the effect to other input pages.

1. Separate shared input primitives from page-local hand-written inputs.
   - First patch the shared primitive (for example a reusable amount input) so every consumer inherits the keyboard/viewport marker or wrapper behavior.
   - Then search for raw native inputs/textareas with the same behavior class (for example `inputMode="decimal"`, search fields, bottom composers) and patch only the matching page-local variants.
2. Distinguish shell-level preservation from field-level focus detection.
   - Full-height composer/search pages may need an outer fixed-header + inner-scroll shell.
   - Simple amount fields can often use the existing global focus detector by marking the field/nearest wrapper with the preservation attribute, without restructuring the page.
3. Preserve domain-specific input logic.
   - Do not replace money sanitization, precision caps, max-length guards, currency metadata, or bidirectional amount calculations while adding viewport behavior.
   - For money fields, keep decimal precision and string handling intact; the viewport fix should be additive.
4. Verify both coverage and representative behavior.
   - Add/extend a shared primitive test proving all primitive instances carry the marker.
   - Add a static or focused contract test that page-local raw amount inputs are covered, especially where there are multiple fields on one page.
   - Run representative existing behavior tests for amount sanitization/capping and affected product cards, plus TypeScript/build checks.
5. Avoid false visual acceptance.
   - Static tests prove propagation coverage, not final mobile pixel acceptance. For A+/UI acceptance, still capture real mobile/PWA screenshots or run the project’s visual acceptance path.

## Legacy frontend static-contract MR slice pattern

Applicability: older frontend/mobile-web repositories with noisy global lint baselines and small route/style/DOM fixes that can be proven by focused file-level contracts. Anti-conditions: do not use this when the user explicitly asks for visual acceptance, device proof, uIMax/A+ certification, animation quality, or safe-area pixel parity; those still require rendered screenshot/device/browser evidence.

Use a fresh worktree from the remote base, add focused JS/static contract tests for each touched behavior or style invariant, run targeted lint on touched files, run `git diff --check` and the project build, then create a reviewable MR without enabling auto-merge unless separately authorized. See `references/legacy-frontend-static-contract-mr-slices.md`.

## Frontend global error-toast backend-message slice pattern

Applicability: browser or mobile-web clients with a central HTTP interceptor and top-level network/server-error toast. Anti-conditions: do not use for page-local validation/business errors, cancellations, aborts, or any flow where the backend message is not already intended for end users.

When a global network/server-error toast currently uses fixed generic copy, preserve backend-provided error text for server responses while keeping the generic network copy as fallback for true no-response failures. Extend the error event detail with optional message, extract only non-blank response-body message fields, keep cancellation/abort excluded, and render backend-message-or-generic-fallback in the top-level listener. Verify with focused interceptor tests for server error with message, server error without message, pure network failure, and cancellation/abort, plus frontend typecheck/build. See `references/frontend-global-error-toast-backend-message.md`.

## Template-variable hydration bugfix slice pattern

Detailed `Template-variable hydration bugfix slice pattern` guidance moved to `references/template-variable-hydration-bugfix-slice-pattern.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Ledger-only executor consumer slice pattern

Detailed `Ledger-only executor consumer slice pattern` guidance moved to `references/ledger-only-executor-consumer-slice-pattern.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
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

Detailed `Agent runtime executor ratchet after ledger-only start` guidance moved to `references/agent-runtime-executor-ratchet-after-ledger-only-start.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
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

Detailed `External adapter write authorization before write-through` guidance moved to `references/external-adapter-write-authorization-before-write-through.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
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
