# Mobile avatar 1:1 reference absorption + voice closure

Applicability: mobile/RN/PWA avatar or AI companion shells where the user asks to learn from a Behance/Dribbble/Figma/product reference, preserve a unified avatar UX despite internal routing lanes, and connect voice as the same avatar's fast lane.

Anti-conditions:
- Do not use this to copy protected brand assets, logos, illustrations, or proprietary iconography. Recreate layout, hierarchy, interaction model, and token feel with owned content.
- Do not expose online/local/offline/model/provider distinctions on the main user surface unless the product explicitly asks for a technical console.
- Do not treat a visual-only button, toast-only stub, or state-machine-only mock as a production voice loop.

## 1:1 absorption workflow

1. Lock exactly one master product and one target screen.
   - Write a reference-lock note with source URL, local screenshot path, target screen, allowed/forbidden secondary references, and copyright boundary.
   - Other references may inform product thinking only; they must not affect the visible layout until separately locked.
2. Build a screen map before coding.
   - Capture viewport, top chrome, brand pill, hero/avatar geometry, main copy block, bottom controls, safe-area, spacing, radii, typography, and accent/glow tokens.
   - Store it as structured JSON or a concise reference doc so implementation is measured rather than vibe-based.
3. Preserve the reference page type.
   - If the master is an avatar-first conversation screen, move engineering cards, diagnostics, queues, and dense explanation into a secondary details/sheet surface.
   - Main surface should remain presence + current intent + primary controls.
4. Map product semantics, not internal architecture.
   - Orb/avatar = assistant presence/state.
   - Primary mic/control = fast input/readback lane.
   - Side controls = text/details/readback entry points.
   - Diagnostics/queue/executor facts = secondary surface.
5. Verify with screenshot readback and regression tests.
   - Screenshot the implemented screen after a Release/native-shell build.
   - Compare hierarchy: top chrome, hint, avatar, intent text, bottom controls, absence of unrelated engineering UI.
   - Add tests for navigation traps introduced by moving controls off the main surface.

## Pitfalls found

- Mixing multiple references creates a plausible generic AI app but fails 1:1 restoration. Lock one master before writing UI.
- Moving composer/chips off the main screen can break product closure if there is no clear path to details/input and no return path. Add tests for `main -> details -> main` and `text control -> input surface`.
- A screenshot that looks Velo-like can still be a dead end if side controls only show toasts. Side controls must route to the real secondary action surface.
- In Jest, `react-native-safe-area-context` may render only `RNCSafeAreaProvider` without children unless mocked. If UI interaction tests cannot find the App subtree, mock `SafeAreaProvider` and `SafeAreaView` to render children.

## Voice fast-lane closure workflow

1. Keep voice as the same avatar input/readback lane, not a separate mode.
2. Add an explicit permission boundary before recording or speech recognition.
   - iOS needs `NSMicrophoneUsageDescription` and `NSSpeechRecognitionUsageDescription`.
3. Use a native/RN wrapper boundary instead of scattering `NativeModules` calls.
   - Wrapper should expose `requestPermissions`, `startListening(locale)`, `stopListening`, `cancelListening`.
   - If the native module is unavailable, fail closed with `unavailable`/error; do not fabricate transcripts.
4. Native iOS minimal path:
   - `SFSpeechRecognizer` + `SFSpeechAudioBufferRecognitionRequest` + `AVAudioEngine`.
   - On start: request/confirm permissions, configure `AVAudioSession`, install input tap, start recognition.
   - On stop: stop engine, end audio, return latest `bestTranscription.formattedString` plus duration.
   - On cancel/error: tear down engine/request/task and surface a short user receipt.
5. Feed transcript back into the existing typed-intent pipeline and persist its provenance.
   - Ordinary tasks become readback/processing receipts.
   - Risky/external actions require confirmation before side effects.
   - Ledger/thread messages should carry an input-mode marker such as `typed` / `voice` / `system`; do not leave voice as a toast-only side channel.
   - UI may show a compact voice-input marker on secondary conversation/details surfaces, but the main avatar surface should stay mode-unified.
6. Treat approved voice identity as a quality boundary.
   - If the user has approved a specific voice persona/provider, do not substitute a generic platform voice just to claim playback closure.
   - App-internal playback needs an explicit user/playback authorization path and evidence that the approved voice source is used.
7. Verification gates:
   - Unit test wrapper semantics with a fake native module.
   - Unit test risky voice intent confirmation.
   - Unit test transcript persistence into the same ledger with `inputMode: 'voice'` or equivalent metadata.
   - Release build must compile native bridge files and include permission strings.
   - Simulator screenshot verifies UI state; real mic/transcription should be verified on device or with a controlled simulator audio path before production claims.

## Manual-boundary closeout

Applicability: use this when all code/test/build steps are complete and the remaining gap is a privacy permission, human speech input, approved voice playback, or external side-effect authority. Anti-condition: do not invoke this boundary for ordinary UI, unit-test, or build failures that the agent can still fix.

When automatic work reaches the boundary, report the single decision point instead of continuing to invent minor optimizations:

- Microphone/speech permission dialogs require the user to approve.
- Real spoken input usually requires a human voice or controlled simulator audio fixture.
- External actions require a separate authority gate beyond dry-run/readback handoff.
- Approved voice playback requires explicit playback authorization and proof of the approved voice source.

## Closeout language

State separately:
- Visual/main-surface closure evidence.
- Navigation/product-loop closure evidence.
- Voice permission/native bridge evidence.
- Voice ledger/provenance evidence.
- What is still not production-closed: e.g. app-internal approved-voice playback, real task executor vs dry-run handoff, real-device speech recognition, or external side-effect authorization.
