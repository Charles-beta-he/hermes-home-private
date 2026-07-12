# Runtime projection UI closeout

Use this reference when a local/operator UI projects internal agent, control-plane, world-model, loop, receipt, or risk state. The UI is not necessarily a product storefront; it is a non-authoritative read-only surface that must make hidden runtime state inspectable without opening execution authority.

## Applicability

Apply when the UI shows any of:

- loop/world-model receipts, reasoning iteration state, confidence, risk, or exit reason
- action intent queues, evidence ledgers, gate ladders, runtime health, or control-plane status
- local workbench/operator dashboards where the UI is a projection of backend/ledger state

Anti-conditions:

- Do not use this to justify real model quality, real-world actuation, external dispatch, taskpool ingestion, deploy/push, payment, credential/secret entry, or destructive operations.
- Do not claim full A+ UI acceptance from static HTML or API smoke alone; require visual/browser evidence and, for high-quality claims, keyboard/contrast/responsive evidence.

## Projection contract pattern

1. Add a DTO/projection helper that maps raw receipts/events to safe UI fields.
   - Preserve schema/version and receipt id.
   - Include user/operator-relevant fields: loop depth, exit reason, confidence, risk, deferred decode label, recommended action, known limits.
   - Collapse raw/internal latent state into explanation summaries; never expose secrets or raw sensitive payloads.
   - Compute a boolean such as `side_effect_open` from boundary flags.
2. Add a read-only runtime endpoint for the projection, e.g. `/projection/<domain>`.
   - `GET` only.
   - No POST simulation or execution route unless separately authorized.
   - Health/readiness can expose `projection_enabled=true` and `execution_enabled=false`.
3. Add dashboard aggregates.
   - Counts by exit reason/risk/status.
   - Latest projected receipts.
   - Do not let dashboard state become source-of-truth; it must be derived from ledger/receipts.
4. Add a static/browser-visible card.
   - Show the key runtime state directly above the fold when possible.
   - Include explicit non-authority copy: “read-only projection”, “execution disabled”, or equivalent.
   - Do not add approval/execute controls in a projection-only slice.
5. Regenerate static artifacts if the project has them.
6. Add tests for projection shape, endpoint readback, static UI text, and forbidden execution paths.
7. Run a browser visual smoke; API/DOM evidence alone is not enough for UI claims.

## Verification checklist

- [ ] Unit tests cover DTO shape and dashboard aggregation.
- [ ] Runtime smoke reads `/healthz`, the projection endpoint, and dashboard endpoint.
- [ ] Projection endpoint returns `side_effect_open=false` or equivalent fail-closed state for the fixture.
- [ ] Static/browser UI visibly shows loop depth / exit reason / confidence / decode label / boundary flags as applicable.
- [ ] No execute/approve/deploy/publish/taskpool/gateway/secret-entry/payment/destructive controls are visible.
- [ ] Browser visual smoke checks clipping/overflow for long schema IDs and action IDs.
- [ ] Static artifact is regenerated and read back.
- [ ] If claiming A/A+, include responsive, keyboard/focus, contrast-token, and console evidence.

## Pitfalls

- Long receipt schemas and action IDs clip in right-hand cards. Use grid rows with `minmax(0, 1fr)`, `overflow-wrap:anywhere`, and right-aligned but wrappable values instead of a flex row that forces horizontal overflow.
- Forbidden-word guards may fail when safety boundary labels include sensitive terms. If the UI must show a boundary flag, prefer safe display labels like `secret_entry` while keeping canonical machine fields inside JSON tests.
- A successful local workbench smoke does not authorize real adapters. Keep model routing, external dispatch, hardware, taskpool ingestion, and credential/secret entry as separate gates with exact authority and readback.
