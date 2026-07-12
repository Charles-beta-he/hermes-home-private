# GitHub reviewed-SHA auto-merge and squash readback

Use this receipt pattern when a GitHub PR is merged after independent review.

## Before merge

1. Read the PR `headRefOid`; it must equal the independently reviewed SHA.
2. Bind the command with `gh pr merge <PR> --match-head-commit <SHA>`.
3. Use `--auto` only when the user authorized auto-merge. If there are no required checks and the PR is immediately mergeable, GitHub may merge immediately; a later `autoMergeRequest: null` is not evidence that the command failed.
4. Do not broaden repository settings merely to make `--auto` available. Enabling repository-wide auto-merge is a separate administrative side effect. Prefer the scoped PR command and read its result.

## After merge

- Read back PR `state`, `mergedAt`, `mergeCommit`, `baseRefName`, and original `headRefOid`.
- Fetch the base branch and verify the reported merge commit is contained in it.
- For squash merges, the reviewed source SHA is not an ancestor of the base. Verify the scoped reviewed files (or patch-id) match between the reviewed tree and squash merge tree instead of using ancestor checks.
- Treat `state=MERGED` plus target-branch readback as the merge proof. Do not infer success from CLI exit text alone.
- If branch auto-deletion is repository policy, a 404 for the source ref after merge is expected readback, not a merge failure.
