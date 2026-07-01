# Stitch → RN WebGL bbox offset correction

Use this reference when a Stitch → React Native parity pass has already embedded or recreated the correct renderer (Skia/WebGL/Three.js), but the user still sees position offset in screenshots.

## Classification

- Reusable procedure: yes — element-level pixel alignment after renderer parity.
- Session/project-specific facts: keep concrete project IDs, local screenshot paths, and target screen IDs in the project evidence doc, not here.
- Anti-condition: do not use this to hide unfinished product wiring behind a full-screen bitmap unless the user explicitly chooses screenshot-diff minimization over native behavior.

## Trigger phrases / signals

- “看截图还存在位置偏移”
- “未达到像素级对齐”
- “not pixel aligned” after a WebGL/Skia renderer pass
- Full-frame diff improved but screenshot still looks shifted
- Renderer is correct, but element placement/scale is wrong

## Core lesson

Renderer parity is not pixel parity. After switching to WebView/Three.js or Skia, stop arguing from implementation fidelity and measure element bboxes against the target screenshot. The user will judge the screenshot, not the architecture.

## Procedure

1. Normalize images into one coordinate system.
   - Resize the RN simulator screenshot into the Stitch target screenshot size, or convert both to percentage coordinates.
   - Keep the original RN screenshot for review and a side-by-side proof.

2. Measure element-level masks, not only full-frame diff.
   Recommended rough masks:
   - `cyan/orb`: `G > 80 && B > 90 && R < 160`, bounded to the main/orb vertical range.
   - `white/title`: `R > 170 && G > 190 && B > 190`, bounded to the title vertical range.
   - `card/border cyan`: `G > 60 && B > 70 && R < 80`, bounded to the lower-card range.
   - `nonblack/header/nav`: `max(R,G,B) > 22`, bounded to the component region.

3. Record bbox center and size deltas for each component.
   Minimum anchors:
   - `header`
   - `orb_particles` — bright particle field only
   - `orb_all_cyan` — includes glow/nucleus/particles
   - `title_white`
   - `card_border`
   - `nav_border`

4. Fix layout by the largest visible anchor error first.
   - If `orb_particles.center.y` is low/high: move the orb surface, not the whole screen.
   - If `orb_particles.size` is too small/large: scale the WebGL/Skia canvas surface, not particle constants first.
   - If `orb_all_cyan` is correct but `orb_particles` is wrong: tune renderer/camera/particle size, not layout.
   - If title/card/nav are shifted after orb correction: adjust their anchors separately; do not regress a now-aligned orb.

5. Verify internal concentricity of composite hero objects.
   - Do not stop after the whole orb bbox is centered. For layered avatar/orb designs, measure or visually inspect each circle/layer: background atmosphere disk, glow disk, particle-ring centroid, WebGL/Skia canvas center, and nucleus/core circle.
   - If a user arrow points at “the circle” being off-center, treat that as a separate layer-registration bug, not a generic screen offset complaint.
   - Make decorative disks share the same parent coordinate system as the renderer surface. Avoid placing a background disk as an absolute child of the whole canvas while the orb renderer lives inside an offset/translated stage.
   - In WebGL/Three.js particle fields, center the generated point cloud around its own mean (`mean x/y/z`) before rendering, or a deterministic/random seed can leave the particle ring visibly off-center from the core even when the canvas is centered.
   - Avoid cumulative per-frame position multiplication when the acceptance target is center stability; animate from immutable base positions each frame so the particle centroid does not drift over time.

6. Rebuild and re-screenshot the real app.
   - Run Jest/lint.
   - Run `pod install` if native packages/assets changed.
   - Release build.
   - Explicit simulator uninstall/install/launch to avoid stale app screenshots.
   - Capture a new screenshot and recompute bboxes.

7. Close with deltas, not adjectives.
   Report before/after center and size deltas. Example format:

```json
{
  "orb_particles": {
    "before_center_delta_px": [0.5, 39.5],
    "after_center_delta_px": [2.0, -1.5],
    "before_size_delta_px": [-199, -225],
    "after_size_delta_px": [48, 43]
  },
  "nav_border": {
    "after_center_delta_px": [0.0, 0.0]
  }
}
```

## Pitfalls

- Do not treat “same Three.js code” as proof of pixel alignment. The WebView canvas can still be too small, too low, or composited differently.
- Do not rely only on full-frame diff. Device chrome, dynamic island, status bar, and unrelated lower surfaces can hide obvious component offsets.
- Do not tune all anchors at once. Fix the dominant visual object first, then title/card/nav.
- Do not crop/flatten the target bitmap as a silent shortcut. If a static bitmap layer is proposed, state the tradeoff explicitly.
- Do not compare raw pixels across simulator and Stitch frame sizes without normalization.
- Do not let a decorative background disk, WebGL/Skia particle field, and center nucleus be positioned by separate coordinate systems. Even if the outer bbox is aligned, non-concentric inner layers are visible immediately in screenshots.
- Do not call a particle orb centered until the particle cloud centroid and nucleus/core center are aligned. Recenter generated particles and animate from base positions to prevent drift.

## Acceptance guidance

For a strong pixel-level pass, aim for:

- header center delta within ~1px in normalized target coordinates;
- orb particle center delta within ~2–4px;
- nav vertical center delta within ~1px;
- title/card deltas stated explicitly if real-device safe area prevents exact alignment.

If one component remains visibly offset, keep iterating that component even if the renderer and tests are already correct.
