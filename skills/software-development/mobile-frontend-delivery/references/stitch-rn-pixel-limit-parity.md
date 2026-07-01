# Stitch → React Native pixel-limit parity notes

Use this reference when a Stitch mobile screen needs to be restored in RN beyond normal visual parity: `1:1`, `最接近`, `甚至更优`, or `极限像素级`.

## Classification

- Reusable procedure: yes — source-derived visual parity for Stitch → RN.
- Project-specific facts: no — keep project IDs, screenshots, and local paths in the project evidence doc, not here.
- Anti-condition: do not use this to flatten an entire product into screenshots unless the user explicitly chooses static-bitmap parity over native behavior.

## Procedure learned

1. Fetch the high-resolution Stitch screenshot. Google image URLs may default to thumbnails; append `=s0` when the metadata says the screen is larger.
2. Read the Stitch HTML source. Extract renderer constants before changing RN:
   - canvas/container size
   - Three.js camera FOV/aspect/z
   - particle count
   - sphere/core geometry and material opacity
   - point material size, opacity, vertex colors, additive blending
   - random distribution formulas
   - animation transforms and scale pulses
3. Recreate or embed the renderer class in RN:
   - Reanimated View particles are acceptable for the first slice.
   - For pixel-limit parity, move to Skia/Canvas or WebGL; do not add thousands of RN Views.
   - If staying native, use Skia/Canvas with a deterministic seeded random function so the point cloud is stable across builds/screenshots.
   - If the user chooses WebGL/Three.js parity, embed the same Three.js runtime in `react-native-webview` and keep the RN shell/product controls outside it.
4. Match typography with real font assets:
   - Download/bundle the target font family when licensing allows.
   - Add `react-native.config.js` with `assets: ['./assets/fonts']`.
   - Run `npx react-native-asset` and inspect iOS project/Info.plist changes.
   - Apply `fontFamily` to each RN role; weights alone are not enough.
5. Verify by real app, not component render:
   - Jest + lint
   - pod install when native deps/fonts changed
   - Release simulator build
   - explicit simulator uninstall/install/launch
   - screenshot after launch
6. Quantify improvements:
   - build side-by-side with target scaled to RN screenshot height
   - compute rough full-frame diff after resizing RN to target size
   - compute anchor bboxes for colored orb/cyan regions and white/title text regions
   - keep the lower-diff iteration unless visual judgment contradicts the metric for a known device-chrome reason

## WebView/Three.js option

Use this when the user explicitly prioritizes renderer identity over a purely native Skia recreation, or chooses a path like “方案2”.

Recommended implementation pattern:

1. Add `react-native-webview` and a local `three` package matching the Stitch CDN version when possible.
2. Generate a self-contained HTML module/string for the orb/page fragment:
   - inline `node_modules/three/build/three.min.js` so production does not fetch a CDN;
   - keep `WebGLRenderer({ antialias: true, alpha: true })` and set transparent clear color/background;
   - copy Stitch constants exactly before tuning: camera, core geometry/material, particle count, `PointsMaterial`, additive blending, rotations, scale pulse, and current/noise update;
   - decide deliberately whether to preserve Stitch’s cumulative particle-position mutation or reset from base positions for stability. Use the exact cumulative version when matching a captured Stitch animation class, but document that the screenshot frame is time-dependent.
3. Embed through `WebView source={{ html }}` inside the RN orb container, with `scrollEnabled={false}`, transparent style/background, no pointer capture unless the WebView itself owns interaction.
4. Keep a native Skia fallback when feasible; it gives a lower-risk escape if WebGL compositing fails on a target device.
5. Add a Jest mock for `react-native-webview`, run `pod install`, then verify Release install/launch/screenshot. A passing component test alone does not prove WebGL rendered.

Pitfalls:

- WebView/Three.js may be renderer-faithful but not numerically lower in full-frame diff if the original Stitch screenshot used an unknown random seed, unknown animation timestamp, or different viewport/device chrome.
- If absolute lowest screenshot diff matters more than native layering, the next escalation is rendering the entire Stitch screen as one WebView and bridging events back to RN. Treat that as an explicit product/architecture tradeoff, not a default.

## Useful pixel anchors

For target-vs-RN comparison, simple threshold bboxes are often enough:

- cyan/orb mask: `G > 80 && B > 80 && R < 150`, bounded to the main content vertical range
- white/title mask: `R > 180 && G > 200 && B > 200`, bounded to the title/main text vertical range

Record bbox percentages rather than raw pixels when comparing different simulator resolutions.

If the user points out remaining screenshot position offset after renderer parity, do not defend the implementation. Switch to element-level bbox correction: measure header/orb/title/card/nav centers and sizes, fix the dominant visual anchor first, then rerun Release install/screenshot and report before/after deltas. See `references/stitch-rn-webgl-bbox-offset-correction.md`.

## Honest boundaries

Do not claim perfect pixel parity when any of these remain:

- Stitch target is a flat canvas but simulator has Dynamic Island, status bar, or home indicator.
- Stitch renderer is WebGL/Three.js but RN renderer is Skia; additive blending and point rasterization differ.
- Fonts are not bundled or iOS/Android font names are not verified.
- Icons are screenshot crops rather than owned vector assets.
- Exact random seed/initial frame of the Stitch WebGL scene is unavailable.

If the user wants lower diff after the native renderer is exhausted, present the explicit tradeoff:

1. static target-bitmap layer + live overlays: lowest screenshot diff, weaker native honesty;
2. WebView/WebGL running the Stitch scene: closest renderer, larger runtime/architecture shift;
3. native Skia source-derived recreation: best product-native compromise.
