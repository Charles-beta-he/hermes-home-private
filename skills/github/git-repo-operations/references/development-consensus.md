# Git Repository Development Consensus

Extracted from `/Users/charles/.hermes/skills/github/git-repo-operations/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Git Repository Development Consensus

Applicability: use for ordinary development work in any Git repository or multi-repo project, especially when a project profile exists. Anti-condition: do not hard-code project names, branch names, remotes, ports, or local paths in this consensus; resolve them from the active repo, project profile, and current user instruction each time.

Core consensus:

1. **Repository role before branch name.** Resolve whether each repo is the primary edit target, reference-only repo, backend/API contract repo, admin/ops repo, generated artifact repo, or deployment/config repo before editing. A sibling/reference repo is read-only unless the user explicitly changes the target.
2. **Branch role before branch operation.** Resolve the branch role (development base, integration/test, release/main, hotfix, personal/topic, stale/gone, variant) before checkout, branch creation, merge, cherry-pick, or push. Do not infer role from names like `main`, `test`, `develop`, or `feat-*` without project evidence.
3. **Fresh remote refs are a gate.** Run `git fetch origin --prune` before creating task branches, comparing branches, merging, cherry-picking, or judging release readiness. If fetch fails, label `origin/*` as cached-local evidence and stop freshness-dependent decisions unless the user explicitly accepts the risk.
4. **Clean/scoped worktree boundary.** Start implementation from a clean worktree or explicitly scoped dirty state. Do not mix unrelated local changes, runtime files, generated files, i18n drift, or reference-repo artifacts into a task commit.
5. **Task branch from resolved base.** Create task branches from the resolved fresh remote base, not from whichever branch happens to be checked out. For multi-repo work, build a repo→base branch map first.
6. **Commit scope is semantic, not convenience-based.** Stage only the files and hunks needed for the current semantic change. Inspect `git diff --cached --stat` and `git diff --cached --name-only` before committing.
7. **Push/PR is an explicit boundary.** Do not push project code by default unless the user asked for push/PR/closeout/deploy flow or the project profile says that workflow requires it. When pushing after rebase, use `--force-with-lease`, never blind force.
8. **Release/integration requires a separate readiness audit.** Merging development branches into test/release/main is not a side effect of ordinary feature work. Compare fresh remote refs, dry-merge in a clean temporary worktree, run relevant tests/build, and report blockers before approving.
9. **Reference parity is evidence, not permission.** When borrowing behavior from another repo/branch/platform, record it as reference evidence, map it into the target repo, and label unsupported/runtime-unverified boundaries. Do not edit or merge the reference line unless explicitly requested.
10. **Report evidence levels.** Distinguish: cached refs vs fresh refs, static diff vs build/test, local branch state vs remote state, reference-code parity vs runtime/browser/device proof, and committed vs pushed state.

Profile/project writeback:

- Stable repo roles, branch roles, allowed merge flows, push policy, reference-only boundaries, and network/fetch quirks belong in the project profile.
- Cross-project reusable mechanics belong in this Git skill.
- One-off branch status, commit IDs, and temporary task progress belong in session evidence/ledger, not global memory.
