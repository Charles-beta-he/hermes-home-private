# Dual-repo fresh-branch closeout

Use this when the user wants both repos confirmed on fresh branches, rebased to the latest remote target, validated, then submitted as PRs.

## Goals
- prove whether each branch is actually new
- rebase onto the current remote target, not stale local `main`
- avoid committing on backend/frontend `main`
- validate both repos AFTER rebase and BEFORE PR creation

## Checklist

### 1) Confirm branch freshness
```bash
# in each repo
git branch --show-current
git ls-remote --heads origin <branch>
gh pr list --state open --head <branch> --json number,baseRefName,headRefName,url
```

Interpretation:
- no remote head + empty PR list => fresh branch
- otherwise => treat as an existing branch/PR and inspect before proceeding

### 2) Refresh remote refs
```bash
git fetch origin --prune
```

### 3) Determine the real base branch
- If a PR already exists, inspect its `baseRefName` and rebase onto `origin/<baseRefName>`
- If no PR exists, default to the intended remote target (commonly `origin/main`)

### 4) Rebase correctly
Repo with active local changes:
```bash
git rebase origin/main --autostash
```

Second repo still on local `main`:
```bash
git pull --rebase origin main
git checkout -b <new-feature-branch>
```

## Important lesson
After rebasing to the latest remote main, run full validation again. Upstream may have introduced a build break unrelated to your feature. Do not open the PR until that break is either fixed or consciously isolated.

Example seen in session:
- rebase to latest `origin/main`
- frontend build failed because `CardAmountLimitsPage` still imported mock exports that `src/data/mock.ts` no longer exported
- fix was not to blame the feature branch, but to recognize an upstream baseline break and restore the missing exports with the smallest viable patch before continuing

### 5) Validate after rebase
Frontend example:
```bash
npm run build
node .hermes/qa/admin-key-pages-playwright.mjs
```

Backend example:
```bash
export JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export PATH="$JAVA_HOME/bin:$PATH"
mvn -pl api/api-admin -am -DskipTests compile
```

### 6) Commit, push, and create PR explicitly
```bash
git push -u origin <branch>
gh pr create --base main --head <branch> ...
gh pr view --json baseRefName,headRefName,mergeStateStatus --jq .
```

## Reporting expectations
When done, report separately for each repo:
- branch name
- whether it was confirmed fresh
- remote base used for rebase
- validation commands that passed
- PR URL
