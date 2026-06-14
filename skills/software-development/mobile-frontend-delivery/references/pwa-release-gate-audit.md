---
name: pwa-release-gate-audit
description: "General audit checklist for PWA release-gate designs that combine backend version policy, Service Worker updates, CDN caching, multi-tab behavior, offline behavior, and old-bundle compatibility."
---

# PWA Release Gate Audit

Scope/applicability: use for any browser PWA or mobile web app that gates access based on a backend-reported app version while also relying on Service Workers and CDN-cached assets. This is especially important for authenticated or transaction-capable apps.

Anti-scope: do not treat this as a mandate for static marketing sites, unauthenticated content sites, or native-only apps with store-managed binary updates.

## Core Principle

Backend release policy can decide **prompt vs block**, but it cannot by itself deliver new code. The deploy path must independently prove that fresh `index.html`, `sw.js`, and hashed assets are reachable and that the current tab can activate a waiting/new Service Worker without deadlocking.

## P0 Audit Items

1. **Version contract is real, not static**
   - Frontend sends `platform`, `currentVersion`, and preferably `buildNumber/gitSha`.
   - Backend returns `latestVersion`, `minSupportedVersion`, `releaseId/build`, `policy: NONE|PROMPT|BLOCK`, `suppressKey`, and user-facing copy/i18n key.
   - `BLOCK` is based on `current < minSupportedVersion`; `PROMPT` is based on newer latest release.

2. **Update button cannot silently no-op**
   - Do not implement `updateApp()` as only `registration.waiting?.postMessage(SKIP_WAITING)`.
   - If `waiting` is absent, explicitly call/await `registration.update()`, wait for installing→installed/waiting with a bounded timeout, then either activate or show a retry/fallback state.
   - For `BLOCK`, provide a fallback reload/cache-bust path and clear error UI; never leave the user blocked with an inert update button.

3. **Multi-tab consistency**
   - A release block discovered in one tab must propagate via `BroadcastChannel` with `localStorage` fallback.
   - Other tabs should enter read-only/blocked state or display “new version installed, refresh this tab”; they must not continue sensitive business APIs on an old bundle.
   - User-initiated reload may remain current-tab-only, but business blocking must be cross-tab.

4. **Startup gate happens before business side effects**
   - Initialize minimal shell/i18n/theme/token only.
   - Run version gate before mounting business routes, polling, SSE, or store loaders.
   - Request layer should prevent business APIs until the gate completes, with explicit allowlist for version/auth-refresh necessities.

5. **Old-bundle backend compatibility**
   - Frontend sends version/build headers on business APIs.
   - Backend critical APIs enforce `minSupportedVersion` and return a standard unsupported-version envelope.
   - Frontend interceptor reacts by entering/broadcasting release block.

## P1 Audit Items

- **CDN/source headers are verified in production**: `index.html`, `/`, `sw.js`, Service Worker registration script, manifest, and the version endpoint should be no-store/no-cache as appropriate; hashed assets should be immutable.
- **Precache/nav strategy is explicit**: if HTML is precached under prompt-only SW, verify that old shell lifecycle and update activation still work after deploy.
- **Version discipline**: CI should ensure package/app version or releaseId changes, dist-injected version matches backend release record, and `sw.js` changes when code changed.
- **Offline/weak-network policy**: define fail-open/fail-closed by prior gate result. Offline should not allow submitting sensitive business actions.
- **Suppress semantics**: 24h suppress applies only to `PROMPT`, is keyed by `releaseId/latestVersion`, and never suppresses `BLOCK`.

## Minimal Acceptance Matrix

1. Build/version injection: app displays or exposes `APP_VERSION` + `BUILD_NUMBER`.
2. Production header checks for `/`, `/index.html`, `/sw.js`, Service Worker registration script, manifest, version endpoint, and hashed JS/CSS.
3. v1 open tab → deploy v2 → gate detects update → click update → controller changes/reloads → version/build becomes v2.
4. Same as above with `registration.waiting` initially absent; update button must not no-op.
5. Two tabs: one discovers `BLOCK`; both tabs stop sensitive business actions.
6. Offline cases: no prior gate, prior non-block gate, prior block gate.
7. Old bundle calls critical API with old version header; backend returns unsupported and frontend blocks.
8. Suppress: prompt suppressed per release for 24h; new release prompts again; block ignores suppress.
