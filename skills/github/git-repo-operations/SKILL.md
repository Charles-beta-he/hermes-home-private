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

Detailed core workflow moved to `references/core-workflow.md`.

Load it when coordinating non-trivial git changes, branch hygiene, diffs, staging, commit/push/PR boundaries, or rollback.

Minimum in-root rule: inspect branch/status/diff before commit/push and keep unrelated dirty work out of the change.

## Git Repository Development Consensus

Detailed development consensus moved to `references/development-consensus.md`.

Load it when deciding commit strategy, PR/MR path, repo ownership, scope, or verification before publication.

Minimum in-root rule: scoped local commits are safe only after status/diff/readback; push/publish needs exact target authority.

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

Detailed git pitfalls moved to `references/pitfalls.md`.

Load it when handling dirty trees, branch mismatch, merge/rebase ambiguity, submodules, worktrees, or accidental broad staging.

Minimum in-root rule: never hide unrelated changes inside the current task commit.

## Self-Managed GitLab MR Automation

Applicability: use when the active repository is hosted on GitLab or a self-managed GitLab-compatible instance and the user asks for automatic MR creation, auto-merge, or merge-when-pipeline-succeeds. Anti-condition: do not encode concrete hosts, project paths, branch names, or token values in this skill; resolve them from the active repository, project profile, and live API each time.

- Use the capability ladder in `references/self-managed-gitlab-mr-automation.md`: SSH push-options can create MRs but cannot verify merge state; `glab`/API auth is required for a grounded auto-merge loop; CI-owned merge bots are the production-grade path.
- Never extract browser cookies, localStorage, session tokens, or saved browser credentials to obtain GitLab API access, even if the user is logged in and asks whether you can get a token. Ask the user to create a PAT/project token and pipe it into `glab auth login --stdin --use-keyring` so the agent never sees the token.
- For self-managed GitLab, `glab auth login --web` may fail with a missing `client_id`; prefer PAT stdin auth unless the instance has an OAuth application configured for glab.
- Treat `glab auth status` showing “Token found” plus `/api/v4/user` returning `401 Unauthorized` as an invalid token state, not as a partial success. Re-create the token with suitable scopes (`api`, `read_repository`, `write_repository`) and verify with `glab api user` before creating or merging MRs.
- Before saying auto-merge is available, verify fresh refs, authenticated API access, target branch protection, approval rules, pipeline requirements, and whether the instance accepts merge-when-pipeline-succeeds / auto-merge. If API auth is unavailable, only report best-effort push-option MR creation.

## Release Branch Merge Readiness Audit

Applicability: use when the user asks whether a shared test/staging/release branch can be merged directly into a production/main branch, especially across multiple repos. Anti-condition: do not encode concrete project names, branch names, or migration versions in this skill; resolve the source/target refs from the project profile or user wording each time.

- Fetch/prune first and compare remote refs, not stale local branches: `git fetch origin --prune`, `git rev-list --left-right --count origin/<target>...origin/<source>`, and both ancestry directions with `git merge-base --is-ancestor`.
- When branches have criss-cross history or multiple merge bases, distinguish history divergence from shipped content: inspect both `git diff origin/<target> origin/<source>` (tree delta) and `git diff origin/<target>...origin/<source>` (merge-base scoped delta). A non-zero ahead/behind count with an empty two-dot tree diff can mean the branches are content-equivalent and only need an optional topology merge.
- Do not run a release merge in a dirty or detached shared worktree. Create a clean temporary worktree from `origin/<target>`, then run `git merge --no-commit --no-ff origin/<source>` there. Read back `git status --short`, `git diff --cached --stat`, and unresolved files before judging readiness.
- A clean textual merge is not enough for release readiness. Run the project’s compile/build gate and at least targeted tests for files changed by the merge result.
- If database migrations are present, scan the merged tree for duplicate migration versions/names before approving. For Flyway-style `VNNN__*.sql`, duplicate numeric versions are a release blocker even when Java/TypeScript compilation passes.
- If a targeted test fails only after the source→target dry merge, classify it as a merge-readiness blocker unless proven pre-existing on the target. If checking the target alone, include required reactor/dependency flags so test compilation itself is meaningful rather than failing due missing upstream modules.
- Report per repo: source/target tips, ahead/behind, tree delta vs history delta, dry-merge result, verification commands, blockers, and whether the action is “no merge needed”, “optional topology merge”, “safe to merge”, or “blocked”.
- Clean up temporary worktrees after the audit.

## Branch-to-Branch Change Audit

Applicability: use when the user asks to compare two shared branches such as test/staging vs main/release, especially in a dirty local worktree. Anti-condition: do not encode concrete project names, branch names, PR numbers, or feature names in this skill; resolve repo path and refs from the project profile or user wording each time.

- Fetch/prune first and compare remote refs (`origin/<left>` / `origin/<right>`) when the user asks about shared branch state. Do not let a local dirty branch, gone upstream, or untracked files contaminate the audit.
- Establish the objective facts before summarizing: short ref tips, merge-base, `git rev-list --left-right --count origin/<left>...origin/<right>`, unique commits on each side with dates/subjects, `git diff --stat origin/<left>..origin/<right>`, `git diff --name-status origin/<left>..origin/<right>`, and optionally `git diff --dirstat=files,0` for a product-area overview.
- Explain two-dot vs three-dot deliberately: two-dot (`left..right`) is the current file-tree delta between branch tips; three-dot (`left...right`) is the change introduced on the right side since merge-base. Use both when history has cross-merges or reverted/reintroduced work.
- For merge-readiness, create a clean temporary worktree from the target branch and run `git merge --no-commit --no-ff origin/<source>` there. Report the merge exit, conflict files (`git diff --name-only --diff-filter=U`), and remove the worktree. Never perform a trial merge in the user's dirty working tree.
- In the final report, separate: branch tips/divergence counts, file-tree delta, major product/technical themes, main-only/source-only notable commits, direct-merge conflict risk, and local dirty-worktree caveat.
- Do not run full tests/build unless the task asks for merge readiness or implementation. For a pure diff audit, `git diff --check` plus a clean-worktree dry merge is enough to ground the risk section.

## Branch-Specific Feature/Page Divergence Audit

Detailed branch/page divergence audit moved to `references/branch-specific-divergence-audit.md`.

Load it when deployed behavior differs by branch, page, feature flag, route, or artifact.

Minimum in-root rule: compare exact commits/build artifacts before concluding code is missing or deployed.

## Deployed Behavior Not Matching a Present Commit

Applicability: use this generic Git + deployment investigation pattern when a fix commit is present on a remote branch but the user reports the deployed or online behavior is not effective. Anti-condition: do not encode concrete project names, service names, domains, environment names, or commit hashes in this skill; resolve those from the current repository and hosting metadata each time.

1. **Branch tip semantics**: prove whether the branch still has the fix at its tip, not merely whether it contains the commit. Run path-scoped checks such as `git log <commit>..origin/<branch> -- <affected-paths>` and `git diff --exit-code <commit> origin/<branch> -- <affected-paths>` to detect later overwrites, reverts, or no-op drift.
2. **Deployment metadata**: inspect the hosting service's active deployment branch, commit, status, and domain mapping where available. Treat similarly named environments or domains as distinct until proven otherwise.
3. **Served artifact content**: fetch the live HTML, extract hashed JS/CSS assets, and search served bundles for robust fix markers such as the API call shape, mapping logic, route/component marker, or UI string. Do not rely only on source identifiers that minification may remove.
4. **Dirty/local-future split**: when local source or untracked files show a new runtime path/API call but the deployed artifact does not, classify it as a future/dirty-worktree implementation path rather than current user-facing behavior. Inspect `git status --short`, `git ls-files <paths>`, and served bundle strings before saying an endpoint is currently used. Report separately: deployed behavior, tracked source behavior, and untracked/local-only behavior.
5. **Diagnosis split**: if one served domain contains the fix and another does not, report a deployment/environment mismatch rather than a Git regression. If the served artifact contains the fix but behavior is still old, separate browser/PWA service-worker cache, installed-app cache, and real backend response/data issues before proposing code changes.

## GitLab Self-Managed MR / Auto-Merge Subflow

Detailed GitLab MR and auto-merge subflow moved to `references/gitlab-mr-auto-merge-subflow.md`.

Load it only when operating self-managed GitLab MR automation and exact target/project authority exists.

Minimum in-root rule: MR automation is an external side effect; verify target project, branch, permissions, and receipts.

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
- `references/control-plane-local-existing-cleanup.md` — session-derived checklist for整理 an existing Hermes/control-plane home: classify durable skills/scripts/docs vs runtime/cache/raw evidence, use repo-local excludes, handle hook false positives without bypassing hooks, and report remaining dirty boundaries.
- `references/dirty-workspace-gain-extraction.md` — compare a stale dirty workspace against a target branch, back up state, classify changes, and extract only beneficial increments into a clean worktree.
- `references/dirty-control-plane-scoped-commit-boundary.md` — stop before staging in broad dirty Hermes/control-plane homes; bucket status entries and emit a DecisionPacket / ContinuationPacket before any scoped commit.
- `references/self-managed-gitlab-mr-automation.md` — self-managed GitLab MR creation/auto-merge capability ladder, safe PAT handling, glab auth pitfalls, push-option fallback, and verification evidence.
- `references/clean-pr-worktree-auto-merge.md` — isolate scoped PRs in fresh worktrees and recover from `gh pr merge` failures caused by sibling worktrees using `--repo OWNER/REPO`.
- `references/clean-gitlab-mr-from-dirty-stale-worktree.md` — create GitLab MRs from a clean target-based worktree when the original worktree is dirty, stale, or has ambiguous target-branch wording.
