# Audio-Reactive Animation Absorption Pattern

Use this reference when a short video/demo shows audio-reactive visuals, VJ effects, particle systems, sound waves, waveform-driven UI, music visualizers, or similar animation effects.

## Transferable pattern

Do not treat the demo as generic video generation. Treat it as a realtime visual system:

```text
audio input -> frequency bands -> spatial zones -> visual field transform -> polish layers -> performance gate
```

## Capability graph

```yaml
atomic_modules:
  - audio_input_adapter
  - fft_band_extractor
  - band_to_zone_mapper
  - matrix_grid_generator
  - block_height_displacement
  - center_ripple_field
  - particle_emitter
  - glow_bloom_pass
  - camera_motion_controller
  - ui_control_panel
  - performance_budget_check

composite_modules:
  audio_reactive_matrix_core:
    subnodes:
      - audio_input_adapter
      - fft_band_extractor
      - band_to_zone_mapper
      - matrix_grid_generator
      - block_height_displacement
      - center_ripple_field

  visual_polish_layer:
    subnodes:
      - particle_emitter
      - glow_bloom_pass
      - camera_motion_controller

  interactive_visualizer_app:
    subnodes:
      - audio_reactive_matrix_core
      - visual_polish_layer
      - ui_control_panel
      - performance_budget_check
```

## V1 -> V2 upgrade recipe

```yaml
v1_baseline:
  - flat grid or low-density matrix
  - single amplitude-to-height mapping
  - minimal particles/light/camera

v2_upgrades:
  - denser matrix or instanced geometry
  - FFT frequency bands
  - bass mapped to center peak and ripple amplitude
  - mids mapped to surrounding terrain waves
  - treble mapped to particles and sparkles
  - radial ripple field
  - emissive core plus bloom/glow
  - camera orbit/angle changes
  - UI controls for density, sensitivity, ripple, particles, and glow
```

## Agent wrappers

```yaml
Audio Analysis Agent:
  wraps: [audio_input_adapter, fft_band_extractor, band_to_zone_mapper]
  policy:
    - preserve realtime constraints
    - do not request microphone without explicit user authority

Generative Visual Agent:
  wraps: [matrix_grid_generator, block_height_displacement, center_ripple_field]
  policy:
    - keep geometry performant
    - expose density and fallback controls

Polish Agent:
  wraps: [particle_emitter, glow_bloom_pass, camera_motion_controller]
  policy:
    - add visual richness without destroying legibility or fps

Performance QA Agent:
  wraps: [performance_budget_check]
  policy:
    - fail or degrade when fps/draw calls/memory exceed target budget
```

## Gates

```yaml
audio_permission_gate:
  pass: use microphone/file source
  warn: use demo audio only
  fail: no audio source
  blocked: user permission required

performance_gate:
  pass: target fps stable
  warn: reduce density/effects
  fail: optimize or fallback
  blocked: target device unknown

visual_quality_gate:
  pass: matrix/ripple/particles/glow/audio response visible
  warn: one layer weak
  fail: effect not distinguishable from baseline
  blocked: no visual evidence
```

## Implementation slice order

1. RED tests for pure audio/visual math modules: band split, matrix field, ripple field, particle spawn.
2. Minimal browser prototype with synthetic/demo audio so no microphone permission is required.
3. Optional file/mic Web Audio adapter behind user/browser permission.
4. Visual verification screenshot/contact sheet.
5. Performance gate before renderer escalation: FPS meter, quality state (`high|medium|low|manual`), adaptive density fallback, reduced particles/glow mode, and tests for the budget function. Do not wait until the WebGL/React packaging step to add this gate.
6. Renderer escalation: keep the Canvas prototype as baseline, then add a WebGL/Three.js `InstancedMesh` variant behind a separate entrypoint. Add a pure render-model adapter (field -> positions/scales/colors/emissive) with tests before binding to Three.js.
7. Browser verification for each renderer: load the actual page, inspect visuals, and check console errors. A syntax/unit green run is insufficient for visualizers.
8. Only then package as a React component or integrate into a larger app.

## Canvas -> WebGL ratchet pattern

When a Canvas audio-reactive prototype is accepted, promote it in small verified slices:

```text
math tests
→ Canvas runnable baseline
→ adaptive performance gate
→ render-model adapter tests
→ Three.js/InstancedMesh page
→ browser visual + console verification
→ README/evidence update
→ component packaging
```

Keep audio analysis and visual-field math renderer-agnostic. The WebGL page should consume the same `splitBands`, `computeMatrixField`, `spawnParticlesForEnergy`, and adaptive budget functions as the Canvas baseline, with only a thin Three.js adapter layer.

## Boundary

- A visual analysis or screenshot proves style absorption, not runtime implementation.
- A local Canvas prototype proves runnable concept, not production WebGL performance.
- A local WebGL/InstancedMesh prototype proves renderer feasibility, not production/mobile performance or reusable component packaging.
- Microphone capture, deployment, publishing, or embedding in a production app requires explicit gate/authority.
