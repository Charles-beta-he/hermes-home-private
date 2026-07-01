# UVISA PWA SW update routing: main-tab auto apply, non-main toast

Applicability:
- Mobile/PWA SPA update flows where a new Service Worker is discovered via `isUpdateAvailable`.
- Apps with business bottom navigation/main sections that are safe activation boundaries, such as U-VISA `Home/Card/Wealth/Me`.
- Use when the goal is: installed PWA should update without reinstall or manual About-screen cache clearing, while avoiding surprise reloads during sensitive flows.

Anti-conditions:
- Do not use this as a general browser-tab synchronization recipe. Browser tabs/page clients are different from in-app bottom navigation tabs.
- Do not treat route-level lazy loading/code splitting as the fix for stale-version safety. Lazy loading can increase old-chunk `ChunkLoadError` risk unless old release assets are retained.
- Do not rely on an About-screen “clear cache/unregister SW” button as the normal release path; keep it as support/failure recovery only.

## Decision pattern

1. Treat `SW isUpdateAvailable` as the single user-facing static-bundle update signal.
2. Classify routes:
   - Main safe boundaries: `/`, `/home`, `/card`, `/wealth`, `/me`.
   - Non-main/sensitive or workflow routes: payout, remit, exchange, topup, payment, confirm/preview, PIN/password/KYC, legal/about/settings, and other flow screens.
3. If `isUpdateAvailable` becomes true on a main safe boundary, call `updateApp()` immediately so the current PWA page activates the waiting SW and reloads itself.
4. If `isUpdateAvailable` becomes true on a non-main route, show an update toast/sheet with an immediate update action instead of auto-reloading. The user can refresh now, but the app does not interrupt an in-progress flow unexpectedly.
5. When the user later navigates back to a main boundary and the update is still available, auto-apply there.

## Browser tab vs app bottom tab vocabulary

- Browser tab / SW client / page instance: a separate document with its own JS runtime, React state, refs, and Service Worker controller relationship.
- App bottom tab / main section: an in-app route such as Home/Card/Wealth/Me inside the same page instance.

Do not conflate the two. “Only reload current tab” usually means the current browser page instance. “Home/Card/Wealth/Me auto-upgrade” means current page instance reloads when its in-app route is a safe main section.

## Regression coverage checklist

Add focused tests around the component or hook that consumes `useServiceWorkerUpdate()`:

- Main route example `/home` with `isUpdateAvailable=true` calls `updateApp()` and does not render the toast.
- Non-main route example `/payout/usdt` with `isUpdateAvailable=true` renders the update toast and does not call `updateApp()` until the action is clicked.
- Existing “only once per session” toast behavior remains scoped to the non-main toast path.

## Release safety notes

This routing reduces stale-version exposure but does not remove the need for release hygiene:

- Retain old hashed assets for at least one release window; otherwise old page instances can still hit chunk/CSS/image 404s.
- Keep backend APIs compatible with at least one old frontend window, especially while users are in sensitive flows.
- Add explicit `reg.waiting` detection after SW registration if the code only listens to `updatefound`; an already-waiting worker may otherwise be missed.
- Consider BroadcastChannel/storage sync only for browser-tab/page-client awareness; do not remote-force reload other page instances during sensitive flows.
