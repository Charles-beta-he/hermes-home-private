# Continuation compaction + recurrent task state implementation pattern

Use this when advancing Hermes memory-cache / recurrent-state evolution past design into safe implementation, especially after the user says “全盘推进至需要人工介入”.

## Safe stopping boundary

The safe automated boundary is:

1. Create or update the SSOT/design note.
2. Add deterministic replay fixtures for recurrent-state preference and token-cost rejection.
3. Generate a read-only continuation compaction manifest.
4. Add compact `recurrent_task_state` to continuation resume paths without deleting checkpoint/history state.
5. Verify health/taskpool/ratchet and commit.
6. Stop before mutation when the manifest has `terminal-audit` or ambiguous `stale-recoverable` packets.

Do not archive/delete continuation packets automatically just because a bucket is named `disposable`. `disposable` means “candidate after reference-safety review”, not “safe to delete now”.

## After explicit human approval

If the user explicitly approves crossing the review boundary, keep mutation narrow and auditable:

1. Implement/use a separate apply script; never add mutation to the manifest generator.
2. Consume the previously generated manifest path; do not rescan and invent a fresh decision set inside the apply step.
3. First run `--dry-run` and write an apply report.
4. Only archive active packets that are all of:
   - `bucket == disposable`
   - `source_dir == active`
   - reason includes `task_status:done`
5. Never mutate `live`, `stale-recoverable`, or `terminal-audit` packets in the same pass.
6. Never delete packets in the first approved pass; move to archived only.
7. Regenerate a post-apply manifest and verify active count changed only by the archived count.
8. Run py_compile, health, ratchet, taskpool dashboard, scoped secret scan, and commit.

A good apply report schema should include `mutation_performed`, `archived_count`, `skipped_count`, `blocked_buckets_not_mutated`, and `delete_performed:false`.

## Manifest shape

A useful manifest should be explicitly read-only:

```json
{
  "schema": "hermes_continuation_compaction_manifest_v1",
  "mode": "dry_run_read_only",
  "mutation_performed": false,
  "counts": {
    "live": 0,
    "stale-recoverable": 0,
    "terminal-audit": 0,
    "disposable": 0
  },
  "human_intervention_required": true
}
```

Bucket semantics:

- `live`: recent or currently running/claimed work. Never mutate.
- `stale-recoverable`: blocked/retry/review/pending work that may need resume or targeted review. Do not delete.
- `terminal-audit`: missing task id, missing task note, invalid JSON, or unresolved ownership. Requires human/multimodel audit before mutation.
- `disposable`: points to terminal/done task and can be considered for cleanup only after reference-safety review.

## Recurrent task state schema

For continuation resume, prefer a compact state block over raw full-history prompt dumps:

```json
{
  "schema": "hermes_recurrent_task_state_v1",
  "task_id": "...",
  "attempt": 1,
  "objective": "...",
  "completed_proof_artifacts": [],
  "files_changed": [],
  "current_blocker": "Iteration budget reached",
  "next_bounded_action": "verify current files/state, then continue the smallest unfinished acceptance item",
  "remaining_steps": [],
  "wrong_source_hypotheses": [],
  "partial_tail": "...",
  "policy": "compact_state_is_resume_hint_not_proof; verify files and artifacts before lifecycle advancement",
  "token_estimate": 250,
  "max_chars": 2400
}
```

Critical rule: compact state is a resume hint, not proof. Lifecycle advancement still requires reading/verifying files, artifacts, command output, or task notes.

## Verification bundle

Before reporting completion:

```bash
python3 -m py_compile ~/.hermes/scripts/continuation_compaction_manifest.py ~/.hermes/scripts/task_continuation.py ~/.hermes/scripts/local_brain_memory_replay_gate.py
python3 ~/.hermes/scripts/continuation_compaction_manifest.py --include-archived-sample 0 --out ~/.hermes/state/continuation-compaction-manifest-YYYYMMDD.json --summary
python3 ~/.hermes/scripts/task_continuation.py recurrent-test
python3 ~/.hermes/scripts/local_brain_memory_replay_gate.py --json --out ~/.hermes/state/memory-cache-recurrent-state-gate-YYYYMMDD.json
python3 ~/.hermes/scripts/unified-health-check.py
python3 ~/.hermes/scripts/experience-ratchet-maze.py validate
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --json
```

Also run a scoped secret scan and inspect scoped git status/diff before commit.

## Pitfalls

- Do not treat a video/article title as a factual architecture proof. It can motivate a direction, but local deterministic gates decide implementation.
- Do not make health green by clearing continuation backlog.
- Do not let compact state replace proof artifacts.
- Do not mutate runtime continuation state in the same script that produces the dry-run manifest.
- Do not create a one-off narrow skill for this pattern; keep it under taskpool-control-plane because it governs long-running work, taskpool debt, continuation, and evidence gates.
