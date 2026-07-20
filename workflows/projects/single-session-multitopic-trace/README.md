# Conversation Workspace OS operator guide

Canonical SSOT: `00-spec/conversation-workspace-os-ssot.md`

## Responsibility split

- SSOT and source readback own durable truth.
- Hermes chat sessions submit handoffs and evidence pointers.
- Claims serialize project-scoped write ownership.
- Git worktrees isolate code-writing lanes.
- Tmux is an ephemeral layout/process projection.
- Taskpool/Mission integration remains closed in this local slice.

## Initialize another project workspace

```bash
python3 scripts/conversation_workspace.py init \
  --root /absolute/path/to/project-ssot \
  --project-id project-id \
  --display-name 'Display Name'
```

Initialization is non-overwriting and serialized by the project-local cross-process state lock. Existing canonical files are preserved; re-initialization with a different project ID fails closed. Claim, handoff and evidence mutations use the same state lock; event append uses a separate append lock with `fsync`. The complete event history and evidence index are validated before dependent canonical mutation, so malformed history fails before any partial projection write.

## Acquire and release a write claim

```bash
python3 scripts/conversation_workspace.py claim-acquire \
  --root /absolute/path/to/project-ssot \
  --claim-id claim-001 \
  --direction-id frontend \
  --owner-session session-id \
  --mode write \
  --scope 'src/frontend/**' \
  --worktree /absolute/path/to/existing/worktree \
  --ttl-minutes 240

python3 scripts/conversation_workspace.py claim-release \
  --root /absolute/path/to/project-ssot \
  --claim-id claim-001
```

A write claim requires an existing worktree. Scope patterns are normalized for Unicode NFC, case, repeated separators and internal `.` aliases before conflict checks. Active write claims may not own the same direction or conservatively overlapping glob/static path prefixes. Claim acquire/release prevalidate the tmux projection before changing canonical claim state. Releasing an elapsed lease reconciles it to `expired`, emits `claim.expired`, and removes its tmux projection without fabricating `released_at`.

## Add a handoff

```bash
python3 scripts/conversation_workspace.py handoff-add \
  --root /absolute/path/to/project-ssot \
  --file /absolute/path/to/handoff.json
```

Use `00-spec/templates/handoff.template.json`. Intake uses a strict field allowlist and validates every required/optional field type. Secret-like, canonical authority/lifecycle flags and arbitrary command fields are rejected after NFKC/camelCase/separator normalization, so aliases such as `clientSecret`, `apiToken`, `externalDispatchRequested`, `taskStatus`, `execute_commands` and `mark-done` fail closed. Every completion evidence ID must resolve in the canonical evidence index and its artifact must still exist with the declared SHA-256 before dependent mutation.

## Add immutable evidence

```bash
python3 scripts/conversation_workspace.py evidence-add \
  --root /absolute/path/to/project-ssot \
  --evidence-id E-001 \
  --kind test \
  --path /absolute/path/to/test.log \
  --summary 'Focused tests passed' \
  --claim-ref local-cli-contract
```

The CLI records SHA-256. Later doctor runs fail if the artifact changes or disappears.

## Read-only doctor

```bash
python3 scripts/conversation_workspace.py doctor \
  --root /absolute/path/to/project-ssot \
  --inspect-tmux
```

`--inspect-tmux` lists sessions/windows only. It never creates, attaches, stops, or mutates tmux.

Optional `--out` writes only beneath a real, non-symlinked `<root>/06-status`; absolute, relative, nested-symlink and status-root-symlink escapes are rejected.

## Tmux recovery plan and reconciliation

```bash
python3 scripts/conversation_workspace.py tmux-plan \
  --root /absolute/path/to/project-ssot

python3 scripts/conversation_workspace.py tmux-reconcile \
  --root /absolute/path/to/project-ssot
```

`tmux-plan` returns the complete desired layout. `tmux-reconcile` compares that layout with the live tmux server and returns only additive recovery commands when possible. Both are plan-only: they never execute commands, replay workers, or remove extra windows.

## Recovery sequence

1. Read project profile and canonical SSOT.
2. Run doctor.
3. Inspect active claims, worktrees and evidence.
4. Resolve expired/orphaned claims before any new writer.
5. Generate the tmux plan.
6. Recreate layout only after reviewing every argv entry.
7. Read the latest valid handoff and revalidate against current source.
8. Resume from `next_safe_step`.

## Hard boundaries

Do not treat tmux existence, pane output, chat summaries, worker reports, or model votes as completion evidence. Unicode NFKC and key-alias normalization precede secret/authority checks. Public events use exact type-specific payload schemas. Canonical events, evidence, claims, handoffs and tmux manifests use strict schemas; malformed history/projections fail before dependent mutation. Released claim timestamps must remain inside the original lease interval. Do not put secrets, credentials, raw tokens, arbitrary commands, external-write requests, or `mark_done` fields into handoffs/events/manifests.
