# Clean PR Worktree + GitHub Auto-Merge Worktree Collision

## When this applies

Use this pattern when the working repo already has unrelated dirty files, runtime state, or an existing long-lived task branch, but the user asks to create/merge a scoped PR from the current fix.

## Pattern

1. Save only the intended diff from the source repo:
   ```bash
   git -C /path/to/source diff -- path/a path/b > /tmp/task.patch
   ```
2. Create a fresh PR worktree from the actual base branch:
   ```bash
   git -C /path/to/source fetch origin --prune
   git -C /path/to/source worktree add -b fix/name /tmp/repo-pr origin/main
   git -C /tmp/repo-pr apply /tmp/task.patch
   ```
3. If the patch fails, do not force it blindly. Inspect the base files and reapply the semantic changes manually.
4. Verify scope before committing:
   ```bash
   git diff --check
   git diff --stat
   git diff -- path/a path/b
   ```
5. Run the relevant targeted tests and production build from the clean PR worktree.
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
