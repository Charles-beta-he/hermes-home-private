# Clean PR Worktree + GitHub Auto-Merge Worktree Collision

## When this applies

Use this pattern when the working repo already has unrelated dirty files, runtime state, or an existing long-lived task branch, but the user asks to create/merge a scoped PR from the current fix. Also use it when the user says “auto merge PR to <base>” but no open PR exists: interpret the goal as “land the intended current scoped fix through PR flow,” not “merge the whole dirty worktree.”

Applicability: reusable Git/GitHub PR operations where the user names a target base branch and the source fix may have been produced in another branch family or temporary worktree. Anti-conditions: do not use this to override branch protection, bypass review requirements, or merge broad branch-family sync diffs under a narrow fix title.

Before creating the PR, treat the user-named base as the SSOT: fetch remote refs, compare target/source ancestry, and if the fix already exists as a scoped commit, create a clean worktree from `origin/<base>` and `cherry-pick <fix-commit>` instead of deriving a broad diff from the source branch. After cherry-pick/apply, `git diff --stat origin/<base>..HEAD` should show only the intended files; otherwise stop and re-scope.

## Pattern

0. Resolve whether there is an existing PR. If `gh pr list` is empty but the user requested PR/merge flow, do not direct-push to the target and do not stage the dirty workspace. Create the PR from a clean target-base worktree after scoping the semantic hunks.
1. Save only the intended diff from the source repo:
   ```bash
   git -C /path/to/source diff -- path/a path/b > /tmp/task.patch
   ```
2. Create a fresh PR worktree from the actual base branch named by the requested PR target, not from habit. If the user names an integration, staging, release, or production branch, use that fetched `origin/<base>` ref rather than the repo default branch:
   ```bash
   git -C /path/to/source fetch origin --prune
   git -C /path/to/source worktree add -b fix/name /tmp/repo-pr origin/<base>
   git -C /tmp/repo-pr apply --index /tmp/task.patch
   ```
3. If a patch was produced from a different branch family and does not apply to the target base, retry with semantic 3-way apply, then resolve conflicts by preserving the target-base behavior and layering only the scoped task addition. If the source worktree is too dirty or the patch would include unrelated historical changes, skip patch application and manually recreate the small acceptance atoms on the clean target worktree from the already-understood requirements; then verify the resulting diff against the target branch before committing:
   ```bash
   git -C /tmp/repo-pr reset --hard
   git -C /tmp/repo-pr apply --3way --index /tmp/task.patch || true
   git -C /tmp/repo-pr diff --name-only --diff-filter=U
   # edit conflicted files; search only line-start markers to avoid matching decorative ===== comments
   grep -R -n -E '^(<<<<<<<|=======|>>>>>>>)' /tmp/repo-pr --exclude-dir=.git
   git -C /tmp/repo-pr add -u
   ```
   Do not force an old patch over the target branch. Inspect the base files and reapply the semantic changes manually where needed. When the target branch has evolved component/test contracts, rewrite the added regression test to the target branch's current imports, i18n keys, service mocks, and state model instead of copying the dirty source test verbatim. The acceptance unit is the behavior, not identical source text.
4. Verify scope before committing. In conflict cases, inspect the staged diff because `git apply --index`/`--3way` can leave a partially staged index:
   ```bash
   git -C /tmp/repo-pr diff --cached --check
   git -C /tmp/repo-pr diff --cached --stat
   git -C /tmp/repo-pr diff --cached --name-only
   ```
5. Run the relevant targeted tests and production build from the clean PR worktree. For Node/pnpm monorepos, a clean Git worktree does not automatically have dependencies; if the source workspace already has a verified `node_modules` and both worktrees are on the same machine, symlink it into the temp worktree as a local acceleration step, then run the tests/build from the temp path. Treat the symlink only as dependency setup, not as CI proof:
   ```bash
   ln -s /path/to/source/node_modules /tmp/repo-pr/node_modules
   pnpm exec vitest run <focused-tests> --reporter=verbose
   pnpm run build
   ```
   If the target branch's build fails on an unrelated pre-existing type/contract blocker, classify it before widening the PR: first verify the blocker is present on the clean target tip and outside the intended diff. If the user asked to land the PR and the minimal blocker fix is required for the target build gate, add the smallest target-branch-compatible fix in the same clean worktree, call it out explicitly in the PR body/final report, and keep it scoped. Do not hide a target build blocker by skipping the build or by copying broad dirty files from the source branch.

   For Maven multi-module targeted tests, prefer the reactor form with dependencies and disable no-test failure in upstream modules:
   ```bash
   JAVA_HOME="$(/opt/homebrew/bin/brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home" \
   mvn -pl <module> -am -Dtest=<TestClass> -Dsurefire.failIfNoSpecifiedTests=false test
   ```
   If `mvn -pl <module> -Dtest=... test` fails with missing dependent classes, that usually means the reactor dependencies were not included; add `-am` before diagnosing the product code. If upstream modules fail only because they do not contain the named test, add `-Dsurefire.failIfNoSpecifiedTests=false`.
6. Commit exact files only, push, create PR.

## Auto-merge collision

In multi-worktree repos, this command can fail:

```bash
gh pr merge 123 --auto --squash --delete-branch
```

Typical failure:

```text
failed to run git: fatal: 'main' is already used by worktree at '...'
```

Do not remove the other worktree. Run the GitHub operation from a neutral cwd with explicit repo targeting:

```bash
gh pr merge 123 --repo OWNER/REPO --auto --squash --delete-branch
```

Then verify actual state and CI:

```bash
gh pr view 123 --repo OWNER/REPO \
  --json state,mergedAt,mergeCommit,autoMergeRequest,statusCheckRollup,headRefName,baseRefName
git -C /tmp/repo-pr fetch origin --prune
git -C /tmp/repo-pr rev-parse origin/<base>
git -C /tmp/repo-pr log --oneline -3 origin/<base>
```

If the PR is already merged, `autoMergeRequest` may be null; rely on `state`, `mergedAt`, `mergeCommit`, and check conclusions. When the base branch has no required checks or branch protection, `gh pr merge --auto --squash --delete-branch` may merge immediately rather than leaving an auto-merge request; this is still a valid outcome if read-back shows `state=MERGED` and the base ref contains the merge commit.

After a clean-worktree PR merge, do **not** automatically clean or reset the original dirty source worktree. Report that the remote/base branch now contains the change and leave local dirty files untouched unless the user explicitly asks to align or discard them.
