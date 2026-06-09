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
| Install prompt / iOS install guidance | `references/pwa-install-prompt.md` |
| Safe area, notch, Home Indicator, splash anti-repeat | `references/pwa-safe-area-handling.md` |
| Android installed PWA bottom TabBar floats too high / `screen.height - innerHeight` safe-area over-offset | `references/android-pwa-safe-area-overoffset.md` |
| App icons, favicons, manifest icon sets, splash colors | `references/icon-asset-pipeline.md` |
| Android installed PWA shows wrong launcher/home-screen icon despite correct manifest paths | `references/android-pwa-launcher-icon-regression.md` |
| Capacitor / WebView native shell decision and pitfalls | `references/hybrid-app-packaging.md` |
| Android native Back should exit on Home/main tabs vs pop history | `references/native-back-button-terminal-tabs.md` |
| Web/PWA browser Back returns from Home/main tab into stale flow pages | `references/native-back-button-terminal-tabs.md` |
| Authenticated production screenshots | `references/playwright-authenticated-screenshots.md` |

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

### Install UX

- Chrome/Edge can emit `beforeinstallprompt`; Safari iOS never does.
- Store the deferred event only after `e.preventDefault()` and consume it once.
- Prompt after value commitment (login / first transaction / repeated visits), not on first paint.
- Provide explicit iOS Share → Add to Home Screen copy when no browser event exists.

### Safe-area and installed-mode layout

- `viewport-fit=cover` is required but not sufficient.
- Run standalone-only polyfills in `<head>` before CSS render if iOS reports zero safe-area values.
- Make `--safe-bottom` / `--safe-top` the single source of truth; avoid compounding constants across App, Screen, and TabBar.
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

### Shared visual-component copy changes

When a mobile/PWA UI task asks to remove, rename, or hide text on a reusable visual component (for example a card face, account tile, banner, bottom action, or detail header), treat the component as the acceptance surface, not only the screenshot route:

1. Locate the reusable component and all route-level consumers before editing.
2. Add a negative regression test at the component level (`queryByText(...)` is null for removed copy) so every consumer inherits the behavior.
3. Keep adjacent non-target visuals intact (icons, status, amount, masked identifiers, spacing intent) unless the task explicitly asks to remove them.
4. Run both the component test and at least one representative route/detail-screen test that depends on the shared component, then run the build gate.
5. In closeout, state which consumers are covered by reuse and which still need live UI evidence before final Lark/production completion.

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
