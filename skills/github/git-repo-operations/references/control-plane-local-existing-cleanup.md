# Control-plane local existing cleanup

Use when整理 an agent/control-plane home repo that contains a mix of durable skills/scripts/docs, submodule pointers, runtime caches, raw evidence, backups, and hook-sensitive files.

## Landing-zone classifier

Classify before staging:

- Durable procedure or reusable debugging path -> skill SKILL.md or `references/` under the matching umbrella.
- Durable local script/test/doc that belongs to the repo -> scoped commit.
- Runtime/cache/dashboard/generated backup -> keep on disk; ignore through repo-local `.git/info/exclude` unless it should be shared policy.
- Raw evidence captures (HTML, screenshots, large fetched repository trees, probe bodies) -> keep on disk or summarize into a reference; do not blindly commit raw captures.
- Project facts/paths/branches -> project profile or scoped reference with applicability and anti-conditions.
- Hook-sensitive but legitimate wording (for example token/security/RL terms or environment variable names) -> do not bypass hooks; either redact/rename into a safer durable artifact or leave as local pending work with the boundary stated.

## Safe sequence

1. Fetch first for every repo/subrepo: `git fetch origin --prune`.
2. Read both status layers: parent repo and nested source/submodule repos.
3. Inventory tracked changes, untracked files, and largest untracked artifacts separately.
4. Add local-only excludes for machine/runtime/raw-evidence patterns in `.git/info/exclude`, not shared `.gitignore`, when the policy is local-only.
5. Stage only the durable slice; inspect `git diff --cached --name-only`, `git diff --cached --stat`, and `git diff --cached --check`.
6. Run targeted tests for any scripts/tools included in the commit.
7. If a commit hook flags a secret-like false positive, reset the flagged paths and commit the safe slice. Do not use `--no-verify` unless the user explicitly authorizes that exact risk.
8. For submodule/source repo work, commit inside the child first, then stage only the parent gitlink pointer plus intended parent files.
9. Before deleting untracked files in a live control-plane home, snapshot them to an out-of-repo tarball and then verify operational references that may point to untracked files (especially cron job `script` paths). If an enabled cron references an untracked script, restore that script from the backup and hide it with local `.git/info/exclude` rather than leaving the job broken.
10. Treat live runtime-persona files separately from source cleanliness. If a tracked file is continuously rewritten by the running agent process (for example `SOUL.md` in Hermes home), either stop the writer and restore it or mark it local-only with `git update-index --skip-worktree <file>` and report the exact unhide command.
11. Final readback: parent/child `status --short --branch`, `status --porcelain=v1` count, untracked count, diff/cached-diff quiet exits, ahead/behind counts, submodule/gitlink status, enabled cron script existence, and backup readability.

## Reporting format

Report:

- what was committed and in which repo;
- what was only locally excluded/kept on disk;
- what remains dirty and why;
- verification commands and outputs;
- push boundary separately from local cleanup.

## Pitfalls

- `git add -A` in a control-plane home can accidentally stage huge raw evidence trees or generated backups. If used as a sweep, immediately inspect and reset non-durable classes before commit.
- A clean untracked list after `.git/info/exclude` does not mean data was deleted; disclose that ignored local artifacts remain on disk.
- Secret scanners can flag variable names or domain terms in legitimate docs/scripts. Treat this as a redaction/landing-zone problem, not as permission to bypass hooks.
- Do not mix child repo commits, parent gitlink updates, runtime notes, and raw captures into one unreviewable commit.
- `git clean -fd` can make the Git status clean while breaking local automation when enabled jobs reference untracked scripts. After any clean sweep in Hermes/control-plane homes, read the scheduler job registry and prove every enabled script path exists; restore operational scripts from the backup and local-exclude them if they are intentionally machine-local.
- A tracked file that is immediately rewritten by a running daemon/agent can make `git restore` appear ineffective. Do not loop on restore; identify the writer or mark the file as local-only with `skip-worktree`, then report that this is cleanliness hiding, not a committed source change.
