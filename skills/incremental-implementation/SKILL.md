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
