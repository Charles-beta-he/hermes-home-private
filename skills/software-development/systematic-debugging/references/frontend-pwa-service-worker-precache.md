# Frontend PWA Service Worker Precache Weak-Network Debugging

Use when a browser/H5/PWA app has slow first screen, persistent loading, or weak-network complaints and Network/Performance shows `/registerSW.js`, `/sw.js`, `workbox-*.js`, or large Service Worker activity near initial load.

## Applicability

- Vite/VitePWA/Workbox or similar generated Service Worker setup.
- Symptoms appear mostly on first visit, after deploy, or when caches are cold.
- User points at `/registerSW.js` or `/sw.js` as "large" or suspicious.

## Anti-conditions

- If the main application chunk itself is large and SW is disabled/not present, use normal bundle analysis instead.
- Do not conclude that `/sw.js` file size is the root cause before inspecting the Workbox precache manifest.
- Do not fix by only adding a fixed delay such as 3–5s; that can merely move bandwidth contention to the moment after the loading screen.

## Investigation path

1. Measure the visible SW files and the hidden precache payload:

```bash
for f in dist/registerSW.js dist/sw.js dist/workbox-*.js; do
  [ -f "$f" ] && printf '%s raw=%s gzip=%s\n' "$f" "$(wc -c < "$f")" "$(gzip -c "$f" | wc -c)"
done
```

2. Parse `dist/sw.js` for `precacheAndRoute` URLs and total their gzip sizes. Root cause is often a broad Workbox glob like:

```ts
globPatterns: ["**/*.{js,css,html,ico,png,svg}"]
```

This makes SW install precache route chunks, CSS, and large images at first registration, competing with first-screen JS/API/image requests on weak networks.

3. Compare top precache payload entries, not just `/sw.js` size. Typical smoking guns are large route chunks, hero images, invite/background images, finance assets, or all lazy chunks in the precache list.

4. Verify the HTML injection path:
   - `injectRegister: 'script'/'auto'` may inject `/registerSW.js` into `index.html`.
   - `devOptions.enabled: true` can accidentally mix dev SW behavior into local builds or diagnostics.
   - Duplicate manifest links (`/manifest.json` plus `/manifest.webmanifest`) are small but avoidable first-screen noise.

## Fix pattern

Prefer reducing first-install work over delaying it.

```ts
VitePWA({
  injectRegister: false,
  devOptions: { enabled: false },
  workbox: {
    // Keep first SW install tiny; runtimeCaching can still cache JS/CSS/images after use.
    globPatterns: ["index.html"],
    runtimeCaching: [/* existing runtime rules */],
  },
})
```

Then register SW after page load and browser idle, without a fixed timeout that forces contention during post-loading rendering:

```html
<script>
  (function () {
    if (!("serviceWorker" in navigator)) return;
    var registerServiceWorker = function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {});
    };
    window.addEventListener("load", function () {
      if ("requestIdleCallback" in window) {
        window.requestIdleCallback(registerServiceWorker);
      } else {
        window.setTimeout(registerServiceWorker, 0);
      }
    });
  })();
</script>
```

## Verification checklist

- `pnpm build` or project build passes.
- Build output says Workbox/PWA precache entry count and size dropped significantly.
- Parse `dist/sw.js`: precache contains only app shell/small manifest/icon assets, not route chunks or large images.
- `dist/index.html` no longer references `/registerSW.js` if manual idle registration is used.
- `dist/index.html` still references `/sw.js` through the deferred registration script.
- No fixed `timeout: 5000` or similar forced idle timeout remains unless explicitly required.
- Browser Cache Storage confirms the Workbox precache does not contain large route chunks/images.

## Why fixed delay is not enough

A fixed delay can improve the first few seconds, but it does not remove the root cause. On weak networks, 5 seconds later the user may still be in the loading-to-content transition or initial API/image fetches. SW install then starts precaching large files and can still steal bandwidth. The durable fix is to make SW install cheap and cache heavy resources at runtime after they are actually requested.
