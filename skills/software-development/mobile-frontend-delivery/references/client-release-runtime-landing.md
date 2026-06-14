# Silent Client Release Runtime Landing

Scope/applicability: class-level pattern for existing React/Vue SPA, PWA, or WebView clients that need silent Release Manifest / OTA runtime after an operator/backend release control plane exists. Anti-condition: do not apply to ordinary release-note pages, native app-store upgrade prompts, or design mockups where real runtime activation is out of scope.

## Runtime implementation pattern

1. Keep responsibilities separate:
   - Admin/governance surface owns release lifecycle, rule editing, rollback preview/execution, and append-only audit.
   - Backend manifest endpoint is the SSOT for per-user/platform/channel/region release selection.
   - Client runtime only executes: fetch manifest, persist release state, preload/activate at safe boundary, report events, and locally recover from bad boot/chunk errors.

2. Client state minimum:
   - `currentReleaseId`
   - `pendingReleaseId`
   - `userBoundReleaseId`
   - `lastKnownGoodReleaseId`
   - `runtimeVersion`
   - `lastManifestAt`

3. Trigger manifest sync on:
   - boot/cold start
   - login success
   - user switch
   - logout
   - safe route transition
   - foreground/focus recovery

4. Activation gate:
   - Allow only on app-defined root/main/auth-safe surfaces.
   - Defer on sensitive flows: payment, identity/KYC, topup, payout, remittance, exchange, confirm/preview/password/PIN routes.
   - Defer when dirty form markers exist, e.g. `[data-dirty="true"]` or `[data-form-dirty="true"]`.
   - Do not show a version-update toast. Silent activation can reload/replace only after the gate passes.

5. Runtime failure handling:
   - On activation, write a boot mark with releaseId and timestamp before reload.
   - On successful mount, mark `lastKnownGoodReleaseId` and clear the boot mark.
   - On next boot, if the previous boot mark exceeded the watchdog timeout, mark that release bad and roll back to `lastKnownGoodReleaseId`.
   - Listen for `error` and `unhandledrejection` with ChunkLoadError / dynamic import / module script patterns and mark the current release bad.

6. Event reporting:
   - Report manifest aligned, pending, activated, safe-boundary deferred, boot success, bad marked, and skipped-bad-release events.
   - Reporting must never block user flow; swallow failures.
   - If anonymous event writes are not protected by signature/rate limit, keep event POST authenticated and let pre-login reporting be best-effort/no-op.

## Backend manifest selection pattern

Do not pick only the latest active release. Evaluate at least:

1. platform match
2. allowed release statuses: rollback-active, active, canary, whitelist
3. asset completeness and non-failed health
4. blacklist before allow rules
5. user override / whitelist
6. channel and region rules
7. gray/percentage rules via stable hash bucket over userId + salt/releaseId
8. release-level gray percent for canary/whitelist fallback
9. active / rollback-active fallback

Return a `matchReason` in manifest context so client/admin evidence can explain why a user was assigned a release.

## Runtime test pattern

Unit-test the runtime separately from UI:

- mock the API client for manifest/event calls
- validate first boot sets current release, not pending
- validate a different release becomes pending
- validate sensitive route and dirty form defer activation
- validate safe route activation promotes pending to current and triggers reload
- validate user login/switch sends userId and records user-bound release
- validate boot watchdog rolls back to lastKnownGood and marks bad release
- validate boot success updates lastKnownGood and reports event

For browser-like test environments, avoid spying on `window.location.replace` directly because it may be non-configurable. Use a small test-only reload injection function while production still calls `window.location.replace`.

## No-fake evidence rule

Screenshots are acceptance evidence only when they come from the real target surface. Do not use route mocks, fake auth, fake permissions, or local mock API responses as proof for release-control admin interactions unless the user explicitly asks for a mockup. If real admin login is blocked, report the real backend response and continue with non-visual verified work such as compile/tests/API/runtime verification rather than fabricating screenshots.
