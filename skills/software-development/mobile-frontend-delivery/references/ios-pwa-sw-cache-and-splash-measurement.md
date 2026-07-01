# iOS PWA service-worker freshness and splash/first-screen measurement

Use when a mobile/PWA user reports that Android installs the latest app but iOS Home Screen still opens an old version, or when a branded loading/splash screen appears to make first-screen loading slow.

## Applicability

- Same web app behaves differently between Android installed PWA/WebAPK and iOS Home Screen PWA.
- iOS stays stale after Safari cache clearing or device restart.
- `/sw.js`, `/registerSW.js`, `manifest.webmanifest`, `version.json`, or the HTML entry may be cached by a CDN/proxy.
- A splash/loading overlay may be a fixed animation rather than a true data/resource loading state.

## Anti-conditions

- Do not treat this as an iOS device-cache problem until the live origin headers and HTML asset hashes are checked.
- Do not apply broad cache-busting to API/data endpoints; finance apps should keep API freshness boundaries separate from app-shell delivery.
- Do not judge latest code from the brand/domain alias if the user provides a Railway/Vercel/staging URL; measure the exact URL they named.

## Live-origin evidence to collect first

For the exact user-reported URL, fetch and compare:

- `/` headers and HTML asset references.
- `/sw.js` headers and body hash.
- `/registerSW.js` headers; expected state may be `404 no-store` if the app owns registration.
- `/manifest.webmanifest` headers and content type.
- `/version.json` headers and body; it should be JSON, not SPA fallback HTML.

Red flags:

- `/sw.js` or `/registerSW.js` returns `Cache-Control: public, max-age=...`, CDN `HIT`, or old `Last-Modified`.
- `/version.json` returns `text/html` and the SPA index body.
- HTML still references `/registerSW.js` after moving to manual registration.

## Durable fix pattern for stale iOS Home Screen SW

- Register the service worker with a build-versioned URL, e.g. `/sw.js?v=<BUILD_NUMBER>`.
- Pass `updateViaCache: 'none'` to `navigator.serviceWorker.register(...)` so the browser bypasses HTTP cache for the SW script/imports.
- Disable plugin auto-registration when the app has its own update/prompt hook (`injectRegister: false` for VitePWA).
- Keep first-install precache tiny; cache route chunks, screenshots, and brand images on demand rather than pulling them during first-screen load.
- Serve `/sw.js`, `/registerSW.js`, `/manifest.webmanifest`, and `/version.json` with explicit no-store/no-cache and CDN no-store headers (`CDN-Cache-Control`, `Cloudflare-CDN-Cache-Control`, `Surrogate-Control` where applicable).
- After deploy, purge CDN entries for `/`, `/index.html`, `/sw.js`, `/registerSW.js`, `/manifest.webmanifest`, and `/version.json`.

## Splash measurement model

Separate two metrics:

1. **Content ready / technical first screen**: login/home text and primary controls are rendered.
2. **User-visible ready**: the splash/loading overlay has disappeared and the user can see/interact with the first screen.

A fixed React-mounted splash adds its duration after JS has loaded. User-visible time often equals:

`resource load + JS execute + React mount + fixed splash duration + fade`

This can make a technically-ready screen feel slow. For example, if content is ready at 1.7s and the splash always runs ~5.2s after mount, the user-visible first screen is ~6.9s.

## Splash implementation pitfalls

- Do not use a re-read `sessionStorage` value as an effect dependency if the effect also writes that value and sets timers. A re-render can flip the dependency, run cleanup, and cancel the removal timer.
- Freeze the per-mount "should play splash" decision in a `useRef` or state initializer, then let timers complete.
- Prefer `minSplashMs` + `maxSplashMs` + `firstScreenReady` over a fixed full animation. Recommended shape:
  - minimum display: 600-900ms to avoid flash;
  - ready fade: 300-500ms after first-screen ready;
  - maximum display cap: about 1800-3000ms depending on product tolerance;
  - after cap, show page-level skeleton/progress for still-loading data instead of continuing a brand splash.

## Verification checklist

- Fetch exact target URL headers and HTML; record asset hashes and Last-Modified.
- Verify `/registerSW.js` is absent from HTML if registration is manual.
- Verify built JS contains the versioned SW URL and `updateViaCache` when that fix is expected.
- Verify Workbox precache count/size from built `sw.js`.
- Browser-measure both normal and throttled mobile network:
  - first paint / FCP;
  - DOMContentLoaded/load;
  - first app text/control present;
  - splash `is-out`, opacity below 0.5, and DOM removal.
- Report both content-ready and user-visible-ready times; do not collapse them into one "loading time".
