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

## Hard stops

- Do not run `git add -A`, `git clean -fd`, or `git checkout .` in a mixed control-plane home repo without an explicit reviewed scope.
- Do not stage live config, memories, or DB files as part of a broad cleanup.
- Do not treat a private remote as sufficient protection for secrets; private repos still need redaction boundaries.
- Do not mix submodule gitlink updates with unrelated runtime/config/skill churn.
