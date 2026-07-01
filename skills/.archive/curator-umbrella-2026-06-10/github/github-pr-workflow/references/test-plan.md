# Test Plan

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/github/github-pr-workflow/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

For integration/release branches, never assume GitHub's default base is correct. Pass `--base <target>` and `--head <working-branch>`, then verify the PR direction:

```bash
gh pr view --json number,state,url,baseRefName,headRefName,mergeStateStatus --jq .
```

Before creating or merging a PR in a named project/repo, first resolve git branch management from the active project profile (or repo AGENTS.md) and treat it as the source of truth over generic branch habits. Interpret branches by role, not by their literal names: trunk, integration baseline, release baseline, environment target, task branch, hotfix branch, and backport branch have different allowed operations. For ordinary task work, create/rebase the task branch from the repo's profile-resolved remote target branch, then open `base=<resolved-target-branch> head=<task-branch>`. Cross-environment, release-sync, hotfix, and backport operations are separate action types and require profile permission plus explicit user intent.

If `baseRefName`/`headRefName` are inverted or violate the project profile branch-management policy, stop before merge: close/supersede the PR or recreate it in the correct direction. See `multi-repo-branch-orchestration` for profile-driven branch target resolution and `references/dual-repo-rebase-push.md` for dual-repo closeout details.

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$OWNER/$REPO/pulls \
  -d "{
    \"title\": \"feat: add JWT-based user authentication\",
    \"body\": \"## Summary\nAdds login and register API endpoints.\n\nCloses #42\",
    \"head\": \"$BRANCH\",
    \"base\": \"main\"
  }"
```

The response JSON includes the PR `number` — save it for later commands.

To create as a draft, add `"draft": true` to the JSON body.
