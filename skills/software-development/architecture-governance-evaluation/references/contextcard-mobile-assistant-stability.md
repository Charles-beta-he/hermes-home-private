# ContextCard Mobile Assistant Stability Pattern

Applicability: use when designing a mobile/PWA/iOS assistant companion that syncs summarized memory/evidence from a canonical agent/brain store for offline local-model Q&A.

Anti-conditions:
- Do not use this as a reason to make the mobile app, PWA, or gateway a canonical fact source.
- Do not apply the polling-watcher shape to high-frequency hard real-time systems without measuring latency and cost.
- Do not treat degraded multi-model review as full certification.

## Stable architecture shape

1. Keep one authority boundary:
   - canonical conversation/task/memory store remains the source of truth;
   - canonical projection cache is a derived artifact;
   - gateway/mobile clients are read/sync consumers only.
2. Generate rich mobile cards through a candidate pipeline, not direct writes:
   - source-bound writer creates candidates from canonical evidence;
   - deterministic repair may fill structure only from existing source/title/summary/sourceRefs;
   - validation checks schema, source refs, source hash, sensitivity/authority, self-ingestion markers, and quality score;
   - promotion backs up production cache and atomically replaces it only after gates pass.
3. Prefer a low-coupling session-end/idle watcher before modifying the agent core:
   - poll canonical session/message tables on a short cadence;
   - consider ended sessions or sessions idle for a threshold as eligible;
   - track a per-session signature such as last message id + message count + last timestamp;
   - trigger refresh only for changed eligible sessions, with a cooldown;
   - keep a slower batch refresh as a safety net.
4. Incremental refresh must merge, not replace:
   - write recent cards to an incremental staging cache;
   - merge incremental cards with production by stable card id;
   - verify `merged_ids == unique(production_ids ∪ incremental_ids)`;
   - then run repair/promote gates over the full staging cache.
5. Keep deterministic fallback separate:
   - fallback projection can be regenerated periodically;
   - it must write to a separate fallback cache unless explicitly promoted;
   - never let a fallback cron overwrite rich production output accidentally.

## Promotion and rollback checklist

- py_compile and unit tests for exporter/writer/promoter/watcher pass.
- Gateway/PWA tests and build pass when relevant.
- Exporter reads the promoted cache and returns matching latest revision/change counts.
- Gateway returns the same latest revision/change counts.
- Pollution markers are absent: system prompts, skill dumps, cron instructions, writer prompts, generated ContextCard JSON, and seed/test cards.
- Backup file exists before production replacement is considered successful.
- Production DB readback verifies row count, latest revision, source kind, and promotion metadata.

## When to upgrade from polling watcher to core hook/plugin

Only consider native session-end hook integration after objective evidence shows polling is insufficient, for example:

- missed session rate exceeds a defined threshold;
- p95 watcher-to-gateway latency exceeds the product requirement;
- polling maintenance/debug cost is high;
- polling or model calls create measurable resource/cost pressure;
- the host agent exposes a supported async hook/plugin API.

Even then, the core hook should enqueue a refresh event only. It should never synchronously run LLM summarization or write production cache on the main conversation close path.

## Multi-model governance note

If a multi-model review partially fails because some providers time out or have auth/quota issues, preserve the distinction:

- usable single-model or degraded-review advice can inform an ADR;
- it must be labelled degraded/not fully certified;
- high-blast-radius changes, such as modifying the agent core, still require renewed evidence and certification.
