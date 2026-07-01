# React Native iOS shell delivery notes

Applicability: use for React Native iOS shell packaging in a monorepo, especially when a PWA/offline assistant core is shared with RN through a pure TypeScript package. Anti-conditions: do not treat the examples here as project-specific paths, bundle IDs, or a mandate to use one RN version; verify against the current RN template and local CocoaPods/Xcode state.

## Core delivery rules

- Do not stop at `xcodebuild build` success. A native shell is not delivered until it can be installed and launched on a simulator/device and a screenshot/log proves the foreground UI is visible.
- For PWA/RN compatibility, keep offline/business logic in a pure TS package and make RN consume that package through Metro/Jest mappings; do not fork the logic into native-only copies.
- Personal-free signing is a human gate: the user must select their Apple account/Personal Team in Xcode. Before that, verify simulator build/launch and provide a signing doctor script.

## Required verification ladder

1. JS/native tests: `npm test -- --watchAll=false`, `npx tsc --noEmit`.
2. Metro bundle: `npx react-native bundle --platform ios --dev false --entry-file index.js --bundle-output /tmp/App.jsbundle --assets-dest /tmp/App-assets`.
3. Xcode simulator build with bundling: `xcodebuild ... -sdk iphonesimulator CODE_SIGNING_ALLOWED=NO FORCE_BUNDLING=1 build`.
4. Install and launch: `xcrun simctl install booted App.app` then `xcrun simctl launch booted <bundleId>`.
5. Screenshot after launch: `xcrun simctl io booted screenshot /tmp/app.png`; inspect that the app UI, not the Home Screen, is foregrounded.
6. If launch returns a PID but screenshot remains Home Screen, inspect logs before claiming success.

## Launch failure diagnosis

Use:

```bash
xcrun simctl spawn booted log show --style compact --last 5m \
  --predicate 'process == "AppName" OR eventMessage CONTAINS[c] "bundle.id"'
```

A common RN new-architecture/prebuilt failure shape is:

```text
OS_REASON_DYLD | Library not loaded: @rpath/ReactNativeDependencies.framework/ReactNativeDependencies
Referenced from: .../App.app/Frameworks/React.framework/React
```

This means build/bundle succeeded but the app is missing a runtime framework. Treat this as a runtime embed issue, not a JS UI failure.

## ReactNativeDependencies pitfall

- `React.framework` may link against `ReactNativeDependencies.framework`.
- If the app bundle contains only `React.framework` and `hermesvm.framework`, launch can crash immediately with dyld while `xcodebuild` still reports success.
- Check with `otool -L App.app/Frameworks/React.framework/React` and `find App.app/Frameworks -name '*.framework'`.
- Be careful with the tempting fix `pod 'ReactNativeDependencies'` directly: it may pull RN third-party pods into source resolution (`fast_float`, `RCT-Folly`, `fmt`, old `glog`/`boost`) and create a different CocoaPods build failure. Prefer a narrow embed/prebuilt-artifact fix, or align with the exact RN template/CocoaPods integration that generates `ReactNativeDependencies.framework` without switching the dependency graph to old source builds.
- If you experiment with explicit pods and CocoaPods begins resolving old `glog`/`boost` source builds, revert that path and document the blocker.
- Applicability: generated RN iOS shells using RN prebuilt artifacts where a failed CocoaPods experiment changed the dependency graph. Anti-condition: do not apply to ordinary source-build RN projects that intentionally compile third-party pods. After reverting a bad explicit-pod experiment, clear polluted Pods state with a clean install rather than trusting the existing `Pods/` tree: remove `Pods`, `Podfile.lock`, and generated iOS build output, then run `bundle exec pod install --clean-install` and verify the lock/app bundle returns to the intended prebuilt shape. The lesson is the clean reset pattern, not a durable claim that ordinary `pod install` is broken.
- Applicability: narrow runtime-embed workaround for missing RN prebuilt dependency frameworks. Anti-condition: skip when the official template/CocoaPods integration already embeds the framework correctly. RN dependency tarballs can contain Mach-O framework binaries without the executable bit (`-rw-r--r--`); if an embed script copies from the RN cache tarball, verify with file existence / Mach-O inspection and `chmod ugo+x` after copy rather than failing solely because the tarball did not preserve execute permission.

## Narrow prebuilt framework embed pattern

Applicability: use only when simulator/device logs prove a dyld launch crash from a missing RN prebuilt dependency framework and the built app bundle lacks that framework. Anti-conditions: do not use this to bypass unresolved CocoaPods source-build failures; do not use it when the framework is already embedded by the current RN template.

1. Locate the verified RN dependency tarballs in the local React Native cache for both debug and release variants.
2. Select the simulator slice for simulator builds and the device slice for device builds.
3. Add an app-target Xcode shell build phase after the CocoaPods framework embed phase that extracts the missing framework from the matching prebuilt tarball and copies it into `$TARGET_BUILD_DIR/$FRAMEWORKS_FOLDER_PATH`.
4. After copy, make the framework binary executable and codesign only when Xcode signing is enabled and a signing identity is present.
5. Verify with a clean DerivedData build, list the built app's `Frameworks/`, assert the missing framework binary exists/executable, then install/launch and screenshot the foreground app UI.

## Interactive shell acceptance

Applicability: RN/iOS shells intended to act as an assistant, companion, offline context reader, or user-facing control surface. Anti-conditions: skip for intentionally read-only diagnostics screens, splash screens, or pure smoke-test fixtures.

- Do not accept a static evidence/status card as a usable assistant shell. The shell must expose at least one real interaction loop: input or selectable prompt, submit action, local answer/refusal/handoff status, and evidence/source inspection when evidence is used.
- Add native Jest or pure-state tests for interaction semantics, not only a render smoke test: evidence-backed questions answer locally with hits/spans, realtime/action/insufficient-evidence questions queue or refuse instead of pretending offline execution, and blank input does not produce a fake answer.
- If simulator-level tap/type injection is unavailable in the local Xcode toolchain, say so explicitly and separate verification layers: screenshot proves controls render, component/state tests prove logic, and XCUITest/manual device testing remains the physical tap/keyboard acceptance layer.
- Accessibility rule: every interactive control needs an accessible label or stable test identifier so later XCUITest/Appium/manual QA can target it reliably.

## Enterprise assistant shell UX baseline

Applicability: production-facing RN/iOS assistant shells, offline companions, or enterprise control surfaces where users expect a usable assistant rather than a smoke-test fixture. Anti-conditions: skip for internal diagnostics, one-screen proof-of-linking demos, or deliberately read-only status dashboards.

A production assistant shell should land the interaction model, not just the rendering model:

1. Use a conversation-led layout with system/user/assistant messages, not isolated static cards.
2. Show operational state near the top: local/online runtime, queue count, capability boundary, and whether the latest answer is local, queued, blocked, or needs online reconciliation.
3. Keep the composer reachable and predictable: multiline input, disabled send for blank input, clear/reset affordance, keyboard-safe layout, and suggested prompts for common intents.
4. Put evidence/source controls before long answer bodies so traceability remains visible above the fold; do not bury citations after a long generated paragraph.
5. Distinguish local evidence answers from realtime/current-fact/action requests. Current/action/insufficient-evidence requests should create a queued handoff/refusal state rather than pretending offline execution succeeded.
6. Test the state machine separately from visual rendering: conversation ledger growth, queue count, blank-input guard, evidence hit/span counts, handoff status, and source-summary generation.
7. For verification, separate layers honestly: native unit/state tests prove logic, simulator screenshot proves production shell rendering, and XCUITest/Appium/manual device QA proves physical tap/keyboard behavior.

## Production shell persistence and UI-test closure

Applicability: RN/iOS assistant shells with local/offline state, queued online handoff, or evidence-backed answers. Anti-conditions: skip for pure stateless demos or apps whose persistence is already owned by a server cache/client sync SDK with its own migration and test harness.

- Do not leave assistant thread/queue state purely in React component memory. Add a small persistence adapter boundary (for example AsyncStorage on RN) that stores only local projection/envelope state: schema version, saved timestamp, conversation/thread projection, and queued handoff projection. Explicitly forbid this layer from writing canonical facts.
- Add tests for persistence semantics, not just render state: save/load/clear, malformed or missing storage returning `undefined`, and envelope contents proving only local projection is persisted.
- Surface persistence state in the UI (`restoring` / `saved` / `error`) and provide a reset affordance that clears local projection and returns queue count to zero.
- For true mobile acceptance, add XCUITest/Appium/Detox once controls exist. Component tests and screenshots are not enough for production UX because they do not prove keyboard/tap flow.
- Keep XCUITest target references and shared schemes under source control, then add a script that runs the UI tests and prints a filtered test summary rather than flooding logs.
- If a Debug UI-test configuration hits RN/new-architecture/native-module link issues but Release build/launch is healthy, prefer a Release UI-test scheme for production interaction coverage. Document the version-specific pitfall with applicability and anti-conditions rather than claiming Debug is generally unusable.
- UI-test coverage should exercise a real user path: launch, verify shell identity/status, find source/evidence control, scroll to composer, type, send, assert queued/offline status, reset, and assert queue zero.

## Grounded small-model first lane

Applicability: RN/iOS or PWA-compatible offline assistant shells where the user wants a local/small-model experience before device signing, model packaging, or native runtime selection is fully proven. Anti-conditions: skip when a real signed device runtime and approved model artifact already exist, or when the task is explicitly only to evaluate CoreML/llama.cpp packaging.

- Do not make the first local-model milestone depend on downloading or committing large model binaries. Start with a tiny bundled adapter behind the same `LocalModelAdapter`/citation contract used by the real runtime: input is retrieved evidence, output is text plus `citedHitIds`.
- Treat the adapter as a production safety lane, not a fake success: its output must be accepted only when citations are non-empty and every cited id is a subset of retrieved evidence. Invalid citations, empty text, or no evidence must fall back to deterministic/refusal behavior.
- Surface the runtime in the UI with user-facing language such as `小模型 · tiny-extractive`, not only internal enum names. Add XCUITest/assertions that the small-model label is visible.
- Keep the adapter swappable: CoreML, llama.cpp, MLX, or WebView/WASM should implement the same grounded contract later rather than forking assistant logic.
- Pair local queued handoff with a dry-run Gateway/API contract before real side effects: validate idempotency, source message id, requested action, and evidence ids; return accepted/rejected/readback status; do not write canonical facts or execute external actions.

## Hybrid Gateway acceptance is not the same as dry-run code

Applicability: RN/iOS or PWA assistant shells that claim online, Hybrid, Gateway, handoff, or production-grade mobile behavior. Anti-conditions: skip only for deliberately offline-only clients where the UI and docs clearly say no online path exists.

- Do not call a shell “Hybrid” or “online handoff complete” merely because a Gateway contract or payload builder exists. The app runtime must actually submit over HTTP (or the chosen transport) and read back accepted/rejected/offline state.
- The UI must reflect the real state. If the app is offline-only, say Local/offline; if Gateway submission is wired, show Hybrid/Syncing/accepted/offline fallback. A screenshot that still says `Local` or `离线分身` disproves an online-complete claim.
- Add a client boundary for submission, not only payload construction: base URL/device id, timeout, accepted/partial/rejected/offline/error states, and a fallback that preserves local queue when Gateway is unreachable.
- For safe production landing, first wire a no-side-effect dry-run endpoint and verify both sides: accepted readback from `POST /.../dry-run`, plus a negative readback proving the dry-run did not write queued records or canonical facts.
- XCUITest should start or require the local Gateway and assert the user-visible accepted/readback state, not just queue count. Release screenshots should visibly show Hybrid/Gateway accepted status.
- If a default Gateway port is occupied, do not kill unrelated processes; move the mobile test lane to a scoped port and document it in scripts/docs.

## Gateway readback must become projection state

Applicability: RN/iOS or PWA assistant shells with local queued handoff plus online/Gateway readback. Anti-conditions: skip for stateless clients or intentionally ephemeral demos.

- Do not stop at storing Gateway accepted/rejected in React/component state. Accepted/rejected readback must be written into the local projection envelope so app restart, persistence, and auto-flush behavior remain correct.
- Accepted handoffs should become a submitted/accepted local projection state and be excluded from future dry-run payloads. Otherwise app restart can resubmit the same handoff and a screenshot can show contradictory state such as `queue 0` plus `Gateway dry-run: pending`.
- Rejected/offline/error handoffs should remain queued/pending with reason, submittedAt, attemptCount, lastError, and nextRetryAt so retry remains possible; do not drop them silently.
- If retry metadata is persisted, add a bounded in-app scheduler that selects the earliest pending nextRetryAt and triggers the same dry-run transport when the app is active. Accepted handoffs must be ignored by scheduler selection, and the scheduler must not bypass dry-run/no-side-effect authority.
- UI status should derive from persisted projection as well as current in-memory result. If `gatewayResult` is missing after hydration but persisted accepted items exist, show accepted/recorded state rather than pending.
- XCUITest should assert the production semantics after send: Gateway accepted, local projection recorded, and pending queue zero. Keep the assertion semantic (`本地投影已记录`) rather than overfitting to a specific bubble/location.

## Gateway config, retry, and cleanup boundary

Applicability: mobile Hybrid/Gateway shells tested against local dev Gateway. Anti-conditions: skip for purely offline shells or clients whose transport/retry is owned by a separate SDK.

- Centralize Gateway base URL, device id, timeout, max attempts, and retry base delay in a small config module; avoid hardcoding them directly in the screen component.
- Surface connection/authority state in the UI: Gateway URL, device id, and whether the lane is dry-run only. This prevents hidden coupling and makes screenshots prove which backend/authority path was exercised.
- Retry only transient network failures/timeouts with a bounded attempt count/backoff. Deterministic HTTP errors (especially validation/auth 4xx) should fail fast and preserve the local queue for operator action.
- When UI tests or screenshot helpers start a local Gateway, clean up Hermes-owned listeners afterwards. Before killing a port, verify the command path belongs to the current project; do not kill unrelated processes just because they occupy the default port.
- If XCUITest fails after adding status assertions, inspect screenshot and app/test logs before weakening the assertion. A failure may reveal a real state-derivation bug rather than flaky automation.

## Monorepo mappings

- Metro needs `watchFolders` and `extraNodeModules` for shared packages outside the generated RN app.
- Jest may need `moduleNameMapper` to map shared packages to TS source if the shared package is ESM-only or uses bundler-style extensionless imports.
- Keep native Jest separate from wrapper/package Vitest. Configure wrapper Vitest `include`/`exclude` so it does not scan `native/__tests__` and try to parse React Native Flow files.

## Signing doctor pattern

Add a script that reports:

- Node/npm/Xcode/CocoaPods versions.
- `security find-identity -p codesigning -v`.
- `xcodebuild -showdestinations`.
- `xcrun devicectl list devices`.
- booted simulators.
- exact Xcode manual steps for personal-free signing.

This keeps account/device gates explicit without pretending the agent can sign with a user’s Apple account.
