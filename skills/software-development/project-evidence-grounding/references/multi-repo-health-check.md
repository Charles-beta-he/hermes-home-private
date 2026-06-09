# Multi-Repo Health Check Workflow

## When to Use

User asks to check project-wide status: "检查其他端是否有未提交代码/未合并PR", "is everything synced?", project hygiene scans.

## Pattern

For each repo in the project (frontend, backend, admin, shared libs):

1. **Uncommitted changes**: `git status --short` — modified, untracked files
2. **Current branch**: `git branch --show-current` — verify not on stale/detached branch
3. **Unpushed commits**: `git log --oneline '@{u}..HEAD'` — commits local but not on remote
4. **Open PRs**: `gh pr list --state open --json number,title,headRefName` — pending merges
5. **Remote tracking**: `git rev-parse --abbrev-ref '@{u}'` — if fails, branch not pushed

## Report Format

Per-repo status with emoji indicators:
- ✅ clean/synced
- ⚠️ has uncommitted changes, unpushed commits, or open PRs

Final summary table.

## Validation After Finding Changes

When uncommitted changes exist, validate against PRD/product docs before recommending commit:
1. Read the diff (`git diff --stat`, then full diff for key files)
2. Cross-reference changes against PRD requirements (PRD section IDs)
3. Check cross-repo contract alignment (backend API ↔ frontend service expectations)
4. Report: compliant / needs review / potential drift

## Pitfalls

- Don't assume repos exist — check with `test -d` first
- `@{u}` fails if branch has no upstream — handle gracefully
- `gh pr list` needs the repo to have a GitHub remote
- Untracked files (??) are easy to miss — always grep for them separately
