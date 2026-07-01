# PWA startup splash: Stitch SDK source + iOS/Android launch surfaces

Use this when a PWA needs branded launch/startup imagery before the web bundle or React splash can render, especially when iOS Home Screen shows a white screen while Android shows a generated launch frame.

## Platform split

- **Android WebAPK / Chrome PWA**: launch surface is synthesized from `manifest.webmanifest` inputs (`background_color`, `theme_color`, `icons`, `short_name`, maskable icon). It is configurable, but not pixel-perfect per-device artwork.
- **iOS Home Screen PWA**: Safari does not synthesize the Android-style branded launch surface from the manifest. Use explicit `<link rel="apple-touch-startup-image" ...>` PNGs for supported iPhone/iPad viewport sizes.
- Do not use the current Android auto-generated frame as the design standard by default. Establish the ideal branded static startup frame first, then align Android manifest inputs toward it.

## Stitch SDK workflow boundary

- Prefer the Hermes/module-library Stitch SDK capability (`@google/stitch-sdk`, local secret config such as `~/.rowboat/config/stitch.json` or `STITCH_API_KEY`) over MCP.
- Do **not** add `@google/stitch-sdk`, Stitch scripts, or Stitch secret handling to the target product app repo just to generate assets. The app should receive final static assets only.
- Never print or commit raw Stitch API keys. Redacted manifests are acceptable in Hermes/project evidence areas, not in the app repo unless intentionally scoped and secret-free.

## Practical generation path

1. Identify the accepted startup standard before generating assets. If the app already has an approved React/in-app `SplashScreen` or loading overlay, treat that as the standard by default. Do **not** redesign or replace it unless the user explicitly asks to change the loading animation itself.
2. Generate or refine native startup artwork through Stitch SDK from the Hermes/module-library side only when a new standard is actually requested. Do not start from the Android WebAPK auto-generated frame unless the user explicitly approves it as the brand source.
3. If text-only generation loses brand fidelity (e.g. wrong icon, missing wordmark, phone mockup frame, transparent/logo-only SVG), iterate or upload a neutral brand reference. Avoid uploading the current Android splash as the baseline when the goal is to create a new standard; doing so just freezes the lowest-common-denominator Android result into Stitch.
4. Treat the approved full-screen frame as a **startup system**, not a single iOS PNG. Derive all launch surfaces from the same geometry, colors, and wordmark:
   - iOS `apple-touch-startup-image` PNGs;
   - React/in-app `SplashScreen` or loading overlay shown after the JS bundle mounts **only when the user approved changing that overlay**;
   - Android manifest icons / maskable icon / `background_color` / `theme_color` that WebAPK uses to synthesize its launch screen.
4. Add `<link rel="apple-touch-startup-image" ...>` entries before the React module script in `index.html`.
5. Keep Android manifest launch inputs aligned with the same approved visual direction: background color, correct icon/maskable icon, `short_name`, and appropriate `theme_color`. Android should approximate the new standard; it is not the standard-setter.
6. Verify the startup images are not added to Workbox precache if they are large; they are native launch resources, not first-install app-shell dependencies.

## Quality gates

Reject Stitch outputs that are:

- standalone logo/SVG assets instead of full-screen mobile launch compositions;
- transparent or black-background when the product requires white launch surface;
- missing the brand wordmark/text;
- using a generic globe/card icon instead of the approved brand mark;
- copying the existing Android auto-generated splash when the task is to define a new standard;
- wrapped in a phone mockup, rounded card, browser chrome, or product UI surface;
- containing marketing copy, buttons, cards, pagination dots, bottom hairlines, or form controls;
- visually disconnected from the React/in-app loading overlay that appears immediately after the native startup screen;
- requiring an unrequested redesign of an already-approved React/in-app loading overlay. If the user says the existing loading is the standard, regenerate native startup assets to match it instead of modifying the overlay.

Minimum verification:

- inspect generated image visually;
- compare native startup image and React/in-app splash screenshot side-by-side for same mark, background, wordmark placement, and absence of unintended loading-visual changes;
- read `dist/index.html` and confirm `apple-touch-startup-image` links exist before the React module script;
- confirm `dist/manifest.webmanifest` Android launch inputs match the same design standard;
- confirm `dist/sw.js` does not precache startup-image assets unless deliberately chosen.

## Anti-conditions

- This is not a fix for normal in-app loading animation duration; handle React splash timing separately.
- This is not a reason to persist Stitch SDK dependencies or credentials in a finance app repo.
- If Stitch SDK/network transiently fails, capture the retry/export pattern, not a durable claim that Stitch is unavailable.
