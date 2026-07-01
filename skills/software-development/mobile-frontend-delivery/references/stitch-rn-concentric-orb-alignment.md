# Stitch/RN concentric orb alignment

Use when a mobile avatar screen has nested orb layers — background atmosphere circle, particle ring, core sphere, glow, or WebGL canvas — and screenshots show that the circles do not share the same center.

## Core lesson

Element-level bbox alignment can still miss nested-center errors. A full orb bbox may look centered while the background atmosphere, particle ring, and core sphere are each positioned in different coordinate systems.

When the user points to a circle being off-center, stop tuning the global screen bbox and inspect the local orb hierarchy.

## Typical root causes

- Background atmosphere circle is an absolute child of the full screen while the particle/WebGL orb is centered inside an orb stage.
- A particle/WebGL layer has a transform such as `translateY`, but the background circle does not share it.
- A WebView/canvas is scaled after the background glow was sized independently.
- Random particle generation has a visible centroid drift relative to the core sphere.
- Animation updates particle positions cumulatively and slowly moves the visible centroid.

## Preferred fix sequence

1. Make all orb visual layers share one parent coordinate system (`OrbStage`).
2. Center each circular layer with the same anchor model: `left/top: 50%` plus negative half-size margins, or flex centering with identical parent bounds.
3. Apply transforms to the shared stage or to every layer that must move together; do not apply translate/scale only to the WebView/canvas.
4. Keep the background atmosphere size independent from the renderer size only if its center is still derived from the same stage center.
5. For deterministic particle fields, compute the generated particle centroid and subtract mean x/y/z before rendering.
6. For animation, derive each frame from immutable base positions plus audio/time factors; avoid cumulative multiplication unless drift is intended.

## Verification checklist

- Background atmosphere circle center equals particle ring center.
- Core sphere center equals particle ring center.
- The center remains stable at idle level and during voice-reactive animation.
- The center is visually checked on the final device screenshot, not only in normalized bbox metrics.
- If title/card spacing changes after centering the orb, treat that as a separate layout pass.

## Anti-patterns

- Declaring pixel parity from full-screen diff while the visible nested circles are off-center.
- Fixing a local circle-center problem by moving the whole screen or header.
- Enlarging the background circle until the mismatch is less noticeable; this often hides the bug and creates title overlap.
