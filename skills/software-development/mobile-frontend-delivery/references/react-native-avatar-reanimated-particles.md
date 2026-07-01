# React Native avatar particle layer with Reanimated

Use when a mobile/RN avatar screen needs a voice-reactive particle/electric orb and the current implementation is a static sphere or static particle layout.

## Library choice

Prefer Reanimated for the first production slice when:

- The app already renders the avatar as React Native `View` layers.
- The goal is motion, pulse, drift, ring rotation, and voice-state amplification.
- You need minimal rewrite risk and native Release simulator proof.

Prefer Skia later when:

- Thousands of particles or shader-like turbulence are required.
- The design requires continuous fluid/noise fields, blur pipelines, or GPU canvas composition.
- The Reanimated View layer becomes too heavy or visually limited.

For RN 0.86, `react-native-reanimated@4.x` also needs `react-native-worklets@0.9.x`.

## Minimal Reanimated setup

Install:

```bash
npm install react-native-reanimated@4.4.1 react-native-worklets@0.9.1
cd ios && bundle exec pod install
```

Babel:

```js
module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: ['react-native-worklets/plugin'],
};
```

Jest can need a local mock instead of importing Reanimated's ESM module directly:

```js
jest.mock('react-native-reanimated', () => {
  const { Animated } = require('react-native');
  return {
    __esModule: true,
    default: Animated,
    Easing: { inOut: (v) => v, sin: (v) => v },
    useAnimatedStyle: (updater) => updater(),
    useSharedValue: (initialValue) => ({ value: initialValue }),
    withDelay: (_delay, value) => value,
    withRepeat: (value) => value,
    withSequence: (...values) => values[values.length - 1],
    withTiming: (value) => value,
  };
});
```

## Implementation pattern

1. Keep product state semantic: voice remains the same avatar fast lane, not a separate “mode”.
2. Generate deterministic particles at module scope so snapshots/tests are stable.
3. Create an `AnimatedOrbParticle` component per particle using `useSharedValue` and `useAnimatedStyle`.
4. Drive idle vs listening/transcribing differences with an `active` prop from voice state:
   - idle: slower pulse, lower opacity, smaller drift
   - listening/transcribing: faster pulse, higher opacity, larger drift, larger nucleus/current ring
5. Animate at least three layers:
   - particle drift/pulse
   - current ring rotation/scale
   - nucleus pulse
6. Keep UI copy product-level (`分身就绪`, `回读`, `确认`) and avoid exposing internal backend/runtime lanes on the main surface.

## Verification checklist

Run all of these before claiming completion:

```bash
npm test -- --runInBand
npm run lint
cd ios && bundle exec pod install
cd ..
CONFIGURATION=Release DERIVED_DATA=/tmp/<name> bash scripts/ios-simulator-run.sh
xcrun simctl io booted screenshot /tmp/<name>.png
```

Inspect the screenshot for:

- no redbox/crash
- particle field visible
- not a flat solid sphere
- control affordances still reachable
- no main-surface copy that over-emphasizes local/offline implementation details

## Pitfalls

- Reanimated 4 ESM can break Jest if you `require('react-native-reanimated').setUpTests()` directly in a non-transformed Jest setup. Use a mock or transform config.
- Installing JS deps is not enough for iOS; run `pod install` and verify the Release simulator build.
- A static particle field may look better than a flat sphere but still does not prove a live particle layer; verify the dependency, Babel plugin, and Release bundle.
- Don't introduce library changes without screenshot proof. Motion work must end with a real simulator/device screenshot, not just passing tests.
