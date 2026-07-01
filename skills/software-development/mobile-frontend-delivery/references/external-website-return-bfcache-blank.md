# External website return bfcache blank recovery

Use this when a mobile H5/PWA/WebView user taps an external website link from inside the app (for example Customer Service → Official Website) and then uses iOS/Android side-swipe or browser back to return, but the app shows a white/blank shell or stale snapshot.

## Applicability

- External link leaves the SPA/PWA to another origin, often via `target="_blank"` or a browser-owned navigation.
- Returning is handled by browser/WebView session history or bfcache (`pageshow` with `event.persisted === true`).
- The app otherwise reloads correctly if manually refreshed.
- Common on iOS installed PWA/Web Clip and embedded WebViews where bfcache restores a snapshot that React/router/runtime does not repaint.

## Anti-conditions

- If the blank appears while swiping between internal SPA routes, use `ios-pwa-native-back-swipe-conflict.md` first.
- If the issue is a missing route or 404 after return, fix router/deep-link handling instead of adding a reload guard.
- If the external page is meant to open inside the same SPA frame, do not mask that product decision with bfcache reloads.

## Root-cause check

Inspect the external link implementation. A plain link like this is often insufficient in installed/mobile runtimes:

```tsx
<a href={website} target="_blank" rel="noreferrer">...</a>
```

It gives the app no intent marker before leaving, so on bfcache return it cannot distinguish a risky external-return restore from ordinary internal pageshow events.

## Fix pattern

1. Add a tiny external-navigation module with a session-scoped marker and a once-only bfcache return guard:

```ts
export const EXTERNAL_NAVIGATION_RETURN_RELOAD_KEY = 'app:external-navigation:return-reload';

export function markExternalNavigationForReturnReload(): void {
  sessionStorage.setItem(EXTERNAL_NAVIGATION_RETURN_RELOAD_KEY, '1');
}

export function installExternalNavigationReturnGuard(): () => void {
  const onPageShow = (event: PageTransitionEvent) => {
    if (!event.persisted || sessionStorage.getItem(EXTERNAL_NAVIGATION_RETURN_RELOAD_KEY) !== '1') return;
    sessionStorage.removeItem(EXTERNAL_NAVIGATION_RETURN_RELOAD_KEY);
    window.location.reload();
  };
  window.addEventListener('pageshow', onPageShow);
  return () => window.removeEventListener('pageshow', onPageShow);
}
```

2. Install the guard once at app startup, before ordinary app runtime work.
3. Mark only links that intentionally leave the app:

```tsx
<a
  href={website}
  target="_blank"
  rel="noopener noreferrer external"
  onClick={markExternalNavigationForReturnReload}
>
  ...
</a>
```

4. Keep the marker session-scoped and remove it before reload so the app cannot enter a reload loop.

## Regression tests

- Unit test the guard:
  - marker is written by `markExternalNavigationForReturnReload()`;
  - `pageshow({ persisted: true })` reloads exactly once and clears the marker;
  - unmarked or `persisted: false` pageshow does not reload.
- Component test the external link:
  - clicking the official website link writes the marker;
  - link keeps `target="_blank"`;
  - link `rel` includes `noopener` and `noreferrer`.

## Verification

- Run the focused guard/component tests.
- Run production build/typecheck.
- Manual QA on the target device: open the app → customer service → official website → side-swipe/browser-back return; app should recover to a rendered shell instead of a blank snapshot.

## Pitfalls

- Do not reload on every `pageshow`; that breaks normal bfcache performance and can disrupt internal route returns.
- Do not store the marker in `localStorage`; it can survive unrelated sessions and cause surprising reloads.
- Do not treat this as a service-worker cache bug unless the served app stays blank after a hard reload.
