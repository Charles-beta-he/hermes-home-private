---
name: process-lifecycle-control-plane
description: Use when designing, auditing, or changing Hermes-managed long-running processes, background tasks, gateways, cron workers, adapters, or any start/stop/restart/status/log control surface.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [processes, lifecycle, control-plane, hermes, operations]
    related_skills: [hermes-agent, systematic-debugging, test-driven-development, requesting-code-review]
---

# Process Lifecycle Control Plane

## Overview

Use this skill to turn external process-manager lessons (notably Overmind-style Procfile supervision) into Hermes-safe implementation and audit steps.

The transferable pattern is not tmux. The durable pattern is an operator control plane: explicit lifecycle state, bounded shutdown escalation, identity-preserving output, scoped runtime artifacts, profile-aware environment resolution, and verifiable status/log surfaces.

## When to Use

- Changing `terminal(background=true)`, `process(...)`, taskpool workers, gateway bridges, cron workers, browser harness servers, SSE/local-device adapters, or similar long-lived processes.
- Auditing whether a daemon/worker can be safely stopped, restarted, observed, and recovered after Hermes/gateway restart.
- Adding notification, fan-in logging, PID/session recovery, profile/env propagation, or generated runtime artifact cleanup.
- Don't use for: one-shot foreground commands with no lifecycle, pure UI changes, or ordinary business logic where no process boundary is involved.

## Required Audit Order

1. Identify the instance boundary.
   - Every generated runtime artifact must include a run/session/process ID.
   - Cleanup must delete only that instance boundary, never a broad shared directory.

2. Make lifecycle state explicit.
   - Prefer state fields over log inference: `starting`, `running`, `stopping`, `exited`, `killed`, `failed`, `detached`, `recovered`.
   - Include policy bits when relevant: `can_die`, `auto_restart`, `notify_on_complete`, `watch_patterns`, `grace_timeout_s`.

3. Implement shutdown as a ladder.
   - Polite stop/TERM first.
   - Bounded wait.
   - Force kill for survivors.
   - Cleanup and checkpoint update.
   - Return the observed exit state, not a guessed success code.

4. Preserve identity in output fan-in.
   - Prefix or structure output by `session_id`, process name, command, event type, and exit code.
   - Keep raw/paginated logs available even when summaries are compact.

5. Use canonical env/profile resolution.
   - Prefer Hermes config/profile helpers over parallel env loaders.
   - For cron/profile jobs, snapshot/restore process-global env and serialize jobs that mutate global runtime state.

6. Verify command-center semantics.
   - At minimum: `status`, `stop/kill`, `logs`, and `wait/poll` should behave consistently.
   - For real daemons: add readiness/health proof, not just PID existence.

## TDD Requirements

Before production code changes:

1. Add a failing test for the lifecycle transition or control-plane contract.
2. Verify RED with the smallest targeted pytest command.
3. Implement the narrowest code change.
4. Verify GREEN with the targeted test and nearby suite.
5. Run static/syntax checks and scoped diff review before commit.

Good test targets:
- TERM-ignoring child escalates to kill after the grace timeout.
- `poll`/`wait` reconcile real process exit before reporting status.
- `kill` returns the observed exit code or a documented unavailable state.
- Notification output includes process identity and event type.
- Checkpoint recovery distinguishes host PIDs from sandbox PIDs.
- Profile/workdir env is restored after the process/job finishes.

## Workflow Ledger / UI Host Pattern

Scope: apply this pattern when a lifecycle/control-plane feature spans multiple operational surfaces (for example a dashboard, task board, worker runtime, cron/watchdog, gateway ingress, evidence view, or orchestration adapter). Do not apply it to ordinary single-component UI or business-logic changes.

When multiple surfaces could each become a source of truth, choose one canonical append-only ledger first. Treat UI hosts, task boards, queues, event streams, and evidence panes as adapters or projections unless they are explicitly migrated behind a command gateway.

Safe rollout order:

1. Create the canonical ledger schema and metadata.
2. Add a read-only snapshot API.
3. Mount UI in an existing plugin/extension host as a projection/control surface, not a fact source.
4. Record adapter observations with payload-hash or idempotency dedupe; do not mutate adapter lifecycle state in the same slice.
5. Add a proposal-only command registry before any executor. Proposed commands must be durable, audited, idempotent, and explicitly marked as not executed.
6. Route higher-risk proposed commands into a human approval inbox before implementing approval decisions or execution.
7. For lifecycle-control surfaces that already have proposed commands and human approval requests, add approval decisions as a separate non-executing lifecycle slice: decisions are single-use, same-decision retries are idempotent, conflicting second decisions fail closed, and decision APIs return explicit `not_executed` state.
8. For lifecycle-control surfaces that need readiness visualization, add a canonical-store-derived workflow map/readiness projection before any executor. Validate node IDs/dependencies/cycles and surface executor eligibility as an explicit blocked gate.
9. When the user broadly authorizes moving past a proposal-only workflow packet, consume only the smallest already-described local boundary first: persist a local registry/template or record a local harness receipt, prove readback, and keep real workers, scheduler, lifecycle writes, external adapters, and publish/deploy/destructive actions closed unless they were separately named with exact target/budget/tool/readback constraints.
10. Stop for policy review before adding any executor, write-through adapter, or lifecycle-affecting action.

Scope and anti-condition: steps 7-8 apply only to multi-surface lifecycle/control-plane systems that need human gates or readiness graphs. Do not add them to single-view read-only dashboards, ordinary business CRUD, or systems that already have a mature policy-gated executor and canonical workflow store.

Verification additions (see `references/proposal-only-command-registry.md` and `references/approval-workflow-map-boundary.md` for reusable checklists):

- Assert proposal actions create command rows and proposal audit events.
- Assert idempotency keys do not duplicate commands/events.
- Assert high-risk proposals create approval-request records and approval-requested events.
- Assert all proposal responses include an explicit `not_executed`/equivalent execution state.

Anti-conditions: if there is already a mature canonical command/event store and policy-gated executor, integrate with it instead of creating another ledger. If the requested change is purely presentational and reads one existing API, do not introduce a ledger.

## Agent/Worker Authority Ladder

Scope: use this pattern for lifecycle-control systems where model, worker, or external-agent output may be promoted toward canonical lifecycle state and later adapter write-through. Applicability requires a canonical ledger/event stream, untrusted or semi-trusted worker proposals, and a risk that a proposed status change could mutate another system. Anti-conditions: do not add this ladder to ordinary CRUD, single-view read-only dashboards, or systems that already have a mature policy-gated command/event store; integrate with the existing store instead.

Safe promotion order:

1. Record runtime start in the ledger only.
2. Accept read-only execution results before allowing any external process to act.
3. Probe external agents/processes with version/health commands before sending task prompts.
4. Allow prompt dry-runs only with tools/write disabled.
5. Pass read-only context as artifact URI/hash rather than inline mutable authority.
6. Accept worker output first as an evidence-backed proposal artifact, not as fact.
7. Promote proposals through certification/review with quorum, truth gate, and evidence binding.
8. Record elevated authorization with actor, decision, TTL, target status, and artifact digest binding; still do not mutate facts.
9. Mutate canonical lifecycle facts only in a separate ledger-local slice that consumes an unexpired authorization.
10. Project adapter write intent only after the canonical fact exists; require adapter allowlist, target reference, readiness check, readback plan, rollback plan, and evidence.
11. Project external write authorization only against an unchanged intent and unexpired elevated approval; still record `write_executed=false`.
12. Add a narrow executor last: consume one authorization, perform one adapter operation, record attempt, read back remote state, and record verified/mismatch. Keep rollback execution as a later, separate slice.

Verification additions for each rung: add RED/GREEN tests for accept and reject paths, provide a CLI/command smoke that walks the full ladder to the new rung, record explicit booleans such as `write_executed=false`, and update the canonical design/SSOT doc in the same scoped commit. See `references/event-governed-agent-authority-ladder.md` for the reusable ladder, local-file adapter harness shape, rejection coverage, and boundary-reporting language. For the hardened first-executor implementation checklist (exact authorization tuple binding, direct-child path safety, descriptor-relative I/O, idempotency, receipt rollback, and adversarial review), see `references/local-file-harness-executor-hardening.md`.

Pitfalls: do not treat certification as fact; do not let intent imply execution; do not accept authority keys from worker/model payloads; do not combine first write-through, read-back verification, and rollback execution into one unreviewable slice. Treat local-file harness write-through as real state mutation but not as real taskpool/Kanban/Lark/Telegram write-through.

For ordered Agent OS / agent-control-plane boundary breakthroughs after broad project-level authorization, advance one rung at a time and certify each with exact target, receipt, readback, independent review, and multi-model evidence before continuing. Use `references/agent-os-boundary-breakthrough-ladder.md` for the reusable rung order: advisory → route preflight → review preflight → local harness → local scheduler heartbeat → local taskpool/Kanban lifecycle → exact external dispatch → stop at publish/deploy/push or destructive DecisionPacket.

## Common Pitfalls

1. Claiming success after sending TERM without waiting for the process to exit.
2. Treating PID existence as health; readiness must be a separate signal.
3. Dropping process identity when fan-in output is summarized.
4. Using shell-level `nohup`/`&` hacks instead of the managed background registry when Hermes needs to track lifecycle.
5. Letting cleanup operate on shared temp/cache directories instead of an instance-specific path.
6. Copying Overmind's tmux dependency or test-coverage gap instead of the process-control semantics.
7. Mutating process-global env in parallel jobs without snapshot/restore and serialization.

## macOS LaunchAgent local-console pattern

When a Hermes-adjacent localhost console should “follow Hermes” at login, use a LaunchAgent wrapper rather than relying on a foreground `pnpm desktop` process. Keep the service helper small and testable: generate the plist, parse `launchctl list`, expose `start/status/stop`, and verify real HTTP readiness. Never persist per-session action tokens in the plist; generate them inside the supervised runner and verify the public snapshot remains no-token/unarmed by default.

See `references/macos-launchagent-local-console.md` for the detailed checklist, plist contract tests, and common pitfalls.

## Verification Checklist

- [ ] Instance/session/run ID is visible in state, logs, and artifacts.
- [ ] Stop path is TERM -> bounded wait -> KILL for survivors.
- [ ] Status is based on actual process state plus readiness when applicable.
- [ ] Output fan-in preserves process identity and raw log access.
- [ ] Env/profile resolution uses canonical Hermes helpers or documents deliberate isolation.
- [ ] Resident macOS services keep secrets out of LaunchAgent plists and prove UI/API readiness with real probes.
- [ ] Tests cover timeout/escalation and not only happy-path exit.
- [ ] Scoped diff excludes unrelated runtime/cache/doc churn.
