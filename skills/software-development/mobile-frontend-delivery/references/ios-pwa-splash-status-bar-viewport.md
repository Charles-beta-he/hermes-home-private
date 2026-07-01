# iOS PWA splash/loading viewport vs normal page safe-area

Applicability: iOS Home Screen PWA / Safari standalone where the startup splash/loading surface appears visually short, cropped, or missing the status-bar/Dynamic-Island area, especially after recent work on first-paint theme/status-bar handling.

Anti-conditions: do not use this as a generic fix for normal app pages being pushed down, TabBar bottom gaps, Android WebAPK viewport issues, or route-return drift. If the screenshot is an already-rendered page with content starting too low, diagnose TopBar/main `--safe-top` consumption separately.

## Symptom split

There are two visually similar but different bugs:

1. **Splash/loading looks short / missing a top strip**
   - The first loading/splash surface does not own the full drawable iOS viewport.
   - Often caused by `apple-mobile-web-app-status-bar-style=default`, which makes the WebView content area avoid the status bar before the app can draw the splash.
   - Changing `.splash-root { inset: 0 }` is insufficient if the missing strip is outside the web content area.

2. **Normal page content is pushed down**
   - The app page renders after loading, but TopBar/title/content starts too low.
   - Often caused by double-counting status bar safe area: WebView already avoids the status bar and the app also applies `--safe-top` to TopBar/main.
   - Fixing this by changing splash CSS can mask the wrong layer.

When the user corrects the target from one to the other, stop and realign scope before editing.

## Debug sequence

1. Extract early frames from the user video or screenshot sequence and classify whether the affected surface is:
   - native OS/PWA startup screen before web content exists;
   - startup/splash/loading rendered by the web app; or
   - already-rendered app page.
2. If the affected surface is the native OS/PWA startup screen:
   - Android/WebAPK is mostly controlled by manifest `background_color`, `theme_color`, icons, maskable icon, and app name; it may show an automatically synthesized static frame.
   - iOS Home Screen PWA needs explicit `apple-touch-startup-image` PNG links; otherwise it often shows a plain white startup screen before React can render.
   - Establish the ideal static launch image first (prefer Stitch SDK from the module-library side), then align Android manifest inputs toward it. Do not treat Android's current auto-generated frame as the visual source of truth.
3. Inspect live/built `index.html` for:
   - `<meta name="apple-mobile-web-app-status-bar-style" ...>`;
   - first-paint theme/status-bar boot script assignments;
   - whether the React module loads after those assignments.
3. For splash-short bugs, preserve existing app page safe-area layout and prefer status-bar ownership fixes first:
   - keep iOS PWA first-paint status bar as `black-translucent` so the web app can draw under the status bar and splash owns the full screen;
   - ensure boot/theme runtime does not rewrite light theme back to `default` before/after React hydration;
   - keep theme-color updates separate from iOS status-bar viewport ownership.
4. For normal-page downshift bugs, do not change splash timing/DOM unless evidence shows the startup surface is involved. Diagnose `--safe-top`, TopBar padding, main scroll inset, and WebView status-bar mode separately.

## Regression tests

Add or update tests that read `index.html` directly:

- assert the `apple-mobile-web-app-status-bar-style` meta is `black-translucent` before the React module script;
- assert the boot script does not contain a light-theme assignment such as `iosStatusBarStyle = 'default'` when the accepted contract is splash/fullscreen ownership;
- keep existing first-paint platform/display-mode marker tests intact.

Update theme-store tests too if the runtime can mutate the same meta tag:

- light/dark/system-resolved-light should all preserve `black-translucent` when the product requirement is fullscreen splash ownership;
- `theme-color` can still switch with app theme, but iOS status-bar style should not switch to `default` as a side effect.

## Verification

Minimum local verification:

```bash
pnpm exec vitest run src/stores/__tests__/theme.store.test.ts src/lib/__tests__/runtimeLayout.test.ts --reporter=verbose
pnpm exec vitest run src/components/__tests__/SplashScreen.chrome.test.tsx src/__tests__/safe-area-layout.test.tsx --reporter=verbose
pnpm run build
```

Then read back `dist/index.html` and confirm:

- `black-translucent` is present for the iOS status-bar meta;
- no `iosStatusBarStyle = 'default'` assignment remains;
- no unrelated splash height, PhoneCanvas, TabBar, or page safe-area constants changed.

## Pitfall

Do not “fix” the wrong complaint. A user saying “首屏 loading 页面少一截” is specifically about the startup/loading surface, not necessarily the normal page being shifted down. Conversely, a normal rendered page starting too low is not proof that splash/loading is short. Treat them as separate acceptance atoms and verify both if both are mentioned.
