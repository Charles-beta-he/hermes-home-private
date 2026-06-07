---
name: git-state-aware-debugging
description: "Use when detect and fix bugs that persist because worktree, staged index, and HEAD differ, especially when downstream tooling consumes staged snapshots or generated patches."
---

# Git State Aware Debugging

## Overview

Detect and fix bugs that persist because worktree, staged index, and HEAD differ, especially when downstream tooling consumes staged snapshots or generated patches. This skill is maintained as a `pipeline`-shaped contract: it should guide ordered multi-stage work with gates, evidence, retries, and closure states without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `git-state-aware-debugging` and requires ordered multi-stage work with gates, evidence, retries, and closure states.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this when a code fix "looks correct locally" but the failure still reproduces in a task runner, patch consumer, review flow, or automation that may read the staged index instead of the worktree.

## Triggers
- The user says a local fix exists but the task/agent still fails.
- `git status` shows staged and unstaged changes for the same file (`MM`, `AM`, etc.).
- A bug report points at lines that no longer match the current worktree.
- A generated patch, task handoff, or automation appears to be reading an older snapshot.

## Core idea
Three versions may exist at once:
1. HEAD: last committed baseline
2. Index: staged snapshot
3. Worktree: current file on disk

Many workflows read the index or a derived patch bundle, not the live worktree. If only the worktree is fixed, the bug can survive in downstream execution.

## Procedure
1. Check repo state first.
   - Run `git status --short`.
   - If the same file has both staged and unstaged modifications, assume snapshot divergence until proven otherwise.
2. Compare all three layers for the suspect file.
   - Worktree: read the file directly.
   - Index: `git show :path/to/file`
   - HEAD: `git show HEAD:path/to/file`
3. For runtime errors caused by reordered code, search all use sites and the initialization site.
   - Example class: `UnboundLocalError` after moving an `append()` block above `context_parts: List[str] = []`.
   - Verify every `append()` / reference occurs after initialization in the active snapshot.
4. Fix the correct layer.
   - If the worktree is right but index is wrong, re-stage the repaired file.
   - If the index is right but worktree drifted, decide whether to keep or discard the drift.
5. Verify the exact consumer path.
   - Re-run the failing task, or at minimum compare the snapshot the task will consume.
   - For Python, also run `python -m py_compile path/to/file.py` after structural edits.

## Pitfalls
- Reading only the worktree and declaring the fix done.
- Forgetting that automation may consume staged patches, not live files.
- Treating line-number mismatch as noise instead of evidence of snapshot drift.
- Fixing variable order in one branch of a large function but not re-checking all early references.

## Hermes-specific notes
- In Hermes local patching, task flows or review/handoff paths may effectively operate on the staged snapshot.
- When editing `run_agent.py` prompt-building sections, verify initialization order around newly moved blocks before concluding the feature is broken elsewhere.

## Verification
- `git status --short` no longer shows unintended staged/unstaged divergence for the target file.
- Worktree and index both show the corrected ordering/content.
- Syntax/compile check passes.
- The original consumer path no longer reproduces the bug.

## References
- `references/hermes-run-agent-ordering.md` — Hermes-specific example of a worktree-fixed/index-broken prompt-builder reorder bug.
