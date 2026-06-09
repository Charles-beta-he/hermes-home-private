---
name: git-conflict-resolution
description: Use when resolving merge or rebase conflicts in git — systematic conflict analysis, resolution strategy, and post-rebase verification.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - Git
    - Rebase
    - Merge
    - Conflict-Resolution
    related_skills:
    - github-pr-workflow
---

# Git Conflict Resolution

## Overview

Systematic approach to resolving merge/rebase conflicts. Covers analysis strategy, resolution patterns, and post-rebase verification. Complements `github-pr-workflow` (which handles the PR lifecycle) — this skill focuses specifically on the conflict resolution phase.

## When to Use

- `git rebase` or `git merge` produces CONFLICT markers
- Need to resolve multiple conflicts across many commits
- Binary file conflicts (images, compiled assets)
- Semantic conflicts where both sides are "correct" but incompatible

## Core Workflow

### Step 1: Assess the Scope

```bash
# See which files have conflicts
git diff --name-only --diff-filter=U

# Count conflicts per file
grep -rl '<<<<<<<' --include='*.ts' --include='*.tsx' --include='*.js' --include='*.json' --include='*.html' --include='*.css' . | while read f; do
  count=$(grep -c '<<<<<<<' "$f")
  echo "$f: $count conflict(s)"
done
```

### Step 2: Classify Each Conflict

For each conflicted file, determine the resolution strategy by understanding WHAT each side changed:

```
<<<<<<< HEAD        ← "theirs" (upstream/base)
  ...changes...
=======               ← separator
  ...changes...
>>>>>>> <commit>     ← "ours" (the feature branch being rebased)
```

**Decision matrix:**

| Situation | Resolution |
|-----------|-----------|
| Only one side changed the conflicting region | Keep that side's version |
| Both sides changed, semantically compatible | Merge both changes |
| Both sides changed, semantically incompatible | Keep the feature branch version (ours) unless upstream fix is more correct |
| Binary conflicts (images, icons) | `git checkout --ours` or `--theirs` based on which is newer/correct |
| Test file assertion conflicts | Align assertions with current implementation behavior |

### Step 3: Resolve

**For text files** — use `patch` tool to replace conflict markers with the resolved content. This is safer than manual editing for multi-file resolutions.

**For binary files** — pick a side:
```bash
# Keep the feature branch version
git checkout --ours path/to/binary.png

# Keep the upstream version
git checkout --theirs path/to/binary.png
```

### Step 4: Stage and Continue

```bash
# Stage all resolved files
git add resolved-file-1.tsx resolved-file-2.tsx

# Continue rebase non-interactively (suppress editor for commit messages)
GIT_EDITOR=true git rebase --continue
```

If more conflicts appear (common when rebasing many commits), repeat Steps 2-4 for each commit.

### Step 4b: Stash Pop Conflicts (different from rebase/merge)

When `git stash pop` produces conflicts, the semantics of `--ours`/`--theirs` are **inverted** compared to rebase:

```bash
# During stash pop:
#   --ours   = current working tree (BEFORE stash)
#   --theirs = stashed changes
# Opposite of rebase where --ours = rebased branch.
```

Resolution workflow:
1. Resolve conflicts the same way (read context, pick version)
2. `git add` resolved files
3. `git stash drop` to remove the applied stash (pop doesn't auto-drop on conflict)
4. Do NOT run `git rebase --continue` — that's only for rebase

Stash conflicts are common when:
- Stash was created on a branch that was then pulled/updated
- Stash modifies files that were also changed upstream
- Binary assets (icons, images) were stashed and also updated on remote

**Key difference from rebase**: After resolving stash conflicts, you have a dirty working tree (not a rewritten history). No force-push needed. Just commit or continue working.

### Step 5: Post-Rebase Verification

After ALL conflicts are resolved and rebase completes:

```bash
# Verify clean state
git status --short
git log --oneline origin/<base>..HEAD

# Type check
npx tsc --noEmit --pretty 2>&1 | tail -5

# Build
pnpm build 2>&1 | tail -10

# Tests
pnpm test 2>&1 | tail -20

# Force push with lease (history was rewritten)
git push --force-with-lease origin $(git branch --show-current)
```

## Common Patterns

### Version Bump Conflicts

When both sides bump a version/cache-buster string (e.g., `v09` vs `v10`), keep the newer version. These conflicts are trivial but common in asset updates.

### Import/Export Conflicts

When one side adds an import and the other side also modifies the import block, usually both additions are needed. Merge by keeping all unique imports.

### Test Assertion Conflicts

When upstream changes expected behavior and your feature also changes it:
1. Understand what the test is actually testing
2. Keep the assertion that matches the feature branch's intended behavior
3. If both behaviors should coexist, add a separate test case

### Refactor + Feature Conflicts

When upstream refactors a file your feature modifies:
1. Apply the refactored structure (theirs)
2. Re-integrate your feature changes into the new structure
3. This often requires understanding the refactoring intent, not just mechanically merging

## Two-Phase Conflict Resolution (stash + rebase)

When you have local uncommitted work AND the upstream has moved forward, the sequence is:

1. `git stash` your work
2. `git pull --rebase` or `git fetch && git rebase origin/<branch>` to get upstream
3. `git stash pop` → **Phase 1 conflicts** (stash vs current working tree)
4. Resolve Phase 1, `git add`, `git stash drop`
5. `git rebase origin/<branch>` → **Phase 2 conflicts** (local vs upstream commits)
6. Resolve Phase 2 per commit, `git rebase --continue`
7. Build + test verification

Phase 1 conflicts are about YOUR changes vs the current state. Phase 2 conflicts are about YOUR resolved changes vs each upstream commit. Don't mix them up — resolve Phase 1 completely before starting Phase 2.

After both phases, `git diff origin/<branch>..HEAD --stat` gives you the clean local delta. Use this to produce a structured summary for the user: group changes by category (feature, refactor, tests, assets) with line counts.

See `references/two-phase-conflict-example.md` for a real-world walkthrough.

## Pitfalls

1. **Don't resolve blindly**: Always read the conflict context to understand what each side changed. A wrong resolution creates subtle bugs that pass type checks.
2. **Binary files need `git checkout`**: `patch` tool cannot resolve binary conflicts. Use `git checkout --ours/--theirs` for images, fonts, compiled assets.
3. **`GIT_EDITOR=true` is required**: Without it, `git rebase --continue` opens an editor for commit messages and hangs in non-interactive contexts.
4. **Check for residual markers**: After resolving, grep for `<<<<<<<` to ensure no conflict markers were accidentally left in. Use `<<<<<<<` specifically (not `=======`) to avoid false positives from comment section dividers:
   ```bash
   grep -r '<<<<<<<' --include='*.ts' --include='*.tsx' --include='*.js' . && echo "LEFTOVER CONFLICTS!" || echo "Clean"
   ```
5. **Many commits = many conflict rounds**: Rebasing 14 commits onto a diverged base may produce conflicts at multiple commits. Each `rebase --continue` may surface the next one. Don't assume one resolution is the end.
6. **Force push after rebase**: A rebase rewrites history. Always use `--force-with-lease`, never `--force`. Verify remote parity after push.
7. **Run verification after rebase**: Upstream changes may have introduced new type errors, test failures, or build issues that weren't present before the rebase. Always run tsc/build/tests after rebase completes.
8. **`git revert` can restore stale lines**: When reverting commit X, git re-applies the inverse diff. If the file was also modified by commits Y and Z between X and HEAD, the revert may restore lines that Y or Z intentionally removed. The result: a clean revert with no conflict markers, but the file now contains stale code (e.g., checking a status value the backend no longer sends, or referencing a removed import). **Always diff the reverted file against the pre-revert state** (`git diff HEAD~1 <file>`) and verify every changed line makes sense. A passing `tsc --noEmit` after revert is not sufficient — the stale line may be type-correct but semantically wrong. Real example: reverting a skeleton-component change restored an `expired` status check that was removed by a different commit, causing `TS2367: types have no overlap` because the type definition had already dropped `expired`.

## References

- `references/common-conflict-patterns.md` — detailed examples of conflict resolution strategies
- `references/two-phase-conflict-example.md` — stash pop → rebase two-phase workflow (UVISA 2026-05)

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
