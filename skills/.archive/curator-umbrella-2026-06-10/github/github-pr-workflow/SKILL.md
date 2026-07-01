---
name: github-pr-workflow
description: Use when you need guidance on full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - GitHub
    - Pull-Requests
    - CI/CD
    - Git
    - Automation
    - Merge
    related_skills:
    - github-auth
    - github-code-review
---

# GitHub Pull Request Workflow

## Overview


Complete guide for managing the PR lifecycle. Each section shows the `gh` way first, then the `git` + `curl` fallback for machines without `gh`.

## When to Use

- You need guidance on full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls
  if [ -z "$GITHUB_TOKEN" ]; then
    if [ -f ~/.hermes/.env ] && grep -q "^GITHUB_TOKEN=" ~/.hermes/.env; then
      GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" ~/.hermes/.env | head -1 | cut -d= -f2 | tr -d '\n\r')
    elif grep -q "github.com" ~/.git-credentials 2>/dev/null; then
      GITHUB_TOKEN=$(grep "github.com" ~/.git-credentials 2>/dev/null | head -1 | sed 's|https://[^:]*:\([^@]*\)@.*|\1|')
    fi
  fi
fi
echo "Using: $AUTH"
```

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout main && git pull origin main

# Create and switch to a new branch
git checkout -b feat/add-user-authentication
```

Branch naming conventions:
- `feat/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

## 2. Making Commits

Use the agent's file tools (`write_file`, `patch`) to make changes, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Commit with a conventional commit message
git commit -m "feat: add JWT-based user authentication

- Add login/register endpoints
- Add User model with password hashing
- Add auth middleware for protected routes
- Add unit tests for auth flow"
```

Commit message format (Conventional Commits):
```
type(scope): short description

Longer explanation if needed. Wrap at 72 characters.
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`, `perf`

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

Detailed `Push the Branch (same either way)` guidance moved to `references/push-the-branch-same-either-way.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Rebase Target for an Existing PR

When a feature branch already has an open PR, inspect the PR's current base before rebasing. Do not assume local `main`, the repo default branch, or an older remembered target is still correct.

If the user instead says the repo should be sync-only and local changes should be deleted, do not create a WIP/safety commit before sync. Fetch first, then reset/clean to the target remote ref after confirming the branch/ref to keep.

```bash
# Verify PR direction first
gh pr list --state open --head $(git branch --show-current) \
  --json number,baseRefName,headRefName,url

# Then fetch and rebase onto the fetched remote base ref
git fetch origin --prune
git rebase origin/<baseRefName>
```

User-correction pattern to preserve: if the user says to "rebase the target branch" or reminds you to use the latest remote target, re-check the PR base from GitHub and rebase onto the fetched remote base ref, not a stale local branch.

### Fresh-Branch Verification Before First Push / PR

When the user asks you to confirm a branch is really new before committing or opening a PR, verify it explicitly instead of assuming from the local branch name:

```bash
# Confirm current branch and whether the remote already has that head
git branch --show-current
git ls-remote --heads origin <branch>

# Check whether a PR already exists for this head
# (empty array/output means no existing PR)
gh pr list --state open --head <branch> --json number,baseRefName,headRefName,url
```

Interpretation:
- no remote head + no existing PR => treat as a fresh branch
- remote head exists or PR already exists => do not describe it as new; inspect and continue from the existing branch/PR lifecycle

For dual-repo work, perform this check in BOTH repositories before committing so you don't accidentally stack new work onto an old remote branch in one repo while the other repo is fresh.

### Dual-Repo Pre-PR Rebase + Verification Closeout

When coordinating frontend/backend (or any dual-repo) delivery and the user wants commit/PR only after both sides are aligned:

1. Fetch both repos first: `git fetch origin --prune`
2. Identify the real remote target branch in each repo (usually `origin/main`, but verify open PR base if one exists)
3. Rebase the repo with local work onto the fetched remote base; if the worktree is dirty but intentional, use `git rebase <base> --autostash`
4. For the second repo that is still on `main`, first fast-forward/rebase local `main` to `origin/main`, then create the new feature branch FROM that updated main
5. Re-run builds/tests after the rebase in both repos before committing; upstream main may introduce unrelated breakage that must be resolved before the PR is truly ready
6. Only after both repos are green: commit, push with upstream tracking, create PR with explicit `--base` and `--head`, then verify PR direction via `gh pr view --json baseRefName,headRefName,mergeStateStatus`

See `references/dual-repo-fresh-branch-closeout.md` for a concrete checklist and command sequence.

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan

Detailed `Test Plan` guidance moved to `references/test-plan.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

**With git + curl:**

```bash
# Get the latest commit SHA on the current branch
SHA=$(git rev-parse HEAD)

# Query the combined status
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Overall: {data['state']}\")
for s in data.get('statuses', []):
    print(f\"  {s['context']}: {s['state']} - {s.get('description', '')}\")"

# Also check GitHub Actions check runs (separate endpoint)
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/check-runs \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for cr in data.get('check_runs', []):
    print(f\"  {cr['name']}: {cr['status']} / {cr['conclusion'] or 'pending'}\")"
```

### Poll Until Complete (git + curl)

```bash
# Simple polling loop — check every 30 seconds, up to 10 minutes
SHA=$(git rev-parse HEAD)
for i in $(seq 1 20); do
  STATUS=$(curl -s \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/$OWNER/$REPO/commits/$SHA/status \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
  echo "Check $i: $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "error" ]; then
    break
  fi
  sleep 30
done
```

### Distinguish “failing CI” from “no CI configured”

Detailed `Distinguish “failing CI” from “no CI configured”` guidance moved to `references/distinguish-failing-ci-from-no-ci-configured.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Check Presence vs Check Failure

If `gh pr checks` reports `no checks reported on the '<branch>' branch`, do not treat that as a failing CI run. Confirm whether the repository actually has any configured checks before starting a fix loop.

```bash
# PR-level view
gh pr view <number> --json mergeStateStatus,statusCheckRollup --jq .

# Workflow inventory
gh api repos/$OWNER/$REPO/actions/workflows
```

Interpretation:
- `statusCheckRollup: []` or `null` plus `workflows: []` means the repo has no configured GitHub Actions / PR checks for this branch.
- In that case, report that there are no checks to fix; the merge gate, if any, is likely review/ruleset based rather than CI-failure based.

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

**With git + curl:**

```bash
BRANCH=$(git branch --show-current)

# List workflow runs on this branch
curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$OWNER/$REPO/actions/runs?branch=$BRANCH&per_page=5" \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)['workflow_runs']
for r in runs:
    print(f\"Run {r['id']}: {r['name']} - {r['conclusion'] or r['status']}\")"

# Get failed job logs (download as zip, extract, read)
RUN_ID=<run_id>
curl -s -L \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/logs \
  -o /tmp/ci-logs.zip
cd /tmp && unzip -o ci-logs.zip -d ci-logs && cat ci-logs/*.txt
```

### Step 2: Fix and Push

After identifying the issue, use file tools (`patch`, `write_file`) to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Use `read_file` + `patch`/`write_file` → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

## 6. Merging

Detailed `6. Merging` guidance moved to `references/6-merging.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Enable Auto-Merge (curl)

```bash
# Auto-merge requires the repo to have it enabled in settings.
# This uses the GraphQL API since REST doesn't support auto-merge.
PR_NODE_ID=$(curl -s \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/pulls/$PR_NUMBER \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['node_id'])")

curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/graphql \
  -d "{\"query\": \"mutation { enablePullRequestAutoMerge(input: {pullRequestId: \\\"$PR_NODE_ID\\\", mergeMethod: SQUASH}) { clientMutationId } }\"}"
```

## PR 前闭环共识（开发闭环后段）

This is the delivery-tail subset of `development-closure-consensus`. Use it after the task's main chain and project-specific validation have been handled, not as a replacement for upstream closure diagnosis.

For dual-repo or high-stakes PR closeout, use `references/pr-closeout-consensus.md` as the condensed rule set. It captures the durable cross-project consensus from repeated manual closeout work: verify fresh branches against the remote, rebase onto the true remote base, rerun validation after any baseline change, distinguish “no checks configured” from “checks failing”, keep commit scope precise, and make frontend/backend dependency + merge order explicit in PR comments.

## 7. Complete Workflow Example

```bash
# 1. Start from clean main
git checkout main && git pull origin main

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (Agent makes code changes with file tools)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Useful PR Commands Reference

| Action | gh | git + curl |
|--------|-----|-----------|
| List my PRs | `gh pr list --author @me` | `curl -s -H "Authorization: token $GITHUB_TOKEN" "https://api.github.com/repos/$OWNER/$REPO/pulls?state=open"` |
| View PR diff | `gh pr diff` | `git diff main...HEAD` (local) or `curl -H "Accept: application/vnd.github.diff" ...` |
| Add comment | `gh pr comment N --body "..."` | `curl -X POST .../issues/N/comments -d '{"body":"..."}'` |
| Request review | `gh pr edit N --add-reviewer user` | `curl -X POST .../pulls/N/requested_reviewers -d '{"reviewers":["user"]}'` |
| Close PR | `gh pr close N` | `curl -X PATCH .../pulls/N -d '{"state":"closed"}'` |
| Check out someone's PR | `gh pr checkout N` | `git fetch origin pull/N/head:pr-N && git checkout pr-N` |

## Per-File Revert (Surgical)

When a commit touches multiple files but only some need reverting, use `git checkout <sha>^ -- <file>` for surgical per-file control instead of `git revert` (which undoes the entire commit). See `references/surgical-file-revert.md` for the full workflow: inspect → revert specific files + tests → verify tsc/tests → commit → PR.

## Branch Already Merged Detection

When `gh pr create` fails with `No commits between <base> and <head>`, the branch is already fully merged into the target — no new PR is needed. This commonly happens when:

- A previous PR already merged the branch's commits
- The local branch wasn't cleaned up after merge

Do NOT force-push or retry `gh pr create`. Instead:
1. Verify: `git log --oneline origin/<target>..HEAD` shows zero commits
2. Report to the user: the branch is already in sync with the target, prior PR already merged
3. Optionally clean up: `git checkout <target> && git pull && git branch -d <feature-branch>`

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
3a. **Verify staging before committing.** After `git add <files>`, always check `git diff --cached --stat` to confirm the files are actually staged. A `git add` can silently fail if the path is wrong, the file is in `.gitignore`, or the working tree state changed. Committing without verified staging leads to "nothing to commit" or empty commits that silently lose work — especially dangerous in `execute_code` where multiple `terminal()` calls can mask the issue.
3b. **MCP `git_add` may not clear prior staging.** When using MCP `git_add(files=[...])`, other files already in the staging area from prior operations remain staged. The subsequent `git_commit` commits EVERYTHING staged, not just the file you just added. After MCP `git_add`, always verify `git diff --cached --stat` and `git reset HEAD -- <junk>` any files that shouldn't be in the commit.
4. **Upstream build errors block deployment even when your changes are clean.** When creating a PR against a branch that already has TypeScript/build errors (e.g. from a previous merge), Railway/CI deployment will fail for YOUR commit even though the error is not yours. Always run `pnpm build` (or equivalent) locally BEFORE pushing to catch pre-existing breakage on the target branch. If you find upstream errors, fix them in your PR and note in the PR body that you also fixed a pre-existing build blocker.
5. **Shell escaping in `gh pr create --body`**: When passing a multiline PR body via `terminal()` to `gh pr create --body "..."`, bash interprets backticks as command substitution, `$()` as subshells, and `!` as history expansion. This silently corrupts the PR body or causes shell errors. **Safe approach**: write the body to a temp file first, then pass via `--body-file`:
6. **Python f-string escaping in `execute_code` commit messages**: When using `execute_code` with `terminal()` to run `git commit -m '...'`, Python f-strings interpret `{curly_braces}` as expressions. A commit message containing `{fx_debit, fx_credit}` triggers `NameError`. **Safe approach**: build the message as a plain Python string variable (no f-string), then pass it to `terminal()` via string concatenation or `.format()` only where needed. For messages with curly braces, use regular strings with `+` concatenation.
   ```bash
   # Write body to temp file, then use --body-file
   python3 -c "
   body = '''## Summary
   - Feature A with \`code\` inline
   - \$variable references preserved
   '''
   open('/tmp/pr-body.md','w').write(body)
   "
   gh pr create --title "feat: ..." --body-file /tmp/pr-body.md --base main --head feature-branch
   ```
   Alternatively, use `write_file` to create the body file, then `terminal()` to run `gh pr create --body-file /tmp/pr-body.md`.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
