# React Native global bottom tab closeout

Use when a mobile/RN shell has bottom navigation, especially after a user reports that tabs appear only on Home, content is clipped by the tab bar, or there is excessive blank space around the tab.

## Reusable procedure

1. Treat “tab only appears on Home” as a P0 information-architecture defect, not a cosmetic issue.
   - The bottom tab must live in the app shell / shared route layout, not inside the Home screen body.
   - If a modal is open, it may cover the tab intentionally; non-modal pages must still show the global tab.

2. Make the tab testable by both code tests and native UI tests.
   - Add stable `testID`s for the tab container and each item.
   - Add explicit `accessibilityLabel`s that are unique and route-level, e.g. `底部导航：主控`, `底部导航：知识库`, `底部导航：语音`, `底部导航：设置`.
   - In XCUITest, assert `app.buttons["底部导航：…"]`, not label `StaticText`s; React Native text inside Pressable often does not appear as standalone `StaticText`.

3. Prefer a layout slot over an overlay for production bottom tabs.
   - An absolute/floating tab can pass presence checks while still covering cards, composers, or list endings.
   - Place the tab as a normal bottom slot in a flex column when feasible.
   - If the design requires overlay, prove there is no overlap with actual screenshots and/or measurable content-inset checks.

4. Screenshot matrix must include every affected route and every scroll endpoint.
   - Home: tab visible, active state correct, no “nav island” blank gap.
   - Input/composer page: tab visible, composer not covered, chips wrap, no half-clipped cards above tab.
   - Settings/detail page: tab visible with correct active state and no overlap.
   - Diagnostics/modal: modal containment, close button, contrast; tab may be behind modal if intentionally dimmed.
   - For any ScrollView/list/detail surface, capture both the first-screen state and a bottom-scrolled state (for example two `swipeUp()` calls) to prove the last card/composer/footer is not hidden by the global tab. A first-screen screenshot alone does not close a bottom-overlap report.

5. Reject invalid screenshots.
   - iOS desktop/home screen is not evidence.
   - Wrong route is not evidence.
   - Loading screen is not evidence.
   - A screenshot after test teardown is not evidence.
   - A screenshot with an iOS system deep-link confirmation prompt such as “Open in <App>?” is not evidence for app UI. If `simctl openurl`/deep links are used, first clear the prompt and then recapture, or prefer in-app/XCUITest taps from real global tab buttons.
   - Add deliberate XCUITest `sleep`/hold windows after reaching the target route and before teardown/opening modal when screenshots are needed.
   - If route launch arguments or URL schemes are used to jump to a surface, first assert the intended page marker; otherwise fall back to user-like XCUITest navigation through the app’s visible controls.

6. If the tab fix creates large blank space, solve the layout problem rather than hiding it.
   - Compress header/hero/composer/card spacing.
   - Add real lightweight product information where appropriate.
   - Remove/shorten first-screen blocks that get clipped by the tab.
   - Do not restore debug/engineering cards to fill space on primary mobile surfaces.

## Verification checklist

- `production:gate` checks global tab anchors.
- RN/Jest asserts tab exists on Home and at least one non-Home surface.
- RN/Jest or component tests assert shared non-Home scroll containers reserve at least the global tab height plus visual margin (for example `contentContainerStyle.paddingBottom >= tabHeight + 24`).
- XCUITest asserts global tab buttons on Input and Settings.
- Real simulator screenshots exist for Home, Input, Settings, and modal/diagnostics when relevant.
- Real simulator screenshots include bottom-scrolled states for long list/detail pages such as Knowledge, Settings, Release, and Input.
- Visual audit explicitly checks: top safe area, tab active state, tab height, content-to-tab gap, no clipping/overlap, chip wrapping, composer+CTA layout.
- Final report records exact commands, screenshot paths, and whether external release remained gated.

## Anti-conditions

- Do not turn this into a project-specific rule about one app’s exact routes or copy.
- Do not preserve transient simulator permission/click failures as durable constraints; capture only the stable workaround: UI-test-driven route navigation plus screenshot hold windows.
