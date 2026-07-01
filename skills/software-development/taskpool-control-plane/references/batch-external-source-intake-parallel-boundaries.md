# Batch external-source intake and parallel boundary hygiene

Use this when creating many taskpool items from one external-source backfill, feed digest, social/media intake, or repo-candidate list.

## Durable pitfall

If every task receives the same free-text `parallel_boundary`, `brain_task_orchestrator.py selfcheck --json` may report a `parallel_boundary_conflict` warning even when the work is conceptually independent. The boundary string is part of the dispatch grouping signal; identical strings can be interpreted as the same contention boundary.

## Preferred pattern

For a batch of independent evidence/advisory tasks:

- Keep shared evidence in one artifact, e.g. `artifact:/.../producthunt-unresolved-backfill-YYYY-MM-DD.md`.
- Give each task a unique boundary key that includes the task/source slug:

```text
--parallel-boundary 'ph-backfill-intake:<task-id-or-source-slug>; independent repo-read/docs-review only; no shared code writes'
```

- Keep `lane=advisory`, `workflow_stage=evidence`, and `completion_boundary=taskpool_candidate` unless the user explicitly asks for implementation work.
- Acceptance should require: repo/source readback, capability mapping, risk/low-coupling check, and prune-or-promote decision.
- Red line should explicitly forbid production code mutation, vendor-copying, and lifecycle/proof gate bypass from the source-intake task alone.

## Verification

After batch add or repair:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
```

Claim completion only when:

- expected task count is present;
- statuses/priorities match the intake policy;
- `selfcheck.status == PASS`;
- `boundary.invalid_count == 0`;
- `boundary.warnings == 0` for newly introduced batch-boundary issues.

Existing semantic-control-plane warnings from unrelated project profiles should be reported as unrelated, not treated as proof that the batch failed.
