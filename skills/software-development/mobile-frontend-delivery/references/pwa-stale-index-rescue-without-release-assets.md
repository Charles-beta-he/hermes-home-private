# PWA stale-index rescue when old release chunks are unavailable

Applicability: installed PWA/Home Screen users see a white screen after a new deploy, specifically after the platform/native startup surface and before the React/Vue loading/splash component can mount. The deploy does not retain old hashed JS/CSS chunks and the server does not actually mount `/releases/{releaseId}/...` asset folders.

Anti-conditions:
- Do not assume this solves true backend/API boot failures after the app bundle has mounted.
- Do not advertise `/releases/{releaseId}` URLs in `version.json` unless those assets are really served and verified with HTTP 200 + correct content-type.
- Do not treat old-bundle compatibility as complete unless either historical assets are retained or a rescue path for missing old chunks is present.

## Root-cause signature

Evidence usually looks like:

- Existing Service Worker precaches `index.html`.
- Service Worker has a navigation fallback such as `NavigationRoute(createHandlerBoundToURL("index.html"))`.
- Old installed PWA opens through the old SW, gets an old `index.html`, and that HTML references old hashed chunks.
- The current deploy has replaced `dist/`, so old `/assets/*.js` returns 404 or SPA fallback HTML.
- React/Vue entry script never executes, so the in-app loading/splash component never appears.

This is a pre-app failure, not a loading component failure.

## Fix pattern when previous chunks cannot be recovered

1. Remove `index.html` from the SW precache and disable the navigation fallback to cached index.
   - In VitePWA/Workbox, avoid `globPatterns` that include `html`.
   - Set `navigateFallback: null` or equivalent if the app cannot retain old chunks.

2. Do not runtime-cache app JS/CSS chunks with `StaleWhileRevalidate`.
   - Hashed bundles should be fetched from the live deployment, or all release bundles must be retained.
   - Keep runtime caches for non-critical assets such as images only.

3. Add an asset-rescue JS endpoint for missing old chunks.
   - For `/assets/*.js`, serve the real file if present.
   - If absent, return a no-store JavaScript module, not HTML.
   - The module should unregister service workers, delete CacheStorage, then reload with a cache-busting query parameter.

Example rescue payload:

```js
(async () => {
  try {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map((r) => r.unregister()));
    }
    if ('caches' in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
    }
  } catch (_) {
    // rescue must not throw
  } finally {
    const u = new URL(location.href);
    u.searchParams.set('pwa-rescue', Date.now().toString());
    location.replace(u.href);
  }
})();
```

Nginx shape:

```nginx
location = /asset-rescue.js {
  default_type application/javascript;
  add_header Cache-Control "no-store, no-cache, must-revalidate" always;
  return 200 '...rescue JS...';
}

location ~ ^/assets/.*\.js$ {
  add_header Cache-Control "public, max-age=604800, immutable";
  try_files $uri /asset-rescue.js;
}
```

4. Make release manifests truthful.
   - If no release asset store exists, emit root URLs such as `/assets/...` and `/version.json`.
   - Only emit `/releases/{releaseId}/...` when that directory/object-store path is actually served.

5. Make build numbers independent of local `.git`.
   - Docker/Railway builds may exclude `.git`; prefer `RELEASE_BUILD_NUMBER`, `VITE_BUILD_NUMBER`, `RAILWAY_DEPLOYMENT_ID`, `GITHUB_RUN_NUMBER`, `RELEASE_GIT_SHA`, `RAILWAY_GIT_COMMIT_SHA`, or `GITHUB_SHA` before local `git rev-parse`.
   - Avoid shipping `image-cache-dev`, `gitSha: unknown`, or `buildNumber: unknown` in production if CI provides identifiers.

## Verification checklist

After build, inspect generated artifacts:

- `dist/sw.js` does not contain `index.html`.
- `dist/sw.js` does not contain `createHandlerBoundToURL("index.html")` or equivalent navigation fallback.
- `dist/sw.js` does not contain app-bundle `static-cache` / `StaleWhileRevalidate` for JS/CSS.
- `dist/version.json` does not contain `/releases/` URLs unless those URLs are served.
- Missing `/assets/old-hash.js` returns JavaScript rescue with `Cache-Control: no-store`, not SPA HTML.

Recommended regression tests:

- Source-level test asserting PWA config excludes HTML from precache and disables navigation fallback.
- Source-level test asserting app JS/CSS runtime caching is absent.
- Server config test asserting `/assets/*.js` has a rescue fallback.
- Release manifest test asserting no fake `/releases` URLs without an asset store.
