# Distinguish “failing CI” from “no CI configured”

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/github/github-pr-workflow/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Distinguish “failing CI” from “no CI configured”

Before entering an auto-fix loop, verify whether the repository actually has checks configured. A PR with no workflows or required statuses is not a failing CI situation.

Symptoms of the no-CI case:
- `gh pr checks` prints `no checks reported on the '<branch>' branch`
- `gh pr view --json statusCheckRollup` returns `[]`
- GraphQL `statusCheckRollup` is `null`
- `gh api repos/$OWNER/$REPO/actions/workflows` returns `total_count: 0`
- Commit status API shows `state: pending` with `total_count: 0` and empty `statuses`

Useful verification commands:

```bash
# PR rollup from REST/gh
gh pr view <PR_NUMBER> --json number,state,mergeStateStatus,statusCheckRollup --jq .

# Workflows configured in the repo
gh api repos/$OWNER/$REPO/actions/workflows

# Commit-level status payload
SHA=$(git rev-parse HEAD)
gh api repos/$OWNER/$REPO/commits/$SHA/status
```

Interpretation:
- If workflows/checks are absent, report that the PR is not blocked by CI; do not claim there are failing checks to fix.
- In that case, remaining blockers are usually review requirements, branch protection, rulesets, or external/non-GitHub checks.
