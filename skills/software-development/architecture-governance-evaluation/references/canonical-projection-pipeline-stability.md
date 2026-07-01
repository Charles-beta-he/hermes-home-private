# Canonical Projection Pipeline Stability Pattern

Use when designing a mobile/PWA/local-assistant projection of a larger agent brain, especially when the edge app needs offline read/query capability but must not become a fact source.

## Core pattern

1. Keep a single durable authority surface:
   - primary system DB / event log / brain memory remains source of truth;
   - projection cache is an auditable, replaceable read model;
   - mobile/PWA/local model is read-only with respect to canonical facts.
2. Separate refresh lanes:
   - near-real-time low-coupling watcher/poller for ended/idle sessions or changed source objects;
   - slower full/batch refresh as safety net;
   - deterministic fallback cache that writes to a separate DB/path and never overwrites the richer production cache.
3. Treat LLM enrichment as candidate generation only:
   - write to incremental staging;
   - merge with existing production by stable object id;
   - run deterministic source-bound repair only from existing fields/source refs;
   - promote only after schema/source/self-ingestion/quality gates pass.
4. Use backup + atomic replace for production cache promotion.
5. Keep hot paths free of model calls:
   - Gateway/sync/PWA should only read canonical projection cache;
   - model calls belong in offline/background refresh lanes.

## Invariants to require before serving cache

- Merge invariant: `merged_ids == unique(production_ids ∪ incremental_ids)`.
- Promotion readback: after atomic replace, reopen production DB and verify row count, latest revision, source kind, promotion metadata, and backup existence when replacing an existing DB.
- Export invariant: when serving full cache (`since == 0`), row count should match latest revision or the system should refuse the cache and fall back to the primary source.
- Self-ingestion guard: filter prompts, system scaffolding, rich-writer JSON, planner boilerplate, and background job text from projected user-facing memory.

## When to choose watcher vs core hook

Prefer a polling/idle watcher as the long-term default when it is already meeting latency and correctness needs. It is lower blast-radius, easier to rollback, and does not mutate core agent lifecycle code.

Only upgrade to a core session-end hook/plugin when objective metrics justify it:

- missed projection rate exceeds a defined threshold;
- p95 watcher-to-sync latency exceeds product requirements;
- polling creates measurable resource/model-cost pressure;
- maintenance/debug cost is repeatedly high;
- the core system exposes a stable async hook API.

Even with a core hook, the hook should enqueue work only. It must not synchronously run LLM enrichment or write production projection cache on the main session-close path.

## Verification checklist

- Projection cache can be rebuilt from source of truth.
- Old fallback writer cannot overwrite richer production cache.
- Batch safety refresh and near-real-time watcher do not race into partial cache replacement.
- Tests cover stale cache fallback, non-contiguous revision fallback, merge dedup, promotion readback, and self-ingestion filtering.
- Docs/ADR record certification boundary: degraded multi-model review is not full certification.

## Anti-conditions

Do not apply this pattern to systems where the edge app must be an authoritative writer. In that case, design bidirectional conflict resolution and explicit write authority instead of a read-only projection pipeline.
