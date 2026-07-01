# React Native iOS Simulator Acceptance

Use this reference when a React Native/mobile shell needs local iOS Simulator acceptance before physical-device or TestFlight gates.

## Applicability

- React Native iOS app in a monorepo with CocoaPods.
- User asks for simulator / 真机式验收 / installed-app acceptance.
- Need evidence beyond Jest: simulator build, install, launch, screenshots, and UI interaction tests.

Anti-conditions:

- Do not claim physical-device acceptance from simulator evidence.
- Do not claim TestFlight/App Store release from local simulator evidence.
- Do not treat XCUITest screenshots on SpringBoard/Home as app UI proof.

## Recommended acceptance stack

1. Preflight JS gates:
   - package lint/typecheck/build if present.
   - RN Jest/component tests.
2. Release simulator build for install/foreground visual proof:
   - Build through the CocoaPods workspace, not the standalone `.xcodeproj`.
   - Example shape:
     ```bash
     xcodebuild \
       -workspace ios/<App>.xcworkspace \
       -scheme <App> \
       -configuration Release \
       -sdk iphonesimulator \
       -destination 'id=<SIM_UDID>' \
       -derivedDataPath /tmp/<app>-release-derived \
       CODE_SIGNING_ALLOWED=NO \
       FORCE_BUNDLING=1 \
       build
     ```
   - Verify `** BUILD SUCCEEDED **` and locate `<App>.app` under `Build/Products/Release-iphonesimulator/`.
3. Install and launch:
   ```bash
   xcrun simctl boot <SIM_UDID> 2>/dev/null || true
   xcrun simctl bootstatus <SIM_UDID> -b
   xcrun simctl uninstall <SIM_UDID> <bundle.id> 2>/dev/null || true
   xcrun simctl install <SIM_UDID> /path/to/<App>.app
   xcrun simctl launch <SIM_UDID> <bundle.id>
   xcrun simctl io <SIM_UDID> screenshot /tmp/<app>-foreground.png
   ```
4. Visual acceptance:
   - Confirm app is foreground, not SpringBoard/Home, blank, or loading.
   - Check header/safe area, bottom navigation, primary action, and readable page identity.
   - For small simulators, distinguish acceptable partial lower-card occlusion from blocked primary controls.
5. XCUITest interaction acceptance:
   - Debug XCUITest for RN usually needs Metro on `127.0.0.1:8081`; start Metro before testing Debug apps.
   - Prefer `ONLY_ACTIVE_ARCH=YES` to reduce simulator test build time.
   - Drive routes through app-visible controls when validating UI layout. `simctl openurl`/deep links can trigger an iOS “Open in <App>?” confirmation prompt; screenshots with that prompt are invalid unless the task is specifically about URL handling.
   - For global bottom-tab or scroll-overlap issues, capture both the first-screen state and a bottom-scrolled state for every long surface. Native existence assertions for the tab buttons are not enough; the screenshot matrix must show that the last card/composer/footer remains readable above the tab.
   - Example shape:
     ```bash
     npm --prefix <rn-app> start -- --host 127.0.0.1
     xcodebuild test \
       -workspace ios/<App>.xcworkspace \
       -scheme <UITestsScheme> \
       -configuration Debug \
       -sdk iphonesimulator \
       -destination 'id=<SIM_UDID>' \
       -derivedDataPath /tmp/<app>-uitest-derived \
       CODE_SIGNING_ALLOWED=NO \
       ONLY_ACTIVE_ARCH=YES \
       -only-testing:<UITestTarget>/<Class>/<testName>
     ```
   - Required evidence: `Executed N tests, with 0 failures` and `** TEST SUCCEEDED **`.
6. Cleanup:
   - Kill Metro/background servers.
   - Verify port 8081 has no listeners unless intentionally kept.
   - Verify no `xcodebuild`, `UITests-Runner`, or app process remains.
   - Report whether the simulator itself is still booted separately from service/process residue.

## Pitfalls and fixes

- **Building `.xcodeproj` instead of `.xcworkspace`.** RN/CocoaPods simulator builds can fail with missing module maps or `no such module React`. Use the workspace.
- **Debug XCUITest without Metro.** The app can launch but render no RN tree. Start Metro for Debug interaction tests, or use Release for screenshot-only proof.
- **Treating SpringBoard after tests as app evidence.** XCUITest may terminate the app and return to Home. Relaunch and capture a final foreground app screenshot before acceptance.
- **Text-only XCUITest selectors drift.** Use stable `testID`/accessibility identifiers where possible, and keep copy selectors as fallback. Current RN/iOS accessibility may expose buttons/testIDs more reliably than long Chinese static text.
- **Deep-link screenshots can be contaminated by iOS confirmation prompts.** `simctl openurl` is useful for routing diagnostics, but the resulting “Open in <App>?” alert makes the screenshot invalid for UI acceptance. Prefer XCUITest taps on the app’s own navigation; if URL routing is required, explicitly dismiss/accept the prompt and recapture after the app page marker is visible.
- **Small-screen bottom navigation covering lower cards.** If a lower quick card is partially under the floating nav, test the visible primary composer/header CTA first; only use coordinate fallback after accessibility/hittability checks fail.
- **First-screen-only screenshots miss bottom overlap.** For ScrollView/list/detail surfaces, swipe to the bottom and capture a second screenshot before claiming the global tab does not cover content. Pair this with a code-level assertion that the shared content container reserves at least the tab height plus margin.
- **Release double-arch XCUITest is slow.** For interaction smoke, Debug + Metro + `ONLY_ACTIVE_ARCH=YES` is usually the practical path; keep Release build/screenshot as installable-app evidence.

## Acceptance wording

Say `PASS for local iOS Simulator acceptance` only when build, install/launch, foreground screenshot, and interaction smoke have all passed. Keep boundaries explicit: physical device, TestFlight/App Store, push/deploy, and external dispatch remain closed unless separately authorized and verified.
