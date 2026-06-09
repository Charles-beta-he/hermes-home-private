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
6. **Scope commits in live-state repos**: when a repository contains scheduler/runtime state files that drift during normal operation (for example cron job counters, next-run timestamps, logs, caches), do not stage the whole dirty file just because one durable config field changed. Build a staged blob from `HEAD:<file>` with only the intended semantic edit, or otherwise stage a minimal patch, then verify `git diff --cached` contains only that scoped change. Leave live runtime drift unstaged.
7. **For user-authorized “推进到边界” work, still commit only the intended slice**: before committing, run status/diff checks, stage exact touched files only, inspect `git diff --cached --stat` and `git diff --cached --name-only`, and explicitly leave unrelated untracked/dirty files unstaged. If verification passes, make the scoped commit; if the next action would enable broad runtime execution, lifecycle mutation, external writes, or other privileged authority, stop and report the boundary instead of silently expanding the commit/task scope.
8. **For submodule operations, verify metadata before claiming recursive health**: if recursive submodule status fails because a tracked gitlink has no mapping, restore the mapping from the tracked path, expected commit, and known remote URL when available. Do not delete backup/history directories just to make recursion pass; make the metadata repair auditable, then rerun the recursive check.

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
