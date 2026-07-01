# PWA silent download + safe-boundary activation

Use when a mobile/PWA app can keep stale frontend code after deploy, especially after lock/unlock, app background/foreground, browser-tab switching, or long idle periods.

## Problem model

- `registration.update()` can quietly check/download a newer Service Worker and its app-shell resources.
- Already-running JavaScript is not hot-swapped. New API call shapes or business logic only take effect after a reload/new navigation boot.
- Finance and transaction apps must not reload in the middle of transfer, payout, payment, KYC, password/PIN, confirmation, preview, scanner, or dirty-form flows.

## Recommended runtime pattern

1. Split update **download** from update **activation**.
   - Download/check silently on app boot, periodic timer, foreground return, `pageshow`, and idle windows.
   - Activation is route/state gated and may reload.

2. Add foreground update checks:
   - `document.visibilitychange` when `document.visibilityState === 'visible'`
   - `window.focus`
   - `window.pageshow`
   - Debounce/throttle them so one foreground return does not call `reg.update()` several times.

3. Add long-idle update checks:
   - Maintain an idle timer, e.g. 5 minutes.
   - Reset on user activity such as `pointerdown`, `keydown`, and `touchstart`.
   - When idle fires and the document is visible, run the same quiet update check and safe-boundary activation attempt.

4. Define a safe-boundary predicate:
   - Safe examples: main tabs, login/public auth, non-editing settings/about surfaces.
   - Unsafe examples: remit/transfer/payout/payment/KYC/password/PIN/confirm/preview, active scanner, focused input, pending submit, or `[data-dirty="true"]` / `[data-form-dirty="true"]`.
   - Require `document.visibilityState === 'visible'`.

5. Activation behavior:
   - If a new worker/release is ready and the safe-boundary predicate passes: activate (`skipWaiting` or release-runtime activation) and reload automatically.
   - If unsafe: do **not** reload; show the existing update Toast/action. Call it a Toast/prompt if that is the real UI component, not a persistent banner/bar.

## Verification checklist

- Unit/static tests assert foreground triggers exist: `visibilitychange`, `focus`, `pageshow`.
- Tests assert idle trigger wiring exists and the reason/analytics label is distinct, e.g. `idle_safe_boundary`.
- Component tests assert ready updates auto-apply on safe routes without showing the Toast.
- Component tests assert unsafe routes show the Toast and only update when the user taps the action.
- Build verifies generated `dist/sw.js` / Workbox output.
- Real-device PWA acceptance still requires installed iOS/Android checks: foreground return, long idle, safe main-tab auto-apply, and sensitive-flow deferral.

## Anti-conditions

- Do not use unconditional reload for transaction flows.
- Do not claim that quiet download updates the currently executing JS without reload.
- Do not let a prompt-only policy remain the only path when the product explicitly wants safe automatic application.
