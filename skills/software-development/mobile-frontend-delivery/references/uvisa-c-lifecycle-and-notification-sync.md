# UVISA-class C-side lifecycle + notification sync pitfalls

## Applicability

Use for mobile/PWA finance apps that combine:

- installed/browser PWA lifecycle events (`visibilitychange`, `focus`, `pageshow`, `online/offline`)
- service-worker or client-release update checks with safe activation boundaries
- notification REST sync plus SSE/WebSocket invalidation
- optional session heartbeat / online-state reporting
- notification rows whose business event time can differ from delivery/creation time

Anti-conditions:

- Do not apply backend-write steps when the user explicitly says backend is read-only; in that case, implement only frontend-compatible gates/feature flags and inspect backend read-only.
- Do not force reload on foreground/resume in transaction/KYC/payment/remittance flows; preserve safe-boundary update activation.
- Do not treat SSE heartbeat as user-online heartbeat; SSE heartbeat is connection keepalive only.

## Pattern

1. Centralize lifecycle instead of adding another timer:
   - `boot/login_success`
   - foreground/resume: `visibility visible`, `focus`, `pageshow`, `online`
   - background: `visibility hidden`, app inactive/background
   - idle boundary after user inactivity
   - route safe boundary

2. On foreground/resume:
   - send explicit heartbeat only if the backend endpoint is enabled/available
   - silently check SW/client-release manifest
   - activate updates only through the existing safe-route boundary
   - run critical REST repair sync (notifications cursor sync first)
   - then reconnect SSE/WebSocket and resume polling

3. On background/offline:
   - stop explicit heartbeat timer
   - stop business polling
   - disconnect SSE/WebSocket and suppress reconnect loops
   - optionally send one best-effort `{state:"background"}` heartbeat without retry storms

4. Heartbeat should be feature-flagged when backend readiness is uncertain:
   - default off until `POST /api/me/session/heartbeat` exists
   - record authenticated-business-request activity from the shared API interceptor
   - skip explicit heartbeat when a successful authenticated business request occurred inside the heartbeat window

5. Notification sync merge rule:
   - new IDs may be prepended
   - existing IDs must be replaced in place, not moved to the top
   - deleted IDs are removed
   - this prevents read/mutation events from making old notifications jump to first position

6. Notification time semantics:
   - list card/footer display time should use delivery/creation timestamp (`createdAt`) when present
   - business event timestamp (`occurredAt`, embedded start/end times in body) is for details/audit and must not drive card ordering/display when product expectation is “latest received first”
   - preserve both fields in normalized client models when they can differ

## Verification checklist

- Unit test: read-state sync for an existing notification updates `read=true` but preserves row order.
- Unit test: notification with `createdAt != occurredAt` displays card time from `createdAt` and preserves `occurredAt`.
- Lifecycle smoke: hidden/offline stops polling and disconnects realtime; visible/online runs REST sync before realtime reconnect.
- Build gate: TypeScript build catches browser-vs-Node timer type mismatches (`number` vs `Timeout`).
- Backend boundary: if backend is read-only, `git status` for backend worktree must remain clean and no migrations/services are committed.
