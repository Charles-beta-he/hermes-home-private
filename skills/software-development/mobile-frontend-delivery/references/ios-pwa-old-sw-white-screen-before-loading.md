# iOS installed PWA white screen before React loading after release

Applicability: installed iOS Home Screen PWA opens the platform/static launch surface, then shows a blank/white web area before the app's React splash/loading component appears, especially after a new package/release deploy.

Anti-conditions:
- Do not treat this as a SplashScreen/loading-component bug until the entry JS module has been proven to execute.
- Do not blame iOS device cache alone until live `/sw.js`, `/index.html`, generated service worker contents, and old chunk URLs are checked.
- Do not claim a release-manifest rollback path works unless the referenced `/releases/{releaseId}/...` assets are actually served and not SPA-fallback HTML.

## Root-cause model

Common failure chain:

1. Old installed PWA is still controlled by an old Service Worker.
2. The old SW precaches `index.html` and registers a navigation fallback such as `createHandlerBoundToURL("index.html")`.
3. On launch, WebKit asks for `/`; the old SW returns old cached `index.html` instead of the fresh network HTML.
4. That old HTML references old hashed JS/CSS chunks.
5. The server/CDN/container only retains the latest `dist/assets/*`, or the advertised release asset directory is not truly served.
6. The entry module 404s or fails as a module script, so React never mounts and the in-app SplashScreen/loading never appears.
7. User sees white screen in the gap between native/static startup and React loading.

This is a pre-React boot failure. Fixing the React loading animation, timers, or page skeleton does not address it.

## Evidence checklist

For the exact live origin:

```bash
base=https://example.com
ua_ios='Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
for p in / /index.html /sw.js /registerSW.js /manifest.webmanifest /version.json; do
  echo "=== $p"
  curl -sS -L -A "$ua_ios" -D /tmp/pwa-h "$base$p" -o /tmp/pwa-b
  grep -iE 'HTTP/|cache-control|cdn-cache-control|cloudflare|age:|expires:|last-modified|etag:|content-type|content-length' /tmp/pwa-h || true
  head -c 240 /tmp/pwa-b | tr '\n' ' '; echo
 done
```

Then inspect the generated/current SW body:

```bash
curl -sS "$base/sw.js" -o /tmp/live-sw.js
python3 - <<'PY'
from pathlib import Path
s = Path('/tmp/live-sw.js').read_text(errors='replace')
for token in ['precacheAndRoute', 'index.html', 'NavigationRoute', 'createHandlerBoundToURL', 'static-cache', 'StaleWhileRevalidate']:
    print(token, s.find(token))
PY
```

Red flags:
- `precacheAndRoute([{url:"index.html"...` or equivalent.
- `NavigationRoute(createHandlerBoundToURL("index.html"))`.
- app JS/CSS route chunks in runtime `StaleWhileRevalidate` caches.
- `/version.json` says `assetBaseUrl: /releases/{releaseId}`, but `/releases/{releaseId}/assets/<chunk>.js` returns 404 or SPA HTML.
- build metadata is `dev` / `unknown`, often because Docker `.dockerignore` excludes `.git` and no CI/Railway build env was passed into Vite/release generation.

## Durable fix pattern

Choose one consistent app-shell strategy:

### Preferred for finance/mobile PWA when old release assets are not retained

- Do not precache `index.html` as the navigation source.
- Do not use a SW navigation fallback that returns cached `index.html` for online launches.
- Make navigation network-first/fresh for online mode; use an explicit offline fallback only when the network is unavailable.
- Do not runtime-cache hashed app JS/CSS with broad `StaleWhileRevalidate`; hashed bundles should either be fetched from network/latest HTML or retained by releaseId.
- Keep `/sw.js`, `/manifest.webmanifest`, `/version.json`, `/registerSW.js` no-store/no-cache at CDN and origin.
- Register the SW with a build-versioned URL and `updateViaCache: 'none'`.

### If silent release / rollback requires old bundles

- Actually publish every release under `/releases/{releaseId}/...` or object storage.
- Verify every `version.json.assets[].url` returns 200 with the expected content type and hash.
- Configure nginx/CDN so `/releases/{releaseId}/version.json` returns JSON and `/releases/{releaseId}/assets/*.js` returns JS, never SPA fallback HTML.
- Keep active/rollback releases from garbage collection.

## Docker/CI build metadata pitfall

If `.dockerignore` excludes `.git`, `git rev-parse` inside `vite.config.ts` or release scripts will return `dev`/`unknown`. Prefer an environment-first build number:

1. `VITE_BUILD_NUMBER` / `RELEASE_BUILD_NUMBER`
2. `RAILWAY_DEPLOYMENT_ID` or CI run number
3. `RAILWAY_GIT_COMMIT_SHA` / `GITHUB_SHA` / `RELEASE_GIT_SHA`
4. local `git rev-parse` fallback only for developer builds

Fail CI or at least warn when production build metadata is `dev` or `unknown`.

## Regression tests / gates

- Build gate reads `dist/sw.js` and fails if it contains both `index.html` precache and a navigation fallback, unless release asset retention is explicitly enabled and verified.
- Build gate reads `dist/version.json`, then checks representative asset URLs against the deployed origin after deploy.
- Production smoke confirms entry JS returns 200 and content-type JavaScript.
- Browser smoke watches `error` and `unhandledrejection` for module script / ChunkLoadError before treating a blank screen as a UI loading issue.
