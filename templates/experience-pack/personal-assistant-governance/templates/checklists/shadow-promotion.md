# Shadow Promotion Gate Checklist

Use when a new model-generated, heuristic, or externally derived output may affect a canonical store, user-visible sync path, or lifecycle/control-plane state.

1. Keep the existing production path intact.
2. Write new output to staging/shadow storage first.
3. Validate schema, source references, authority, sensitivity, and anti-self-ingestion rules.
4. Promotion command defaults to dry-run.
5. Production replacement requires an explicit promote flag and backup.
6. Read back the promoted production path.
7. Reconcile old writers so deterministic or fallback jobs cannot overwrite the promoted path.
8. Keep rollback/fallback executable until stability is proven.
