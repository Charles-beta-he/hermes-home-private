# UVISA PWA stale Service Worker / missing chunk root-cause path

Applicability: UVISA `uvisa-app-2.0` or similar VitePWA/Railway-installed PWA reports: after a version update, the installed PWA opens to a white/blank screen, and killing/reopening the app sometimes restores it.

Anti-conditions:
- Do not treat this as an in-app React loading bug unless the React splash/loading component actually mounts.
- Do not certify the fix from source comments only; inspect the generated `dist/sw.js` and probe the live URL.
- Do not store project paths, branches, release IDs, or one-off run status here; re-read the project profile/current repo before acting.

## Root-cause signature

Likely chain:
1. Installed PWA still has an old Service Worker.
2. Old SW serves a cached/stale `index.html` for navigation.
3. That stale HTML references old hashed `/assets/*.js` chunks.
4. The new deploy only hosts the current `dist/`, so old chunks are gone.
5. Module script load fails before React/Vue mounts.
6. User sees white screen; killing/reopening only changes lifecycle timing and may allow fresh entry/update discovery.

## Evidence ladder

Use a clean temporary copy for old-HEAD/old-config reproduction if the working tree already contains fixes.

1. Inspect current source:
   - `vite.config.ts`: look for `globPatterns` including `html`, `navigateFallback` to index, and JS/CSS `StaleWhileRevalidate`/`static-cache` runtime caching.
   - server config (`nginx-templates/default.conf.template`, `serve.js`): look for `/asset-rescue.js` and `/assets/*.js` rescue fallback.
   - SW registration hook: versioned `/sw.js?v=<build>` and `updateViaCache: 'none'` improve discovery.

2. Build and inspect generated artifacts:
   - Run the release build (`pnpm run build:release` if present).
   - Inspect `dist/sw.js` for absence of: `index.html`, `createHandlerBoundToURL`, `NavigationRoute`, `static-cache`, `StaleWhileRevalidate`.
   - Inspect `dist/version.json`: if there is no real release asset store, `assetBaseUrl` should be empty/root-relative and asset URLs should not start with `/releases/`.

3. Probe the live deployed origin:
   - Fetch `/sw.js`, `/version.json`, `/manifest.webmanifest`, `/asset-rescue.js`, and a definitely missing `/assets/<old>.js`.
   - Expected for a fixed deployment: `/sw.js` no-store/no-cache and no stale-index/navigation-fallback strings; missing `/assets/*.js` returns JavaScript rescue (`serviceWorker.getRegistrations`, CacheStorage cleanup, reload), not HTML.
   - Check full headers because duplicate `Cache-Control` can exist; ensure a no-store/no-cache directive is present.

4. Compare old/current behavior:
   - Old-risk build commonly shows a large precache count, `index.html` in `sw.js`, Workbox `NavigationRoute/createHandlerBoundToURL`, and `static-cache`/`StaleWhileRevalidate` for JS/CSS.
   - Fixed build should have a tiny precache allowlist and no app JS/CSS runtime cache.

## Fix pattern

- Do not precache `index.html` unless historical release assets are retained.
- Disable navigation fallback to cached index (`navigateFallback: null` or equivalent).
- Do not runtime-cache app JS/CSS bundles in the SW when old chunks are not retained.
- Add missing-old-chunk rescue for `/assets/*.js`: return executable no-store JS that unregisters SWs, deletes CacheStorage, and reloads with a rescue query.
- Keep `/sw.js`, `/registerSW.js`, `/manifest.webmanifest`, `/version.json`, and `/` non-cacheable at CDN/server boundaries.
- Generate honest release manifests: no `/releases/{releaseId}` URLs unless those paths are actually served and read back.

## UVISA/Railway build metadata pitfall

If live `version.json` shows `gitSha: "unknown"` or `buildNumber: "unknown"`, separate it from the white-screen root cause. It weakens release audit/SW versioning but may not itself cause the white screen.

Common reason: Docker build excludes `.git` and release/build env vars are not passed into the build stage. Prefer CI/Railway variables such as `RELEASE_BUILD_NUMBER`, `VITE_BUILD_NUMBER`, `RAILWAY_DEPLOYMENT_ID`, `RELEASE_GIT_SHA`, `RAILWAY_GIT_COMMIT_SHA`, `GITHUB_RUN_NUMBER`, or `GITHUB_SHA`, and wire them as build args/env before running the release build.

## Acceptance

Minimum acceptance for the root-cause fix:
- Targeted PWA release safety tests pass.
- Release build passes.
- Generated `dist/sw.js` lacks stale-index/navigation-fallback/static-cache signatures.
- Live missing `/assets/*.js` returns rescue JS with no-store cache headers.
- Real installed PWA can open after a deploy; if old chunks are missing, it may reload once but must not stay permanently white.
