---
name: github
description: Use when you need the Github workflow umbrella. See references/ for detailed
  guides.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - github
    - workflow
    - umbrella
    - routing
    related_skills:
    - codebase-inspection
    - github-auth
    - github-code-review
    - github-issues
    - github-pr-workflow
    - github-repo-management
---

# Github

## Overview

This umbrella skill is the routing surface for github. Use it to choose the most specific child skill, reference, or workflow instead of treating the category name as a one-size-fits-all procedure.

## When to Use

- You need help somewhere inside github and want the quickest route to the right child skill.
- You are not yet sure which github sub-workflow best matches the request.
- You want a compact map of the github skill family before loading a more specific procedure.
- Don't use for: a request that already clearly matches one specific github child skill; load that child skill directly.

## Routing Guide

- `codebase-inspection` — asked to check lines of code, repo size, language composition, or codebase stats.
- `github-auth` — you need guidance on set up GitHub authentication for the agent using git (universally available) or the gh CLI.
- `github-code-review` — you need to review code changes by analyzing git diffs, leaving inline comments on PRs, and performing thorough pre-push review.
- `github-issues` — you need guidance on create, manage, triage, and close GitHub issues.
- `github-pr-workflow` — you need guidance on full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge.
- `github-repo-management` — you need guidance on clone, create, fork, configure, and manage GitHub repositories.

## Selection Rules

- Prefer the narrowest child skill that matches the user request, platform, and desired artifact.
- Stay at the umbrella level only for routing, taxonomy, or category-wide orientation.
- If the request spans multiple subskills, use this umbrella to map the lane first, then hand off to the specific workflow that will do the real work.

## Open-source GitHub Project Research / Due Diligence

When the user asks to “分析研究” an open-source GitHub project, do not stop at README summary or star count. Produce a grounded project brief from live repository evidence:

1. Resolve identity first: search GitHub for the exact/project variants, pick the canonical upstream by stars/forks/description, and report forks/ports separately.
2. Fetch authoritative metadata: GitHub API repo fields, languages, latest release/assets/download counts, contributors, open issues, default branch, timestamps, license API result.
3. Inspect code, not just docs: clone shallow when practical; read README, package/build metadata, security/privacy/license files, changelog, and key entrypoints.
4. Run low-risk verification when feasible: syntax checks, dependency install with scripts disabled when appropriate, dependency audit, and a small local smoke test for documented server/API entrypoints. Cite exact commands/results and stop short of claiming full UI/product verification unless actually exercised.
5. Classify findings into product value, architecture, engineering maturity, security/privacy, licensing/compliance, ecosystem/community, and adoption/adaptation recommendations.
6. Separate reusable inspiration from unsafe copying: names/logos/visual expression, platform terms, unofficial APIs, credentials/cookies, and installer/update chains need explicit risk treatment.

Pitfall: fast-growing visual/demo repos can look more mature than they are. Always check whether the code is a large single-file prototype, whether tests exist, whether dependency audit passes, and whether release/install history includes security advisories or rollback notes.

## Upstream Sync with Local WIP

When the user says to save code and pull latest, especially because others changed the online branch:

0. First classify the request before preserving anything:
   - If the user wants to keep local work, save WIP first.
   - If the user explicitly says "do not modify locally", "only sync remote", "delete/discard local changes", or equivalent, do not create a safety commit. In that case fetch first, then hard-reset to the target remote ref and clean untracked files (`git reset --hard origin/<branch>` + `git clean -fd`). Report that local-only commits will be dropped.
1. Inspect first: `git status --short && git branch --show-current && git remote -v && git log -3 --oneline`.
2. If the worktree is dirty and the user wants preservation, make a local WIP/safety commit before pulling. Use explicit pathspecs for task files rather than `git add -A` in dirty repos, then run `git diff --cached --check`.
3. Fetch/prune and inspect divergence: `git fetch origin --prune`, `git branch -vv`.
4. Prefer `git pull --rebase origin <branch>` for this user's workflow when the goal is to preserve local commits: local commits are preservation points; do not push unless explicitly asked.
5. On conflicts, preserve upstream/online behavior when it represents newer deployed product contract, then re-apply local safety/guard logic without reverting the online change. Example: if upstream changed login from phone to email OTP, keep email flow and merge only the payment-PIN gate. If the conflict is between upstream safety hardening and local UI/layout/observability work, keep the upstream validators/guards and adapt local tests/data to the stricter contract before continuing the rebase.
6. After rebase or hard reset, verify: `git diff --check`, search for conflict markers, run project tests/build when relevant, then report clean/ahead/behind state.
7. If the user explicitly says “rebase/sync origin/main, do not merge to main and do not push”, keep the current feature branch checked out, run `git rebase origin/main`, resolve conflicts there, and stop after local verification. Do not fast-forward local `main`, do not merge the feature branch into `main`, and do not push.
8. For conflict resolution during rebase, preserve upstream/main behavior when it contains newer deployed product contracts, then layer the feature branch’s narrow additions back in. Example pattern: in a Spring Security whitelist conflict, keep all upstream permit rules and add only the feature branch’s missing endpoint(s), rather than replacing the upstream block. After resolving a conflicted commit, run the smallest affected tests before `git rebase --continue` so semantic conflicts (e.g. stricter upstream validators requiring safer fixtures) are caught at the conflict boundary, not after the full rebase.
9. When Maven/Java verification fails after upstream sync, check `mvn -v` before treating it as code failure. Very new JDKs can break annotation processors; for uvisa-backend use JDK 21 (`JAVA_HOME=/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home`) when JDK 25 reports Lombok/javac errors such as `TypeTag :: UNKNOWN`.
10. **Corrupted git ref pitfall**: If `git pull --rebase` fails with `bad object refs/remotes/origin/<branch>` or `cannot lock ref ... Resource deadlock avoided`, there's a corrupted ref file in `.git/refs/remotes/origin/`. Fix: `rm -f` the bad file → `git remote prune origin` → `git fetch origin` → retry. See `references/rebase-conflict-resolution.md` for details.
11. **Non-interactive rebase**: In agent/headless environments, `GIT_EDITOR="true" git rebase --continue` avoids the dumb-terminal editor prompt.
12. **Batch conflict resolution**: When 4+ files have conflicts, write a Python script to resolve them all at once rather than editing each file manually. See `references/rebase-conflict-resolution.md` for the pattern.
13. When the goal is "remote-only sync" for a documentation/prototype repo, dropping the local ahead commit is usually correct after confirmation; do not preserve a throwaway local WIP commit just because it exists.
## References

- `references/rebase-conflict-resolution.md` — batch conflict resolution, corrupted ref fixes, non-interactive rebase, complementary-change merge strategy.

## Absorbed Workflow Packages (6 consolidated in curator umbrella pass)

These former narrow child skills are now treated as subsections/reference packages under this class-level umbrella. Load the package only when the task needs that provider/tool's detailed commands, templates, or scripts; support package directories preserve any former references/templates/scripts/assets under the demoted package; otherwise use the umbrella routing rules above.

- `codebase-inspection` → `references/packages/codebase-inspection/README.md`: Use when asked to check lines of code, repo size, language composition, or codebase stats.
- `github-auth` → `references/packages/github-auth/README.md`: Use when you need guidance on set up GitHub authentication for the agent using git (universally available) or the gh CLI.
- `github-code-review` → `references/packages/github-code-review/README.md`: Use when you need to review code changes by analyzing git diffs, leaving inline comments on PRs, and performing thorough pre-push review.
- `github-issues` → `references/packages/github-issues/README.md`: Use when you need guidance on create, manage, triage, and close GitHub issues.
- `github-pr-workflow` → `references/packages/github-pr-workflow/README.md`: Use when you need guidance on full pull request lifecycle — create branches, commit changes, open PRs, monitor CI status, auto-fix failures, and merge.
- `github-repo-management` → `references/packages/github-repo-management/README.md`: Use when you need guidance on clone, create, fork, configure, and manage GitHub repositories.


## Common Pitfalls

1. Using the github umbrella as the full procedure even though a more specific child skill already fits.
2. Reading the routing map but never loading the referenced child skill or support material that contains the actual execution steps.
3. Choosing a child skill without checking that its platform, tools, and expected artifacts match the current task.
4. **Product/discovery redirect links are not repo identity**: Product Hunt or similar sources may expose a "Github" link only as a redirect that browser/terminal cannot resolve because of Cloudflare. Treat `github_link_detected_unresolved` as a lead, not metadata. Resolve by searching GitHub/public web for the product tagline/name, then verify the live GitHub API repo metadata (`full_name`, description, stars, forks, license, pushed_at, default_branch) before analyzing or reporting the project.
5. **Direct repo taskpool intake still needs evidence shape**: When the user says “分析添加任务池” and gives a direct GitHub repo (including shorthand like `GitHub - owner/repo`), do not make a generic “review repo” card. Normalize to the canonical URL, fetch authoritative API metadata, read upstream README/docs, note platform/license/runtime boundaries, then create an adaptation/evaluation card with explicit non-goals and expected proof. If `README.md` is missing, list repo contents or try actual casing such as `readme.md` before concluding there is no README.
4. **PR scope leakage during verification fixes**: If a focused PR (for example layout/theme/safe-area) fails build because unrelated main-branch tests/types are already broken, do not silently fold broad business-code repairs into the focused commit without calling out the scope expansion. Prefer a separate commit/PR for the baseline repair, or explicitly label the extra change as a build-unblocking compatibility fix in the PR body and final report. After merge, if asked why an unrelated hunk changed, explain it from actual test/build evidence rather than the PR title.
4. **PR scope leakage during verification fixes**: If a focused PR (for example layout/theme/safe-area) fails build because unrelated main-branch tests/types are already broken, do not silently fold broad business-code repairs into the focused commit without calling out the scope expansion. Prefer a separate commit/PR for the baseline repair, or explicitly label the extra change as a build-unblocking compatibility fix in the PR body and final report. After merge, if asked why an unrelated hunk changed, explain it from actual test/build evidence rather than the PR title.
5. **Auto-merge is still gated by fresh risk signals**: If the user asks to auto-merge a PR and then requests a same-batch/iceberg scan, or reports a fresh regression in the same message/batch, pause the merge before executing it. Scan adjacent commits and the PR diff for hidden regressions, amend the PR if the findings are in-scope, rerun focused verification, comment the added evidence, and only then merge. Split unrelated findings into a separate PR.
6. **Dirty worktrees must not become PR scope.** When the user's current repo has unrelated uncommitted WIP, do not create or merge a PR from that checkout. Create a clean temporary worktree from the target base branch, apply only the intended files/commits, run verification there, push that branch, and merge the PR. If `gh pr merge` succeeds remotely but local cleanup fails because a branch name is already used by another worktree, verify the PR state and `origin/<base>` commit with GitHub/readback before reporting success; treat the local cleanup error as local-only.
7. **React list key changes are low-risk only when scoped**: Replacing `key={translatedLabel}` with a stable business key is acceptable to satisfy tests or avoid i18n/key churn, but it should not be bundled with semantic label/hint changes unless those are part of the requested product change and covered by tests.
5. **Auto-merge is still gated by fresh risk signals**: If the user asks to auto-merge a PR and then requests a same-batch/iceberg scan, or reports a fresh regression in the same message/batch, pause the merge before executing it. Scan adjacent commits and the PR diff for hidden regressions, amend the PR if the findings are in-scope, rerun focused verification, comment the added evidence, and only then merge. Split unrelated findings into a separate PR.
6. **Dirty worktrees must not become PR scope.** When the user's current repo has unrelated uncommitted WIP, do not create or merge a PR from that checkout. Create a clean temporary worktree from the target base branch, apply only the intended files/commits, run verification there, push that branch, and merge the PR. If `gh pr merge` succeeds remotely but local cleanup fails because a branch name is already used by another worktree, verify the PR state and `origin/<base>` commit with GitHub/readback before reporting success; treat the local cleanup error as local-only.
7. **React list key changes are low-risk only when scoped**: Replacing `key={translatedLabel}` with a stable business key is acceptable to satisfy tests or avoid i18n/key churn, but it should not be bundled with semantic label/hint changes unless those are part of the requested product change and covered by tests.

## PR merge readback notes

- For `auto merge PR to <base>` requests from a dirty checkout, use a clean temporary worktree from `origin/<base>` and apply only the intended patch/commit before opening the PR.
- After `gh pr merge --auto`, always read back both GitHub PR state and base branch state. `--auto` can merge immediately when the PR is mergeable and has no required pending checks; do not assume it only schedules future auto-merge.
- Minimum readback: `gh pr view <n> --json state,mergedAt,mergeCommit,baseRefName,headRefName` plus `git fetch origin <base> --prune && git log -1 origin/<base>`.
- If the original checkout still shows the same modified files after the clean-worktree PR is merged, classify that as local dirty state, not remote merge failure. Do not clean it unless the user explicitly asks.

## Verification Checklist

- [ ] The request was mapped to the best-fitting child skill or explicitly kept at umbrella level for routing only.
- [ ] The selected child skill descriptions, references, and prerequisites were checked before substantive execution.
- [ ] Any claimed handoff, output, or route decision was read back against the specific child workflow before completion.



## 输入

- 用户请求的具体参数

## 约束

- 遵循项目规范
- 在 context budget 内完成

## 检查点

- [ ] 输入参数完整
- [ ] 输出符合预期格式
