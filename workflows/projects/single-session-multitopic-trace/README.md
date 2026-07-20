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

Initialization is non-overwriting. Existing canonical files are preserved. Mutating claim, handoff and evidence commands are serialized by a project-local cross-process state lock; event append uses a separate append lock with `fsync`.

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

A write claim requires an existing worktree. Active write claims may not own the same direction or overlapping static path prefixes.

## Add a handoff

```bash
python3 scripts/conversation_workspace.py handoff-add \
  --root /absolute/path/to/project-ssot \
  --file /absolute/path/to/handoff.json
```

Use `00-spec/templates/handoff.template.json`. Secret-like and authority-smuggling fields are rejected.

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

Do not treat tmux existence, pane output, chat summaries, worker reports, or model votes as completion evidence. Do not put secrets, credentials, raw tokens, arbitrary commands, external-write requests, or `mark_done` fields into handoffs/events/manifests.
