# PWA install prompt / `beforeinstallprompt` debugging

Use when comparing why one web app shows the browser native install affordance quickly while another waits, shows only custom UI, or never triggers.

## Core model

There are two separate paths:

1. Browser-default install affordance: the browser decides the app is installable and may show its own install UI/omnibox/menu/mini-infobar.
2. App-controlled prompt: app listens for `beforeinstallprompt`, calls `event.preventDefault()`, stores the event, then later calls `event.prompt()` inside a real user gesture.

If app code calls `event.preventDefault()` on `beforeinstallprompt`, it intentionally suppresses the browser default install prompt path. From that point, native confirmation appears only after the app calls cachedEvent.prompt(), normally from a user click/tap.

## Comparison workflow

1. Search both repos for:
   - `beforeinstallprompt`
   - `appinstalled`
   - `event.preventDefault()` near install handling
   - `prompt()` on a cached install event
   - `serviceWorker.register`, `registerSW`, `virtual:pwa-register`
   - `rel="manifest"`, `manifest.json`, `manifest.webmanifest`
   - Workbox/PWA plugin config (`VitePWA`, `@vue/cli-plugin-pwa`, `GenerateSW`, `InjectManifest`)
2. Read the manifest source and the actual HTML link path.
   - Static `<link rel="manifest" href="/manifest.json">` in initial HTML is the simplest/earliest discovery path.
   - Plugin-injected manifests are valid, but verify the built/served HTML actually contains the link and the URL returns valid JSON with correct MIME.
3. Compare install event handling.
   - No listener/no `preventDefault()` means the browser default install affordance can appear naturally.
   - Listener + `preventDefault()` means the app owns timing and must expose a click path to `prompt()`.
4. Compare Service Worker activation posture.
   - `skipWaiting: true` + `clientsClaim: true` is aggressive and may make SW readiness/client control settle faster.
   - `skipWaiting: false` + `clientsClaim: false` is safer for user-controlled updates but more conservative.
   - Do not change update policy just to improve install timing without weighing reload/update UX.
5. Compare manifest completeness and icon compatibility.
   - Required/common fields: `name`, `short_name`, `start_url`, `scope`, `display: standalone`, `theme_color`, `background_color`, PNG icons 192 and 512.
   - For OEM/mobile compatibility, prefer separate `purpose: "any"` and `purpose: "maskable"` icons at 192 and 512 rather than relying only on a combined `purpose: "any maskable"` entry.
6. Verify runtime, not just source.
   - Fetch served HTML and manifest from the actual acceptance URL/build preview.
   - Check manifest link, response status, content-type, icon fetches, SW registration status, and console Application/PWA installability diagnostics.
   - In Chrome, `beforeinstallprompt` timing is browser-owned; there is no fixed delay guaranteed by app code.

## Interpreting “fast native prompt”

If app A appears to show the native install prompt quickly and app B does not, check first whether A simply does not intercept `beforeinstallprompt`. A may be letting the browser show its default affordance, while B is deliberately suppressing it to show a custom banner/toast and call `prompt()` only after the user clicks.

This is usually a UX-policy difference, not a manifest performance optimization.

## Reporting template

- Install handling: default browser path vs app-controlled path.
- Manifest discovery: static HTML link vs plugin-injected/built link; served URL evidence.
- SW posture: aggressive activation vs prompt/update-safe activation.
- Manifest/icon compatibility: missing or nonstandard fields/icons.
- Launch container evidence: standalone PWA vs browser tab/Chrome shortcut. Use visible browser chrome, `display-mode`, and `appinstalled`/standalone evidence; do not assume a home-screen icon means standalone PWA.
- Auth/session-state evidence when the symptom crosses login boundaries: check whether the shortcut opens `manifest.start_url` or a saved current URL, then trace the app's auth bootstrap from persistent storage to route guards. If a user is mid-login/MFA/PIN and shortcut launch opens a protected page, root cause may be an auth-state-machine bug, not PWA config.
- Likely cause priority: rank behavior-level interception and auth persistence/route-guard evidence before lower-level config details.
- Safe options:
  1. Let browser default prompt show (remove/avoid `preventDefault()` for targeted platforms).
  2. Keep custom prompt but verify/strengthen manifest discovery.
  3. Add manual install guidance fallback for browsers that never emit `beforeinstallprompt`.
  4. If install/shortcut launch bypasses an unfinished login step, fix the authentication state model first: incomplete MFA/PIN/challenge states must not be persisted as fully authenticated route-guard state.

## Anti-conditions

- Do not claim `skipWaiting`/`clientsClaim` alone causes native install prompts; it is at most an indirect readiness factor.
- Do not treat `userChoice: accepted` as proof that the app icon was created; OEM launchers may still require a second shortcut permission flow. Prefer `appinstalled` or later `display-mode: standalone` as installed evidence.
- Do not convert a product requirement for user-controlled SW updates into aggressive auto-claim/auto-reload without explicit acceptance.
- Do not jump from "shortcut opens the wrong page" to a solution such as changing `start_url` before tracing route/auth state. If the user asks for root cause, prove the chain: install surface → launch URL/container → persistent storage → auth bootstrap → route guard → rendered page.
