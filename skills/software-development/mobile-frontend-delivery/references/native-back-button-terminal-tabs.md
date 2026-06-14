# Native Android back button: terminal main-tab routes

Use this when analyzing whether Android system Back / gesture navigation should return to prior in-app pages after a user lands on Home or another primary tab in a Capacitor/WebView SPA.

## Durable lesson

Do not infer native-back behavior from browser history alone. In hybrid apps, the app can intentionally treat main tab routes as terminal destinations and call `CapacitorApp.exitApp()` even when `window.history.length > 1`.

## Audit steps

1. Locate the app shell/root layout and confirm whether a native back hook is mounted globally.
   - Search for `backButton`, `CapacitorApp.addListener`, `hardwareBackPress`, `BackHandler`, `useAndroidBackButton`, `useSwipeBack`, `navigate(-1)`, and `exitApp`.
2. Find the terminal-route predicate.
   - Common names: `isMainTabPath`, `MAIN_TAB_PATHS`, `isTabPage`, `primaryRoutes`.
   - Compare it with the actual TabBar links; the two lists must stay in sync.
3. Read the ordering, not just the comments.
   - If code checks `isMainTabPath(location.pathname)` before `window.history.length`, then terminal tabs exit the app and never pop history.
   - If history is checked first, the same current URL may still pop to a previous page.
4. Separate surfaces:
   - Capacitor/native Android: `App.backButton` policy applies.
   - Web browser/PWA without native hook: browser back follows browser history unless a separate `popstate`/router guard exists.
   - In-WebView edge swipe may have its own hook; Android system gesture can bypass DOM touch handlers unless surfaced by Capacitor.
5. State the boundary precisely in the conclusion: current path, platform, native shell vs browser, and whether the route is a terminal tab.

## iOS standalone PWA caveat

Plain iOS Safari / Add-to-Home-Screen PWA is not the same as Capacitor native. Safari already owns the interactive left-edge back-swipe. If the SPA shell also implements a `touchstart`/`touchend` edge-swipe that calls `navigate(-1)`, one physical swipe can double-pop history and leave the standalone PWA on a white/blank snapshot while returning from deep flow pages to a main tab. For that symptom, see `references/ios-pwa-native-back-swipe-conflict.md` and prefer runtime-gating the custom swipe handler off for iOS Web/PWA while preserving Capacitor/native behavior.

## Expected UX policy for finance-style apps

Primary tabs such as Home / Card / Wealth / Me should normally be terminal: Android Back from them exits/minimizes the app rather than resurrecting sensitive or stale intermediate flow pages from history. Deeper flow pages can pop one route unless the flow explicitly uses `replace` to collapse completed or invalid steps.

## Web/PWA browser Back parity

Native Android can exit on terminal tabs because Capacitor surfaces `App.backButton`. Plain Web/H5/PWA browser Back is different: it pops the browser history unless the SPA adds an explicit guard. A common failure path is:

```text
/home → /account/USD → /tx/123 → /home
```

If the final `/home` navigation is a normal push, browser Back can resurrect `/tx/123` or another stale completed flow page. `replace: true` helps for individual completion buttons, but it is easy to miss one entry point and does not cover all programmatic/tab/logo navigation.

Durable pattern for Web/PWA parity:

1. Keep the native terminal-route predicate as the source of truth (`isMainTabPath`, `MAIN_TAB_PATHS`, etc.).
2. In the root shell, track the previous pathname.
3. On non-native platforms only, when the current path is a main tab and the previous path was not a main tab, push a same-URL guard entry with a marker in `history.state`.
4. On `popstate`, if the guard is armed and the browser is still on a main tab, immediately push the same-URL guard entry again.
5. Do **not** arm on initial direct `/home` load or normal main-tab switching (`/card → /home`), or users can feel trapped in a browser tab.
6. Keep deeper routes unchanged: browser Back from `/tx/123`, `/card/topup`, etc. should still pop normally unless the flow itself collapsed history with `replace`.

Minimal policy helper to unit-test:

```ts
export function shouldArmMainTabHistoryGuard(currentPathname: string, previousPathname: string | null): boolean {
  return Boolean(
    previousPathname
    && isMainTabPath(currentPathname)
    && !isMainTabPath(previousPathname),
  );
}
```

## Regression checks

- Unit-test the terminal-route predicate (`/home/` should normalize to `/home`).
- Test native back on each main tab returns to phone home / exits app.
- Test native back on representative subpages performs one router pop.
- Test a path reached via TabBar after a deep page: Back should still follow terminal-tab policy, not the prior history entry.
- Test Web/PWA route policy: non-main → main arms the guard; main → main and direct main load do not; deeper → deeper does not.
- Run targeted hook tests and typecheck after adding a guard; full lint may be noisy in migration repos, so also run scoped lint on new guard files.
