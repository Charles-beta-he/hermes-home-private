# React Native Simulator UIMax Variant

Use this when UIMax is applied to a React Native app running in iOS/Android simulator rather than a browser DOM.

## Procedure

1. Run the native project gate first: lint, Jest, TypeScript if available.
2. Install/launch the app in a named simulator/device and capture screenshots with platform tooling (`xcrun simctl io ... screenshot` for iOS).
3. Score from both flow truth and pixels:
   - Flow truth: Jest/e2e assertions for route transitions, return paths, action receipts, and accessibility labels.
   - Pixels: simulator screenshots for hierarchy, wrapping, spacing, CTA discoverability, bottom navigation, and page identity.
4. Treat user-facing engineering/debug copy as a first-class UIMax issue. Examples: raw system state, Monorepo, authority chain, dry-run, device IDs, internal alpha, `RESTORE_SYSTEM_DEFAULTS`, `ACTIVE MONITORING`, English placeholders in an otherwise Chinese UI.
5. Add negative regression tests or production-gate checks that keep those strings out of default user surfaces.
6. Write before/after screenshot paths and a scoped grade such as `B+ local-production prototype`; do not call it external production unless distribution, signing, real-device, and cloud-write gates are verified.
7. If simulator clicks or deep links are unreliable, add/update native UI tests and let XCTest/Detox/Maestro drive the route. For iOS, prefer `xcodebuild test ... -only-testing:<UITest>` with accessibility labels/testIDs over desktop coordinate clicks. Capture screenshots while the test is deliberately holding on the target surface; do not capture after teardown.
8. Reject invalid screenshot evidence immediately: iOS home screen, launch screen, white/blank screen, bundle-loading overlay, permission/open-url confirmation dialogs, or the wrong route are FAIL/invalid evidence, even when tests pass.

## RN-specific scoring reminders

- Accessibility: `Pressable` should have `accessibilityLabel` and `accessibilityRole`; tab/segmented controls should have clear labels.
- Navigation: icon-only bottom bars often look Home-only; add visible labels and page identity.
- Bottom navigation must be pixel-audited after visual-system changes: background must match the design system, active/inactive colors must be intentional, items should have even spacing, and safe-area/bottom padding must not make it feel detached or cramped.
- Typography: large Chinese headlines must be checked on actual simulator screenshots for awkward line breaks.
- Top safe area and header spacing are not optional; if a screenshot shows content crowding/notch/header chrome, score the surface as failing until spacing is fixed and re-captured.
- Chips and quick prompts must be checked for right-edge clipping, inconsistent gap, and stale color systems; horizontal scroll rows need content padding at both ends. If a chip row still clips on the simulator, prefer a wrapping `flexDirection: 'row'` + `flexWrap: 'wrap'` layout for finite prompt sets rather than accepting horizontal-scroll edge clipping.
- Composer/input rows must be checked as pixels, not only contracts: input and primary CTA should read as one unit, CTA contrast must be clear, and disabled/low-contrast states must not look accidental.
- Avatar/orb-heavy designs: visual identity can be prominent, but it must not consume so much vertical space that CTA and navigation become secondary or hidden.
