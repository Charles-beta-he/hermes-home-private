# Operational Watchdog Cron Scripts

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Operational Watchdog Cron Scripts

When a no-agent autorun/summary cron reports an error while `selfcheck` and `proof-check` pass, first use `references/human-escape-autorun-cron-triage.md`: distinguish safe `human_escape` preclaim pauses, duplicate P2/evolution candidates, empty no-op output, and real live dispatch blockers before treating the cron as broken.

When building or modifying `no_agent=True` cron scripts that monitor task pool health (budget-exhausted triage, auth-blocked notifications, stale-claim cleanup) — or any script that calls `brain_task_orchestrator.py` as a subprocess — load `references/operational-cron-watchdogs.md`: it covers the script-path pitfall (`script` takes filename only, not full path), deduplication/cooldown patterns, JSONL logging, kanban DB query templates, hook registry `post_task_block` integration, the budget-exhausted triage decision matrix (续费/拆分/降级/放弃 by domain × complexity × progress), and the subprocess timeout pitfall (orchestrator `list --json` can exceed 30s on cold cache with 300+ task files — always use `timeout=120`).

When Hermes selfcheck/sentinel alerts spam Telegram or repeatedly report `repeated finding(s) coalesced inside debounce window` / `repair plan(s) are waiting for judgement`, load `references/selfcheck-alert-noise-governance.md`: keep the selfcheck ledger intact, make live Telegram delivery default-off/explicit-opt-in, batch-limit delivery, treat failed receipts as terminal, ignore sentinel debounce bookkeeping in repeated-finding counts, dry-run close L0 `diagnose.*` repair plans, and verify no live send occurs by default.

When selfcheck is otherwise healthy but warns about handoff backlog, snapshot bloat, or maintenance cron drift, use `references/reversible-handoff-snapshot-gc.md`: dry-run first, archive/move with manifests instead of deleting, prefer deterministic `no_agent=True` cron scripts for routine GC, then rerun the originating selfcheck to prove the warning cleared. Keep this separate from task lifecycle mutation or external dispatch authority.
