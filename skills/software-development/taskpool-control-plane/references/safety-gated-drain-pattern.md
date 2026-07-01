# Safety-gated drain pattern

Scope: domain-level procedure for local queue/control-plane drains. This note intentionally contains no task IDs, project names, paths, branches, or session outcomes.

Applicability: use when an operator authorizes continued drain work but the live queue still contains blocked, retry, claimed, running, or pending items and existing lifecycle/proof gates must remain authoritative.

Procedure:
1. Read the live health report and queue-state summary before acting.
2. If an autonomous reviewer, multimodel lane, or worker consumer is disabled or stopped by a human safety gate, do not bypass it. Treat the skip as a boundary and choose a lower-risk lifecycle operation.
3. Prefer resolver/reconcile/review operations that move work to retry or pending over any action that marks work complete.
4. If a claimed item cannot be consumed, release or verify release to retry/pending so it does not remain claimed without progress.
5. Finish with fresh health, proof, watcher/report, and scoped version-control evidence.

Pitfalls:
- A safety skip can be successful progress when it prevents stale claims.
- Health PASS does not mean the queue is drained; report remaining retry/running/pending/proof-debt counts.
- Never clear proof debt or complete work without evidence linked to the lifecycle gate.

Anti-conditions: do not use this pattern for destructive operations, external dispatch, publish/deploy/push, credentials, payments, or broad fan-out.
