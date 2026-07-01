# Canonical Projection Cache Pattern

Use this when a mobile/edge/PWA companion needs fast offline sync from Hermes-owned facts without making the edge gateway a fact author.

## Applicability

Use for:
- PWA/mobile companion sync where Gateway must stay a projection/sync boundary.
- ContextCard / evidence-span style offline packs.
- Production automation where request-path generation would be too slow or risky.
- Cases where Hermes/Brain/state DB remains the unique source of truth.
- Near-real-time companion memory updates where a polling watcher is acceptable before invasive core hooks.

Anti-conditions:
- Do not use as a second truth source; the cache is a projection cache only.
- Do not make Gateway/PWA generate authoritative facts.
- Do not put LLM generation on the sync request path without an explicit gate.
- Do not cache secrets, credentials, system prompts, skill dumps, planner payloads, cron/private background output, or iteration-relay boilerplate.
- Do not let a small incremental refresh replace the full production cache; merge it with the existing production projection first.

## Architecture

```
Hermes SSOT (state.db / Brain)
  -> canonical exporter or writer
  -> SQLite projection cache
  -> Gateway read-only ContextSource
  -> PWA/mobile offline sync
```

For rich/LLM summaries, prefer this production shape:

```
state.db sessions/messages
  -> session-end/idle watcher (polling, no-agent cron)
  -> rich writer to incremental staging
  -> merge incremental with current production cache
  -> source-bound quality repair/validation
  -> promotion gate with backup
  -> production projection cache
  -> Gateway/PWA sync
```

The Gateway may support fallback deterministic projection for development, but production should prefer a Hermes-side exporter/cache.

## Production-grade sequence

1. Define the projection contract first:
   - `context_card` and `evidence_span` objects.
   - `revision`, `type`, `object_json`, `updated_at`.
   - `source.kind` distinguishes `canonical_contextcard_cache` from fallback sources.
2. Build exporter read path:
   - Fresh cache wins.
   - Stale/missing cache falls back to SSOT read-only projection.
   - `--since` cursor filters emitted changes.
3. Build idempotent deterministic writer:
   - Read Hermes SSOT read-only.
   - Write cache in a single SQLite transaction.
   - Use local lock file to avoid concurrent writers.
   - Emit compact JSON metrics.
4. Add silent cron wrapper:
   - `no_agent=true` cron.
   - Success stdout empty; log JSON metrics to file.
   - Non-zero exit alerts through cron error path.
5. Wire Gateway via environment variables:
   - `HERMES_STATE_DB`
   - `HERMES_CONTEXTCARD_EXPORTER`
   - `HERMES_CONTEXTCARD_CACHE_DB`
   - `HERMES_CONTEXTCARD_CACHE_MAX_AGE_SECONDS`
6. Verify with real readback:
   - Python unit tests for exporter/writer.
   - Gateway tests/build.
   - Curl `/v1/sync/changes` and assert seed/system/cron noise is absent.

## Rich writer promotion pattern

When introducing Hermes/Brain/LLM richer generation, do not jump straight from model output to production cache.

1. Keep the rule-based writer as fallback.
2. Add an LLM command boundary that reads source-card/evidence JSON from stdin and returns exactly one ContextCard JSON object.
3. Validate before write:
   - required fields present;
   - `sourceRefs` non-empty;
   - `sourceHash` present and source-bound;
   - `authorityLevel` and `sensitivityLevel` present;
   - array fields have the correct type;
   - no source-external claims;
   - no rich-writer prompt/JSON self-ingestion markers.
4. Write rich output to staging first.
5. Run a promotion verifier in dry-run mode until sample/schema/quality gates pass.
6. Promotion must create a backup and atomically replace production only after gates pass.
7. Keep deterministic fallback writing to a separate fallback DB; pause or redirect any old deterministic cron that writes the same production DB, otherwise it will overwrite rich production cache.

## Near-real-time session-end/idle watcher pattern

If the user approves near-real-time updates but a core Hermes session-end hook would be too invasive, use a polling watcher first:

1. Poll `sessions` + `messages` from the Hermes state DB read-only.
2. Eligible sessions are either explicitly ended (`ended_at` present) or idle for a configurable interval, e.g. 180 seconds since last message.
3. Restrict to user-visible sources such as `cli` and `telegram`; exclude `cron` by default.
4. Store a per-session signature (`last_message_id`, `message_count`, `last_message_at`) in a small watcher state file.
5. Trigger rich production refresh only when an eligible session signature changes.
6. Add a cooldown, e.g. 600 seconds, to prevent LLM refresh storms.
7. Run as `no_agent` cron every few minutes; success should be silent, failure should alert.
8. Preserve a slower full batch cron as a safety net.

## Incremental refresh merge pitfall

Near-real-time refreshes often generate only a handful of recent cards. If that staging DB is promoted directly, it can shrink production from a full cache to only the incremental cards or fail the minimum sample-size gate. Always:

1. write the small batch to an incremental staging DB;
2. load the current production cache;
3. merge by stable ContextCard id (`object.id`): replace matching cards, insert new cards, keep unchanged production cards;
4. write the merged full staging DB with renumbered revisions;
5. run quality repair/validation and promotion against the merged full staging DB.

## Quality gate and repair

Useful automatic scoring checks:
- summary length not too short/long;
- decisions/constraints/keywords/topics/entities present when source evidence supports them;
- self-ingestion markers absent;
- average score and below-threshold list emitted in JSON.

Source-bound repair is allowed only for structural gaps and must not invent new facts. Safe repairs can extend a short summary with an explicit source-bound disclaimer and fill generic constraints such as “use only the referenced evidence; refuse or escalate when evidence is insufficient.”

## Filtering checklist

Exclude known non-user-facing content before mobile sync:
- skill injection / `[IMPORTANT:` skill dumps
- `<available_skills>`
- planner/internal architecture payloads
- smoke-test strings
- cron/background sources unless explicitly allowed
- max-iteration relay boilerplate
- rich-writer prompts such as `SOURCE_CARD:` / `EVIDENCE_SPANS:`
- serialized ContextCard JSON produced by the writer (`sourceRefs` + `sourceHash` + `cardVersion` markers)
- secrets, credentials, tool outputs with sensitive paths/tokens

Default allowed session sources should be user-visible, e.g. `cli`, `telegram`; treat `cron` and `unknown` as excluded unless the product explicitly opts in.

## TDD checks

Minimum RED/GREEN coverage:
- exporter reads fixture state DB and filters private/system content
- fresh cache hit wins over state projection
- stale cache falls back to state projection
- writer first run writes rows
- writer rerun is idempotent and refreshes `updated_at`
- exporter can read writer-produced cache
- rich writer rejects candidates without `sourceRefs`
- promotion verifier blocks insufficient sample size and invalid cards
- promotion creates a backup and exporter can read promoted production cache
- quality report detects below-threshold cards
- session watcher detects changed ended/idle sessions, executes refresh, and becomes idle on second run with the same signature
- Gateway script ContextSource passes cache args

## Human gates

A rule-based writer is safe to automate. Introducing LLM/Brain richer generation requires a dry-run validator first. Once rich staging has passed source-bound, quality, and promotion gates, it may become the steady-state production writer.

The next higher-risk gate is replacing the low-coupling polling watcher with a Hermes core native session-end hook/plugin. Stop before changing Hermes core unless the user explicitly accepts the higher blast radius and post-update patch replay cost.
