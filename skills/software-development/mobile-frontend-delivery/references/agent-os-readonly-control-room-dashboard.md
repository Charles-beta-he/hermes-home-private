# Read-only Control-room Dashboard Surfaces

Use when promoting an agent/control-plane status packet, CLI projection, or local SSOT into a dashboard page without granting execution authority.

## Applicability

- A backend already has a read-only projection/packet/CLI/API shape.
- The user asks to keep advancing and not stop at phase labels or generic manual intervention.
- The safe local slice is UI/readback/projection, not capability execution.
- The dashboard is authenticated or token-protected and can consume an internal API.

Anti-conditions:

- Do not open execution, task lifecycle writes, external dispatch, secret reveal, payment/legal signing, or physical-device control just because the page says "control room".
- Do not add the endpoint to a public allowlist unless every field is safe for unauthenticated uptime probes and random curl users.
- Do not claim runtime control; label proposal-only / read-only / projection-only states explicitly.

## Procedure

1. Start from the read-only backend projection.
   - Prefer a single loader that reads local packet files and returns a compact JSON shape.
   - Include both summary counts and detail arrays only if they are non-secret: evidence nodes, authority records, proposal inbox, device/service-contract stubs.
   - Normalize side-effect fields so UI can show `no` rather than `unknown` when the packet uses a differently named boolean.
2. Expose an authenticated dashboard API.
   - Mirror the CLI/status shape through a `GET /api/.../status` endpoint.
   - Keep it behind the dashboard session/OAuth gate unless the payload passes the public allowlist test.
   - Add a backend test using the dashboard session token/cookie path, not a public unauthenticated request.
3. Add a dashboard route and nav item.
   - Render high-level cards first: capability count, backlog/status, authority count, evidence count.
   - Add boundary rows for every possible side effect: capability execution, external dispatch, runtime mutation, payment/credential action, physical-device effect.
   - Add detail panels only as read-only lists: evidence DAG, authority ledger, proposal inbox, device/service contracts, external dependency boundary.
   - Within this reference's applicability only, add local read-only filters to operator detail panels and show `Showing N of M` counts so records are locatable without creating new write actions.
   - Within this reference's applicability only, render remaining external dependencies as an inbox with status/risk/automation badges and boundary text; anti-condition: do not collapse them back into a vague stop condition.
4. Add a receipt packet only as a read-only, user-triggered projection.
   - CLI shape: add `agent-os receipt --json` (or the local equivalent) that builds a receipt from already-loaded projection state, not by executing capabilities.
   - API shape: add an authenticated `GET /api/.../receipt` endpoint that returns the same packet; do not add it to public health/status allowlists by default.
   - UI shape: add a `Build receipt` action that fetches and displays JSON locally; do not write files, copy to clipboard automatically, dispatch messages, or unlock execution.
   - Receipt contents should include schema/version, counts, boundary booleans, open external dependencies, doctor/findings, and an explicit `side_effects_executed=false`.
   - TDD path: write the CLI receipt test first and watch it fail as an invalid subcommand; write the API receipt test and watch it fail as 404; then implement the minimal command/endpoint/UI and rerun the full dashboard test slice.
5. Preserve product copy boundaries.
   - Use "read-only", "projection", "proposal-only", and "external dependency" labels.
   - Avoid raw debug-only claims as primary UX; surface them as operator diagnostics.
   - Make external ecosystem gaps structured boundary records, not human-intervention stops.
6. Verify through the real dashboard surface.
   - Run backend tests for the projection/API shape.
   - Run frontend typecheck/build.
   - Start the dashboard with the built dist and browse the route.
   - Verify key text/sections are present and browser console has no JS errors.
   - Stop the temporary dashboard process; exit 143/SIGTERM from that validation process is expected if you killed it intentionally.

## Verification checklist

- Backend projection test passes and asserts the detail arrays are present.
- Dashboard API test passes through the authenticated/token path.
- `npm run build` or equivalent frontend build/typecheck passes.
- Browser readback confirms the route is non-blank and shows summary cards plus detail panels.
- If filters were added, type a distinctive query and verify the visible `Showing N of M` count and matching record text update without a network write or console error.
- If an external dependency inbox exists, verify it is visible as structured records with boundary/status labels rather than free-form human-stop copy.
- If a receipt packet exists, verify CLI and API outputs share the same schema, all boundary booleans remain false for safe local projections, the UI `Build receipt` action renders JSON locally, and no file/export/dispatch side effect occurs.
- Browser console has zero JS errors after load and after one representative interaction.
- The temporary validation server is stopped and not mistaken for a production daemon.
- Receipts/ledger/backlog record the safe slice and the side-effect boundaries.
