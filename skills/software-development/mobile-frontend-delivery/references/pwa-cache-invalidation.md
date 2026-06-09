---
name: pwa-cache-invalidation
description: "Coordinate PWA version bumps, cache-bust strategies, and service worker cache invalidation so deployed updates actually reach users. Use when iOS shows stale PWA icons, old JS/CSS persists after deploy, version checks don't detect new releases, or users see outdated content after Railway/Vercel/CF deploy."
triggers:
  - PWA cache bust
  - stale PWA icon
  - version bump PWA
  - cache invalidation service worker
  - iOS apple-touch-icon stale
  - old JS after deploy
  - workbox cache name version
  - skipWaiting clientsClaim
  - Vite PWA version strategy
---

# PWA Cache Invalidation

Coordinate package version, HTML cache-bust params, and SW cache names so
deployed updates actually reach end users — especially iOS where icon caching
is OS-level, not browser-level.

## The Three-Layer Problem

| Layer | What caches | Invalidation mechanism |
|---|---|---|
| **Browser HTTP cache** | JS, CSS, images | `Cache-Control` headers + query params (`?v=...`) |
| **Service Worker cache** | Precached assets, runtime fetches | Cache name change triggers re-fetch; `skipWaiting` + `clientsClaim` for immediate activation |
| **OS-level cache** (iOS) | `apple-touch-icon`, manifest icons | Only invalidated by: full Safari cache clear, PWA remove+re-add, or new iOS version |

Each layer requires a different strategy. Missing any one means stale content.

## Step 1: Single Version Source

**package.json.version** is the single source of truth. All other version
references derive from it.

```json
// package.json
{ "version": "1.0.1" }
```

Inject into build via Vite define:

```ts
// vite.config.ts
import pkg from './package.json' with { type: 'json' };

export default defineConfig({
  define: {
    'import.meta.env.VITE_APP_VERSION': JSON.stringify(pkg.version),
    // Build number: monotonically increasing, auto-invalidates all caches
    __BUILD_NUMBER__: JSON.stringify(Date.now()),
  },
});
```

`__BUILD_NUMBER__` changes every build → any cache name referencing it auto-invalidates.

## Step 2: index.html Cache-Bust Strategy

index.html is **not processed by Vite's transform pipeline** (it's the entry
point). So `import.meta.env` replacements don't work there.

**Best approach**: Use package.json version directly in query params:

```html
<!-- index.html — static HTML, not Vite-transformed -->
<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=1.0.1" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png?v=1.0.1" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=1.0.1" />
<link rel="mask-icon" href="/brand/icon-mask.svg?v=1.0.1" color="#1326FD" />
```

**Why not timestamps?** Timestamps change every dev-server restart, breaking
browser cache in development. Version only changes on actual releases.

**Why not build hash?** Build hash requires a Vite plugin to inject into
index.html at build time — more complexity for minimal benefit over version.

**Update flow**: When bumping version, update cache-bust params in index.html
to match. `npm version patch` → edit index.html → commit together.

## Step 3: Versioned SW Cache Names

Workbox/vite-plugin-pwa caches must include a version identifier so new
deployments auto-invalidate old caches:

```ts
// vite.config.ts — VitePWA config
VitePWA({
  workbox: {
    // Runtime image cache: versioned by build number
    runtimeCaching: [
      {
        urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
        handler: 'CacheFirst',
        options: {
          cacheName: `image-cache-${__BUILD_NUMBER__}`,  // ← auto-invalidates
          expiration: { maxEntries: 100, maxAgeSeconds: 30 * 24 * 60 * 60 },
        },
      },
      {
        urlPattern: /\.(?:js|css)$/,
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: `static-cache-${__BUILD_NUMBER__}`,  // ← auto-invalidates
          expiration: { maxEntries: 60, maxAgeSeconds: 24 * 60 * 60 },
        },
      },
    ],
    // Ensure new SW activates immediately
    skipWaiting: true,
    clientsClaim: true,
    // cleanupOutdatedCaches: true,  // default true in vite-plugin-pwa
  },
});
```

**Key**: `__BUILD_NUMBER__` is a Vite `define` constant → replaced at build
time → each build produces unique cache names → Workbox's `cleanupOutdatedCaches`
removes the old-named caches automatically.

## Step 4: iOS Icon Cache Strategy

iOS caches `apple-touch-icon` at the OS level. See also `pwa-safe-area-handling`
skill for the full user-side vs developer-side breakdown.

**Developer-side prevention** (what you control):

1. **Short `Cache-Control` during rollout**: Serve `apple-touch-icon.png` with
   `max-age=300` (5 min) during icon change rollout. Extend to `max-age=86400`
   after confirming users picked up the new icon.

2. **Version query param**: `?v=1.0.1` in `<link rel="apple-touch-icon">`
   forces HTTP cache miss (but NOT OS-level cache miss on iOS).

3. **SW precache**: If the SW precaches `apple-touch-icon.png`, a new SW
   activation replaces the cached version. Combined with `skipWaiting` +
   `clientsClaim`, this helps for installed PWAs.

**What does NOT help** (common misconceptions):

- Changing `?v=` alone — iOS OS cache ignores query params for icons
- Just redeploying — OS cache persists across deploys
- Clearing browser tab cache — doesn't touch icon cache

**What DOES help** (user action required):

- Settings → Safari → Clear History and Website Data
- Remove PWA from Home Screen → re-add
- Wait (days/weeks for OS garbage collection)

## Step 5: Version Check in App

If the app has a version-check mechanism (polling or websocket), ensure it
compares the right value:

```ts
// src/lib/version.ts
export const APP_VERSION = import.meta.env.VITE_APP_VERSION;  // from package.json

// Check against server
async function checkForUpdate() {
  const res = await fetch('/version.json', { cache: 'no-store' });
  const { version } = await res.json();
  if (version !== APP_VERSION) {
    // Trigger update notification
  }
}
```

The `/version.json` file should be generated at build time or served by the
backend with the deployed version. Use `cache: 'no-store'` to bypass HTTP cache.

## Update Notification UX

For the user-facing update notification pattern (Toast with action button, swipe-to-dismiss, persistent mode), see `references/uvisa-update-notification-ux.md`. This covers the UVISA-specific pattern of replacing sticky banners with action-capable Toast notifications for SW updates.

## Related Skills & References

- `pwa-install-prompt` — beforeinstallprompt, iOS fallback, install UX
- `references/uvisa-backend-i18n-architecture.md` — backend i18n 3-layer system (MessageSource + i18n_text DB + Locale chain)

## Pitfalls

1. **Manual date strings in cache-bust params**: `?v=20260529-v09` requires
   manual updates on every deploy and is error-prone. Prefer `?v=1.0.1` (package
   version) when available — single source of truth, updated via `npm version`.
   Some projects (e.g. UVISA) intentionally use date-based params as a deployment
   convention — respect the project's established pattern when it exists.

2. **Unversioned cache names**: `cacheName: 'image-cache'` or
   `cacheName: 'static-cache'` persist across deployments. Always interpolate
   `__BUILD_NUMBER__` or `__APP_VERSION__`.

3. **Missing `skipWaiting` + `clientsClaim`**: Without these, new SW waits for
   all tabs to close before activating. Users see stale content until they
   manually close and reopen.

4. **index.html not in Vite transform pipeline**: `import.meta.env` replacements
   don't apply to index.html. Use raw values or a Vite plugin
   (`transformIndexHtml` hook) if you need dynamic injection.

5. **Vite `define` and TypeScript**: When using `__BUILD_NUMBER__` in TS files,
   declare it to avoid TS errors:
   ```ts
   // src/vite-env.d.ts
   declare const __BUILD_NUMBER__: string;
   ```

6. **Manifest `version` field**: The `version` field in `manifest.json` is
   **not** a standard W3C field. It's a Chrome extension concept. Don't rely
   on it for cache invalidation. Some TypeScript types (e.g.,
   `ManifestOptions` in `vite-plugin-pwa`) may not include it — remove it
   from the manifest config to avoid TS errors.

7. **package-lock.json must be committed**: `npm version patch` modifies both
   `package.json` and `package-lock.json`. Both must be staged and committed.
   If `package-lock.json` is in `.gitignore`, the version bump won't propagate
   to CI/CD.

8. **Pre-existing test failures vs new ones**: When making cache/version
   changes, run tests before AND after. Use `git stash` to verify which
   failures are pre-existing vs introduced. Don't claim "0 new failures"
   without this check.

9. **Lost `data-*` attributes when extracting wrapper components**: When
   refactoring a component by extracting a wrapper (e.g. `SwipeableBanner`
   from `Toast`), any `data-*` attributes used as test selectors (like
   `data-tone`) must be explicitly passed through to the new wrapper.
   The outer div that carried the attribute becomes the wrapper's internal
   div — tests that query `[data-tone="error"]` will silently fail if the
   attribute isn't forwarded. Always check test files for attribute-based
   selectors after a component extraction refactor.
