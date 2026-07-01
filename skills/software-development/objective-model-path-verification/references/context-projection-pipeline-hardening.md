# Context Projection Pipeline Hardening

Use this reference when a project turns agent/session history into a mobile/offline/sync projection cache, especially when an LLM enriches records before they reach a production cache.

## Applicability

Applies when:
- Hermes/session/state history is projected into a downstream cache or Gateway/PWA/mobile sync surface.
- A richer/LLM writer is introduced before production consumers.
- Near-real-time refresh is desired but the core lifecycle hook has higher blast radius than an external watcher.

Anti-conditions:
- Do not use this to justify writing mobile/PWA output back as canonical facts.
- Do not use this to put LLM calls on a hot request path or a core session-close path.
- Do not treat one successful watcher run as evidence to lower cooldowns or mutate core.

## Stable architecture pattern

1. Keep one authority source.
   - Canonical source remains the primary state DB / Brain / SSOT.
   - Gateway/mobile/PWA are projection consumers, not fact writers.

2. Split production lanes.
   - Near-real-time lane: low-coupling watcher or event consumer detects ended/idle/changed sessions.
   - Safety lane: periodic batch refresh catches watcher misses.
   - Deterministic fallback lane: writes a separate fallback cache; it must not overwrite the promoted rich production cache.

3. Put LLM output behind staging and promotion.
   - LLM writer emits candidates only.
   - Validate schema, source refs, source hashes, authority/sensitivity fields, self-ingestion markers, and quality score.
   - Promotion requires backup plus atomic replace.

4. Prevent small-batch overwrite.
   - Near-real-time refreshes are usually incremental.
   - Merge incremental staging with existing production by canonical object id before promotion.
   - Enforce `merged_ids == unique(production_ids ∪ incremental_ids)`.

5. Add post-promotion readback.
   - After `os.replace` or equivalent, reopen production storage and verify row count, latest revision, source kind, promotion metadata, and backup presence.

6. Add exporter cache invariants.
   - For full sync (`since == 0`), verify cache row count matches latest revision / contiguous revision expectations before serving cache.
   - For incremental sync (`since > 0`), avoid full-row assertions that would false-positive.

7. Add self-ingestion filters.
   - Exclude the writer's own prompts, generated JSON, system/skill boilerplate, iteration-exhaustion relay text, cron output, and seed/demo payloads from future projections.

8. Add observability before core mutation.
   - Health report should be read-only and include production invariant, watcher age/status, latest promotion status, and objective core-hook recommendation reasons.
   - Normal health checks should be silent; error paths should emit.

## Core hook decision rule

Prefer external watcher/event consumer until metrics prove it is insufficient. Consider core hook/plugin only when objective thresholds are met, e.g. missed-session rate, p95 latency, maintenance cost, or polling/LLM cost exceed agreed limits.

If core is entered, it should only enqueue an event/outbox record. It must not run the rich writer, call models, or write production projection cache synchronously on the main session lifecycle path.

## Verification checklist

- [ ] Old deterministic writers cannot overwrite promoted rich production cache.
- [ ] Incremental merge preserves old cards and inserts/replaces by id.
- [ ] Promotion backup exists before success is reported.
- [ ] Readback invariants pass after production replacement.
- [ ] Exporter/Gateway full sync revision counts match.
- [ ] Self-ingestion/prompt markers are absent from exported payloads.
- [ ] Tests cover stale cache fallback, invalid staging rejection, merge dedup, promotion readback, watcher state, and health-report threshold behavior.
- [ ] Cron/list readback confirms the active and paused jobs match the intended steady state.
