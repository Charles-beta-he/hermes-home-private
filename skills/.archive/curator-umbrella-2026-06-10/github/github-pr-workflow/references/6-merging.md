# 6. Merging

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/github/github-pr-workflow/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

**Pitfall: `gh pr merge --auto` may merge instantly.** If the repo has no branch protection rules or CI checks configured, `--auto` doesn't wait — the PR merges immediately. This is correct behavior but can be surprising. If you need the PR to stay open for review, do not use `--auto`; use plain `gh pr merge --squash` only after approval.

**Pitfall: local worktree checkout errors can mask a successful remote merge.** `gh pr merge --auto --squash --delete-branch` may perform the GitHub-side merge and then fail locally while fetching/checking out the base branch, for example `fatal: 'main' is already used by worktree ...`. Do not assume the merge failed from the local exit code alone. Immediately verify remote truth with `gh pr view <n> --json state,mergedAt,mergeCommit,statusCheckRollup`, then watch/check CI if present and `git fetch origin --prune` to confirm branch deletion/base containment.

**With git + curl:**

```bash
PR_NUMBER=<number>

# Merge the PR via API (squash)
curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER/merge \
  -d "{
    \"merge_method\": \"squash\",
    \"commit_title\": \"feat: add user authentication (#$PR_NUMBER)\"
  }"

# Delete the remote branch after merge
BRANCH=$(git branch --show-current)
git push origin --delete $BRANCH

# Switch back to main locally
git checkout main && git pull origin main
git branch -d $BRANCH
```

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`
