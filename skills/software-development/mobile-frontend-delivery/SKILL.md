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

When a Vite mobile web/PWA page is visible but API-backed sections are blank in local dev or `vite preview`, inspect the frontend API base URL against the exact opened host/port, then verify both `server.proxy` and `preview.proxy`. Prefer same-origin `/api` for dev/local-preview and prove the exact reported URL renders real API rows. See `references/vite-dev-preview-proxy-api-base.md`.

When local H5 parity needs to be advanced beyond a visual fix, package the verification as a mobile smoke evidence slice: exact preview URL, `/api` readback, 375/390/414 viewport screenshots or geometry checks, bottom TabBar route clicks, anonymous-vs-auth boundaries, banner redirect fixture coverage, and bounded wording such as `local H5 preview runtime-verified` rather than `certified`. See `references/h5-preview-parity-smoke-evidence.md`.

When Chrome/CDP mobile smoke scripts evaluate an empty DOM or strange syntax/runtime errors despite the app being visible, verify the selected DevTools target before debugging product code. Chrome can expose extension/background targets; select the page by expected app URL/origin, then assert `location.href` before DOM checks. See `references/chrome-cdp-mobile-smoke-target-selection.md`.

When the user asks for `certified` / `全量验收完成` on an H5 parity effort, promote scattered smoke evidence into a deterministic loop-engineering packet: explicit certification levels, a project-local command such as `npm run certify:h5:local`, tracked-evidence checks via `git ls-files`, scoped lint/build, JSON evidence parsing, latest+timestamped reports, and independent verifier amend resolution before L3 wording. See `references/h5-certification-loop-engineering.md`.

When the user asks for a web/H5 product to be 1:1 with an existing native app, do not use an issue tracker as the execution plan. Build a native-reference parity plan first: reference hierarchy, route/screen map, web-specific adjustments, red-line state/API fields, branch strategy, and evidence gates. Then ship small slices with code diff + targeted lint + build + browser screenshot/readback before merging to the develop-equivalent branch. See `references/native-app-parity-h5-development.md`. For native route-contract preservation and raw Chrome/CDP mobile smoke target-selection pitfalls, also see `references/h5-native-parity-route-and-cdp-smoke.md`; keep that pattern generic and put project-specific paths/IDs/evidence in the project profile or SSOT.

When advancing transaction-like H5 screens such as spot trading/orderbook/balance surfaces under a local-only safe-slice mandate, use `references/h5-trading-control-semantics-safe-slices.md`: convert narrow non-semantic controls to buttons/labels without changing business behavior, verify mobile CDP DOM+behavior+negative side-effect evidence, store project-specific evidence in SSOT/profile, and stop at a DecisionPacket when the next useful slice requires auth, fixtures, real mutations, push/deploy, device, or PWA-install authority.

When a mobile H5 header combines menu/search with right-edge actions and screenshots show message/customer/scan or similar controls missing, do not rely on DOM presence or `--window-size` alone. Use `references/h5-header-right-edge-viewport-proof.md`: inspect DOM plus actual viewport metrics, pixel-probe the right header band, prefer page-scoped layout fixes over shared Header rewrites, and verify 375/390/414px screenshots before calling the visual slice closed.

When a mobile image upload flow fails specifically for iOS camera images, check HEIC/HEIF end-to-end rather than treating it as a generic network issue: frontend `accept`, client MIME allowlist, multipart field name, backend MIME/magic-byte/extension gates, and object-storage 5xx behavior. Use `references/ios-camera-heic-upload.md`.

When an iOS Camera/Photo Library upload from a chat/composer/support surface reports generic “send image failed” or “network error”, trace the full file path rather than assuming FormData is broken: check multipart headers, iOS HEIC/HEIF frontend + backend allowlists, backend magic-byte validation, OSS/S3 availability, safe same-origin fallback URLs, and rendering sanitizer rules. See `references/ios-camera-image-upload-chat.md`.

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

Keyboard-focus history/rollback pitfall: when a mobile money/transfer/remit page reports focus-induced page push or displaced icons/cards, inspect page history and scroll-owner/keyboard-shell changes before editing. If the user says “先别改/先整理”, produce the scoped history first; rollback in an isolated worktree/branch and restore only affected screen, keyboard/focus shell, and test files. See `references/mobile-keyboard-focus-rollback-scope.md`.

Minimum in-root rule: do not delete features/fields/routes and do not claim UI completion without real visual/runtime evidence.

## Stitch SDK / design-tool → mobile 1:1 screens

For Stitch work, prefer the SDK path and treat the MCP route as deprecated unless the user explicitly re-authorizes it for a legacy task. Follow `references/stitch-sdk-mobile-design-sync.md` for SDK credential handling, artifact download, explicit screen IDs, and verification. For pixel-parity reconstruction, keep the high-resolution screenshot / product-logic separation / simulator screenshot proof principles from `references/stitch-mcp-to-rn-1to1.md`, but acquire the source artifacts through the SDK or approved export path rather than MCP.

## Enterprise-ready Stitch/PWA delivery guard

When converting a Stitch/mobile design into a PWA/RN product surface, do not stop at design parity, no-op gates, or a backlog list if the user asked for enterprise-grade delivery or full closure. Advance every safe local slice before stopping: replace dead navigation with bounded real anchors/routes, make status chips runtime-backed, remove demo/mock/fixture wording from product copy, and update PRD/workflow/config so the remaining backlog contains only true unresolved boundaries.

Keep test fixtures isolated. It is acceptable for Playwright to mock camera, Controller, WebSocket, or model responses, but product UI must not leak `mock`, `demo`, `sample`, `stub`, raw `mode=...`, or `evidence=...` debug strings. Convert technical states into operator-facing labels such as “模型待接入”, “证据 3”, and “置信 87%”, while keeping the degraded/model boundary visible in diagnostics. Add negative UI tests that assert fixture/debug strings are absent from user-facing advice.

When a PWA/mobile product has a vision node, distinguish adapter architecture from real model availability. Add or run a read-only inventory/readiness path that reports implemented adapters, available non-stub adapters, and unavailable dependencies/model weights. Surface Controller `/health/ready` or equivalent in diagnostics. Do not claim real recognition until a non-stub adapter is available and verified by runtime readback plus an analysis smoke; otherwise keep the fail-visible operator label.

When promoting an agent/control-plane packet or CLI projection into a dashboard, advance safe local UI/API slices instead of stopping at phase labels: expose an authenticated read-only status endpoint, add a route/nav page with cards plus evidence/authority/proposal/device detail panels, and keep all execution/lifecycle/external/secret/payment/device actions visibly false or proposal-only. Use `references/agent-os-readonly-control-room-dashboard.md` for the full pattern and verification checklist.

For bottom navigation generated by a design tool, avoid leaving `href="#"` placeholders. If full multi-page routing is out of scope, the minimum safe slice depends on the user’s delivery bar:

- If the task is only to remove dead links, map the nav to real in-page operator anchors and document the boundary.
- If the user asks for project-level authorization, enterprise-grade delivery, or “fill all product surfaces,” promote the nav into local product panels inside the PWA shell (for example overview, voice, diagnostics, safety). Use `data-tab-target`, `hidden`, and `aria-current`; add runtime tab switching, panel-specific content, visual/interaction assertions, and screenshots for each panel. See `references/stitch-pwa-product-tabs-vision-readiness.md`.
- If one panel is already optimized and the user says other pages also need `极限` / `项目级别全盘推进`, audit every sibling panel and close them as product surfaces too: panel-specific hero/status, concise command/checklist cards, conclusion-first diagnostics, duplicated runtime state kept in sync, tests and screenshots for every tab. For true project-level closure, productize the screenshot loop as a reusable gate (for example `make product-screenshots`) that regenerates every panel and fails on horizontal overflow or missing bottom navigation, then add it to workflow/config/tests/docs. See `references/stitch-pwa-all-panel-ux-closeout.md`.

### Stitch SDK screen ordering and simulator discoverability

When syncing Stitch SDK artifacts into RN/mobile surfaces, do not treat the first screen returned by `list_screens` as the canonical latest screen unless the API response exposes and you verify a reliable chronological field. Lock explicit screen IDs for each accepted surface, store the artifact/manifest, map each screen to a distinct runtime surface, and verify with route tests plus a simulator/device screenshot. If the app technically has multiple pages but the home screen shows only unlabeled abstract icons, treat that as a UX discoverability bug: add visible labels for primary destinations and rerun the simulator install/screenshot check.

- Notification centers with incremental sync, read-state mutations, card-footer time semantics, or foreground/background polling/SSE coordination should use `references/notification-sync-time-and-lifecycle.md`: update existing items in place, use raw `createdAt`/delivery time for card display and ordering, keep `occurredAt` for business event detail, pause realtime/polling in background, and guard heartbeat/activity timers.

- PWA/background push feasibility audits should use `references/pwa-background-push-feasibility.md`: separate in-app notification truth source, foreground SSE/polling invalidation, and OS-level background push; verify permission/token/subscription/SW/provider evidence before claiming push support; report Android/Desktop PWA, iOS Home Screen PWA, and native-shell feasibility separately.

- If a notification settings page shows an App/PWA push switch in a browser that cannot enable Web Push, use `references/pwa-web-push-unsupported-channel-visibility.md`: hide the App Push channel control when `getWebPushSupport()` or equivalent says unsupported, keep Email/category preferences visible, and do not mutate the server push preference merely because this browser is unsupported.

- Applicability: when designing production Web Push for security-sensitive or finance-like PWAs with an authenticated in-app notification center, use `references/pwa-web-push-finance-formal-architecture.md`; anti-condition: do not apply it to native-only push tasks or to apps where push itself is the authoritative message store.

- When the user names a shared backend branch as the source of truth for PWA/Web Push (for example “pull latest test”) or the local checkout is dirty/stale, use `references/pwa-web-push-branch-aligned-backend-verification.md`: verify the exact remote branch in a clean worktree, keep every command's execution directory pinned to that worktree, separate long-lived foreground streams from the push-toggle await chain, explicitly start idempotent SW registration before readiness, bound never-settling browser promises, and prove unrelated full-suite failures on a second clean baseline before classifying them as pre-existing.

- When a PWA notification settings surface shows "push service unavailable", flips an App/PWA push switch off unexpectedly, or conflicts with a product rule such as "new users default app notifications on", use `references/pwa-web-push-preference-vs-subscription-debugging.md`: keep user notification preference separate from physical browser/provider subscription state, show transient failures via toast, explicitly capture status-returning failures, and run a frontend/backend/provider iceberg scan before claiming system push availability.

- Applicability: when a PWA notification switch is intended to represent current-device OS notification readiness, not only account-level preference, and existing users may already have server preference defaulted on. Use `references/pwa-web-push-preference-device-ready-switch.md`: derive checked state from server preference plus current-device permission/subscription/register evidence. Anti-condition: if the switch is explicitly account-level preference, keep it server-state driven and add a separate device-status row.

- Applicability: when backend/product owners say an existing backend field such as `pushEnabled` is the authoritative App Push subscribed/enabled state, use `references/pwa-web-push-backend-field-authoritative-switch.md`: first verify the field is exposed by the existing API, render the switch from server state, and on enable subscribe first then write the backend field true. Anti-condition: if the field is merely preference intent, use the current-device-ready switch pattern instead.

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
