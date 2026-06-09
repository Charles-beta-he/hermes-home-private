# Hermes self-governance scoped commit pattern

Use this reference when a Spec-Stateful SDD run changes Hermes itself: skills, memory, docs, health artifacts, logs, taskpool files, or diagnostics.

## Learning

A successful self-governance run often creates two different kinds of change:

1. Governed durable artifacts
   - skills and references
   - private SSOT docs / ADR-like notes
   - memory compaction edits
   - project/profile config changes explicitly in scope

2. Runtime or recovery artifacts
   - rotated logs
   - compressed log backups
   - health-history append-only files
   - taskpool/kanban/cron runtime state
   - generated caches and lockfiles

Do not commit these as one blob. Stage and commit only the governed durable artifacts unless the user explicitly asked to version runtime state.

## Recommended sequence

1. Before self-modifying work, identify or create the SSOT artifact.
2. Make the skill/docs/memory changes.
3. Run diagnostics or other relevant health checks.
4. If logs/task files are safely compacted, keep a local backup for recovery.
5. Inspect scoped git status for the exact intended paths.
6. Stage only the durable governed files.
7. Commit with a message describing the governance change.
8. Report remaining runtime artifacts as intentionally uncommitted.

## Pitfall

`git status` under `~/.hermes` can contain large unrelated dirty state. Never infer that all dirty files belong to the current task. Use path-scoped status/diff and path-scoped staging.

## Example commit boundary

Commit:
- `docs/private/<ssot>.md`
- `skills/<class-skill>/SKILL.md`
- `skills/<class-skill>/references/<detail>.md`
- `memories/MEMORY.md` when memory compaction was explicitly part of the work

Do not commit by default:
- `logs/*.jsonl`
- `backups/log-rotation-*`
- generated caches
- unrelated notes/taskpool files touched by background hooks
