# React Native voice-reactive orb closure

Applicability: RN/iOS avatar or voice assistant surfaces where a visual orb/particle field should react to live microphone input while preserving a unified avatar UX.

Anti-conditions:
- Do not use this for passive/always-on microphones; voice must remain user initiated.
- Do not expose implementation lanes such as provider/model/local/online in the main UX.
- Do not claim final microphone proof from simulator-only screenshots; physical mic response needs real-device verification.

## Target pipeline

A production-ready voice orb should close this loop:

`user opens voice channel -> microphone permission -> AVAudioEngine/Speech tap -> audio profile -> RN bridge -> WebGL/Skia/Reanimated visual response -> transcript returns to the same avatar intent pipeline -> high-risk intent confirmation remains intact`.

## Professional-interaction mapping

Treat voice input as a subfunction whose mature reference domain is professional audio software, not generic chatbot animation. Map:

- RMS / loudness -> overall orb energy and opacity
- peak -> instantaneous particle pop
- low band -> slow radius / bass breathing
- mid band -> particle flow / ripple
- high band -> sparkle / edge jitter
- transient -> shock pulse
- noise gate -> calm idle in quiet rooms
- attack/release -> smooth response without jitter

Translate these mechanics into user-visible feedback; do not surface FFT/RMS/provider jargon in ordinary copy.

## Performance-safe implementation pattern

1. Native side: reuse the existing speech-recognition audio tap; do not add a second recording pipeline.
2. Keep audio analysis cheap on the hot path. Lightweight envelope/filter bands are often enough for an orb. Avoid multi-frequency Goertzel or FFT inside every tap callback unless profiled.
3. Emit a compact UI profile at a bounded cadence, e.g. `level`, `rms`, `peak`, `decibels`, `low`, `mid`, `high`, `transient`, `gate`.
4. RN side: store the latest profile in a ref/shared value if it only drives animation. Do not `setState` on every audio level event.
5. WebView/Three.js side: inject control messages on an active-only fixed cadence such as ~66ms, while the WebGL `requestAnimationFrame` loop renders independently.
6. Inactive state: send one idle reset and clear intervals. Jest open-handle warnings are a signal that the animation bridge is not lifecycle-clean.
7. Stop/failure state: reset the visual energy so stale loudness does not survive after no-speech or cancelled listening.

## Verification checklist

- Unit tests for voice state machine still pass.
- Lint passes.
- iOS Release simulator build installs and launches.
- Screenshot proves no blank WebView/redbox and no circle alignment regression.
- If a no-speech toast appears, distinguish environment/simulator mic input from speech pipeline bugs.
- Real iPhone mic acceptance checks: quiet room gate, normal speech flow, loud/low radius expansion, high-frequency sparkle, transient shock pulse, transcript handoff, external/high-risk confirmation.

## Common pitfall

A visually sophisticated orb can still be non-production if the data path is `audio event -> React state -> render -> WebView injection`. That couples high-frequency audio metering to the React scheduler and causes stutter. Decouple the hot data path from rendering and use throttled control messages.
