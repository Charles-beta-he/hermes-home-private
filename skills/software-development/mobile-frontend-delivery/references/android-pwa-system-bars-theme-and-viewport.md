# Android PWA/WebView system bars: theme, viewport, and TabBar triage

## Trigger

Use when an Android mobile screenshot shows black or mismatched system chrome around a web/PWA/WebView app:

- A black top status bar above the app header even though the app surface is light.
- A black bottom navigation/gesture bar under or over the app.
- The app TabBar is clipped by the bottom system bar, or the app content appears to continue behind it.
- The task mentions Android/iOS height adaptation, status bar, navigation bar, safe area, installed PWA, WebAPK, or WebView.

## First classification

Treat top and bottom issues as separate atoms. They may share the same screenshot but often require different fixes.

1. **Top system status bar not themed**
   - Symptom: status icons sit on a black rectangle while the page below is light.
   - Likely class: system-bar theming / app-shell ownership, not React layout alone.
   - Web/PWA path: verify live `<meta name="theme-color">`, manifest `theme_color`, deployed manifest freshness, and WebAPK/home-screen install cache.
   - Native WebView path: web meta may not control the bar. The native shell must set status bar color, navigation bar color, light/dark icon mode, and edge-to-edge/decor fitting.

2. **Bottom system navigation underlap**
   - Symptom: floating TabBar or bottom controls are partially hidden by the black navigation/gesture area.
   - Likely class: layout viewport extends behind a visual system bar; `env(safe-area-inset-bottom)` may report 0.
   - Web/PWA fix path: separate bounded Android-only visual inset from `visualViewport`, consumed only by TabBar placement/reserve.
   - Do not fix by using `screen.height - innerHeight` as generic bottom safe area; that previously over-lifted Android TabBars.

3. **iOS over-lift / blank band**
   - Symptom: TabBar floats too high with a large empty band below it.
   - Opposite direction from Android underlap. Do not apply Android visual inset to iOS, and do not make TabBar gap additive with synthesized iOS bottom safe-area guesses.

## Required probes before deciding the fix

If runtime access is available, capture these values from the affected device/build without printing secrets:

```js
({
  ua: navigator.userAgent,
  standalone: matchMedia('(display-mode: standalone)').matches || navigator.standalone === true,
  platform: document.documentElement.dataset.platform,
  displayMode: document.documentElement.dataset.displayMode,
  themeColor: [...document.querySelectorAll('meta[name="theme-color"]')].map(m => m.content),
  safeTop: getComputedStyle(document.documentElement).getPropertyValue('--safe-top'),
  safeBottom: getComputedStyle(document.documentElement).getPropertyValue('--safe-bottom'),
  androidVisualBottomInset: getComputedStyle(document.documentElement).getPropertyValue('--android-visual-bottom-inset'),
  tabbarBottomGap: getComputedStyle(document.documentElement).getPropertyValue('--tabbar-bottom-gap'),
  innerHeight: window.innerHeight,
  vv: window.visualViewport && {
    height: window.visualViewport.height,
    offsetTop: window.visualViewport.offsetTop,
    offsetLeft: window.visualViewport.offsetLeft,
    scale: window.visualViewport.scale,
  },
})
```

Also fetch the deployed manifest with cache bypass and compare:

- `theme_color`
- `background_color`
- `display`
- `display_override`
- `start_url` / `scope`
- asset hash/build marker if the project has one

## Decision matrix

Applicability: generic PWA/WebView system-bar triage; this section is not project-specific.
Anti-condition: do not remove a deliberate “follow system” product feature unless that requirement has been explicitly superseded. If the user says “do not remove follow system”, preserve it as a controlled user choice.

| Evidence | Likely fix |
|---|---|
| Requirement says fixed app theme choices must not be overridden by OS dark/light mode, but “follow system” remains a product option | Keep **one** authoritative `<meta name="theme-color">` with no media-bound duplicates. Resolve the app theme from persisted user choice: `light` and `dark` are fixed app-owned modes; only explicit `system` reads `matchMedia('(prefers-color-scheme: dark)')`, listens for system changes, and updates `data-theme` + `theme-color`. Keep the theme picker’s Follow System option and add tests for all three modes. |
| Requirement says the app no longer supports following system at all | Remove media-bound theme-color tags and system preference boot logic. Keep one app-owned `<meta name="theme-color">`, update it from persisted in-app theme, and migrate legacy `system` theme state to an explicit default such as `light`. Do this only after product confirmation. |
| Web/PWA standalone, live meta/manifest theme is wrong | Fix HTML/meta/manifest theme-color and redeploy. |
| Web/PWA standalone, live theme is right but installed app still shows black bars | Suspect WebAPK/PWA install cache, old deployed package, or Chrome-hosted WebappActivity/shortcut rather than true WebAPK. Verify freshness, reinstall/refresh WebAPK, and inspect `adb shell pm list packages | grep -i webapk` plus focused activity/window attrs before changing layout code. |
| Chrome-hosted Android PWA (`com.android.chrome/org.chromium.chrome.browser.webapps.WebappActivity`) has correct live `theme-color` and `data-theme`, but bottom gesture/navigation bar remains black | This can be native Chrome window ownership, not web layout: dumpsys may show `LIGHT_STATUS_BAR`/`LIGHT_STATUS_BARS` but no `LIGHT_NAVIGATION_BAR`, and app bounds exclude the navigation bar (`mAppBounds` bottom above physical display bottom). Web CSS cannot paint outside the app bounds; meta `theme-color` may recolor the status bar only in this runtime. Treat as WebAPK/native-shell boundary or emulator/install-mode limitation. |
| Native WebView / app shell, web theme is right but bars are black | Fix native shell system-bar configuration; web meta may not control the bar. |
| PWA-layer runtime is correct in preview (`data-theme`, single `theme-color`, manifest), but no Android device is attached | Report code/build/PWA-runtime proof as PASS and installed WebAPK/device screenshot as BLOCKED. Do not call Lark closeout fully done until a real installed PWA or WebView screenshot verifies the status bar. |
| Bottom TabBar clipped, `visualViewport` bottom delta is plausible | Use Android-only bounded visual inset token, e.g. `--android-visual-bottom-inset`, and feed TabBar bottom gap/content reserve. |
| Bottom delta is huge or only `screen.height - innerHeight` shows a gap | Do not synthesize a huge inset. Add device-specific evidence and look for browser/system chrome, keyboard, or shell viewport configuration. |
| iOS blank band below TabBar | Keep TabBar base gap fixed; remove synthesized bottom safe-area participation from TabBar. |

## Verification checklist

- [ ] Screenshot classified as Android/iOS and browser/PWA/WebView where possible.
- [ ] Top status-bar theming and bottom viewport underlap were evaluated separately.
- [ ] Live meta theme-color and manifest theme_color were inspected from the deployed target, not assumed from source.
- [ ] If fixed app-owned light/dark is required but Follow System remains a product feature, built HTML has exactly one `meta[name="theme-color"]`, no `media="(prefers-color-scheme:...)"` theme-color variants, and boot/theme-store code reads OS color-scheme **only** inside the explicit `system` choice path.
- [ ] If legacy persisted `system` theme state can exist, either keep it as a controlled follow-system mode or migrate it only after product confirmation that Follow System is removed.
- [ ] The theme picker/UI contract matches product intent: do not remove Follow System unless explicitly approved; if present, tests cover `light`, `dark`, and `system` behavior.
- [ ] If native/WebView is suspected, the conclusion names the native shell boundary instead of trying to solve it with React padding alone.
- [ ] Any Android bottom compensation is scoped to Android standalone/WebView and uses a bounded visualViewport-derived token.
- [ ] No generic `screen.height - innerHeight` bottom safe-area heuristic was introduced.
- [ ] iOS first-launch over-lift protections remain intact.
- [ ] Build/test or runtime proof includes both CSS token presence and absence of broad unsafe safe-area variables when relevant.

## Anti-conditions

- Do not use this for ordinary desktop browser spacing bugs.
- Do not merge top status-bar color and bottom TabBar clipping into one undifferentiated “safe-area issue.”
- Do not claim Lark final closeout from source analysis alone when the task requires online/mobile UI evidence.
