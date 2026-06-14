---
name: git-repo-operations
description: "Use when coordinating Git repository operations beyond a single edit: resolving merge/rebase/stash conflicts, managing branches across one or more related repos, syncing from profile-defined target branches, and verifying push/PR readiness."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [git, github, conflicts, branches, multi-repo, rebase]
    related_skills: [github-pr-workflow, github-code-review]
---

# Git Repository Operations

## Overview

This umbrella covers operational Git work: conflict resolution, stash/rebase edge cases, branch orchestration, multi-repo consistency, and post-operation verification. It consolidates the conflict-specific and multi-repo branch workflows into one class-level runbook.

## When to Use

- `git merge`, `git rebase`, or `git stash pop` produces conflicts
- Need to coordinate frontend/backend/service branches across a project
- Need to create task branches from project-profile target branches
- Need to verify branch consistency, upstream tracking, ahead/behind state, or force-push safety
- Need to resolve binary, import/export, test assertion, or semantic conflicts

Don't use for:
- Simple one-file edits with no repository state changes
- PR review content analysis without Git operation changes

## Core Workflow

1. **Discover state**: `git status --short --branch`, current branch, upstream, and dirty files.
2. **Resolve the target**: for project work, read the project profile and map repo role → target branch. Do not assume `main`/`master`/same branch for every repo.
3. **Fetch before acting**: `git fetch origin --prune` before checkout, rebase, or branch creation.
4. **Classify operation**:
   - conflict resolution: merge/rebase/stash markers and semantic merge
   - branch orchestration: sync/check/create/rebase multiple repos
   - release/PR readiness: verify remote parity and required tests
5. **Resolve mechanically, verify semantically**: remove markers and stage files, then run the relevant build/test/typecheck slice.
5. **Push safely**: after rebase, use `--force-with-lease`; never blind `--force`.
6. **Scope commits in live-state repos**: when a repository contains scheduler/runtime state files that drift during normal operation (for example cron job counters, next-run timestamps, logs, caches), do not stage the whole dirty file just because one durable config field changed. Build a staged blob from `HEAD:<file>` with only the intended semantic edit, or otherwise stage a minimal patch, then verify `git diff --cached` contains only that scoped change. Leave live runtime drift unstaged. For heavily dirty skill/docs files where one new durable line must be committed without absorbing unrelated working-tree churn, construct a clean blob from `git show HEAD:<path>` plus the intended insertion, write it with `git hash-object -w`, stage it with `git update-index --cacheinfo <mode>,<blob>,<path>`, then inspect `git diff --cached` before committing.
7. **For user-authorized “推进到边界” work, still commit only the intended slice**: before committing, run status/diff checks, stage exact touched files only, inspect `git diff --cached --stat` and `git diff --cached --name-only`, and explicitly leave unrelated untracked/dirty files unstaged. If verification passes, make the scoped commit; if the next action would enable broad runtime execution, lifecycle mutation, external writes, or other privileged authority, stop and report the boundary instead of silently expanding the commit/task scope.
8. **For submodule operations, verify metadata before claiming recursive health**: if recursive submodule status fails because a tracked gitlink has no mapping, restore the mapping from the tracked path, expected commit, and known remote URL when available. Do not delete backup/history directories just to make recursion pass; make the metadata repair auditable, then rerun the recursive check.
9. **When committing scoped submodule work from a dirty child repo, separate gitlink pinning from child dirtiness and pre-existing parent index state**: commit the intended files inside the child first. In the parent, inspect `git diff --cached --name-only` *before* staging the gitlink; if unrelated files are already staged, unstage or stop rather than mixing them into the pointer commit. Then stage only the submodule pointer plus any explicitly intended parent-level files, re-check `git diff --cached --stat --submodule=short` and `git diff --cached --name-only`, and commit only if the cached diff contains the intended slice. If an accidental parent commit already mixed unrelated staged files with the gitlink, make a corrective follow-up commit that restores those unrelated paths from the previous commit while preserving the gitlink, then verify the net diff from the prior good parent contains only the submodule pointer. If `git status` still shows `m <submodule>` because unrelated child files remain dirty, disclose that as pre-existing/unrelated child dirtiness rather than trying to clean or stage it. Do not stage ignored runtime state such as cron DB/job counters or rollback backups just to make parent status clean.
10. **When clearing mixed control-plane homes, distinguish shared policy from local overlay**: commit `.gitignore`/`git rm --cached` migrations for durable runtime/secret boundaries, but use repo-local `.git/info/exclude` for huge machine-specific overlays that should not become shared policy. A clean status can legitimately mean "tracked state clean; local overlay ignored and kept on disk" — disclose that distinction.
10. **For PRs from dirty or shared worktrees, isolate the PR branch before commit/merge**: export the intended diff to a patch, create a clean temporary worktree from the true base (`git worktree add -b <branch> /tmp/<repo>-pr origin/<base>`), apply only the scoped patch, install/build/test there, then commit/push/PR from that clean worktree. This prevents unrelated local changes or active runtime state from leaking into the PR.
11. **When enabling GitHub auto-merge from a repo with multiple worktrees, avoid implicit local checkout operations**: `gh pr merge <n> --auto ...` may try to inspect/check out the base branch and fail if that branch is already checked out in another worktree (`fatal: '<base>' is already used by worktree ...`). Retry from a neutral cwd with explicit repo targeting: `gh pr merge <n> --repo OWNER/REPO --auto --squash --delete-branch`, then verify with `gh pr view <n> --repo OWNER/REPO --json state,autoMergeRequest,mergedAt,statusCheckRollup`.

## Conflict Resolution Subflow

- List unresolved files: `git diff --name-only --diff-filter=U`.
- Count conflict markers and read surrounding context before editing.
- For text conflicts, patch the resolved content; for binary assets, choose `--ours`/`--theirs` intentionally.
- During rebase, remember marker labels can be counterintuitive; during stash-pop, `--ours` is current working tree and `--theirs` is the stashed content.
- After each round: stage resolved files and continue (`GIT_EDITOR=true git rebase --continue` for rebase).
- Search for residual `<<<<<<<` before declaring the tree clean.

## Multi-Repo Branch Subflow

- Parse project profile for repo paths, repo roles, branch roles, and allowed transitions.
- Build an explicit repo → target branch map.
- For each repo: fetch, checkout resolved target, pull `--ff-only`, or create task branch from `origin/<target>`.
- Verify all repos report expected current branch, upstream, and ahead/behind state.
- Do not infer branch targets from memory; remote refs + project profile are the source of truth.

## Common Pitfalls

1. **Treating every repo as if it shares the same target branch.** Resolve per repo role.
2. **Resolving conflicts by side instead of meaning.** Read both changes and preserve semantics.
3. **Forgetting stash-pop semantics.** `--ours`/`--theirs` differ from rebase mental models.
4. **Leaving conflict markers.** Search for `<<<<<<<`, not just `=======`.
5. **Force-pushing unsafely.** Use `--force-with-lease` only after verifying the branch.
6. **Revert can restore stale lines.** Diff reverted files and verify semantics, not just type correctness.
7. **Auto-merge command fails because of sibling worktrees.** Do not delete or disturb the sibling worktree just to satisfy `gh`; rerun the merge command with `--repo OWNER/REPO` from a neutral directory and verify PR state afterward.
8. **Patch application from an old dirty branch can silently omit intended changes.** After applying a patch into a fresh PR worktree, compare `git diff --stat` and the named files against the original intent before committing.
9. **Stale local branches can fabricate a sync need.** For branch synchronization decisions, compare freshly fetched remote refs (`origin/source...origin/target`), not local `source`/`target` branches that may be behind or checked out in another worktree. Verify ancestry with `git merge-base --is-ancestor origin/<source> origin/<target>` and direct remote tips with `git ls-remote` when the user suspects new remote commits.
10. **Do not open no-op sync PRs.** If the source branch is already an ancestor of the target branch, a clean worktree merge will be `Already up to date` and the candidate branch will be `0 0` ahead/behind the target. Stop and report the no-op evidence instead of pushing an empty branch or creating an empty PR.
11. **Private-repo install paths must not assume a GUI, browser, or GitHub CLI.** For private source distributions, document at least three token-safe paths: GitHub CLI/device-code login when available, headless SSH/deploy-key clone for servers or containers, and an existing-checkout/offline-transfer finalizer. Never ask users to put a token in a clone URL or make `curl | bash` from a private raw URL the only primary path.

## Branch-Specific Feature/Page Divergence Audit

Applicability: use this only as a generic Git investigation pattern when comparing a visible feature or page between two branches. Anti-condition: do not encode concrete project names, branch names, PR numbers, or page names in this skill; resolve those from the current repository each time.

- Fetch/prune before conclusions, and compare remote refs when the user is asking about deployed or shared branch behavior.
- Quantify both directions of divergence before inspecting files: count left/right commits and list unique commits on each side with dates and subjects.
- Narrow the investigation to the feature's component, tests, locale files, data/config files, and services. Run path-limited logs in both directions so branch-wide drift is not mistaken for the page-specific cause.
- Use the branches' merge-base for scoped diff stats when deciding which side introduced the behavior.
- Inspect branch-tip file contents and diffs, not only commit subjects. For UI symptoms, tie screenshot-visible rows, labels, or controls to exact additions/removals in code and tests.
- When reporting, separate: current branch divergence, the commit(s) that explain the visible behavior, which branch matches the screenshot/symptom, and merge/cherry-pick risk from unrelated unique commits.
- If a single feature/fix commit is present on one remote branch but missing from the target branch, verify portability without disturbing the user's worktree: create a temporary detached worktree from `origin/<target>`, `git cherry-pick --no-commit <commit>`, inspect `git diff --cached --stat/name-status` and `git diff --cached --check`, then remove the worktree. This distinguishes "safe scoped cherry-pick" from "merge the whole divergent branch".
- When the commit adds its own focused test, run that test in the temporary worktree after the no-commit cherry-pick. If dependencies are already installed in the main worktree and the temp worktree is on the same machine, a symlinked `node_modules` can speed verification; treat it as local acceleration only, not evidence that CI has dependencies.

## Deployed Behavior Not Matching a Present Commit

Applicability: use this generic Git + deployment investigation pattern when a fix commit is present on a remote branch but the user reports the deployed or online behavior is not effective. Anti-condition: do not encode concrete project names, service names, domains, environment names, or commit hashes in this skill; resolve those from the current repository and hosting metadata each time.

1. **Branch tip semantics**: prove whether the branch still has the fix at its tip, not merely whether it contains the commit. Run path-scoped checks such as `git log <commit>..origin/<branch> -- <affected-paths>` and `git diff --exit-code <commit> origin/<branch> -- <affected-paths>` to detect later overwrites, reverts, or no-op drift.
2. **Deployment metadata**: inspect the hosting service's active deployment branch, commit, status, and domain mapping where available. Treat similarly named environments or domains as distinct until proven otherwise.
3. **Served artifact content**: fetch the live HTML, extract hashed JS/CSS assets, and search served bundles for robust fix markers such as the API call shape, mapping logic, route/component marker, or UI string. Do not rely only on source identifiers that minification may remove.
4. **Diagnosis split**: if one served domain contains the fix and another does not, report a deployment/environment mismatch rather than a Git regression. If the served artifact contains the fix but behavior is still old, separate browser/PWA service-worker cache, installed-app cache, and real backend response/data issues before proposing code changes.

## Verification Checklist

- [ ] Working tree conflict markers are gone.
- [ ] Staged files match the intended semantic resolution.
- [ ] Current branch and upstream are correct for each repo.
- [ ] Typecheck/build/tests relevant to touched files were run or explicitly scoped out.
- [ ] Remote push strategy is safe and branch-aware.
- [ ] Pipeline control: each stage has an explicit gate before the workflow advances.
## Support Files

- `references/git-conflict-resolution.md` — conflict marker, rebase, stash-pop, binary conflict, and verification details.
- `references/multi-repo-branch-orchestration.md` — project-profile-driven branch sync and batch templates.
- `references/control-plane-home-workspace-triage.md` — classify and safely clean mixed agent/control-plane home repos with config, runtime DBs, logs, notes, skills, task evidence, vendored checkouts, and submodules.
- `references/clean-pr-worktree-auto-merge.md` — isolate scoped PRs in fresh worktrees and recover from `gh pr merge` failures caused by sibling worktrees using `--repo OWNER/REPO`.
