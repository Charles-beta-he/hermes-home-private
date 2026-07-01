# React Native voice-reactive WebGL/particle orb

Use when an RN avatar/orb visual should respond to live voice input, especially when the user references professional recording software, audio meters, or multi-dimensional sound-driven motion.

## Applicability

- React Native native shell with an iOS speech/microphone bridge.
- Avatar/orb visual is rendered by WebView/Three.js, Skia, Reanimated, or another particle/canvas runtime.
- User expects the orb to react to the recorded voice itself, not just to `listening` / `transcribing` state.

Anti-conditions:

- If microphone permission is not explicitly granted or voice channel is not open, do not start audio metering.
- Do not add a second hidden recording pipeline just for visuals; reuse the existing input tap when possible.
- Do not expose provider/runtime terms in the main UX.

## Core lesson

State-reactive animation is not voice-reactive animation. If the orb only changes when the state becomes `listening`, it is a fake/proxy response. Professional recording-style visuals need real audio features from the live input stream.

## Recommended architecture

1. Native speech/audio bridge emits lightweight level events while the existing mic tap is active.
2. RN listens to level events and stores a normalized `voiceLevel` / `voicePeak` state.
3. RN forwards the normalized values to the renderer:
   - WebView/Three.js: `webViewRef.current?.injectJavaScript(...)`
   - Skia/Reanimated: shared values or props with smoothing.
4. The renderer maps audio to multiple dimensions, not just one scale value.
5. Verify with tests/lint/build and a real simulator/device screenshot. A screenshot only proves rendering; real mic reactivity still needs device/manual or native event-injection proof.

## iOS metering pattern

When an `AVAudioEngine` input tap already feeds speech recognition, compute metering inside that tap:

- RMS: smoothed loudness
- Peak: transient emphasis
- dB: normalized loudness curve
- Level: UI-ready 0..1 value

Throttle events to about 30 FPS to avoid bridge overload.

Pseudo-flow:

```swift
inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
  emitAudioLevel(buffer)
  recognitionRequest.append(buffer)
}
```

`emitAudioLevel` should:

- read `buffer.floatChannelData`
- compute sum of squares and peak across channels
- smooth RMS with attack/release-like weighting
- convert to dB and normalize to 0..1
- emit a React Native event such as `HermesSpeechLevel`

## WebView / Three.js mapping pattern

Expose a safe setter in the WebView document:

```js
window.__setVoiceLevel = function(payload) {
  voiceLevel = clamp(payload.level)
  voicePeak = clamp(payload.peak)
}
```

Map level/peak to several visual dimensions:

- particle radius / expansion
- global orb scale
- particle size
- particle opacity / brightness
- core sphere scale
- core sphere opacity
- rotation speed / energy
- peak transient shock or sparkle

Keep base positions immutable and derive each frame from base + audio factor. Avoid cumulative multiplication of particle positions unless deliberate drift is desired.

## Professional-audio upgrade path

RMS/peak is the first real voice-reactive layer. For professional recording software aesthetics, add FFT/vDSP or WebAudio-style band analysis:

- Low band controls slow radius / bass pulse.
- Mid band controls flow speed / particle density.
- High band controls sparkle / edge particles.
- Transient detector controls quick outward shockwaves.
- Noise gate prevents idle shimmer in quiet rooms.
- Attack/release curves keep the movement musical rather than jittery.

## Verification checklist

- Unit tests still pass for speech runtime and UI rendering.
- Lint passes.
- iOS pod/build still succeeds after native bridge changes.
- Release simulator/device app renders without blank WebView or redbox.
- Voice channel only emits level events while explicitly listening.
- Orb remains visually centered when level is 0 and does not drift after sustained input.
