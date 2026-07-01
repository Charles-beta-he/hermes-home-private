# Shadow Promotion Gates for Production Automation

Use when a production-grade automation task introduces model-generated, heuristic, or otherwise quality-variable output that could affect a canonical store, user-visible sync path, or control-plane state.

## Pattern

1. Keep the stable production path intact.
   - Existing deterministic writer / exporter / gateway should continue serving production.
   - New richer/model output must not replace the canonical cache on first introduction.

2. Add a shadow writer.
   - Write candidates to a staging store, not the production store.
   - Make the writer source-bound: every claim must trace to source references or evidence spans.
   - Validate schema, sourceRefs, sourceHash, sensitivity, authority, and anti-self-ingestion markers before accepting candidates.

3. Add continuous dry-run verification.
   - A no-agent cron can run verifier checks and write logs.
   - Successful blocked states (for example insufficient sample size) should be silent; actual errors should alert.
   - Do not treat “blocked by configured promotion gate” as failure.

4. Promotion requires explicit gate crossing.
   - Promotion script should default to dry-run.
   - Require an explicit flag such as `--promote` to replace production.
   - Before replacement, create a backup and use an atomic swap/rename where possible.
   - After replacement, verify the production reader/exporter can read the promoted data.

5. Avoid self-ingestion loops.
   - Filter prompts, generated JSON, model-adapter session content, and other internal writer artifacts from future source projections.
   - Add regression tests that insert such artifacts into fixture history and assert they do not appear in exported payloads.

6. After first promotion, reconcile every existing writer.
   - Search for older cron jobs, wrappers, hooks, or fallback writers that still write the production store.
   - Pause or retarget deterministic/legacy writers before declaring the promoted path steady-state; otherwise they may silently overwrite the promoted rich cache on the next interval.
   - Preserve deterministic output as a separate fallback artifact (for example `*.deterministic.db`) rather than letting fallback and promoted production share one path.
   - Replace shadow-only cron fragments with one steady-state batch path when appropriate: refresh staging → repair/score → promote with backup → reader readback.

## Stop condition vs progress report

For “全盘推进” / production automation tasks, do not stop at stage reports or suggested next slices. Continue implementing safe reversible layers: dry-run verifier, staging store, backup/rollback, cron check, readback tests, and documentation. Stop only at a real authority boundary such as executing first production promotion, destructive replacement without rollback, credentials, external side effects, or a gate that currently fails.

## Verification checklist

- RED tests exist for blocked gate, invalid candidate, successful promote, backup, and production readback.
- Full test/build suite still passes.
- Real staging run produces machine-readable metrics.
- Production path remains unchanged until explicit promotion.
- Logs distinguish `blocked` from `error`.
