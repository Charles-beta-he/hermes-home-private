# Hermes Conversation Workspace OS — Canonical SSOT

Status: implementation-in-progress
Stable project id: `single-session-multitopic-trace`
Display name: `Hermes Conversation Workspace OS`
Created from approved multi-session fusion design: 2026-07-20

## Objective

Make multi-topic and multi-session Hermes work recoverable, mergeable, conflict-safe, and evidence-backed. Chat sessions and tmux are replaceable execution surfaces; project SSOT and source readback own durable truth.

## Success criteria

1. A project can be initialized into a canonical directory layout without overwriting existing files.
2. Direction, task, worker-runtime, and chat-session states remain separate domains.
3. Handoff packets and tmux manifests are schema-validated and reject authority-smuggling or secret-like fields.
4. Active write claims reject overlapping project/direction scopes and expose stale/orphaned runtime drift.
5. A read-only doctor detects malformed JSON/JSONL, duplicate claims, expired leases, missing worktrees/evidence, tmux drift, and `done` without evidence.
6. A tmux planner emits commands or an argv plan but does not execute tmux, workers, lifecycle mutation, or external actions by default.
7. A machine restart or missing tmux session can be recovered from SSOT artifacts without trusting pane history.
8. Existing single-session multitopic trace remains an additive capability under the broader workspace OS; the stable project id is preserved.
9. Portfolio profile/registry remain structurally and semantically truthful.

## Non-goals and closed authority gates

- No Hermes core/model-tool addition.
- No external dispatch, gateway send, deploy, push, credential entry, destructive cleanup, broad fan-out, production write, or payment action.
- No automatic taskpool/Mission lifecycle mutation.
- No worker may promote canonical `done`.
- No tmux pane, terminal output, model verdict, or chat summary is completion authority.
- No automatic replay of side-effecting commands during tmux recovery.
- No tmux-resurrect dependency as the canonical recovery path.

## Source-of-truth hierarchy

1. Current source code/API/real runtime readback.
2. This project SSOT: specs, append-only events, evidence pointers, decisions and claims.
3. Generated snapshots/progress projections.
4. Taskpool/Mission/dashboard/chat/tmux projections.

## Architecture decision

Promote the existing stable project `single-session-multitopic-trace` into a platform-shaped `Hermes Conversation Workspace OS` instead of creating a duplicate project. The original single-session trace/query capability becomes one component; multi-session fusion, handoff, claim lease and tmux workspace become additional components.

## Canonical state domains

- Direction maturity: `proposal`, `contract-ready`, `in-progress`, `validated`, `promoted`, `released`, `superseded`.
- Task lifecycle: `backlog`, `ready`, `claimed`, `running`, `review`, `blocked`, `done`, `cancelled`.
- Worker runtime: `starting`, `running`, `stopping`, `exited`, `failed`, `killed`, `detached`, `recovered`.
- Chat session: `active`, `handoff-ready`, `archived`, `stale`.

No adapter may collapse these domains into one status field.

## Concurrency contract

- Event append uses a dedicated advisory file lock plus `flush` and `fsync`.
- Claim, handoff and evidence read/check/write transactions share a separate cross-process state lock.
- Conflict and idempotency checks execute while that state lock is held; concurrent sessions cannot both pass a stale pre-write check.

## Tmux role

- One durable project may project to one tmux session named `hx-<project-id>`.
- One active direction projects to one tmux window.
- One code-writing claim owns one branch/worktree.
- Tmux is an ephemeral interactive process workspace, never a canonical ledger.
- Runtime recovery rebuilds safe layout only; it does not replay arbitrary commands.

## Filesystem contract

```text
00-spec/       canonical spec and decisions
01-directions/ direction cards
02-ledger/     append-only events plus generated snapshot
03-evidence/   evidence index and artifact pointers
04-handoffs/   session/worker handoff packets
05-runtime/    claims, worktrees, tmux manifest and receipts
06-status/     doctor reports and bounded projections
scripts/       local-only CLI implementation
tests/         deterministic temporary-home verification
```

## Risk and path selection

Selected path: local edge capability under the existing project profile, implemented as Python stdlib CLI plus schemas/tests. This is preferred over Hermes core changes, tmux plugins, or a new project because it is reversible, profile-scoped, testable in temporary directories, and preserves the narrow-waist architecture.

## Acceptance evidence

- Python syntax/compile output.
- Focused deterministic unit/integration tests in temporary directories.
- Real tmux version/list-session readback, with no created session required for default tests.
- CLI `init`, `doctor`, `tmux-plan` and negative-case output.
- Portfolio doctor and strict verify readback after metadata update.
- Scoped Git diff/status readback; no push.

## Converge boundaries

A local validated claim may cover schema, CLI, temporary-home tests, tmux planning and read-only doctor behavior. It must not be expanded to autonomous worker execution, real external adapter writes, global certification, or production readiness without separate evidence and authority.
