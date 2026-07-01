# Mobile composer focus: header occlusion vs real header loss

Scope/applicability: mobile web / PWA / WebView pages with a bottom composer (`textarea`, chat input, support/AI input) where focusing the input appears to remove the top FlowNav/header. Applies especially to iOS Safari/Home Screen and routes such as support chat or AI assistant surfaces.

Anti-conditions:
- Do not apply to ordinary form pages where the product intentionally scrolls the focused field into view.
- Do not claim success from DOM `getBoundingClientRect()` alone when an overlay/toast is present; the pixels are the acceptance source.
- Do not globally suppress install prompts or change global safe-area tokens; scope suppression/fixed headers to keyboard-sensitive composer routes.

## Debugging path

1. Wait for splash/loading to fully detach before testing. If `.splash-root.is-out` stays mounted, fix splash teardown first; otherwise it can hide the real page state.
2. Separate **DOM focus** from **real soft-keyboard visual state**. Playwright `input.focus()` proves DOM focus and app-layout response, but headless/mobile emulation does not prove native iOS keyboard behavior. Label evidence accordingly and ask for/collect real-device pixels before final UI acceptance.
3. Focus the composer input and capture an actual mobile screenshot after keyboard/viewport settle.
4. Classify the top area:
   - **Install/update/offline toast covers header**: the header may exist but is not visible. Suppress/defer top toasts on keyboard-sensitive composer routes before accepting the fix.
   - **Header really moved above viewport**: outer `[data-screen-scroll]` is still scrollable or has keyboard reserve/scroll-padding. Pin the route-level outer scroller with `overflow-y: hidden` and no keyboard reserve; delegate scrolling to the inner message/content owner.
   - **Outer scroller is pinned but header still not visible**: make the FlowNav/header a fixed route-local layer (`fixed inset-x-0 top-[var(--safe-top)] z-* max-w-[app-width]`) and add a matching top padding reserve on the page shell.
5. When asked to check other input pages, classify pages before copying the composer fix. Full-height chat/support/AI composer routes usually need outer scroll lock + inner message scroll + fixed header. Ordinary forms/search/amount/password/address pages generally should keep natural keyboard scrolling and the normal keyboard reserve, otherwise bottom fields, CTAs, or validation messages can become unreachable.
6. Keep install nudges away from these surfaces. A top PWA install prompt can fully cover the FlowNav and make a fixed header fix look unsuccessful.
7. Verify again with toast suppressed/deferred and the input focused.

## Implementation pattern

- Route predicate: identify keyboard-sensitive composer routes (`/support/chat`, `/customer/ai`, etc.).
- App shell: for those routes, `data-screen-scroll` should be pinned (`overflow-y-hidden`) and should not carry keyboard reserve/scroll-padding.
- Page shell: `h-full min-h-0 flex-col overflow-hidden` with an inner `min-h-0 flex-1 overflow-y-auto` message/content owner.
- Header: when iOS still clips the normal-flow header, wrap FlowNav in a fixed route-local layer and reserve its height (`pt-[52px]` or tokenized equivalent) inside the page shell.
- Toast/install UX: defer top install/update prompts on keyboard-sensitive routes, or move them to a non-covering surface.

## Verification checklist

- Screenshot after splash ends and input is focused shows the header/title and actions in pixels, not just DOM presence.
- Evidence distinguishes DOM-focus smoke from real native-keyboard proof; do not call headless Playwright focus a complete iOS keyboard acceptance test.
- Top overlay/toast is absent or does not cover the header.
- `data-screen-scroll` computed `overflow-y` is `hidden` for the keyboard-sensitive route.
- Header rect is inside the visual viewport, and screenshot confirms it is visible.
- Composer remains bottom-aligned and the inner message/content area remains scrollable.
- Other input pages have been classified as composer routes vs ordinary form/search pages before applying route-level scroll locking.
- Tests cover route classification, fixed-header class/height reserve, install-toast suppression on composer routes, and the focused mobile smoke path.
