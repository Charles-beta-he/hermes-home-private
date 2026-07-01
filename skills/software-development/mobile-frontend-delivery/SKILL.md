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

When a mobile route depends on API/session/native data, blank-page prevention is part of delivery: verify that the initial state matches a visible template branch, that loading/error/empty fallback states render, and that slow or unavailable APIs cannot leave the screen permanently blank. See `references/api-dependent-mobile-page-fallback.md`.

When a login/auth or short mobile form reports page-upward movement on input focus, classify the interaction model before applying a requested tweak. Prefer the class-level pattern in `references/mobile-pwa-keyboard-focus-layout.md`: no global keyboard reserve/scrollBy; ordinary flows keep safe-area bounds; short auth screens can keep default full-height + bottom CTA and reveal an inline CTA with CSS `group-focus-within`; full-screen composer shells shrink internal content with `visualViewport`.

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

The detailed mobile-frontend routing-by-subproblem map was moved to `references/routing-by-subproblem.md`.

Load it when classifying whether the task is WebView/H5, RN/native shell, auth, storage, routing, visual parity, performance, or release delivery.

Minimum in-root rule: choose the narrowest target layer and preserve existing app behavior before editing.

## Default Delivery Checklist

1. **Resolve target surface first**: browser tab, installed PWA, iOS Safari, Android Chrome, Capacitor iOS, Capacitor Android, or desktop.
2. **Verify deploy freshness**: package/app version, build number, cache-bust params, service worker activation, and runtime URL.
3. **Check installed-mode behavior**: standalone detection, safe-area variables, TabBar/header offsets, splash rules, and back-button behavior.
4. **Verify assets**: icon dimensions, manifest references, apple-touch-icon link, maskable safe area, `theme_color`, and `background_color`.
5. **Capture evidence**: screenshot the target viewport after authentication; don't rely on local dev unless the task explicitly asks for local-only proof.

## Key Patterns

Detailed mobile-frontend implementation patterns were moved to `references/key-patterns.md`.

Load it for concrete coding patterns, browser/device verification, H5/RN interoperability, adapter seams, or production delivery checklists.

Minimum in-root rule: validate on a real browser/device or explicit local equivalent; DOM-only or toast-only evidence is not UI acceptance.

## Mobile Hybrid Avatar UX

When building mobile avatar/control-room shells where implementation has online/server, device/cache fallback, readback queues, or voice/TTS lanes, keep those distinctions out of the main user experience. Present one avatar experience with context, tasks, readback, confirmation, and voice as a fast lane. Put explanations and diagnostics on secondary surfaces or short toasts instead of filling the interaction layer. See `references/mobile-hybrid-avatar-unified-ux-and-voice.md`.

Before claiming mobile/RN usability, run a UI optimization pass, not only functional routing/tests. A page that exposes Monorepo, authority-chain, dry-run, device IDs, internal alpha, or other engineering diagnostics as the default user surface is a UX failure even if every button routes correctly. First make the primary surface user-facing (status, next useful action, clear action cards, truthful receipts), then move diagnostics behind Settings/诊断 or a secondary detail affordance, and verify with simulator screenshots plus regression tests that the engineering copy is absent by default.

When a subfunction has a mature professional-software analogue, use that analogue as the interaction authority before inventing a bespoke AI-app pattern. Examples: voice input should learn from professional recording/metering software; release readiness from CI/CD/SRE dashboards; risk confirmation from payment/trading/deploy confirmations; long-running task progress from GitHub Actions/Vercel logs. Absorb the professional mechanism (signals, state, thresholds, feedback timing, failure modes) and translate it into the avatar's product language instead of copying the surface skin or exposing expert jargon.

For mobile voice recognition, do not start from a new mobile-only ASR design if an existing desktop/server transcription stack already has provider selection, upload guards, timeout, and silence filtering. Migrate the proven server-side rules into a Gateway-backed mobile path: subscription ASR is primary, OS speech is a fast/fallback lane, embedded local ASR is fallback/draft only, and post-ASR fluency compensation must preserve action/risk keywords before confirmation. See `references/react-native-voice-asr-gateway-fallback.md`.

When the avatar visual needs to evolve from a static/flat sphere into a voice-reactive particle/electric orb, use `references/react-native-avatar-reanimated-particles.md`: Reanimated is the low-risk first production slice for RN View-layer motion; Skia is the later shader/canvas path. If the user expects professional recording-software behavior, do not stop at active/listening state animation: use `references/react-native-voice-reactive-particle-orb-final.md` for native mic metering, multi-band/peak/transient audio profile, noise gate, renderer mapping, and real-device mic verification. Verify with Jest, lint, pod install/Release build, screenshot proof, and label physical microphone testing as a separate hardware boundary when only simulator evidence exists. If the user expects professional recording-software behavior, do not stop at state-driven `listening` animation; wire live audio RMS/peak (and later FFT bands) into the renderer, using `references/react-native-voice-reactive-webgl-orb.md`.

When the user asks for “1:1” restoration/absorption from a product reference, do not treat this as a loose style prompt. Lock one master reference and one screen, produce a screen map, move non-reference engineering surfaces to secondary details, and verify by screenshot diff/readback. Then audit the product loop, not just the pixels: every visible control must either perform the reference-equivalent action or route to the secondary surface that owns it; every secondary surface needs a return path; moved controls such as text composer, diagnostics, reset, or quick actions need regression tests proving they are still reachable. When the reference screen includes voice/avatar interaction, close the native permission/bridge/ledger path too: transcript must re-enter the same intent pipeline with provenance metadata, approved voice playback must not be replaced by a generic voice, and privacy/side-effect authority boundaries should be reported as the single manual decision point rather than disguised as remaining optimizations. See `references/mobile-reference-1to1-absorption.md` and `references/mobile-avatar-1to1-voice-closure.md`.

## Common Pitfalls

Detailed mobile-frontend pitfalls were moved to `references/common-pitfalls.md`.

Load it when UI acceptance, H5 regressions, auth/state-machine risk, screenshot parity, or design-tool-to-runtime transfer is involved.

Keyboard-focus pitfall: if a user proposes a specific layout tweak for PWA keyboard movement, do not blindly apply it. First classify the page model and choose the best class-level interaction. For short auth/login screens, prefer `group-focus-within` dual-CTA swaps and no React focus state, blur timers, global keyboard reserve, or JS scrollBy; see `references/mobile-pwa-keyboard-focus-layout.md` and `references/pwa-login-keyboard-cta.md`.

Minimum in-root rule: do not delete features/fields/routes and do not claim UI completion without real visual/runtime evidence.

## Stitch SDK / design-tool → mobile 1:1 screens

For Stitch work, prefer the SDK path and treat the MCP route as deprecated unless the user explicitly re-authorizes it for a legacy task. Follow `references/stitch-sdk-mobile-design-sync.md` for SDK credential handling, artifact download, explicit screen IDs, and verification. For pixel-parity reconstruction, keep the high-resolution screenshot / product-logic separation / simulator screenshot proof principles from `references/stitch-mcp-to-rn-1to1.md`, but acquire the source artifacts through the SDK or approved export path rather than MCP.

## Enterprise-ready Stitch/PWA delivery guard

When converting a Stitch/mobile design into a PWA/RN product surface, do not stop at design parity, no-op gates, or a backlog list if the user asked for enterprise-grade delivery or full closure. Advance every safe local slice before stopping: replace dead navigation with bounded real anchors/routes, make status chips runtime-backed, remove demo/mock/fixture wording from product copy, and update PRD/workflow/config so the remaining backlog contains only true unresolved boundaries.

Keep test fixtures isolated. It is acceptable for Playwright to mock camera, Controller, WebSocket, or model responses, but product UI must not leak `mock`, `demo`, `sample`, `stub`, raw `mode=...`, or `evidence=...` debug strings. Convert technical states into operator-facing labels such as “模型待接入”, “证据 3”, and “置信 87%”, while keeping the degraded/model boundary visible in diagnostics. Add negative UI tests that assert fixture/debug strings are absent from user-facing advice.

When a PWA/mobile product has a vision node, distinguish adapter architecture from real model availability. Add or run a read-only inventory/readiness path that reports implemented adapters, available non-stub adapters, and unavailable dependencies/model weights. Surface Controller `/health/ready` or equivalent in diagnostics. Do not claim real recognition until a non-stub adapter is available and verified by runtime readback plus an analysis smoke; otherwise keep the fail-visible operator label.

For bottom navigation generated by a design tool, avoid leaving `href="#"` placeholders. If full multi-page routing is out of scope, the minimum safe slice depends on the user’s delivery bar:

- If the task is only to remove dead links, map the nav to real in-page operator anchors and document the boundary.
- If the user asks for project-level authorization, enterprise-grade delivery, or “fill all product surfaces,” promote the nav into local product panels inside the PWA shell (for example overview, voice, diagnostics, safety). Use `data-tab-target`, `hidden`, and `aria-current`; add runtime tab switching, panel-specific content, visual/interaction assertions, and screenshots for each panel. See `references/stitch-pwa-product-tabs-vision-readiness.md`.
- If one panel is already optimized and the user says other pages also need `极限` / `项目级别全盘推进`, audit every sibling panel and close them as product surfaces too: panel-specific hero/status, concise command/checklist cards, conclusion-first diagnostics, duplicated runtime state kept in sync, tests and screenshots for every tab. For true project-level closure, productize the screenshot loop as a reusable gate (for example `make product-screenshots`) that regenerates every panel and fails on horizontal overflow or missing bottom navigation, then add it to workflow/config/tests/docs. See `references/stitch-pwa-all-panel-ux-closeout.md`.

### Stitch SDK screen ordering and simulator discoverability

When syncing Stitch SDK artifacts into RN/mobile surfaces, do not treat the first screen returned by `list_screens` as the canonical latest screen unless the API response exposes and you verify a reliable chronological field. Lock explicit screen IDs for each accepted surface, store the artifact/manifest, map each screen to a distinct runtime surface, and verify with route tests plus a simulator/device screenshot. If the app technically has multiple pages but the home screen shows only unlabeled abstract icons, treat that as a UX discoverability bug: add visible labels for primary destinations and rerun the simulator install/screenshot check.

- Notification centers with incremental sync, read-state mutations, card-footer time semantics, or foreground/background polling/SSE coordination should use `references/notification-sync-time-and-lifecycle.md`: update existing items in place, use raw `createdAt`/delivery time for card display and ordering, keep `occurredAt` for business event detail, pause realtime/polling in background, and guard heartbeat/activity timers.

- [ ] Target platform and installed/browser mode are named explicitly.
- [ ] Cache/version/service-worker state was verified, not assumed.
- [ ] Icon dimensions, manifest references, and apple-touch-icon link were checked.
- [ ] Safe-area layout was checked on the relevant mobile viewport/device mode.
- [ ] Hybrid packaging decisions include native capability/security gaps.
- [ ] Visual proof is captured from the authenticated target surface when claiming UI delivery.
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.

## Verification Checklist

- [ ] Target surface was identified: browser tab, installed PWA, iOS Safari, Android Chrome, WebView shell, or desktop.
- [ ] Build/deploy freshness and cache/service-worker behavior were verified when relevant.
- [ ] Loading/error/empty states prevent blank screens for API/session-dependent pages.
- [ ] UI acceptance used real screenshot/visual/runtime evidence, not DOM-only or toast-only proof.
- [ ] Existing routes, fields, H5 behavior, auth state machines, and secondary diagnostics remained reachable.
