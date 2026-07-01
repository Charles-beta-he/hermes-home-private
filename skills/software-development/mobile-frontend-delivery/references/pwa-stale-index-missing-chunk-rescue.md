# Installed PWA stale-index / missing-chunk rescue

Applicability: installed browser PWAs, especially iOS Home Screen PWAs, where users report a white screen after a deploy and the app appears to fail before the React/Vue loading/splash component mounts.

Use when all or most of these are true:
- the native/platform startup surface or static page appears, then the app becomes blank before in-app loading;
- the previous release's hashed JS/CSS chunks are not available anymore;
- a Service Worker may have precached `index.html` or serves navigation requests with `createHandlerBoundToURL('index.html')` / NavigationRoute fallback;
- the deploy server only hosts the current `dist/` and does not provide a real `/releases/{releaseId}/...` asset store.

Anti-conditions:
- Do not assume `/releases/{releaseId}/...` exists just because `version.json` advertises it. Probe the URLs or inspect server config first.
- Do not claim old installed PWAs are fixed until the deployed `/sw.js`, `/version.json`, and a missing old `/assets/*.js` request have been read back.
- Do not use this to justify forced reloads during sensitive transaction flows; this is an entry-bundle rescue path for a bundle that cannot boot.

## Root-cause model

Common failure chain:

1. Old installed PWA opens.
2. Old Service Worker returns a precached/stale `index.html` for navigation.
3. That stale HTML references hashed JS/CSS chunks from the previous release.
4. The server no longer hosts those old chunk files.
5. The module script fails before the app bundle executes.
6. React/Vue loading/splash never mounts, so the user sees a white screen after the platform/static startup surface.

## Durable fix pattern when old chunks cannot be recovered

1. Stop future SWs from pinning navigation to stale HTML:
   - do not precache `index.html` unless you retain all release assets;
   - disable Workbox navigation fallback to `index.html` (`navigateFallback: null` or equivalent);
   - keep `/`, `/index.html`, `/sw.js`, `/manifest.webmanifest`, and `/version.json` no-store/no-cache at CDN/server boundaries.

2. Do not runtime-cache app JS/CSS bundles behind Service Worker caches:
   - hashed JS/CSS should be fetched as live immutable deploy assets;
   - avoid `StaleWhileRevalidate` runtime rules for `/\.(js|css)$/` app bundles unless the release asset store is proven.

3. Add a missing-chunk rescue route for old `/assets/*.js` requests:
   - if the requested chunk exists, serve it normally;
   - if it is missing, return JavaScript, not SPA fallback HTML;
   - the rescue JS should unregister Service Workers, delete CacheStorage, then reload with a cache-busting query.

Example rescue body:

```js
(async()=>{
  try {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map(r => r.unregister()));
    }
    if ('caches' in window) {
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
    }
  } catch (e) {
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
  return 200 '...rescue js...';
}

location ~ ^/assets/.*\.js$ {
  add_header Cache-Control "public, max-age=604800, immutable";
  try_files $uri /asset-rescue.js;
}
```

Express/local-preview shape:

```js
app.get('/asset-rescue.js', (_req, res) => {
  res.type('application/javascript');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  res.send(assetRescueScript);
});

app.get(/^\/assets\/.*\.js$/, (_req, res) => {
  res.type('application/javascript');
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
  res.send(assetRescueScript);
});
```

4. Make release manifests honest:
   - if no real release asset store is mounted, do not default `assetBaseUrl` to `/releases/{releaseId}`;
   - emit root-relative current deploy URLs such as `/assets/...` and `/version.json`;
   - only advertise `/releases/...` when the server/object store actually serves those paths.

5. Build number discipline:
   - Docker builds often exclude `.git`; prefer CI/host vars such as `RELEASE_BUILD_NUMBER`, `VITE_BUILD_NUMBER`, `RAILWAY_DEPLOYMENT_ID`, `GITHUB_RUN_NUMBER`, `RELEASE_GIT_SHA`, `RAILWAY_GIT_COMMIT_SHA`, or `GITHUB_SHA` before falling back to `git rev-parse`;
   - never let production SW/cache names collapse to `dev` or `unknown` silently.

## Verification checklist

After build and after deploy, verify:

- built/deployed `sw.js` does not contain `index.html` precache;
- built/deployed `sw.js` does not contain `createHandlerBoundToURL` / navigation fallback to index;
- built/deployed `sw.js` does not contain `static-cache` or `StaleWhileRevalidate` for app JS/CSS;
- `version.json.assetBaseUrl` is empty/root-relative unless `/releases/...` is actually served;
- no `version.json.assets[].url` starts with `/releases/` when there is no release asset store;
- a missing old chunk URL like `/assets/old-missing.js` returns JavaScript containing `serviceWorker.getRegistrations`, not HTML;
- real installed iOS PWA opens, may perform one rescue reload, then reaches the new app.

## User-facing expectation

This fix makes old installed PWAs capable of self-rescue after deploy. The first open may briefly flash or reload once. The acceptance target is no permanent white screen and successful entry into the new bundle.
