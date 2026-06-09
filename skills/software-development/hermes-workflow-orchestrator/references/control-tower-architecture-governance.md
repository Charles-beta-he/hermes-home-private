# Control Tower architecture governance pattern

Use this reference when a user asks to consolidate Hermes control surfaces, design visual workflow operations, or "push forward until human intervention" for agent workflow/control-plane work.

## Durable product shape

Treat the target as an AgentOps control plane, not a decorative workflow graph:

- Event-driven by default; cron is watchdog/recovery/report fallback only.
- Use **one canonical workflow fact source**: the Control Tower Ledger.
- Taskpool, Kanban, dashboard, CLI views, worker queues, event streams, evidence pages, gateway views, and cron watchdog pages are adapters or projections over that ledger, not competing sources of truth.
- Evidence maturity is still central, but Evidence Spine is a ledger-backed projection/authority view, not an independent SSOT.
- Policy/human gates are first-class workflow primitives.
- Worker runtime is execution plane; workers submit results/evidence events but cannot directly mark tasks done.
- Dashboard/CLI/Kanban/workflow map are projections and controlled command surfaces, not separate truth stores.

## Recommended architecture contract

Before code/schema/UI work, create or identify one SSOT architecture artifact (usually an ADR) covering:

1. Control plane vs execution plane boundaries.
2. Single canonical fact source: one ledger owns durable workflow facts; task state, causality, and closeout are projections/views, not separate SSOTs.
3. Command/event/projection model.
4. Event-driven triggers and cron fallback limits.
5. Evidence maturity model: advisory -> observed -> verified -> certified -> release_confirmed.
6. Human gate and action risk levels L0-L4.
7. Worker lease/heartbeat/idempotency contract.
8. Dashboard modules: Overview, Workflow Map, Taskpool Health, Kanban, Event Stream, Worker Runtime, Evidence Spine, Human Inbox, Policy Gates, Gateway, Cron Watchdogs, Skills/Memory Governance.
9. Non-goals and invariants.
10. Explicit human decisions required before implementation.

## "全盘推进至需要人工介入" workflow

When the user approves a strategic direction and asks to push forward until human intervention:

1. Load Hermes/workflow/ADR skills as appropriate.
2. Inspect current repo/docs/plugin surfaces enough to avoid writing into the wrong place.
3. Land durable docs first:
   - ADR / architecture SSOT.
   - Implementation packet / backlog with phases and acceptance criteria.
4. Verify by reading back, `git diff --check`, and scoped status/diff inspection.
5. If this is Hermes self-work and repo policy requires it, make a scoped commit containing only the current docs/change.
6. Stop before code/schema/UI/lifecycle mutations if unresolved decisions affect blast radius.
7. Report the exact files, verification commands, commit hash, unrelated pre-existing dirty files, and the decisions needed from the human.

## Human-decision boundary examples

Stop and ask before implementation when these are undecided:

- Primary fact source: choose one canonical Control Tower Ledger; existing stores are adapters/projections during migration, not competing SSOTs.
- UI host: built-in dashboard page vs plugin vs private overlay first.
- Integration depth: read-only aggregation vs command write path vs lifecycle DB migration.
- Approval UX: dashboard-only vs gateway-first plus dashboard mirror vs both with approval tokens.
- Initial action permissions: read-only only, L1 maintenance, selected L2, or L3 project-policy-gated worker starts.
- External framework stance: Hermes-native now vs optional future Temporal/OpenTelemetry hooks.
- Private-first vs upstream-first landing.

## Phase-1 implementation pattern: read-only Control Tower slice

Scope/applicability: use this only for Hermes Agent self-work or a project that explicitly has an existing dashboard plugin host, ledger home, and adapter/projection architecture. Anti-condition: do not apply these file paths, plugin names, or commands to unrelated products; translate the pattern to that product's own extension host and test harness.

When the single-ledger SSOT decision is resolved and the user approves proceeding, the safest first code slice is:

1. Add a small control-plane module that initializes the Control Tower Ledger at the approved ledger path.
2. Create schema-versioned tables for commands/events/tasks/workflow runs/steps/worker runs/evidence/policy decisions/human approvals/adapter observations/projection checkpoints.
3. Expose a read-only snapshot shape with `schema_version`, `generated_at`, `ledger`, `ui_host`, `adapters`, `taskpool_health`, `next_dispatchable`, `top_blockers`, `worker_runs`, `cron_watchdogs`, `evidence_summary`, and `adapter_conflicts`.
4. Treat existing boards/task pools/brain stores as projection adapters. If observing existing board tasks, write deduped adapter observations into the ledger and emit an observation event; do **not** mutate board lifecycle state.
5. Prefer the existing dashboard plugin host as UI host when available: manifest + backend plugin API + static assets, mounted under the plugin API prefix and tab path. This reuses the established plugin host without making Dashboard the fact source.
6. Keep Phase 1 strictly L0/read-only. Stop before any action registry, lease release, retry, evidence attach, worker claim/handoff, approval, or write-through adapter.

Focused verification for this slice:

```bash
python -m pytest -o addopts='' -q <snapshot-tests> <dashboard-plugin-tests>
python -m py_compile <control-plane-module> <plugin-api> <snapshot-tests> <plugin-tests>
git diff --check -- <control-plane-module> <plugin-dir> <tests> <implementation-doc>
```

Smoke-check the snapshot with an isolated home/profile and verify it reports the canonical ledger, the selected UI host, and adapter roles as non-canonical projections.

## Anti-patterns

- Building a graph UI before defining state/event/evidence contracts.
- Letting the dashboard execute arbitrary shell.
- Letting worker completion directly close tasks.
- Treating model review as real verification without evidence.
- Making cron the primary workflow trigger.
- Writing WIP task progress into memory.
- Creating parallel state in UI, gateway, taskpool, and evidence stores.
- Splitting durable truth into task-state, causality, and closeout SSOTs instead of a single ledger with projections.
- Silently reconciling adapter mismatches with last-write-wins instead of explicit conflict facts/events.
