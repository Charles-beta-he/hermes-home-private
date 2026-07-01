# Stitch MCP to React Native 1:1 mobile-screen workflow

Use this when a Stitch-generated mobile screen becomes the visual source of truth for a React Native/PWA/mobile avatar shell.

## Applicability

- Stitch MCP is available and can return project/screen metadata.
- The target is a mobile screen that must be implemented in React Native or a mobile shell.
- The user asks for “1:1”, “全盘推进”, screenshot parity, or visual diff-level work.

Anti-conditions:

- Do not treat Stitch/HTML/Figma as product logic. Preserve the product architecture, routing, safety gates, queueing, and domain language separately from visual reconstruction.
- Do not expose internal lanes such as local/offline/online/Gateway/fallback/model mode on the main avatar UX unless the product spec explicitly asks for diagnostics.
- Do not copy third-party copyrighted reference assets. For generated Stitch output, prefer product-owned replacements or use generated assets only as temporary implementation references.

## Procedure

1. Read the Stitch project and screen through MCP:

   - `get_project`
   - `list_screens`
   - `get_screen`

2. Persist source evidence locally:

   - HTML from `screen.htmlCode.downloadUrl`
   - Screenshot from `screen.screenshot.downloadUrl`

3. Fetch high-resolution screenshots deliberately. Google image URLs may default to thumbnails; append `=s0` or a specific size suffix when the target screen metadata says the screenshot should be larger.

   Example pattern:

   ```python
   urllib.request.urlretrieve(download_url + "=s0", "target@fullres.png")
   ```

4. Extract implementation anchors before coding:

   - target dimensions
   - header height and positions
   - root/background colors
   - orb/canvas bounding box
   - primary title and status chip positions
   - input/transcript card bounds
   - bottom navigation bounds
   - typography family/weight/line height assumptions
   - icon/logo assets and ownership status

5. Implement in small RN slices:

   - structural layout first
   - text and spacing second
   - icon/asset pass third
   - animation/particle fidelity last

6. For generated icon/logo parity, crop target-owned/generated assets only when acceptable for the prototype, then clean transparent backgrounds. Record that production should replace screenshot crops with owned vector assets.

7. Verify with the real app, not just code:

   ```bash
   npm test -- --runInBand
   npm run lint
   CONFIGURATION=Release DERIVED_DATA=/tmp/<name> bash scripts/ios-simulator-run.sh
   xcrun simctl uninstall <device> <bundle-id>
   xcrun simctl install <device> <app-path>
   xcrun simctl launch <device> <bundle-id>
   xcrun simctl io <device> screenshot /tmp/<proof>.png
   ```

   Explicit uninstall/reinstall prevents stale simulator screenshots after asset changes.

8. Produce a side-by-side proof image by scaling the Stitch target and RN screenshot to a common height. This catches layout drift that single screenshots hide.

## Pixel-limit escalation path

When the user asks for `最接近`, `甚至更优`, or `极限像素级`, do not keep hand-tuning by eye. Escalate in this order:

1. Read the Stitch HTML implementation and extract renderer constants, not just screenshot pixels. For Three.js-style Stitch screens, capture particle count, camera FOV/aspect/z, sphere/core geometry, material opacity/blending, color endpoints, and animation transforms.
2. Rebuild native parity from those constants. For an RN avatar/ion orb, prefer a Skia/Canvas point renderer over thousands of RN Views; use a deterministic seeded random distribution that mirrors the Stitch formulas so future builds are stable.
3. Preserve product logic separately from pixel parity. Do not turn a native avatar into a static bitmap unless the user explicitly chooses the `lowest screenshot diff` path; static crops are acceptable for prototype icon parity, but record asset-ownership boundaries.
4. Match typography with real assets, not only weights. Download/bundle the Stitch font families when licensing allows, add `react-native.config.js` assets, run `npx react-native-asset`, and apply `fontFamily` to the matching RN text roles.
5. Quantify iteration. Produce a side-by-side image by scaling target and RN proof to a common height, and record rough full-frame diff plus anchor bboxes for cyan/orb and white/title regions. Use the metric to decide whether a change improved or regressed before continuing.
6. Stop at the honest renderer/device boundary: Dynamic Island/status/home indicators, Skia-vs-WebGL additive blending, target-flat-canvas vs real simulator aspect ratio, and font rasterization can remain even after all source-derived parameters are matched.

## React Native pitfalls

- Simulator hardware chrome (Dynamic Island, status bar, home indicator) can make a flat Stitch canvas look mismatched. Use a device matching the target aspect ratio where possible, but do not use a short SE screen as the only parity proof for a tall target canvas.
- `react-native-safe-area-context` may add top padding that Stitch flat canvases do not include. If the target is a full-canvas mock, consider `edges={['left', 'right']}` on the top-level SafeAreaView and handle safe areas intentionally.
- Reanimated View particles can approximate an ion cloud, but hundreds of View nodes are not equivalent to a 1500–2500 point WebGL/Skia point cloud. Stop increasing View count when fidelity becomes renderer-bound; move to Skia/WebGL/canvas.
- RN system fonts rarely match Stitch fonts exactly. For true parity, bundle the target font family as a native asset and verify it is linked into iOS/Android before claiming font parity.
- Cropping screenshot icons can help prototype parity but may carry black matte pixels. Run a transparency cleanup pass and document replacement with owned vector assets.
- If the target is a hybrid/offline avatar, keep online authority and local fallback out of the main visual surface unless the spec explicitly asks for diagnostics; 1:1 visual restoration should not accidentally reposition the product as an offline-local-model-first assistant.

## Closeout evidence

A good closeout records:

- Stitch project/screen IDs
- local HTML and high-resolution screenshot paths
- RN screenshot path
- commands and real outputs for tests/lint/build
- side-by-side comparison path
- explicit remaining non-1:1 deltas and whether they are renderer/device/font/asset-bound
