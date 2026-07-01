# PWA platform startup screens: iOS startup images vs Android WebAPK splash

Applicability: installed browser PWAs where the OS/native launch surface appears before web content, especially when iOS shows a blank/white pre-React screen while Android shows a branded WebAPK splash.

Anti-conditions: do not use this for in-app React splash timing after the JavaScript bundle has mounted; measure that separately. Do not use it for native iOS/Android apps whose launch screens are controlled by Xcode/Android resources rather than web/PWA metadata.

## Core distinction

Android and iOS do not use the same startup-screen mechanism:

- **Android Chrome/WebAPK** synthesizes a native launch screen from the Web App Manifest. The app can influence it with `background_color`, `theme_color`, `icons`/maskable icon, and `name`/`short_name`, but cannot pixel-control every element.
- **iOS Home Screen PWA** does not reliably synthesize the same visual from the manifest. To avoid the pre-React white screen, ship explicit `<link rel="apple-touch-startup-image" ...>` PNGs matched by device-size media queries.

Do not use the weaker/default platform result as the visual standard. Establish a target brand startup page first, then align both platforms toward it.

## Preferred workflow

1. Treat the approved design-tool output as the startup visual SSOT. For Stitch work, use **Stitch SDK rather than Stitch MCP**.
2. If the design SDK is temporarily unavailable, a locally generated SVG/PNG implementation may be used only as a reversible placeholder; state that boundary and keep the wiring reusable.
3. Export/derive iOS startup PNGs from the approved visual for common iPhone/iPad portrait sizes.
4. Update `index.html` with `apple-touch-startup-image` links before the React module script.
5. Align Android WebAPK inputs to the same visual standard:
   - `manifest.background_color` = approved startup background;
   - `manifest.theme_color` = desired system chrome color;
   - `icons`/`maskable` = approved launcher mark;
   - bump icon query/version when Chrome/WebAPK must refetch launcher artwork.
6. Verify Android separately; manifest changes may require reinstall/WebAPK refresh before the launch surface updates.

## Implementation checklist

- Keep `apple-mobile-web-app-capable=yes`.
- For fullscreen iOS startup ownership, preserve `apple-mobile-web-app-status-bar-style=black-translucent` unless the product explicitly wants WebView content below the status bar.
- Include startup image links early in `<head>`, before the React module script.
- Cover current common iPhone/iPad portrait sizes; add landscape only if the app supports landscape.
- Use cache-bust query strings on startup images and manifest icons when changing visual assets.
- Keep startup images out of Workbox precache if first-install payload must stay tiny; they are OS launch assets, not app-shell critical path.
- Add a regression test that reads `index.html` directly and asserts startup image links exist before the React module script.
- After build, read back `dist/index.html`, `dist/manifest.webmanifest`, `dist/sw.js`, and the copied startup image directory.

## Verification checklist

Minimum for a Vite/React-style PWA:

```bash
pnpm exec vitest run <runtime-layout-tests> <safe-area-tests> <theme-tests> --reporter=verbose
pnpm build
```

Then verify:

- `dist/index.html` contains expected `apple-touch-startup-image` count and links before the module script.
- The built startup-image directory contains the generated PNGs.
- `dist/sw.js` does **not** precache the startup PNGs unless explicitly intended.
- `dist/manifest.webmanifest` has the approved Android `background_color`, `theme_color`, and icon URLs.
- Live deployed headers for `index.html`, `manifest.webmanifest`, and `sw.js` are fresh/no-store where appropriate.

## Pitfalls

- Android's launch screen may look like a screenshot or app-provided static page, but it is usually WebAPK/Chrome-generated from the manifest.
- iOS clearing Safari cache does not necessarily update Home Screen PWA state; reinstall may be needed for startup image/icon changes.
- Do not claim iOS startup parity from browser automation alone; final acceptance needs a real iOS Home Screen install/reinstall screenshot or video.
- Do not store design-tool/API keys in the app repo; SDK scripts must read local secrets/environment and redact output.
