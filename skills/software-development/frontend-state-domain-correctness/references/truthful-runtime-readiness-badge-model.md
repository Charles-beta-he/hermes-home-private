# Truthful Runtime / Readiness Badge Model

Extracted from `/Users/charles/.hermes/skills/software-development/frontend-state-domain-correctness/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Truthful Runtime / Readiness Badge Model

Scope: frontend surfaces that show compact status badges such as "online", "ready", "deliverable", "production", "synced", or "authorized" while underlying facts come from different subsystems.

Rule: do not replace a hardcoded status string with another broad label. First split the status into independent axes, then derive a short badge from a view-model function with visible data-source boundaries.

Recommended axes:

1. Connectivity: checking, online/synced, online/empty, offline-with-cache, error, wipe/reset-required.
2. Backend or control-room sync: live, local projection, needs attention, blocked, unavailable.
3. Release/readiness: local candidate, simulator verified, device gate pending, external/TestFlight/App Store gate pending, externally released/verified.
4. Action authority: read-only, local-safe, handoff queued, readback accepted, external gated, publish/deploy/push gated, blocked.

Implementation shape:

- Build a pure selector/view-model such as `buildHeaderStatusBadge(inputs)` that returns `{ label, tone, primaryState, secondaryState, dataSources, blockingReason }`.
- Keep runtime connectivity, release readiness, and authority as independent inputs; never infer one from another.
- Use conservative wording when proof is missing: "local candidate", "simulator verified", or "awaiting authorization" instead of unconditional "deliverable" or "released".
- If external release or destructive/publish actions require human approval, the badge must surface the gate rather than hiding it behind a green state.

Anti-condition: if the product explicitly wants a purely decorative marketing tagline, keep it visually separate from operational status and do not wire it to domain state.


Checklist:

1. State the page invariant in business terms before deriving numbers or visibility.
   - Example shapes: placeholder-only surface, active-items-only list, historical ledger, balance fallback, compliance-gated summary.
2. Put feature gates and placeholder rules before aggregation.
   - If a surface is intentionally disabled, not launched, or placeholder-only, return the placeholder view model before reading raw entities.
3. Filter by page eligibility before `reduce`/`map`.
   - Do not assume "nothing user-visible" means the raw collection is empty.
   - Check status, ownership/session freshness, lifecycle state, product type, visibility flag, and other domain-specific eligibility.
4. Centralize semantic conversion.
   - Currency conversion, precision, status mapping, earnings/revenue field choice, and type splits belong in selectors/domain helpers, not ad-hoc page reducers.
5. Preserve raw vs derived boundaries.
   - Service normalization handles transport compatibility; selectors handle page display semantics.
6. Test negative cases.
   - Raw entities exist but the feature is disabled.
   - Raw entities are non-displayable for this page.
   - Persisted cache or failed refresh would otherwise leak stale/cross-context data.

Anti-conditions: this pattern is unnecessary for a truly page-local collection whose API contract already returns exactly the page view model and has no shared reuse, lifecycle filtering, feature gate, or cross-surface aggregation.

Falsifier: if the backend contract explicitly guarantees the endpoint returns only entities eligible for that exact page surface and the collection is not reused elsewhere, page-level selectors may be minimal pass-throughs.
