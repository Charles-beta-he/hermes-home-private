# React Native Skia ion-cloud upgrade for Stitch/mobile avatar parity

## Applicability

Use when a React Native mobile/avatar screen needs to match or exceed a Stitch/Figma/Behance-style particle/electric/ion orb, and a View/Reanimated particle implementation has reached renderer-bound limits.

Anti-conditions:

- Do not add Skia just for a few decorative dots; use Reanimated Views for the first low-risk slice.
- Do not keep increasing RN View particles past a few hundred if the target is a dense WebGL/Three.js point cloud; switch renderer class.
- Do not claim exact 1:1 if remaining deltas are device chrome, font metrics, asset ownership, or original Three.js point-generation logic.

## Pattern

1. Preserve product logic and UX routing first. Treat Skia as the visual renderer only.
2. Keep Stitch/Figma screenshot as visual SSOT; fetch high-res Google-hosted images with `=s0` when the MCP screen metadata says the canvas is larger than the default thumbnail.
3. Use Skia Canvas for dense point fields:
   - precompute deterministic point arrays outside render;
   - use `Points` groups rather than thousands of RN Views;
   - layer fine cyan points, bright cyan points, and subtle violet accents;
   - add radial glow and a faint ring with Skia primitives.
4. Keep Reanimated for container-level liveness: rotate/scale/opacity the Skia canvas on voice/active state rather than animating every point from JS.
5. If generated screenshot icons are temporarily cropped for prototype parity, clean black matte pixels to alpha and document that production should replace them with owned vector assets.
6. Add Jest mocks for `@shopify/react-native-skia` so existing behavior tests still run without native Skia.
7. Run `bundle exec pod install`; verify codegen includes `rnskia` before Release build.
8. For simulator evidence after asset/native dependency changes, explicitly uninstall/reinstall the app before screenshotting to avoid stale bundles/assets.

## Minimal Skia shape

```tsx
import {
  BlurMask,
  Canvas,
  Circle,
  Group,
  Points,
  RadialGradient,
  Rect,
  vec,
} from '@shopify/react-native-skia';

const SIZE = 238;
const CENTER = SIZE / 2;
const points = Array.from({ length: 1500 }, (_, index) => {
  const spiral = index / 1500;
  const turn = spiral * Math.PI * 9.6 + (index % 7) * 0.9;
  const radius = 38 + Math.sqrt(spiral) * 78 + Math.sin(index * 0.31) * 9;
  return vec(CENTER + Math.cos(turn) * radius, CENTER + Math.sin(turn) * radius * 0.86);
});

<Canvas style={{ width: SIZE, height: SIZE }}>
  <Rect x={0} y={0} width={SIZE} height={SIZE}>
    <RadialGradient
      c={vec(CENTER, CENTER)}
      r={114}
      colors={['rgba(0,242,255,0.18)', 'rgba(0,138,150,0.06)', 'rgba(0,0,0,0)']}
    />
  </Rect>
  <Circle cx={CENTER} cy={CENTER} r={74} color="rgba(0,242,255,0.08)">
    <BlurMask blur={18} style="normal" />
  </Circle>
  <Group color="rgba(89,234,244,0.46)" strokeCap="round" strokeWidth={1.05}>
    <Points mode="points" points={points} />
  </Group>
  <Circle cx={CENTER} cy={CENTER} r={78} color="rgba(0,242,255,0.12)" style="stroke" strokeWidth={1} />
</Canvas>
```

## Jest mock shape

```js
jest.mock('@shopify/react-native-skia', () => {
  const React = require('react');
  const { View } = require('react-native');
  const SkiaNode = ({ children, style }) => React.createElement(View, { style }, children);
  return {
    __esModule: true,
    BlurMask: SkiaNode,
    Canvas: SkiaNode,
    Circle: SkiaNode,
    Group: SkiaNode,
    Points: SkiaNode,
    RadialGradient: SkiaNode,
    Rect: SkiaNode,
    vec: (x, y) => ({ x, y }),
  };
});
```

## Verification gate

```bash
npm test -- --runInBand
npm run lint
cd ios && bundle exec pod install
cd ..
CONFIGURATION=Release DERIVED_DATA=/tmp/<derived> DESTINATION='id=<sim-udid>' bash scripts/ios-simulator-run.sh
xcrun simctl uninstall <sim-udid> <bundle-id> || true
xcrun simctl install <sim-udid> /tmp/<derived>/Build/Products/Release-iphonesimulator/<App>.app
xcrun simctl launch <sim-udid> <bundle-id>
xcrun simctl io <sim-udid> screenshot /tmp/<proof>.png
```

## Closeout language

Report remaining deltas by class, not as generic TODOs:

- renderer-bound: fixed by Skia/WebGL/native canvas;
- font-bound: fixed by bundling target fonts;
- asset-bound: fixed by owned vector assets matching screenshot geometry;
- device-bound: dynamic island/status bar/home indicator vs flat design canvas;
- source-bound: exact Three.js point placement requires extracting/recreating the original point-generation function.
