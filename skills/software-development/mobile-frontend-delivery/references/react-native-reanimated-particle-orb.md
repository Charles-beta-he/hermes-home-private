# React Native Reanimated particle orb for mobile avatar shells

Scope: React Native mobile avatar/control-room screens where a central avatar/voice orb must feel alive (particle/electric/ion field) without making offline/local-model positioning the primary product message.

Applicability:
- RN 0.83–0.86 apps that can add `react-native-reanimated` and `react-native-worklets`.
- Avatar/voice surfaces that currently use static Views/gradients and need a minimal production-verifiable animation slice.
- Projects where the user experience should remain one unified avatar even if internal lanes include online authority, local cache, fallback, queue, or voice.

Anti-conditions:
- Do not use animation work as a substitute for product logic, permission gates, or evidence/readback wiring.
- Do not expose internal terms like local/offline/fallback/model/provider in the main interaction layer unless the product explicitly asks for diagnostics.
- If the project already uses Skia or needs thousands of particles/custom shaders, prefer a Skia canvas; this reference is the lightweight View/Reanimated path.

## Minimal Reanimated slice

1. Install compatible deps, checking the RN peer range first:

```bash
npm view react-native-reanimated version peerDependencies --json
npm install react-native-reanimated@<compatible> react-native-worklets@<compatible>
```

For RN 0.86, `react-native-reanimated@4.4.1` pairs with `react-native-worklets@0.9.x`.

2. Add the worklets Babel plugin:

```js
// babel.config.js
module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: ['react-native-worklets/plugin'],
};
```

3. Pod install for iOS:

```bash
cd ios
bundle exec pod install
```

Expected autolink/readback includes `RNReanimated` and `RNWorklets`.

4. Use Reanimated only for the moving layer; keep the surrounding shell ordinary RN Views. A proven structure:

- deterministic particle seed array (stable count, radius, angle, drift, delay, size, opacity)
- `AnimatedOrbParticle` with its own `useSharedValue`
- `withDelay(withRepeat(withSequence(withTiming(...))))` for pulsing
- `useAnimatedStyle` for opacity, translateX/Y, and scale
- separate animated current ring and nucleus pulse
- active voice/listening state changes duration, amplitude, brightness, and nucleus scale

5. Keep React Native lint happy by moving fixed anchors like `{ left: '50%', top: '50%' }` into a StyleSheet entry; dynamic width/height can stay inline when derived from particle size.

## Jest handling

If Jest fails to parse Reanimated ESM from `node_modules`, use a narrow mock in `jest.setup.js` instead of weakening the whole transform boundary:

```js
jest.mock('react-native-reanimated', () => {
  const { Animated } = require('react-native');
  return {
    __esModule: true,
    default: Animated,
    Easing: {
      inOut: (value) => value,
      sin: (value) => value,
    },
    useAnimatedStyle: (updater) => updater(),
    useSharedValue: (initialValue) => ({ value: initialValue }),
    withDelay: (_delay, value) => value,
    withRepeat: (value) => value,
    withSequence: (...values) => values[values.length - 1],
    withTiming: (value) => value,
  };
});
```

This keeps component tests focused on render/flow behavior while the simulator build verifies native animation packaging.

## Verification checklist

- `npm test -- --runInBand`
- `npm run lint`
- `bundle exec pod install` from `ios/` after adding native deps
- Release simulator build, not only Metro/dev render
- Simulator screenshot after launch: no redbox/crash; central orb visibly shows particle field/current ring/nucleus instead of a flat sphere
- If voice state is part of acceptance, capture both idle and active/listening screenshots or a short screen recording
- For 1:1 reference absorption, compare the generated/design-reference PNG and the fresh simulator screenshot visually, then record concrete deltas (particle density, safe-area frame, glyph/font substitutions, card/nav placement) in a scoped reference note. Do not call the slice aligned from tests alone.

## Existing Reanimated retry path

When the user asks to “上 Reanimated/Skia 粒子层” but the app may already have Reanimated installed, inspect before adding new rendering tech:

1. Read `package.json` for `react-native-reanimated` and `react-native-worklets` versions.
2. Verify `babel.config.js` contains `react-native-worklets/plugin`.
3. Check Jest setup for a narrow Reanimated mock.
4. Check `ios/Podfile.lock` / pod output for `RNReanimated` and `RNWorklets`.
5. If all are present, prefer improving the existing Reanimated View-layer orb before escalating to Skia. Skia is a later path for shader/canvas parity or thousands of particles.
6. Re-run pod install and Release simulator build after touching native deps or codegen-sensitive packages; RN/Reanimated builds can emit many third-party warnings while still succeeding.

## Pitfalls

- Installing Reanimated without the worklets plugin can pass static tests but fail at runtime.
- Skipping `pod install` after native deps leaves iOS build stale.
- Jest `setUpTests()` may import ESM and fail before tests start in some RN/Jest setups; a local mock is often lower-blast-radius.
- Do not let the improved animation reintroduce product copy that over-emphasizes offline/local model implementation. The main avatar surface should stay user-language-first.
- Do not switch to Skia just because the first screenshot is not pixel-perfect. If the product screen already uses Reanimated and passes Release build, first close the low-risk delta: density, scale, nucleus/ring proportions, top-bar/card/nav placement, icon/font assets, and reference-vs-simulator screenshot evidence.
