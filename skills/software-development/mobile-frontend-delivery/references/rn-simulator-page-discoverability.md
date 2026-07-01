# React Native simulator page discoverability and routing verification

Use when a React Native mobile shell appears to show only the Home page even though additional surfaces exist in code/tests.

## Applicability

- RN/iOS simulator app has multiple logical surfaces behind icon-only controls, bottom docks, avatar controls, or a generic detail page.
- User feedback says pages do not seem usable, clicks all appear to land on the same screen, or non-home pages are hard to discover.
- The task is UI/UX production readiness or simulator demo validation, not only unit-test correctness.

## Anti-conditions

- Do not apply this as a substitute for implementing missing routes. First verify whether the destination surface actually exists and has content.
- Do not claim real-device hardware features, permissions, microphone, push, App Store/TestFlight, or deployment readiness from simulator evidence alone.
- Do not record project-specific screen IDs, bundle IDs, or simulator UDIDs here; keep those in the project profile or run evidence.

## Procedure

1. Classify the issue before coding: missing surface, wrong route, touch-target overlap, or discoverability failure.
2. Verify the current runtime, not only tests:
   - run Metro if needed;
   - install/launch with `npx react-native run-ios --udid <booted-simulator-udid>`;
   - capture proof with `xcrun simctl io <udid> screenshot <path>`.
3. If the page exists but users cannot tell it exists, add visible labels to icon-only navigation. Accessibility labels are not enough for sighted discoverability.
4. If multiple controls route into one generic detail container, add an in-page segmented/tab switcher on the detail surface so users can move among pages without returning Home.
5. Keep current page state visually highlighted, and keep a visible return-to-home action.
6. Add regression assertions for:
   - visible navigation labels on Home;
   - each main entry changing `detail-surface-title` or equivalent visible page identity;
   - in-page tabs switching among at least two distinct non-home surfaces;
   - every `Pressable` retaining `accessibilityLabel` and `accessibilityRole`.
7. Re-run native lint/Jest, the production/UI gate if present, RN TypeScript build, and reinstall to the simulator.
8. Re-capture screenshots after reinstall; a pre-change screenshot is not proof of the running app.

## Pitfalls

- Unit tests can prove routing exists while the simulator still looks like Home-only because icon-only controls are visually ambiguous.
- A page titled with a generic concept such as “能力与边界” can make distinct routes look like a catch-all page; add page-local navigation or stronger page identity.
- Accessibility labels do not solve user-visible affordance; use both spoken labels and visible text labels for production demos.
- Rebuilding with Metro running does not guarantee the user is seeing the new UX unless the app was reinstalled/relaunched and a fresh simulator screenshot was captured.
