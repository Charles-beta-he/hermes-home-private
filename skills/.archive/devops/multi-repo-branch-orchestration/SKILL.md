---
name: multi-repo-branch-orchestration
description: "Use when batch git branch management across multiple related repositories based on project profile conventions. Use when switching all repos in a project to their designated branches, verifying branch consistency, pulling latest across repos, or coordinating frontend/backend branch strategies. Triggers: 'switch all branches', 'multi-repo branch', 'batch git checkout', 'branch consistency', 'project branch strategy', '前端发布分支', '后端发布分支'."
triggers:
  - multi-repo branch management
  - batch git branch operations
  - branch consistency across repos
  - project profile branch strategy
  - frontend backend branch coordination
  - 前端发布分支
  - 后端发布分支
---

# Git Branch Management via Project Profile

## Overview

Batch git branch management across multiple related repositories based on project profile conventions. Use when switching all repos in a project to their designated branches, verifying branch consistency, pulling latest across repos, or coordinating frontend/backend branch strategies. Triggers: 'switch all branches', 'multi-repo branch', 'batch git checkout', 'branch consistency', 'project branch strategy', '前端发布分支', '后端发布分支'. This skill is maintained as a `memory`-shaped contract: it should guide retrieval, durable context selection, notes, or knowledge-management workflows without stealing adjacent workflows or relying on unstated assumptions.

Role-based git branch management for one or more repositories. Resolve each repository's remote target branch from the active project profile, then create/sync/rebase/push/PR from that resolved target instead of assuming a universal branch name.

## When to Use

- Project has one or more repos (frontend, backend, admin, mobile, demo, service, library)
- Each repo may have a different remote target branch declared by project profile
- Need to switch repos to their resolved target branches
- Need to create task branches from the correct per-repo remote target
- Need to rebase/sync local work against the correct remote target branch
- Need to verify branch consistency across repos before push/PR/merge

## Workflow

### 1. Resolve Project Profile

Read the project profile to determine branch conventions:

```bash
cat ~/.hermes/project-profiles/<project>.json
```

Look for:
- repo role → local path mapping
- repo role → remote target branch mapping
- branch roles such as trunk, integration, release, environment, task, hotfix, backport
- allowed source-role → target-role transitions
- release/promotion exceptions and required approvals

Principle: concrete branch names are project-profile data. The reusable workflow only consumes roles and resolved remote target refs.

### 2. Discover Repos

Find all repos in the project workspace:

```bash
# Local
ls -d ~/Desktop/work/*/

# Remote (via Edge Worker)
curl -s -X POST http://<edge-ip>:9002/command \
  -H "Content-Type: application/json" \
  -d '{"action":"list_dir","params":{"path":"~/Desktop/work"}}'
```

### 3. Check Current Branch Status

For each repo, check:
- Current branch
- Tracking branch (upstream)
- Ahead/behind status

```bash
# Local
for repo in */; do
  echo "=== $repo ==="
  cd "$repo" && git branch -vv && cd ..
done

# Remote
for repo in repo1 repo2 repo3; do
  echo "=== $repo ==="
  curl -s -X POST http://<edge-ip>:9002/command \
    -H "Content-Type: application/json" \
    -d "{\"action\":\"run_command\",\"params\":{\"command\":\"cd ~/Desktop/work/$repo && git branch -vv\"}}"
done
```

### 4. Resolve Remote Target Branches and Switch

For each repo, resolve the target branch from the project profile before running git operations:

```bash
# Conceptual sequence, with <target> resolved from project profile for this repo/role
git fetch origin --prune
git checkout <target>
git pull --ff-only origin <target>
```

For task work, create the task branch from the resolved remote target, not from the repo default branch or memory:

```bash
git fetch origin --prune
git checkout -B <task-branch> origin/<target>
```

For existing task branches, rebase against the resolved remote target:

```bash
git fetch origin --prune
git rebase origin/<target>
```

### 5. Verify Consistency

After switching, verify all repos are on their target branches:

```bash
for repo in repo1 repo2 repo3; do
  echo "$repo: $(cd ~/Desktop/work/$repo && git branch --show-current)"
done
```

## Branch Strategy Patterns

### Per-Repo Remote Target Map

```
repo-role A → remote target branch declared in profile
repo-role B → remote target branch declared in profile
repo-role C → remote target branch declared in profile
```

The workflow never assumes that all repos share the same target branch. It asks the project profile for the target branch of the current repo and action type.

### Environment-Based

```
repo role(s) → environment branch declared in profile
promotion action → allowed environment transition declared in profile
```

### Role-Based

```
task branch → resolved integration/release baseline
hotfix branch → resolved emergency target
backport branch → resolved maintenance target
release/promotion branch → explicit profile-approved environment/release target
```

## Handling Common Issues

### Divergent Branches

```bash
# Set merge strategy then pull
git config pull.rebase false && git pull
# OR
git config pull.rebase true && git pull
```

### Tracking Branch Gone

```bash
# Switch to main and pull
git checkout main && git pull
```

### Local Commits Need Push

```bash
# Push local commits
git push
```

### Merge Conflicts

```bash
# Check conflict status
git status

# Resolve conflicts, then
git add . && git commit -m "merge: resolve conflicts"
```

## Batch Operation Template

```bash
#!/bin/bash
# Git branch management template driven by project profile.
# Fill BRANCH_MAP from ~/.hermes/project-profiles/<project>.json or a profile parser.

WORK_DIR="/path/to/workspace"
declare -A BRANCH_MAP=(
  ["repo-a"]="<resolved-target-a>"
  ["repo-b"]="<resolved-target-b>"
)

for repo in "${!BRANCH_MAP[@]}"; do
  target="${BRANCH_MAP[$repo]}"
  echo "=== $repo target=$target ==="
  (
    cd "$WORK_DIR/$repo" && \
    git fetch origin --prune && \
    git checkout "$target" && \
    git pull --ff-only origin "$target"
  )
done

printf "\n=== Verification ===\n"
for repo in "${!BRANCH_MAP[@]}"; do
  target="${BRANCH_MAP[$repo]}"
  current=$(cd "$WORK_DIR/$repo" && git branch --show-current)
  upstream=$(cd "$WORK_DIR/$repo" && git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || true)
  printf "%s current=%s target=%s upstream=%s\n" "$repo" "$current" "$target" "$upstream"
done
```

## Integration Points

### With Edge Worker

Use Edge Worker API for remote multi-repo operations. See `cloud-edge-architecture` skill, `references/remote-multi-repo-git-operations.md`.

### With Project Profiles

Read project profiles to determine branch conventions. Profiles live at `~/.hermes/project-profiles/<project>.json`.

### With Taskpool

When taskpool dispatches tasks, ensure the correct branch is checked out before implementation. Branch strategy is part of project context.

## Pitfalls

- **Don't assume all repos use the same target branch** — resolve the remote target branch per repo from the project profile
- **Don't use repo default branch as a universal base** — default branch is repository metadata, not necessarily the task target
- **Don't infer branch targets from memory** — project profile + current remote state are the source of truth
- **Don't force-push without checking** — always verify what's on the remote before pushing
- **Don't skip verification** — always check current branch, upstream, and remote parity
- **Don't ignore divergent branches** — handle merge/rebase strategy before pulling
- **Don't forget to fetch before checkout/rebase** — target branches must be current remote refs
- **Project profile is source of truth** — when in doubt, check the profile, not memory

## References

- Project profile branch maps — per-project data source for repo role → remote target branch
- Git remote refs — runtime source of truth for current target state
- GitHub PR base/head metadata — verification source before PR creation or merge

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
