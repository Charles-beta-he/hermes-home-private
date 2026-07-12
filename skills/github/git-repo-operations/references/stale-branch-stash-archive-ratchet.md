# Stale branch / stash archive ratchet audit

Use when a dirty worktree or stash has been converted into an archive branch, or when deciding whether an old task branch should be merged into a current shared branch.

## Problem pattern

Old task branches and stash-archive branches often have a very old merge-base. A direct two-dot diff against the current target can show thousands of unrelated file changes because the branch tip predates many upstream/private merges. This does **not** mean the archive itself has thousands of intended changes.

## Procedure

1. Fetch/prune and inspect remote refs, not stale local names.
2. For each candidate branch, record:
   - `git merge-base <target> <branch>` and its date/subject;
   - `git rev-list --left-right --count <target>...<branch>`;
   - `git diff --stat <target>..<branch>` as a danger signal only;
   - for stash-derived branches, the real intended patch with `git diff --stat <branch>^1..<branch>`.
3. Classify:
   - **feature/task branch with current merge-base**: normal dry merge may be appropriate;
   - **feature/task branch with stale merge-base**: do not merge whole branch; cherry-pick or re-apply the intended semantic commit(s) onto a clean worktree from the current target;
   - **stash archive branch**: default to evidence retention only. Merge only after extracting a small reviewed patch from `<branch>^1..<branch>`.
4. Test timing:
   - test the branch locally to prove its own patch is coherent;
   - before merge, test `current target + extracted patch`, not `old base + patch`;
   - after conflict resolution, run targeted tests for touched surfaces and the repo's update/selfcheck gate if applicable.
5. Reporting:
   - say whether the branch is `direct-mergeable`, `ratchet-cherry-pick-only`, `archive-only`, or `retire/drop-candidate`;
   - include conflict files from the dry cherry-pick/merge;
   - never claim merge readiness from a branch-local green test when the current-target dry replay conflicts.

## Pitfalls

- Do not convert a stash to an archive branch and then later merge the archive branch wholesale; a stash commit has a synthetic parent structure and usually represents a patch, not a branch lineage.
- Do not rely only on `git diff target..archive` for old archives; inspect `archive^1..archive` to see what was actually stashed.
- Clean up temporary worktrees after dry replay attempts, even when cherry-pick conflicts.
