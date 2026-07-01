# PWA update toast vs missing-chunk rescue

Applicability: installed PWA/H5 release update bugs where users ask whether opening the app should detect a new version and show an "Update now" toast, especially when a prior symptom was a white screen after deploy.

Anti-conditions:
- Do not use the toast path to explain a white screen that happens before React/Vue mounts; no app component can render a toast before the bundle starts.
- Do not claim every app open shows an update toast. It only appears when the Service Worker update lifecycle has a waiting/installed new worker and the current page is already controlled by an older worker.
- Do not treat backend/client-release manifest sync as the same surface as the Service Worker toast unless the current code explicitly wires it to the toast provider.

## Mental model

There are two separate update recovery lanes:

1. **SW update toast lane** — app bundle has booted.
   - On app open, register `/sw.js` (prefer versioned URL such as `/sw.js?v=<build>` and `updateViaCache: 'none'`).
   - Call `registration.update()` once on mount/open, and optionally on foreground/visibility plus a bounded interval.
   - If a new worker reaches `installed`/`waiting` while `navigator.serviceWorker.controller` exists, mark update available.
   - The UI can show a prompt/toast with an action such as "立即更新".
   - The action should post `SKIP_WAITING` only to the waiting/installed worker and reload only the tab that the user explicitly initiated.
   - Guard against repeated prompts in one browser session if product wants one notification per session.

2. **Missing-old-chunk rescue lane** — app bundle has not booted.
   - An old SW or stale HTML references an old hashed `/assets/*.js` that the current deploy no longer serves.
   - React/Vue never mounts, so no `UpdateBanner`/toast can appear.
   - The server must return executable rescue JavaScript for missing old chunk requests, not HTML fallback: unregister SWs, clear CacheStorage, then reload with a cache-busting query.

## Debugging checklist

- Inspect the built/deployed `sw.js` for `index.html`, `createHandlerBoundToURL`, `NavigationRoute`, `static-cache`, or `StaleWhileRevalidate`.
- Inspect source hook logic for: registration URL, `updateViaCache`, mount/open `reg.update()`, foreground checks, waiting-worker detection, and current-tab-only reload guard.
- Inspect the UI surface that consumes `isUpdateAvailable`; confirm whether it uses `sessionStorage`/in-memory guards and whether the action can become a no-op when `registration.waiting` is empty.
- Probe a definitely missing old chunk URL like `/assets/__missing_old_chunk__.js`; it should return `application/javascript` rescue code, not SPA HTML.
- Keep client-release manifest/runtime sync separate in the report: it can activate a release at safe boundaries, but it is not the SW update toast unless wired to that UI.

## Reporting wording

Use precise wording:

"Opening the app checks for a Service Worker update. If the app is already controlled by an old worker and a new worker becomes waiting/installed, the app can show the update toast. If the app is white before the bundle boots, the toast cannot help; missing-chunk rescue is the relevant path."
