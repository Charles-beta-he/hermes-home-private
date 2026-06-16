# Android PWA system navigation underlap

## Trigger

Use when an Android installed PWA / WebView screenshot shows the bottom TabBar or floating action chrome partially hidden by a black system navigation bar / gesture handle area. This is the opposite of the Android over-offset problem: the bar is too low and clipped, not floating too high.

## Symptoms

- Top status bar is Android-style (VPN/network speed/5G/Wi-Fi/battery), not iOS.
- A black system navigation area or gesture handle appears at the very bottom.
- The app TabBar pill is partially covered or cropped by that black area; only its top portion is visible.
- Content may continue behind the TabBar, but the interactive bottom chrome is not fully tappable/readable.

## Distinguish from related issues

- **iOS first-login / cold PWA relaunch over-lift**: TabBar is pushed upward and leaves a large blank band below it. Do not fix that by adding Android bottom inset.
- **Android over-offset**: TabBar floats too high because code synthesized an iPhone-style inset from `screen.height - window.innerHeight`. Do not reintroduce that global heuristic.
- **Liquid Glass visual strip**: TabBar is positioned correctly but an extra solid backing strip appears behind it. That is a styling/scroll-viewport issue, not system-nav underlap.

## Root cause pattern

On some Android installed PWA / WebView surfaces, `env(safe-area-inset-bottom)` returns `0px` or a very small value even though the screenshot has a bottom system navigation area that visually covers the page. If the TabBar uses only a fixed product gap (for example `18px`) or a tiny clamped Android safe-area (for example `0..8px`), the pill can sit inside the system bar area and become clipped.

Do **not** fix this by using `screen.height - window.innerHeight` as a universal bottom inset. That delta can include status bar, browser chrome, or display cutout effects and previously caused Android TabBars to float too high.

## Safer diagnostic / fix path

1. First identify platform and display mode from runtime markers or direct probes:
   - Android: user agent contains Android.
   - Installed/standalone: `matchMedia('(display-mode: standalone)').matches` or WebView shell evidence.
2. Measure the visible bottom obstruction with `visualViewport` when available:
   - Candidate: `window.innerHeight - visualViewport.height - visualViewport.offsetTop`.
   - Ignore while an editable element is focused or the keyboard is open.
   - Clamp to a narrow, plausible system-nav range, e.g. `0..40px` or a product-approved max.
3. Write the result to a separate token such as `--android-visual-bottom-inset`, not to the generic `--safe-bottom` and not to iOS tokens.
4. Let only Android standalone TabBar placement consume the token:
   - `--tabbar-bottom-gap: calc(<product-gap> + var(--android-visual-bottom-inset, 0px));`
5. Keep content reserve and TabBar placement using the same token so the last content is not hidden behind the now-raised TabBar.
6. Add regression tests for both directions:
   - Android with plausible bottom obstruction raises the TabBar enough to avoid clipping.
   - Android with large `screen.height - innerHeight` but no `visualViewport` obstruction does not synthesize a huge inset.
   - iOS first-launch over-lift fix remains intact and does not consume the Android token.

## Playwright / simulator probe pattern

When a physical Android device or full Android emulator is unavailable, use a Playwright mobile Chromium probe to verify the web-side contract, but label it as a **web-runtime simulation**, not OS-level proof:

1. Use a Pixel/Android user agent and mobile viewport.
2. Override `matchMedia('(display-mode: standalone)')` to return `true` for the standalone case.
3. Override `window.visualViewport` so `height = innerHeight - <simulatedSystemNavPx>` and `offsetTop = 0`.
4. Seed auth/session state enough to render the target chrome; skip startup splash if it would cover the TabBar proof.
5. Measure and save:
   - `document.documentElement.dataset.platform` / `dataset.displayMode`;
   - `--android-visual-bottom-inset`, `--tabbar-bottom-gap`, `--tabbar-content-reserve`;
   - TabBar `getBoundingClientRect()`;
   - `gapToLayoutBottom = innerHeight - navRect.bottom`;
   - `gapToVisualBottom = visualViewport.height - navRect.bottom`.
6. Expected result for a plausible obstruction such as 32px: `--android-visual-bottom-inset: 32px`, TabBar `bottom = productGap + 32px`, and `gapToVisualBottom == productGap`.
7. Also test an implausibly large obstruction to prove the cap works and the old over-lift bug does not return.

Limitations:
- Playwright mobile emulation does **not** draw real Android status/nav bars. It cannot prove `theme-color`, WebAPK cache behavior, OEM navigation-bar color, or native WebView `statusBarColor/navigationBarColor`.
- If screenshots still show a black top status bar while HTML/manifest `theme-color` is correct, classify it as WebAPK cache / browser shortcut / native shell system-bar configuration until proven otherwise.
- If a real device still underlaps while the Playwright visualViewport probe passes, collect real-device `visualViewport`, display-mode, CSS variable, and TabBar rect values before changing heuristics.

## Verification checklist

- [ ] Screenshot/environment classified as Android, not iOS.
- [ ] The observed defect is clipping/underlap by system nav, not a blank band below the TabBar.
- [ ] No generic `screen.height - window.innerHeight` bottom safe-area heuristic was introduced.
- [ ] If a first-paint HTML script still uses `screen.height - window.innerHeight` for iPhone's 34px fallback, the calculation is inside an iPhone-only branch; Android remains `0px` there and uses the separate visualViewport token later.
- [ ] Android-specific inset token is separate from `--safe-bottom` / iOS top or bottom fallbacks.
- [ ] TabBar placement and scroll-content reserve consume the same bottom-gap token, so raising the TabBar does not leave the last content hidden behind it.
- [ ] Targeted tests cover Android underlap, Android over-offset prevention, keyboard-focused ignore, and iOS over-lift prevention.
- [ ] Built CSS/JS/HTML inspected for the intended tokens and absence of broad unsafe safe-area variables; do not fail merely because the literal `screen.height - window.innerHeight` remains in an explicitly iPhone-only fallback.
- [ ] If using Playwright/mobile emulation, results are labeled as web-runtime simulation; real OS status/nav-bar color still requires full emulator/physical-device or native-shell evidence. Chromium's `visualViewport` object may be effectively read-only or normalized despite `addInitScript`; prefer unit tests for the measurement helper and a real-device console probe for final inset values.
