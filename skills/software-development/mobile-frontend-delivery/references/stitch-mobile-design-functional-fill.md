# Stitch mobile design functional fill

Use when a Stitch/RN mobile screen already has strong visual parity but the visible controls still route to one generic details page or placeholder actions.

## Procedure

1. **Find the latest design evidence first.** Prefer Stitch MCP `get_project`/`list_screens`/`get_screen`. If Stitch MCP is unavailable, use the latest local immutable Stitch evidence under the repo (`references/stitch/**`) and explicitly label it as a tool-connection boundary, not as cloud freshness.
2. **Read the screen visually as a control map, not just style.** For each visible affordance, record its user-facing role: top status/connection icon, central prompt/quote card, active logo/home, graph/insight, microphone, settings, etc.
3. **Map every visible control to a reachable product surface.** Avoid routing all controls to a generic `guide`/details page. Typical mapping for a mobile avatar shell:
   - top connection/sensor -> status/readiness surface;
   - quote/task card -> text task composer;
   - active logo/home -> main guide/control surface;
   - graph -> evidence/readback/queue surface;
   - microphone -> real native speech / ASR flow, not a fake button;
   - settings -> connection/diagnostics surface.
4. **Keep implementation lanes out of the main screen.** The main avatar surface should not expose internal terms such as Local/Hybrid/Gateway/MCP/Stitch/Figma/model-provider unless the user explicitly requests diagnostics. Put those on secondary settings/status pages.
5. **Preserve safety and product boundaries.** Mobile remains a projection/draft/handoff client; do not make it write canonical facts. External/risky actions still require confirmation/readback.
6. **Regression-test navigation semantics.** Add tests that press each design control and assert the dedicated surface title/content appears. This prevents future visual-only refactors from collapsing all controls back into one page.
7. **Verify with the relevant SDK gates.** For RN, run native lint/Jest, workspace `tsc`/build, and any shared entry/gateway regression tests touched by the surfaces. If design is cloud-sourced, record the Stitch screen ID/artifact path in project profile/ledger.

## Anti-conditions

- Do not overwrite owned RN UI with generated Stitch HTML.
- Do not treat a local Stitch PNG/HTML as proof of latest cloud state when MCP is disconnected.
- Do not add credentials or tokens to config while trying to restore Stitch access.
- Do not claim visual parity solely from unit tests; screenshot/simulator evidence is still needed for pixel-level acceptance.
