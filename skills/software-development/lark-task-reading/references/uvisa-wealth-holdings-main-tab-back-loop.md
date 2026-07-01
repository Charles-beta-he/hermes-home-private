# UVISA C-end wealth holdings → wealth main-tab back-loop triage

Scope: UVISA `uvisa-app-2.0` C-end tasks where the user enters `/wealth/holdings` from Asset/Home (or Me), taps the empty-state CTA such as “查看理财产品”, lands on `/wealth`, then iOS PWA side-swipe / browser Back loops between “我的持仓” and “财富” or cannot return to the original source page.

Applicability:
- User-visible symptom mentions iOS Add-to-Home/PWA side-swipe, Android browser back, main tab return, wealth holdings, or “查看理财产品”.
- The target flow is source page → deep holdings page → wealth main tab.
- The bug is navigation/history behavior, not backend wealth data correctness.

Anti-conditions:
- Do not remove the global main-tab history guard wholesale; it protects flows such as `/wealth/buy/finish -> /wealth`, `/card/topup/finish -> /card`, and `/me/security/devices -> /me` from returning to stale flow pages.
- Do not treat a top FlowNav back-button fix as sufficient for iOS native side-swipe/browser Back. FlowNav `onBack` does not run for native browser history gestures.
- Do not close the Lark task from code inspection alone; PWA/mobile UI proof is still required when the task asks for side-swipe behavior.

## Root-cause pattern

A common failing stack is:

```text
/home
/wealth/holdings?from=home
/wealth              # pushed by “查看理财产品”
/wealth              # same-URL guard entry inserted by main-tab history guard
```

Two things combine:

1. `HoldingsScreen` derives a source-aware `backTo` for the top-left FlowNav button (`?from=home` or `location.state.backTo`), but the empty-state CTA uses a plain `nav('/wealth')` push. This leaves `/wealth/holdings?from=home` behind `/wealth` in native history.
2. `useMainTabHistoryGuard` arms whenever a non-main route lands on a main tab. `/wealth/holdings -> /wealth` therefore inserts a same-URL guard entry. Browser/PWA Back pops the guard entry and the handler re-arms it, making the user feel trapped on `/wealth` or see `/wealth/holdings` flash and loop back.

## Diagnosis steps

1. Read the Lark title/video and atomize the exact path: source page, deep page, CTA label, target main tab, expected Back destination.
2. Inspect source link: for Asset/Home it should normally be `/wealth/holdings?from=home` with `state.backTo='/home'` as compatibility.
3. Inspect the deep page CTA. If it uses `nav('/wealth')` push, suspect stale source page retention.
4. Inspect both web/PWA swipe handlers and native/Capacitor back handlers. Android gesture navigation may surface as Capacitor `App.backButton`, bypassing DOM touch listeners; a fix that only updates `useSwipeBack` can leave Android returning to app-exit behavior instead of the source tab.
5. Inspect `useMainTabHistoryGuard` or equivalent main-tab terminal-route guard. If it arms on all deep→main transitions, check whether this business path needs an escape/skip state.
6. Reproduce with a real browser/PWA history gesture, Android/Capacitor back event, or a test that simulates source → deep → CTA → Back; do not rely only on clicking the custom FlowNav back button.

## Fix pattern

Preserve the global guard, but make this business transition source-aware:

1. When the deep page CTA intentionally exits a source-owned deep page into a main tab, replace the deep page rather than pushing another entry.
2. Carry explicit navigation state such as:

```ts
nav('/wealth', {
  replace: true,
  state: {
    mainTabBackTarget: '/home',
    skipMainTabHistoryGuard: true,
  },
});
```

3. Teach the main-tab history guard to skip arming only for that explicit marker (or equivalent scoped state), while keeping normal deep→main flow-finish guards intact.
4. Align every back surface that can fire on the target platform with the same source-target contract:
   - iOS PWA/custom swipe should read the main-tab back target and `navigate(target, { replace: true })`.
   - Android/Capacitor `App.backButton` should check the same target before applying ordinary main-tab `exitApp()` behavior.
5. If the product expects Back from `/wealth` to return to `/home`, ensure the browser/native history stack or a platform back bridge can reach `/home` directly; do not only change React state that native swipe/back handlers cannot see.

## Regression tests

Add both policy and route-flow tests:

- `shouldArmMainTabHistoryGuard('/wealth', '/wealth/buy/finish') === true` stays true.
- `/home -> /wealth/holdings?from=home -> click 查看理财产品 -> /wealth -> Back` lands on `/home`, not `/wealth/holdings`.
- `/wealth/holdings` opened directly still uses normal holdings back behavior.
- If the app supports `/me -> /wealth/holdings?from=me`, cover the equivalent source target.
- iOS/profile PWA swipe on source-directed `/wealth` calls `navigate('/home', { replace: true })` instead of swallowing the main-tab gesture.
- Android/Capacitor `App.backButton` on source-directed `/wealth` calls `navigate('/home', { replace: true })` and does not `exitApp()`.
- Ordinary `/wealth` without a source target preserves the platform's existing main-tab behavior (for native Android, exit app; for iOS PWA, swallow to avoid blank snapshot).

## Closeout proof

- Deterministic test for the route/history path.
- Mobile/PWA runtime proof using native side-swipe or browser Back, not only FlowNav click.
- Screenshot/video evidence should show the source page after backing from `/wealth`, and no repeated `/wealth` guard loop.
