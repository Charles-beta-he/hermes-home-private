# Clean GitLab MR from a dirty or stale worktree

Use when a user asks to create a GitLab MR from a local branch/worktree that has any of these signs:

- untracked Finder/copy artifacts such as `* 2.*` files;
- the local feature branch is behind the intended target branch;
- the target branch name in wording may be shorthand (`dev`) while the real remote branch is `develop` or another integration branch;
- previous work was committed locally on the wrong/ambiguous branch and needs MR flow.

Anti-conditions:

- Do not use this as permission to merge, auto-merge, or delete source branches.
- Do not create a new target branch just because the requested target name is absent; verify with the user or map from project profile/live refs.
- Do not include session-specific duplicate/untracked files unless they are proven semantic changes.

## Procedure

1. Fetch and verify the target exists as a live remote branch:
   - `git fetch origin --prune`
   - `git ls-remote --heads origin <target>` or GitLab branch API.
   - If `<target>` is absent, list close live refs such as `develop`, `dev-*`, `testing`, then stop for clarification or apply an explicit user correction.
2. Inspect current state:
   - `git status --short --branch`
   - `git rev-list --left-right --count origin/<target>...HEAD`
   - `git diff --name-status origin/<target>..HEAD`
   - Check existing MRs for the candidate source/target.
3. If the source worktree is dirty or behind the target, isolate the MR:
   - `git worktree add -b <mr-branch> /tmp/<repo>-mr origin/<target>`
   - Cherry-pick only the intended commit(s), or apply a scoped patch.
   - Resolve conflicts semantically against the target tip; preserve target-side newer assets/contracts.
4. Verify the candidate branch before push:
   - `git diff --check origin/<target>..HEAD`
   - `git diff --stat --name-status origin/<target>..HEAD`
   - search/check for conflict markers in touched files;
   - run focused tests and the project build when feasible.
5. Push only the clean MR branch:
   - `git push -u origin <mr-branch>`
6. Create/read back the MR through `glab` or GitLab API:
   - verify `state=opened`, expected `source_branch`, expected `target_branch`, head SHA, conflict/mergeability fields, and pipeline status.
   - For older/self-managed `glab` versions, prefer API calls when list/create flags differ or `glab repo view` cannot resolve a private project.
7. Clean up temporary description files and report any excluded dirty files in the original worktree separately.

## Pitfalls

- A local commit message mentioning “dev” is not proof that a remote `dev` branch exists. Live refs/API are the source of truth.
- A feature branch that is behind the target may create an MR that appears to delete target-side newer files. Rebase/cherry-pick into a clean worktree from `origin/<target>` instead.
- `glab mr list --state` and `glab repo view --json` are not universally available. Use `glab mr list --all --source-branch ... --target-branch ... --output json` when supported, or `glab api /projects/<id>/merge_requests?...` for stable readback.
- Keep Finder/copy artifacts such as `file 2.js` out of the MR unless a diff proves they contain intended unique semantic work.
