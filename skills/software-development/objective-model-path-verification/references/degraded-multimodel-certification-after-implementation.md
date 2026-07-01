# Degraded multimodel certification after deterministic implementation

Use when a full-landing or taskpool-governed implementation slice has real proof (tests, commit, DB/API/UI readback) but a multimodel/truth-gate certification run returns `not_certified` or `degraded_not_certified`.

## Procedure

1. **Split proof layers.**
   - Deterministic implementation proof can justify saying the bounded code slice works.
   - Governed lifecycle proof is separate; do not mark `done` while required multimodel/truth-gate certification is incomplete.

2. **Preserve hook ownership.**
   - If a taskpool transition to `review` triggers a multimodel hook and the task is reclaimed into `running`, treat it as lifecycle governance, not as failed implementation.
   - Record proof and stop at the smallest certification boundary.

3. **Ground certification evidence deliberately.**
   - Provide claim-linked file/command/commit evidence.
   - Prefer evidence objects with `supports: ["C-001"]` rather than boolean `supports: true`; some local evidence normalizers expect an iterable and may crash or fail to ground claims.
   - If the truth gate still reports unsupported claims, inspect evidence shape/linking before weakening the implementation claim.

4. **Issue an intervention packet instead of forcing closure.**
   - Include: deterministic proof, commit hash, failed/degraded manifest path, exact certification reasons, remaining gate, next safe reversible slice.

## Safe final wording

> The implementation slice landed and deterministic verification passed, but governed multimodel certification is degraded/incomplete; I am not marking the task done. Next step is certification repair/completion or another safe non-production slice.

## Anti-conditions

- Do not use this pattern to bypass failed tests, failed migrations, failed DB readback, or unresolved severity>=3 objections.
- Do not save transient provider/auth/quota failures as durable rules; save only the certification-boundary and evidence-shape handling pattern.
