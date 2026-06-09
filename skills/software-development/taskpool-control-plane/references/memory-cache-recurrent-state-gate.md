# Memory-cache / recurrent task state / continuation compaction gate

Use this reference when a Hermes/taskpool evolution request is inspired by long-context, memory-cache, RNN/recurrent-state, or similar external architecture signals.

## Durable lesson

Treat external videos/articles as direction signals until grounded by deterministic local proof. Do not turn a title like “memory-cache RNN will end Transformer” into a runtime claim. For Hermes, the useful class-level pattern is:

- Do not solve long-running agent work by injecting full history into every prompt.
- Split long-term capability into:
  - `working_context`: current-turn essentials only.
  - `recurrent_task_state`: objective, completed proof artifacts, current blocker, next bounded action, and wrong-source hypotheses not to repeat.
  - `memory_cache`: rebuildable retrieval/cache layer, never SSOT.
  - `proof_artifacts`: structured evidence, not natural-language summaries.
  - `continuation_packet`: budget-exhaustion resume package that must be classified before cleanup.

## Low-risk implementation sequence

1. Write a small SSOT/design note first, with explicit source/evidence boundary.
2. Add deterministic replay fixtures before runtime semantics change.
3. Add token-cost prefilter cases that accept compact recurrent state and reject raw-history/full-context dumps.
4. Compile the design into a taskpool task with acceptance evidence and red lines.
5. Add a read-only continuation compaction manifest before any cleanup. The manifest must emit `mode: dry_run_read_only` and `mutation_performed: false`.
6. Add compact `recurrent_task_state` to continuation resume paths only as a resume hint, never as proof or lifecycle evidence.
7. Stop at human/multimodel review when the manifest contains `terminal-audit` or ambiguous `stale-recoverable` packets; do not cross into archive/delete mutation automatically.

For the concrete implementation scaffold, manifest schema, recurrent-state schema, and verification bundle, see `references/continuation-compaction-recurrent-state-implementation.md`.

## Replay gate fixture classes to include

A useful minimum fixture suite covers:

- evidence-backed positive recall
- red-line/noise rejection
- temporal drift rejection
- external-memory marketing claim rejection
- recurrent task state compaction preference
- token-cost prefilter rejection

Gate output should include accepted/rejected evidence decisions and token estimates so reviewers can see why compact state won over raw history.

## Continuation compaction boundary

Do not batch-delete active continuation packets. First produce a no-mutation dry-run manifest with buckets:

- live
- stale-recoverable
- terminal-audit
- disposable

Deletion/archive is only safe after reference-safety review. Count reduction alone is not success; prove no live work was lost.

## Red lines

- No “full history always” prompt strategy.
- No automatic clearing of continuation backlog to make health green.
- No lowering proof/lifecycle/multimodel gates.
- No treating retrieval hit as usable memory without staleness/proof/red-line checks.
- No marketing-only adoption of external memory systems.
