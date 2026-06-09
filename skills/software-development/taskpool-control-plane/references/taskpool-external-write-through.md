# Taskpool external write-through safety pattern

Use this when extending Hermes Control Tower or another ledger/control-plane path from projection-only state into a real taskpool/brain-note mutation.

## Scope that proved safe

For agent/control-plane write-through in general, use the staged chain in `references/event-governed-agent-write-through-boundaries.md`: proposal artifact → certification → elevated done authorization → ledger-local canonical fact → adapter write intent → adapter write authorization → one narrow executor with read-back.

For a narrow closeout write-through, keep the mutation small and digest-bound:

- adapter is explicitly allowlisted (`taskpool`, not a dynamic arbitrary adapter).
- operation is explicitly allowlisted (`closeout`).
- an approved external-write preflight must be consumed by exact `command_execution_digest`.
- before mutation, re-read and verify every freshness boundary: evidence gate, closeout authorization, external write intent/review/authorization, command payload hash, and digest-bound columns such as `adapter_name`, `external_ref`, `operation`, and `mutation_digest`.
- taskpool write changes only the frontmatter `status` field and appends an audit marker; it must not rewrite the full task body or invent lifecycle proof.
- rollback stores the pre-write status in the write-run rollback snapshot and restores only that status after a matching digest-bound rollback request.
- conflicting-evidence override remains a separate feature; enabling write-through must not imply override.

## Path safety checklist for taskpool note writes

A slug check alone is insufficient. Before writing `05-实践与项目/tasks/{external_ref}.md`:

1. Reject `external_ref` when empty, `.`/`..`, containing `/`, or ending in `.md`.
2. Construct the configured path under the configured vault, but do not trust ancestor directories.
3. Reject symlinks in the configured vault/task path chain, especially:
   - configured vault directory;
   - `05-实践与项目` directory;
   - `tasks` directory.
4. Reject the final task note if it is a symlink.
5. Require `path.parent` to equal the configured tasks directory before resolving.
6. Resolve the file and require `resolved.parent` to equal the resolved configured tasks directory.
7. Require the resolved target to be a regular file.

Pitfall found in review: checking only `path.is_symlink()` catches a symlinked task note but misses a symlinked `tasks/` ancestor. Comparing `path.resolve().parent` to `_taskpool_tasks_dir().resolve()` also misses this, because both sides resolve outside the vault together.

## Kanban DB closeout variant

When the authorized adapter is `kanban`, keep it as narrow as the taskpool note variant:

- require the same ledger-bound write authorization and unchanged adapter/ref/status/digest fields;
- reject symlinked DB paths and missing/unexpected schema before opening write mode;
- require `tasks` table and exactly one target row;
- use parameterized SQL only (`UPDATE tasks SET status=? WHERE id=?`), never interpolated SQL;
- mutate only `tasks.status` to `done`, no schema/title/body/metadata changes;
- read back `SELECT status FROM tasks WHERE id=?` before appending `kanban_db_write_verified`;
- make replay idempotent by returning the existing verified event for the same authorization/intent/target tuple.

## Tests to add

At minimum, cover these fail-closed cases before committing:

- RED test proves taskpool adapter is initially disabled or unsupported before the slice is enabled.
- happy path: `review -> done` with write run/event/adapter observation and rollback snapshot.
- rollback path: `review -> done -> review`, matching command digest, one rollback run.
- idempotency: rerunning the same preflight returns the existing write run without a second note mutation or extra observation.
- digest/column drift: mutate `adapter_name`, `external_ref`, or `mutation_digest` after preflight and verify mutation fails before any note changes.
- unsupported adapter still fails closed after taskpool is enabled (use `unknown`, not `taskpool`).
- final task-note symlink escape fails and the outside target remains unchanged.
- ancestor directory symlink escape (`tasks -> outside`) fails and the outside target remains unchanged.
- rollback target/current-state drift fails closed when current status is no longer the expected post-write state.

## Verification sequence

Use the normal pre-commit pipeline plus a smoke that exercises the actual ledger chain:

1. focused tests for the Control Tower snapshot and dashboard plugin.
2. syntax checks (`py_compile`, `node --check`) and `git diff --check`.
3. coverage over the changed control-plane/API files with the established fail-under threshold.
4. taskpool smoke in a temporary `HERMES_HOME` and temporary brain vault: create a real task note, run evidence -> closeout auth -> external write intent/review/auth/preflight -> write -> rollback, then assert note status and ledger counts.
5. static scan for secrets/shell/eval/deserialization/new interpolated SQL in the diff.
6. independent pre-commit review focused on path escape, digest binding, rollback/idempotency, and overclaiming in docs/UI.

## Documentation/UI wording

When a narrow taskpool write-through is enabled, docs and dashboard copy should say exactly that: `Kanban/taskpool closeout write-through plus digest-bound rollback/reopen`. Do not claim broad adapter operations, arbitrary taskpool lifecycle mutation, or conflicting-evidence override.
