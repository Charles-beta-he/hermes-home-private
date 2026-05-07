---
type: backlog
layer: L2
status: active
created: 2026-05-08T00:06:02+08:00
concepts: [p9, task-breakdown, implementation-backlog]
---

# P9 - Implementation Backlog

## P0 — Landing package, complete in current loop

- [x] Create project north-star document.
- [x] Create P10 long-term strategy.
- [x] Create P9 implementation backlog.
- [x] Create executable playbook.
- [x] Create task note template.
- [x] Create task workflow contract template.
- [x] Create derived runtime dashboard spec.
- [x] Create multi-model selfcheck review artifact.
- [x] Create expiring task proof ledger.
- [x] Create durable atom for source-of-truth boundary.
- [x] Run self-check script, brainctl sync/reindex/search, multi-model selfcheck, and scoped local commit.

## P1 — Read-only indexer

Task Prompt:

1. Objective: parse `05-实践与项目/tasks/*.md` frontmatter and produce queue rows.
2. Input: task note template and this project strategy.
3. Output: JSON with pending/claimed/running/retry/stale/done counts and rows.
4. Constraints: no file mutation; no network; no LLM; fail on malformed dates only for affected row.
5. Checkpoints: sample all current task notes; dashboard text generated deterministically.
6. Acceptance: script exits 0, reports stale/no-expiry separately, and never changes files.

## P2 — Safe claim/release mutator

Task Prompt:

1. Objective: safely acquire/release task leases in Markdown frontmatter.
2. Input: read-only indexer output, task id, actor id.
3. Output: atomic note update with `claimed_by`, `claim_expires_at`, `run_id`.
4. Constraints: only mutate `05-实践与项目/tasks/`; preserve body; make backup or use atomic rename.
5. Checkpoints: expired lease can be stolen; active lease cannot be stolen without explicit `--force`.
6. Acceptance: tests cover duplicate claim, expired claim, release by owner, release by non-owner.

## P3 — Autonomous execution loop

Task Prompt:

1. Objective: cron claims one eligible task and launches bounded Hermes execution.
2. Input: workflow contract template, task note, project playbook.
3. Output: proof appended to task log and dashboard regenerated.
4. Constraints: T2/T3 route for high blast radius; no arbitrary note hooks; budget cap.
5. Checkpoints: dry-run mode; kill switch; claim release on failure.
6. Acceptance: dry-run demonstrates full claim->execute->proof->release path without touching unrelated notes.

## P4 — Optional external tracker bridge

Only after P1-P3 pass: mirror selected task rows to Linear/GitHub Issues as derived views. Do not reverse canonical direction by default.
