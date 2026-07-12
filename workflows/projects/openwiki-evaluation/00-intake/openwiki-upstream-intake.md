# OpenWiki Upstream Intake — openwiki-evaluation

Captured: 2026-07-07T16:18:23+08:00
Source: https://github.com/langchain-ai/openwiki

## Positioning

OpenWiki is accepted as a candidate repo-local documentation layer for coding agents. It is not accepted as a replacement for Hermes project profiles, SSOT ledgers, taskpool evidence, or durable skills.

## Evidence summary

- Canonical upstream: langchain-ai/openwiki
- License: MIT
- GitHub stars/forks at capture: 8142 / 545
- Open issues at capture: 104
- Latest push: 2026-07-06T23:37:14Z
- npm last-week downloads: 3828
- Local verification: install/typecheck/test/audit/build/help/dry-run all exited 0 in `/tmp/openwiki-langchain`.

## Transferable value

- Generates `openwiki/` docs as a repository-local codebase map.
- Adds agent entrypoint hints through root `AGENTS.md` / `CLAUDE.md`.
- Uses git evidence and update metadata to keep documentation surgical.
- Fits Hermes as a per-repo context accelerator, especially for unfamiliar repositories.

## Boundaries

- Generated docs are advisory indexes, not source-of-truth facts.
- Production/code changes still require source reads, tests, and UI/API/log evidence.
- No CI auto-update or auto-merge until a pilot repository passes the decision task.
- Do not run on protected work repos unless the user explicitly switches to that project.
- Watch for AGENTS.md/CLAUDE.md pollution and monorepo/binary-file gaps.

Evidence file: `03-evidence/openwiki-upstream-research-20260707T161823+0800.json`
