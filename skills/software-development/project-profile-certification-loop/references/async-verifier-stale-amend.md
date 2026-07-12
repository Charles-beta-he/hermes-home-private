# Async verifier stale-AMEND handling

Use this when an independent verifier returns AMEND for a slice that was dispatched earlier, but local autonomous safe-slice work has continued meanwhile.

## Trigger

A verifier says the target slice/evidence/code checks are OK, but AMENDs because the repo was dirty or at an older `ahead` count during its run.

Typical signs:

- The verifier target commit is not current HEAD anymore, but should be an ancestor of current HEAD.
- The only blocker is `git status` not clean or a WIP diff in a later safe slice.
- The verifier explicitly reports evidence JSON / loop report / target commit scope as OK.

## Required classification

Do **not** immediately treat this as a product defect.

Classify it as `stale-environment-amend-not-product-blocker` only if fresh readback proves:

1. Current repo is clean except ahead:
   - `git status --short --branch`
2. Current HEAD contains the target commit:
   - `git merge-base --is-ancestor <target_commit> HEAD`
3. The target evidence JSON still exists and passes the material assertions.
4. Latest certification loop/report is still OK for the current clean repo.
5. The verifier did not identify a target-slice code/evidence semantic defect.

If any of those fail, treat the AMEND as a real blocker and fix or revert before continuing.

## SSOT receipt shape

Write a small receipt under the project SSOT, for example:

```json
{
  "generatedAt": "...",
  "sourceDelegation": "deleg_xxx",
  "slice": "spot-side-tab-semantics",
  "verifierVerdict": "AMEND",
  "verifierObjectiveBlocker": "working tree was dirty during stale verifier run",
  "currentReadback": {
    "gitStatus": "## dev...origin/dev [ahead N]",
    "head": "abc1234"
  },
  "classification": "stale-environment-amend-not-product-blocker",
  "action": "fresh verifier redispatch required; do not upgrade to L3 from this AMEND",
  "evidence": "/path/to/evidence.json",
  "okToContinueLocalSlices": true
}
```

Then update the project profile / ledger to keep the slice at L2 with a stale-AMEND marker, not L3.

## Fresh re-dispatch brief

The replacement verifier brief must include:

- Current expected clean-state snapshot:
  - current HEAD
  - expected `git status --short --branch`
- Target commit under review.
- Whether later local commits are allowed because the target commit is an ancestor of current HEAD.
- Exact evidence JSON/report paths and assertions.
- Clear rule: APPROVE if the only previous blocker was dirty tree and current clean readback is valid; AMEND only for objective target-slice/evidence/current-readback blockers.

## Dispatch discipline for autonomous continuation

When safe local work continues while verifier jobs are pending, the verifier may inspect a dirty worktree from a later slice and return AMEND even though the target slice is sound. To reduce false AMEND churn:

- Prefer dispatching verifiers immediately after a committed, clean slice boundary.
- If you will continue new slices in the same file before the verifier returns, explicitly brief the verifier that current HEAD may advance and the target commit only needs to be an ancestor of the clean current HEAD.
- After every verifier AMEND, first perform a fresh clean-state readback before changing product code.
- If fresh readback is clean and the target commit/evidence remain valid, record a stale-AMEND receipt and re-dispatch; do not treat dirty-state AMENDs as product defects.
- Do not let stale-AMEND processing become a stopping point: if the project has an autonomous safe-slice switch and hard-stop gates remain closed, continue with the next safe slice after recording/redispatching.

## Repeated stale-AMEND avoidance

A retry can itself become stale if you immediately start another WIP patch in the same file. When a target has already received a stale dirty-tree AMEND:

- Re-dispatch from a committed, clean tree using the current HEAD/ahead count.
- Prefer selecting the next autonomous slice in a different file/surface until that retry has had a chance to read clean state.
- If no different-file safe slice is available, pause additional same-file mutations briefly after dispatching the retry rather than creating a guaranteed second stale AMEND.
- If a second stale AMEND still arrives, fresh-read the repo. If it is clean and the target evidence remains valid, write a second stale-AMEND receipt and retry once more; do not rewrite target code just to appease the stale verifier.

## Important anti-claims

- Do not promote to L3 from the stale AMEND.
- Do not rewrite product code just to satisfy a stale verifier run.
- Do not stop safe local progress solely because old preview/background processes emit SIGTERM notifications; first re-check process list, endpoint health, and repo clean state.
- Do not claim production/device/auth/PWA certification from this path.
