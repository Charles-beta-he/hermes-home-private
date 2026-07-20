# Direction — Single-session multitopic trace

State: validated-local-readback

## Goal

Preserve topic boundaries, trace links and current-state projections inside one Hermes conversation without treating context as canonical project state.

## Existing truth

This was the original scope of stable project id `single-session-multitopic-trace`. A real read-only query against the local Hermes session DB resolved prior same-project context while keeping the Project SSOT as current-state authority.

## Validation evidence

- `E-WSO-008`: local session query returned one matching prior same-project session (`20260720_203614_b2c683`, message `830383`).
- The artifact records that chat is a projection, no external-state claim was made, no cross-project content was merged, and the query did not mutate task or direction state.

## Next evidence gate

Enrich trace relations only when a concrete product consumer requires them; do not promote session history to canonical project state.
