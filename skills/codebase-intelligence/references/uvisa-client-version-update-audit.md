# UVISA client version update audit

Use when checking whether the user-facing H5/PWA client always updates from any local version to the latest available version.

Applicability:
- UVISA frontend repo: `uvisa-app-2.0`
- UVISA backend repo: `uvisa-backend`
- Client release / PWA / About-screen version update behavior.

Anti-conditions:
- Do not treat this as a product requirement by itself; verify current PRD/task wording first.
- Do not assume “latest” means max semantic app version or newest DB row. In this implementation it may mean the backend-selected eligible release.
- Do not certify live update behavior from unit tests only; browser/SW/cache-header evidence is needed for production acceptance.

## Audit path

1. Separate the three update surfaces.
   - PWA Service Worker update flow: `src/hooks/useServiceWorkerUpdate.ts` + `vite.config.ts`.
   - Client release manifest/runtime flow: `src/lib/clientReleaseRuntime.ts` + `src/hooks/useClientReleaseRuntime.ts`.
   - About/manual version probe: `src/screens/me/AboutScreen.tsx`, `src/services/appVersion.service.ts`, backend `AppVersionController.java`.

2. Backend release selection is not necessarily absolute latest.
   - Public manifest endpoint: `api/api-public/.../ClientReleaseController.java`.
   - Selection filters commonly include platform, release status, asset completion, health status, rules/gray/whitelist/blacklist.
   - Check ordering and rule evaluation before saying “latest”. A rollback-active or active release may outrank a newer canary/whitelist row.

3. Inspect the local-current comparison.
   - Frontend sends `currentReleaseId` from local runtime state to `/client-release/manifest`.
   - If manifest release differs, frontend should mark a pending release and activate only at safe boundaries.
   - Watch for first-boot/localStorage-loss behavior: if code uses `prev.currentReleaseId ?? manifest.releaseId`, a client with no stored state may align itself to the server release without creating pending/reload evidence.

4. Inspect activation boundaries.
   - Safe routes typically include main tabs/login-style boundaries.
   - Sensitive flows, dirty forms, hidden document state, and failed/bad releases should defer activation.
   - `forceReload` must be traced from backend response to frontend behavior; do not infer it from admin labels or comments.

5. Inspect SW update semantics separately.
   - `registerType: 'prompt'`, `skipWaiting: false`, `clientsClaim: false` means user-prompted activation, not automatic forced reload.
   - SW can usually jump from an old worker to the current deployed `/sw.js`, but only if registration/update/install/waiting/skip-waiting/reload all occur and cache headers allow discovery.
   - Multi-tab behavior may intentionally reload only the tab that initiated update.

6. Inspect About/manual check separately.
   - `/api/app/version` may be only a label/prompt endpoint.
   - **UVISA-scoped implementation note (applicable only to the repos named in this reference; re-verify before use):** current backend `AppVersionController` returns the standard `ApiResponse` envelope with `data={ latest, forceUpdate, releasedAt }` from config keys `uvisa.app.version.latest`, `uvisa.app.version.force-update`, and `uvisa.app.version.released-at` (defaults observed in code: `1.0.0`, `false`, and server `LocalDate.now()`).
   - **Anti-condition:** do not generalize this endpoint as the release-push source of truth. Frontend `AboutScreen` compares `data.latest` against `APP_VERSION` and may show an update prompt, but that does not by itself select a release, activate a waiting service worker, or prove static assets changed.
   - `latest > APP_VERSION` plus `forceUpdate=true` does not prove an actual update unless the UI invokes SW activation or release-runtime activation.

7. Inspect the UVISA release-push control plane separately from the toast trigger.
   - **Applicability:** UVISA `uvisa-app-2.0` + `uvisa-backend` release/update audits only; re-read current files before claims because release control code is actively changing.
   - Build layer: `pnpm run build:release` runs Vite build plus `scripts/release/generate-version-json.mjs`, writing `dist/version.json` with `releaseId`, `runtimeVersion`, `appVersion`, `gitSha`, `buildNumber`, `assetBaseUrl`, `manifestUrl`, and per-asset `sha256`/`integrity`/`cacheControl`.
   - Serving layer: nginx should keep `/sw.js`, `/registerSW.js`, `/manifest.webmanifest`, and `/version.json` non-cacheable/no-store so clients can discover new workers/manifests.
   - Backend control plane: admin release rows live in `client_release`; rules live in `client_release_rule`; public selection is `/api/client-release/manifest`, filtered by platform, eligible status, complete assets, non-failed health, and rule matching (blacklist, whitelist/override, channel, region, gray/percentage).
   - `version.json` is release asset-manifest evidence, usually registered/imported into backend asset metadata and exposed under the manifest context; it is not the direct condition for the global `UpdateBanner` toast.
   - Global update toast is SW-driven: `UpdateBanner` fires only when `useServiceWorkerUpdate()` reports `isUpdateAvailable`, which comes from `updatefound -> installed` while `navigator.serviceWorker.controller` exists, guarded to once per session via `sw-update-toast-notified`.
   - Client-release activation is separate and currently silent: frontend stores `currentReleaseId`/`pendingReleaseId` in `uvisa:client-release:state`, then activates at safe route/foreground boundaries with `location.replace`; it does not call `ToastProvider` unless future code adds that explicitly.

## Reporting template

Applicability: UVISA frontend repo `uvisa-app-2.0` only, for questions about the user-facing version-update toast / “发现新版本” / “立即更新” prompt.

Anti-conditions:
- Do not generalize this to other projects or to all PWA update systems.
- Do not treat `/client-release/manifest` runtime activation as the toast source unless code now wires it to `ToastProvider`.
- Do not use dev-mode behavior as proof of production toast behavior; this implementation unregisters stale SW/caches in dev and returns before normal SW update prompting.

When the user asks specifically about the user-facing version-update toast, separate it from the broader release runtime:

1. Global update toast is Service Worker driven, not client-release-manifest driven.
   - Frontend surface: `src/components/UpdateBanner.tsx`, mounted from `src/App.tsx` inside the app shell.
   - Trigger state: `useServiceWorkerUpdate().isUpdateAvailable === true`.
   - Deduping: in-memory `firedRef` plus `sessionStorage['sw-update-toast-notified']`; one prompt per browser session.
   - Toast shape: title/body from `update.available` / `update.toastBody`, action label `update.button`, `onAction: updateApp`.

2. `isUpdateAvailable` is set only when a new Service Worker reaches `installed` while an existing SW already controls the page.
   - Check `src/hooks/useServiceWorkerUpdate.ts`: production-only SW registration of `/sw.js?v=${BUILD_NUMBER}`, `reg.update()` on mount, periodic `reg.update()` about every 60 minutes, `updatefound` → installing worker `statechange`.
   - Required condition: `newWorker.state === 'installed' && navigator.serviceWorker.controller`.

3. The toast action is prompt-only activation.
   - `updateApp()` requires `registration.waiting`, sets a user-initiated flag, and posts `{ type: 'SKIP_WAITING' }`.
   - `controllerchange` reloads only if the current tab initiated `updateApp()`; other tabs receiving the event should not auto-reload.
   - Cross-check `vite.config.ts`: `registerType: 'prompt'`, `skipWaiting: false`, `clientsClaim: false`; do not treat autoUpdate behavior as current behavior unless these settings changed.

4. About-screen/manual check is a separate prompt path.
   - `src/screens/me/AboutScreen.tsx` calls `/app/version`, compares backend `latest` against local `APP_VERSION`, and may show an informational/warning toast.
   - That version-number toast does not prove a waiting Service Worker exists and normally does not activate an update unless `isUpdateAvailable` is already true.

5. Client release runtime is separate from the toast.
   - `src/lib/clientReleaseRuntime.ts` and `src/hooks/useClientReleaseRuntime.ts` sync `/client-release/manifest`, store `pendingReleaseId`, and activate at safe boundaries.
   - It reports release events and may reload on safe boundary, but it does not call `ToastProvider` for the global version-update toast.

## Reporting template

- Verdict: “absolute latest”, “backend-selected eligible release”, “prompt-only update”, “SW-toast prompt-only”, or “not guaranteed”.
- Evidence by layer:
  - Backend selection evidence: file + status filters + ordering + rule logic.
  - Frontend manifest state evidence: current/pending comparison + activation boundaries.
  - SW evidence: registration type, waiting/skipWaiting/reload behavior, cache headers if tested.
  - About evidence: version comparison and whether it triggers actual activation.
- Caveats:
  - First-boot/no-local-state behavior.
  - Gray/whitelist/rollback/health/asset gates.
  - User-prompt vs forced reload.
- Verification run:
  - Unit tests for helper/state paths are useful but not enough for production SW behavior.
  - For live acceptance, use browser evidence: app version, SW registration state, network fetch of `/sw.js`, `version.json`/manifest cache headers, localStorage release state before/after, and reload result.
