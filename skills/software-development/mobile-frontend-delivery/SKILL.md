---
name: mobile-frontend-delivery
description: "Use when delivering web/PWA/mobile-frontends across browser, installed PWA, and WebView/native-shell environments: cache invalidation, install prompts, safe areas, icon assets, hybrid packaging, splash behavior, and authenticated production screenshots."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [frontend, pwa, mobile, capacitor, icons, screenshots, delivery]
    related_skills: [baseline-ui, fixing-motion-performance, fixing-accessibility]
---

# Mobile Frontend Delivery

## Overview

This is the umbrella for shipping a web frontend as a reliable mobile experience: browser PWA, installed PWA, iOS/Android safe-area behavior, icon/splash assets, native WebView shells such as Capacitor, and production screenshot verification.

Use the root workflow for default decisions. Load support references only when the subproblem is specifically about that lane.

## When to Use

- PWA users see stale content, stale icons, or old JS/CSS after deploy
- Adding or debugging `beforeinstallprompt`, iOS Add to Home Screen guidance, or installed-mode detection
- `env(safe-area-inset-*)` returns 0, TabBar overlaps Home Indicator, or splash repeats in Android PWA
- Updating favicon, manifest, apple-touch-icon, Android/iOS app icons, maskable icons, or splash colors
- Packaging an existing SPA through Capacitor/Cordova/WebView wrappers
- Capturing authenticated mobile/desktop production screenshots as visual evidence

Don't use for:
- Pure web styling with no mobile/PWA delivery concerns
- Native-only React Native feature work with no WebView/PWA reuse path
- Generic browser automation unrelated to authenticated product evidence

## Routing by Subproblem

| Subproblem | Default section / support file |
|---|---|
| Stale deployed PWA content or icons | `references/pwa-cache-invalidation.md` |
| Backend-driven PWA release gates: prompt/block policy, SW update activation, CDN headers, multi-tab, offline, and old-bundle compatibility | `references/pwa-release-gate-audit.md` |
| Long-term silent release/OTA control plane: release list, candidate-table selection, rollback preview/audit, per-user manifest alignment | `references/silent-release-control-plane.md` |
| Implementing the client runtime side of silent release: manifest sync, local release state, safe-boundary activation, boot watchdog, chunk-error recovery, and runtime tests | `references/client-release-runtime-landing.md` |
| Real authenticated verification of a release-control plane: distinguish UI render, API dispatch, deployed backend endpoint availability, and write/read-back evidence | `references/release-control-plane-real-verification.md` |
| Railway-hosted H5/PWA silent release CI/CD: generate release manifest, retain versioned assets, register releases internally, and avoid container-overwrite chunk 404s | `references/railway-client-release-cicd.md` |
| Railway PWA PR merge → live URL verification, local preview against Railway backend, branch/environment alignment, Vite proxy vs direct API base, and asset-marker proof | `references/railway-pwa-production-verification.md` |
| Install prompt / iOS install guidance, including Android OEM launcher permission layers and HarmonyOS browsers that do not emit `beforeinstallprompt` | `references/pwa-install-prompt.md` |
| Safe area, notch, Home Indicator, splash anti-repeat | `references/pwa-safe-area-handling.md` |
| H5/browser is correct but installed iOS/Android PWA TabBar has inconsistent safe-area or too much bottom whitespace | `references/pwa-standalone-tab-safe-area-normalization.md` |
| UVISA C-end bottom TabBar must match prototype iOS Liquid Glass and avoid an extra solid strip | `references/uvisa-tabbar-liquid-glass-verification.md` |
| Android installed PWA bottom TabBar floats too high / `screen.height - innerHeight` safe-area over-offset | `references/android-pwa-safe-area-overoffset.md` |
| App icons, favicons, manifest icon sets, splash colors | `references/icon-asset-pipeline.md` |t - innerHeight` safe-area over-offset | `references/android-pwa-safe-area-overoffset.md` |
| App icons, favicons, manifest icon sets, splash colors | `references/icon-asset-pipeline.md` |
| Android installed PWA shows wrong launcher/home-screen icon despite correct manifest paths | `references/android-pwa-launcher-icon-regression.md` |
| Android / OnePlus / ColorOS reports install success but launches as a browser shortcut instead of standalone PWA | `references/android-pwa-webapk-vs-shortcut.md` |
| Verify whether a deployed origin satisfies Android Chrome PWA installability, including CDP `Page.getInstallabilityErrors`, `beforeinstallprompt`, and Chrome menu `Install` vs `Create shortcut` evidence | `references/android-chrome-pwa-installability-verification.md` |
| Capacitor / WebView native shell decision and pitfalls | `references/hybrid-app-packaging.md` |
| Android native Back should exit on Home/main tabs vs pop history | `references/native-back-button-terminal-tabs.md` |
| Web/PWA browser Back returns from Home/main tab into stale flow pages | `references/native-back-button-terminal-tabs.md` |
| iOS installed PWA left-edge swipe returns through deep flow pages and shows white/blank screen | `references/ios-pwa-native-back-swipe-conflict.md` |
| Authenticated production screenshots | `references/playwright-authenticated-screenshots.md` |
| Local frontend UI verification against an online backend via same-origin Vite proxy | `references/vite-proxy-online-backend.md` |

## Default Delivery Checklist

1. **Resolve target surface first**: browser tab, installed PWA, iOS Safari, Android Chrome, Capacitor iOS, Capacitor Android, or desktop.
2. **Verify deploy freshness**: package/app version, build number, cache-bust params, service worker activation, and runtime URL.
3. **Check installed-mode behavior**: standalone detection, safe-area variables, TabBar/header offsets, splash rules, and back-button behavior.
4. **Verify assets**: icon dimensions, manifest references, apple-touch-icon link, maskable safe area, `theme_color`, and `background_color`.
5. **Capture evidence**: screenshot the target viewport after authentication; don't rely on local dev unless the task explicitly asks for local-only proof.

## Key Patterns

### PWA cache/version strategy

- Treat `package.json.version` as the human release source.
- Inject a build number for service-worker cache names so each deploy invalidates Workbox runtime caches.
- Keep `skipWaiting` + `clientsClaim` on when immediate activation is desired.
- Remember iOS icon caching is OS-level: `?v=` and redeploys can prove the server is correct without changing the Home Screen icon immediately.

### Silent release / OTA control-plane pattern

When the task is long-term silent client hot-update / OTA governance, do **not** reduce the answer to SSR, a version-update toast, or a single "latest version" config. Treat it as a release control-plane problem:

- Backend decides the user/platform/channel-specific release manifest; client executes preload, safe-boundary activation, rollback, and reporting.
- Admin release list is the governance surface for the full lifecycle; ordinary version dropdowns are insufficient for release selection because operators must compare status, asset completeness, API contract, health, and disabled reasons.
- For publish/rollback/override actions, prefer a modal/drawer with a candidate Release table filtered by `usage` over a dropdown. Show `selectable`, `recommended`, and `disabledReason` from the backend.
- Rollback interaction should include target selection, backend preview/impact analysis, reason type + required reason text, target `releaseId` re-entry, privileged confirmation/GA if available, append-only audit with before/after, and a post-rollback observation panel.
- Historical release assets should be versioned by `releaseId` under CDN/object storage; CDN is a distribution/cache layer, not the source of truth. Keep rollback targets and still-active releases from being garbage-collected.
- When the test environment uses Railway Docker deploys, do not treat container image replacement as the release artifact store. Generate a business `release-manifest.json` during app build, retain `/releases/{releaseId}/...` assets via Railway Volume or external object storage, and have the app/CI register the release with the backend. See `references/railway-client-release-cicd.md`.

### Install UX

- Chrome/Edge can emit `beforeinstallprompt`; Safari iOS never does.
- Store the deferred event only after `e.preventDefault()` and consume it once.
- Treat `beforeinstallprompt.userChoice === 'accepted'` as “browser prompt accepted,” not final installation. Android OEM launchers such as OnePlus/ColorOS may still show a separate home-screen icon permission, and users can still end up with only a Chrome shortcut.
- For Android install copy, distinguish **generic user-facing guidance** from **OEM troubleshooting detail**:
  - Generic C-side banners/toasts, especially Pixel/Chrome fallback states, should stay concise: show the action as “查看步骤 / View steps”, then give browser-menu install guidance. Do **not** mention specific systems/OEMs, icon permissions, “desktop icon”, “shortcut”, OnePlus/ColorOS, or “Chrome creates shortcut” in the normal customer-facing copy.
  - Put OEM-specific launcher permission wording in troubleshooting/support docs or conditionally shown recovery flows only. If OnePlus/ColorOS then shows a system dialog worded “允许 Chrome 创建桌面快捷方式吗?”, the internal support guidance can explain that allowing it places the installed PWA icon. See `references/pwa-install-prompt.md`.
- For Android install copy, distinguish target families before writing user-visible guidance. Pixel/Google Chrome fallback copy should stay generic and action-led: show “查看步骤 / View steps”, tell the user to use the browser menu and choose the install option, and avoid concrete OEM/system/icon/shortcut wording such as “一加/ColorOS/鸿蒙/桌面图标/创建桌面快捷方式/浏览器快捷方式”. OEM-specific launcher-permission wording belongs only in an OEM-specific troubleshooting surface, not in the generic user toast. See `references/pwa-install-prompt.md`.
- Mark an app installed only from standalone-mode readback or a later runtime check after launch from the desktop icon; do not hide install UX solely because `userChoice` was accepted or because `appinstalled` fired. Treat `appinstalled` as “desktop entry created / install flow completed”, not proof of standalone WebAPK.
- When auditing an existing install implementation, inspect both the hook and its tests: tests may have encoded the wrong product model by expecting `isInstalled === true` after `userChoice.accepted` or `appinstalled`. Update the state model and regression tests together so intermediate Chromium signals remain distinct from `standaloneVerified`.
- For Android Chrome/Edge install UX, gate proactive install UI on the real `beforeinstallprompt` event. Do not show a timed “查看步骤 / View steps” fallback on mainstream Chrome just because no event arrived; keep it silent until browser readiness. Reserve timed manual guidance for Harmony/Huawei/OEM browsers that are known not to emit the event reliably. See `references/pwa-install-prompt.md`.
- Prompt after value commitment (login / first transaction / repeated visits), not on first paint.
- Provide explicit iOS Share → Add to Home Screen copy when no browser event exists.

### Safe-area and installed-mode layout

- `viewport-fit=cover` is required but not sufficient.
- Run standalone-only polyfills in `<head>` before CSS render if iOS reports zero safe-area values.
- Make `--safe-bottom` / `--safe-top` the single source of truth; avoid compounding constants across App, Screen, and TabBar.
- When H5/browser is correct but installed iOS/Android PWA spacing differs, derive platform/display-mode data attributes and feed TabBar through normalized app tokens (`--tabbar-bottom-gap`, `--tabbar-content-reserve`) rather than raw `env(safe-area-inset-bottom)`. See `references/pwa-standalone-tab-safe-area-normalization.md`.
- When browser H5 shows a solid strip under a floating Liquid Glass TabBar, debug placement separately from glass styling: browser mode usually wants `--tabbar-bottom-gap: 0px`, while standalone mode can opt into a bounded safe-area gap. See `references/browser-h5-tabbar-safe-area-strip.md`.
- On Android installed PWAs, do **not** synthesize iPhone-style bottom inset from `screen.height - window.innerHeight`; that delta can include system chrome and lift the TabBar too high. See `references/android-pwa-safe-area-overoffset.md`.
- On Android installed PWAs, do **not** synthesize iPhone-style bottom inset from `screen.height - window.innerHeight`; that delta can include system chrome and lift the TabBar too high. See `references/android-pwa-safe-area-overoffset.md`.

### Icon, splash, and installed app labels

- Map native source packages to web targets intentionally: iOS 180 for apple-touch-icon, Android playstore 512 for manifest/maskable, high-res source for favicons.
- Strip SVG shadows, filters, and decorative strokes from production favicon/mask assets.
- Verify dimensions and hashes after generation, especially when design packages contain multiple visual variants.
- When changing the installed PWA/home-screen app name, update every install-label surface together: web manifest `name` and `short_name`, `<meta name="application-name">`, `<meta name="apple-mobile-web-app-title">`, and any native-shell config such as Capacitor `appName`. Keep browser `<title>` and in-app brand copy unchanged unless the request explicitly asks for those too.
- Verify the built artifact, not only source: parse `dist/manifest.webmanifest` for `name`/`short_name`, inspect `dist/index.html` for app-name meta tags, and run the normal build gate before committing.

### Hybrid WebView packaging

- Prefer Capacitor when the existing SPA is clean, team is web-focused, and native requirements are moderate.
- Intercept native back button and route through the SPA router; otherwise system back/side-swipe can exit the app.
- For primary TabBar routes, explicitly decide terminal-route behavior. If Home/Card/Wealth/Me should behave like app roots, check the route predicate before `window.history.length` and call `CapacitorApp.exitApp()`; don't let Android Back resurrect prior flow pages just because browser history exists. See `references/native-back-button-terminal-tabs.md`.
- Plan native/security gaps explicitly: biometrics, push, SSL pinning, secure keyboard, jailbreak/root detection.

### Screenshot verification

- Use an existing Chrome profile when production auth is required.
- Run Playwright from a project with `@playwright/test` installed.
- Prefer `domcontentloaded` plus a bounded render wait over `networkidle` for production SPAs with polling/SSE.
- Always check whether the page redirected to login before treating screenshots as authenticated evidence.
- For local UI verification that must hit an online backend, use same-origin Vite proxy (`VITE_DEV_API_PROXY_TARGET=...` with runtime API base still `/api`) instead of setting `VITE_API_BASE` to the online URL. Start with `--strictPort`, kill stale listeners first, and verify both transformed `api.ts` and a proxied `/api/...` request. See `references/vite-proxy-online-backend.md`.
- For release-control screenshots, distinguish authenticated UI render from backend state evidence. Before claiming end-to-end success, probe the exact deployed API endpoints and confirm write/read-back; if the dev proxy points at a backend that lacks the new API, report the structured not-found response instead of mocking data. See `references/release-control-plane-real-verification.md`.

### Shared visual-component copy changes

When a mobile/PWA UI task asks to remove, rename, or hide text on a reusable visual component (for example a card face, account tile, banner, bottom action, or detail header), treat the component as the acceptance surface, not only the screenshot route:

1. Locate the reusable component and all route-level consumers before editing.
2. Add a negative regression test at the component level (`queryByText(...)` is null for removed copy) so every consumer inherits the behavior.
3. Keep adjacent non-target visuals intact (icons, status, amount, masked identifiers, spacing intent) unless the task explicitly asks to remove them.
4. Run both the component test and at least one representative route/detail-screen test that depends on the shared component, then run the build gate.
5. In closeout, state which consumers are covered by reuse and which still need live UI evidence before final Lark/production completion.

### Prototype restoration must include semantic routing

When restoring a mobile screen to match a prototype, do not stop at visual parity. Check every card/CTA against the product/PRD content source that defines its meaning:

1. Verify visible labels, links, and destination routes together. A card that visually says “AI assistant” but routes to human chat is a bug even if the screenshot looks correct.
2. If the product has split content sources (for example a full knowledge base vs a curated FAQ), map each UI entry to the right source and route: assistant/search surfaces should use the full knowledge base; FAQ surfaces should use curated FAQ entries.
3. Add route-level regression assertions for key links (`getByRole('link', { name: /.../ })` + `href`) alongside visual/text assertions.
4. Preserve intentionally requested deviations from the prototype (such as removing a contact channel) and state them explicitly in closeout so they are not mistaken for missed parity.

## Common Pitfalls

1. **Treating PWA as one cache layer.** Browser cache, service-worker cache, and OS icon cache have different invalidation paths.
2. **Changing `?v=` and assuming iOS Home Screen icon updates.** Server freshness and OS icon cache freshness are separate.
3. **Prompting install before engagement.** It harms UX and Chrome may suppress future prompts after dismissal.
4. **Stacking safe-area padding.** One global custom property should drive all components.
5. **Using dark/mockup icon sources for production web assets.** Verify the source visually before generating every target size.
6. **Calling WebView packaging “native complete.”** Security and platform affordances still need explicit bridge/plugin work.
7. **Using `networkidle` for screenshots.** Long-polling apps may never become idle.

## Verification Checklist

- [ ] Target platform and installed/browser mode are named explicitly.
- [ ] Cache/version/service-worker state was verified, not assumed.
- [ ] Icon dimensions, manifest references, and apple-touch-icon link were checked.
- [ ] Safe-area layout was checked on the relevant mobile viewport/device mode.
- [ ] Hybrid packaging decisions include native capability/security gaps.
- [ ] Visual proof is captured from the authenticated target surface when claiming UI delivery.
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.
