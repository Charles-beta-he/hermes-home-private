# PWA Service Worker first-load performance debugging

Use when a browser app reports slow first screen on unstable networks and the network panel highlights `/registerSW.js`, `/sw.js`, `workbox-*.js`, or Service Worker installation.

## Applicability

- Generated Service Worker setups such as Workbox or VitePWA.
- Symptoms happen on cold load, first install, after deploy, or PWA launch.
- Network screenshot shows SW registration files, but their individual gzip size may be small.

## Anti-conditions

- Do not assume the project from similar filenames. Resolve the exact project/repo first, especially on machines with multiple apps and worktrees.
- Do not treat `/sw.js` byte size alone as root cause. The expensive work may be the precache manifest that `/sw.js` triggers after registration.
- Do not use a fixed delay such as 5 seconds as the primary fix. It can merely move the bandwidth spike to the moment after the loading screen when app data/images are still competing.

## Investigation steps

1. Resolve the target repo before editing.
   - Check project profile, repo instructions, or the user-provided project name.
   - Inspect git status in the resolved repo and preserve pre-existing changes.
   - If you edited the wrong repo, revert only your touched files before continuing.
2. Find PWA/SW sources.
   - Search for `VitePWA`, `vite-plugin-pwa`, `registerSW`, `serviceWorker.register`, `workbox`, `globPatterns`, `injectRegister`.
   - Distinguish plugin auto-injected registration from project-owned SW hooks that call `navigator.serviceWorker.register('/sw.js')`.
3. Quantify the generated SW behavior from a production build.
   - Run the project build.
   - Read build output for `precache N entries` and size.
   - Parse the generated SW for precache `url` entries and compute raw/gzip totals for the referenced files.
   - Rank the top precached assets. Large route chunks, vendor bundles, screenshots, brand images, and icons in the precache list are first-install bandwidth competitors.
4. Trace registration timing.
   - Locate where SW registration is triggered in the app tree.
   - If it runs during initial render/mount, it can compete with first-screen JS, CSS, images, and bootstrap API calls.
5. Identify root cause.
   - Common root cause: immediate SW registration plus broad Workbox precache patterns causing first-install caching of non-critical assets.
   - The fix point is the precache policy and registration timing, not just compression.

## Fix pattern

- Preserve the product's intended update semantics unless explicitly changing update behavior.
- Disable duplicate plugin auto-injection if the app owns SW registration: `injectRegister: false`.
- Shrink first-install precache to the app shell only, for example `globPatterns: ['index.html']`.
- Keep JS/CSS/images in runtime caching so they cache on demand after actual use.
- Register after `load` and then idle, not during initial render:
  - use `requestIdleCallback` when available;
  - fallback to `setTimeout(..., 0)` after load;
  - avoid a fixed 5s timeout as the primary mitigation.
- If multiple components can call the update hook, dedupe registration with a module-level registration promise.
- Ensure cleanup clears any scheduled registration and periodic update interval.

## Verification checklist

- Project build passes.
- Build output shows precache count/size reduced from broad MB-scale list to a small app-shell list.
- Generated HTML no longer references `/registerSW.js` if `injectRegister: false` is intended.
- Local preview/curl confirms first HTML does not directly pull `/sw.js` or `/registerSW.js`.
- Browser performance entries during first few seconds do not show SW registration files competing with first-screen resources.
- After idle, `navigator.serviceWorker.getRegistrations()` shows SW registration succeeds.
- Cache Storage precache contains only app-shell files; no large route chunks, vendor bundles, screenshots, or brand image galleries.
- Related update UI tests still pass and the intended update prompt/activation behavior is preserved.
