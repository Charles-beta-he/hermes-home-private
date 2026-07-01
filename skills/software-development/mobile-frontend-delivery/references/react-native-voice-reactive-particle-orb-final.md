# React Native voice-reactive particle orb final closure

Use when an RN avatar/orb must behave like a professional recording interface rather than a generic active/listening animation.

## Applicability

- RN/iOS avatar shell with a voice button and native speech recognition.
- Orb is rendered with Skia, Reanimated, WebView/Three.js, or another renderer that can consume live audio parameters.
- User expects the particles to respond to actual microphone input across multiple dimensions.

## Anti-conditions

- Do not auto-enable the microphone for visual polish. Voice remains user-initiated and permission-gated.
- Do not add a second recording pipeline if the existing speech-recognition `AVAudioEngine` tap can provide metering.
- Do not expose provider/model/runtime terms in the main UX.
- Do not claim physical mic responsiveness from simulator-only evidence; real-device mic testing remains a hardware boundary.

## Pattern

1. Split voice state from audio reactivity.
   - State animation (`idle/listening/transcribing`) is not enough.
   - Real reactivity must consume live microphone levels.

2. Reuse the existing native audio tap.
   - On iOS, compute metering in the same `AVAudioEngine` input tap used by `SFSpeechAudioBufferRecognitionRequest`.
   - Emit throttled events around 30 FPS to avoid bridge/UI overload.

3. Emit a multi-dimensional audio profile.
   - `level`: dB-normalized overall amplitude.
   - `rms`: smoothed loudness.
   - `peak`: instantaneous peak.
   - `decibels`: estimated dB.
   - `low`: low-band energy proxy.
   - `mid`: mid-band energy proxy.
   - `high`: high-band energy proxy.
   - `transient`: attack/plosive/clap detector.
   - `gate`: noise-floor gate to suppress idle shimmer.

4. Prefer lightweight band probes before full FFT.
   - Goertzel probes are sufficient for orb-driving bands and lower-risk than a full FFT path.
   - Example probe groups: low 90/160/250 Hz, mid 500/1000/2000 Hz, high 3500/5500/7500 Hz.
   - Promote to vDSP FFT only when the UI needs an actual spectrum analyzer, not just an expressive orb.

5. Map audio bands to visual dimensions, not one scalar.
   - Low band -> radius / bass breathing / core pulse.
   - Mid band -> particle flow / ripple / rotational energy.
   - High band -> sparkle / edge jitter / color brightness.
   - Peak -> immediate pop / point size.
   - Transient -> shockwave / ring pulse.
   - Gate -> quiet-room suppression.

6. Keep transcript and safety flows unchanged.
   - Partial/final transcripts should still enter the same avatar intent pipeline.
   - External or risky voice intents still require confirmation.

## Pixel/UI pitfall

For Stitch/Figma/RN parity, do not treat a whole-orb bbox as proof that internal circles are centered. Check each layer independently:

- dark atmosphere circle
- particle cloud/ring
- center sphere/core
- any shockwave/wireframe overlay

If circles are in different coordinate systems (for example WebView orb inside one container and atmosphere as a separate absolute sibling), move them under one parent coordinate system or compute explicit shared centers. User-visible arrows often point to layer-center mismatch even when the overall bbox is acceptable.

## Verification checklist

- Unit tests and lint pass.
- Native Release build passes after bridge changes.
- App launches with no blank WebView/redbox.
- Static screenshot confirms renderer and layout did not regress.
- Real-device test confirms microphone-driven response:
  - quiet room remains calm due to gate
  - low voice expands radius/breathing
  - normal speech increases particle flow
  - sibilants/high frequencies increase sparkle
  - clap/plosive triggers transient shockwave
  - transcript still reaches same avatar flow
  - high-risk voice commands still require confirmation
