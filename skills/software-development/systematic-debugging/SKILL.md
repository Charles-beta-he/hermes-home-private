---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior. 4-phase root cause investigation — NO fixes without understanding the problem first.
version: 1.2.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
metadata:
  hermes:
    tags:
    - debugging
    - troubleshooting
    - problem-solving
    - root-cause
    - investigation
    related_skills:
    - writing-plans
    - test-driven-development
---

# Systematic Debugging

Reference: `references/hermes-cli-regression-proofing.md` — notes on debugging CLI regressions caused by evolving optional argparse fields, plus a pattern for collapsing wrapper scripts to direct native CLI calls with `--dry-run` verification.

## Hermes taskpool/control-plane stalls

When debugging Hermes/local-brain taskpool stalls, first separate active-task blockers from historical governance debt. If Lark tasks need to be removed temporarily, quarantine them with a manifest instead of deleting. If `dispatchable: true` exists but autorun does not claim, check the narrow autorun policy before changing lifecycle state. Historical `done task missing evidence` proof debt may be tolerated at the dispatch tick layer only when selfcheck and boundary checks still pass; keep the debt visible as tolerated errors and keep active-task proof failures fail-closed. See `references/taskpool-flow-tolerance.md`.

When retry count grows across advisory/evolution review-gap tasks, debug it as retry churn rather than worker failure: classify retry tasks by gap type, verify whether PASS/LOOP_DONE JSON is present but only stored in `evidence_refs`/`evidence`, check for historical compact schemas not recognized by `task_multimodel_passed()`, stop recursive `补证闭环` repair children when a task already has `review_gap_parent`, and add/verify a transient multimodel retry cap that keeps capped tasks blocked instead of returning them to retry forever. Detailed taskpool-specific checklist: `taskpool-control-plane/references/taskpool-retry-churn-root-cause.md`.

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

**Don't skip when:**
- Issue seems simple (simple bugs have root causes too)
- You're in a hurry (rushing guarantees rework)
- Someone wants it fixed NOW (systematic is faster than thrashing)
- Don't use for: requests that do not need encountering any bug, test failure, or unexpected behavior. 4-phase root cause investigation — NO fixes without understanding the problem first; choose a more specific child skill or a broader routing skill that actually matches the task.
## The Four Phases

You MUST complete each phase before proceeding to the next.

---

## Phase 1: Root Cause Investigation

Detailed Phase 1 root-cause investigation moved to `references/phase-1-root-cause-investigation.md`.

Load it when a bug/test failure requires reproduction, logs, history, data-flow tracing, vendor/update sustainability, memory ghost audit, automation escalation, or claim-validation audit.

Minimum in-root rule: reproduce or observe the failure before changing code; do not debug from assumptions.

## Phase 2: Pattern Analysis

Detailed Phase 2 pattern analysis moved to `references/phase-2-pattern-analysis.md`.

Load it after initial evidence when multiple files/symptoms may share a root cause.

Minimum in-root rule: look for repeated patterns before applying isolated fixes.

## Phase 3: Hypothesis and Testing

Detailed Phase 3 hypothesis/testing workflow moved to `references/phase-3-hypothesis-testing.md`.

Load it when you need to test candidate causes before committing to a fix.

Minimum in-root rule: make hypotheses falsifiable and run the narrowest check that can disprove each one.

## Phase 4: Implementation

**Fix the root cause, not the symptom:**

### 1. Create Failing Test Case

- Simplest possible reproduction
- Automated test if possible
- MUST have before fixing
- Use the `test-driven-development` skill

### 2. Implement Single Fix

- Address the root cause identified
- ONE change at a time
- No "while I'm here" improvements
- No bundled refactoring

### 3. Verify Fix

```bash
# Run the specific regression test
pytest tests/test_module.py::test_regression -v

# Run full suite — no regressions
pytest tests/ -q
```

### 4. If Fix Doesn't Work — The Rule of Three

- **STOP.**
- Count: How many fixes have you tried?
- If < 3: Return to Phase 1, re-analyze with new information
- **If ≥ 3: STOP and question the architecture (step 5 below)**
- DON'T attempt Fix #4 without architectural discussion

### 5. If 3+ Fixes Failed: Question Architecture

**Pattern indicating an architectural problem:**
- Each fix reveals new shared state/coupling in a different place
- Fixes require "massive refactoring" to implement
- Each fix creates new symptoms elsewhere

**STOP and question fundamentals:**
- Is this pattern fundamentally sound?
- Are we "sticking with it through sheer inertia"?
- Should we refactor the architecture vs. continue fixing symptoms?

**Discuss with the user before attempting more fixes.**

This is NOT a failed hypothesis — this is a wrong architecture.

---

## Red Flags — STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals a new problem in a different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (Phase 4 step 5).

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. Process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is FASTER than guess-and-check thrashing. |
| "Just try this first, then investigate" | First fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it. |
| "Multiple fixes at once saves time" | Can't isolate what worked. Causes new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms ≠ understanding root cause. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern, don't fix again. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

## Hermes Agent Integration

Detailed Hermes Agent integration / development iceberg scans moved to `references/hermes-agent-integration.md`.

Load it for Hermes-specific debugging, taskpool/control-plane issues, or development iceberg scans.

Minimum in-root rule: distinguish Hermes runtime/control-plane evidence from ordinary application debug evidence.

## Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

**No shortcuts. No guessing. Systematic always wins.**

## Related references

Detailed related-reference index moved to `references/related-references.md`.

Load it when looking for adjacent debugging workflows or specialized runbooks.

Minimum in-root rule: choose the narrowest debugging reference that matches the observed failure.

## Absorbed Debugger Packages

These debugger-specific former skills are now support packages under the class-level debugging umbrella. Load them only when root-cause investigation reaches a language/runtime debugger boundary; keep the default workflow in this skill as the entry point.

- `node-inspect-debugger` → `references/packages/node-inspect-debugger/README.md`: debugger-specific command recipes and pitfalls preserved as a support package.
- `python-debugpy` → `references/packages/python-debugpy/README.md`: debugger-specific command recipes and pitfalls preserved as a support package.

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. When a Hermes script/unit test asserts behavior for an 'unknown provider' or similar runtime-integration hook, remove runtime overlay discovery from the test boundary first: randomize the missing name, seed the mapping explicitly, and assert the deterministic outcome instead of branching on whether the local environment already recognized the synthetic entity.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
4. **Python `in` is substring, not word-boundary**: `"dependency" in "dependencies"` → `False`. Source text must contain the exact literal sequence the test asserts. See `references/text-assertion-mismatch.md`.
5. **pytest xdist `-p no:xdist` doesn't clear `-n auto`**: Use `-o "addopts="` to override config-level addopts. See `references/pytest-override-flags.md`.
6. **macOS `sed -i` requires empty string extension**: `sed -i 's/old/new/'` fails on macOS with "extra characters at end of h command". Use `sed -i '' 's/old/new/'` or, better, use the `patch` tool which handles both platforms correctly. Prefer `patch(mode='replace')` over terminal sed for file edits.
7. **React component swap breaks `getByRole` selectors**: When replacing `<Link>` with `<CtaBtn>` (or any interactive component migration), `getByRole('link')` silently fails because Testing Library resolves by rendered HTML element, not React component name. Grep tests for the old role before committing. See `references/react-aria-role-migration.md`.
9. **Provider proxy/TUN false root causes**: For LLM/provider timeouts, do not jump directly from `hermes chat`/wrapper timeout to "provider broken" or "model name wrong". First compare raw configured endpoint vs wrapper vs DNS/proxy/TUN route. If a provider host resolves to `198.18.0.0/15`, a global VPN/fake-ip layer is involved and ordinary `NO_PROXY` may not bypass it. Keep account-scoped base URLs from the console; do not replace them with public defaults unless the key is valid there. Prefer bounded direct adapters, min-quorum-aware health breakers, and stdin-based remote relays for global-only VPN setups. See `references/provider-proxy-relay-debugging.md`.
10. **Auth availability is not runtime availability**: OAuth/session/API-key probes only show a provider is configured. If the exact provider/model runtime path returns no final response, account-disabled errors, or CLI wrapper failures, record a scoped runtime-unavailable snapshot and make routing honor it before generic OAuth assumptions. Do not lower the readiness gate to hide the failure. See `references/provider-runtime-availability-vs-auth.md`.
11. **Catalog/approval is not the same as current key+endpoint entitlement**: Applicability: provider/model debugging where an approval notice, docs/catalog, or cached picker lists a model but runtime rejects it. Anti-condition: do not store provider-account facts globally or add a model as verified callable without current key/base readback. Split evidence sources and test the exact active base URL, active key, exact model id, and a known-good control model before concluding availability. See `references/provider-catalog-vs-runtime-entitlement.md`.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
- [ ] Reviewer calibration: findings include a severity or rubric boundary and cite evidence.
