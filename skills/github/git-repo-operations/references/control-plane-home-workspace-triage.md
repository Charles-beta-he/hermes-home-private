# Control-plane home workspace triage

Use when a repository doubles as a local agent/control-plane home and has a very large dirty working tree. This applies to repos that mix source-like assets, private configuration, memory/profile state, runtime databases, task evidence, logs, vendored checkouts, and submodules. It does **not** apply to ordinary application repos with normal source-only layouts.

## Principle

Treat the repo as a mixed state store, not a normal application repo. Do not use broad Git operations until the dirty tree is classified.

## Safe discovery sequence

1. Verify remote parity first:
   - `git status --short --branch`
   - `git rev-list --left-right --count <upstream>...HEAD` when an upstream exists.
2. Confirm nothing is staged:
   - `git diff --cached --stat`
3. Collect machine-readable status without flooding the transcript:
   - `git status --porcelain=v1 -z`
   - Group by top-level path and status (`M`, `D`, `??`).
4. Inspect submodules separately:
   - `git diff --submodule=log -- <submodule-path>`
   - `git -C <submodule-path> status --short --branch`
5. Produce a classified report before editing or committing.

## Classification buckets

- **Sensitive/personal state**: local config, provider/quorum config, memories/profile files, `.env*`, credentials. Do not stage directly. If backup is needed, use redacted examples or an encrypted/private backup strategy.
- **Runtime/cache/log state**: runtime DBs, route/outcome DBs, lock files, gateway state, context-length caches, model caches, volatile logs, snapshots. Usually do not commit ongoing drift; consider a separate `git rm --cached` plus `.gitignore` migration if these are tracked.
- **Brain/docs**: local notes and private governance docs. Usually durable but should be committed separately after the relevant validator or a scoped "no new violations" check.
- **Scripts/control-plane code**: local automation scripts, execution workers, eval baselines, tests. Commit by feature slice after compile checks, focused tests, or the script's own selfcheck.
- **Skills**: skill libraries and curator outputs. Large skill syncs often mix real improvements, generated reports, hub/bundled changes, and deletions. Never batch-submit all deletions without a deletion review.
- **Task/runtime evidence directories**: task queues, task progress, task evidence, repair evidence. Treat as live control-plane state unless explicitly promoted through a manifest.
- **Vendor/worktrees/tmp/tools**: inventory first; do not blindly delete.

## Recommended cleanup order

1. Commit or intentionally defer a single submodule gitlink update if the submodule is already pushed and the parent should follow it.
2. Separate a runtime boundary migration: `.gitignore` additions plus `git rm --cached` for volatile tracked artifacts. Do not delete local files unless explicitly requested.
3. Commit brain/docs sync separately from code.
4. Commit scripts/control-plane code by tested feature slice.
5. Triage skills last: first review deletes, then generated curator/steward reports, then durable skill content.
6. After all durable tracked work is committed, handle the remaining untracked local overlay without deleting it. Prefer repository-local `.git/info/exclude` for huge profile/media/runtime/experiment overlays that should be invisible on this machine but should not become project-wide `.gitignore` policy.

## Durable vs local-only ignore boundary

- Use committed `.gitignore` for class-level repo policy: secrets, live runtime DBs, state snapshots, logs, task queues, generated caches, and other paths that no clone should normally track.
- Use `.git/info/exclude` for machine-local overlays discovered during cleanup: archived profiles, pasted files, screenshots, experiments, backup checkouts, local bridge projects, or other paths where committing an ignore rule would pollute the shared policy.
- When using `.git/info/exclude` from status output, iterate until `git status --porcelain` is empty: ignoring a directory can reveal nested untracked paths that were previously hidden by the parent entry.
- Record the decision in the final report: "clear" may mean clean tracked state plus ignored local overlay, not file deletion.

## Pre-commit guard handling

- Treat secret/credential pre-commit guards as fail-closed. Do not bypass hooks to finish a cleanup.
- If a durable governance/eval/skill file only contains variable names or placeholder examples, either broaden the guard's allowed documentation prefixes in the guard code (while keeping value detection active) or rewrite the example to avoid secret-like values.
- Redact placeholder values that match real credential-shaped examples (for example bearer-key placeholders, signing-value placeholders, or sample credential env files). Prefer `[REDACTED_PLACEHOLDER]` or prose instructions over fake-but-pattern-matching credentials.
- After guard changes, run a small syntax check/test for the guard or touched script before committing.

## Submodule cleanup details

- If tracked external skill submodules are kept but their internal working trees are noisy, set `ignore = dirty` in `.gitmodules` for those specific external submodules rather than committing their internal build artifacts.
- If a tracked submodule path has been intentionally removed from the working tree, remove the corresponding `.gitmodules` section in the same commit that stages the gitlink deletion.

## Verification before final clear

- Verify parent repo: `git status --short --branch`, `git rev-list --left-right --count HEAD...origin/<branch>`.
- Verify child repos/submodules that were touched: `git -C <path> status --short --branch`.
- After push, verify local and remote HEAD match with `git rev-parse --short HEAD` and `git rev-parse --short origin/<branch>`.
- If `.git/info/exclude` was used, optionally count ignored overlay entries with `git status --ignored --porcelain | grep '^!!' | wc -l` and disclose that local overlay remains ignored on disk.

## Hard stops

- Do not run `git add -A`, `git clean -fd`, or `git checkout .` in a mixed control-plane home repo without an explicit reviewed scope.
- Do not stage live config, memories, or DB files as part of a broad cleanup.
- Do not treat a private remote as sufficient protection for secrets; private repos still need redaction boundaries.
- Do not mix submodule gitlink updates with unrelated runtime/config/skill churn.
