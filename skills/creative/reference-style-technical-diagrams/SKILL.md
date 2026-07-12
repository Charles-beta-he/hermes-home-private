---
name: reference-style-technical-diagrams
description: Use when creating or revising technical/system diagrams where a user-provided image is a visual-style reference but the diagram content must match a different real system or architecture.
---

# Reference-Style Technical Diagrams

## Overview

Create technical diagrams that borrow a reference image's UI/visual language while keeping the content grounded in the target system. This skill is for the common failure mode where the agent either copies the reference diagram's architecture or over-labels the generated artwork with meta-explanations instead of producing a clean diagram.

## When to Use

- The user supplies an image and asks for a diagram in the same style.
- The user says the image is only a UI/visual reference, not the content source.
- The user corrects diagram style, legibility, resolution, or labels.
- You are generating SVG/HTML/PNG architecture diagrams, workflow maps, or capability graphs from a real system chain.

## Procedure

1. Split the brief into two tracks before drawing:
   - **Visual style source:** palette, illustration density, card shape, stroke, icon style, typography mood, background, arrow style.
   - **Content source:** the actual system chain, modules, boundaries, event flow, governance layer, or API/runtime facts.
2. Treat the reference image as style-only unless the user explicitly asks to copy its architecture.
3. Remove meta-labels from the artwork. Do not include phrases such as "real", "cartoon version", "content aligned", "style reference", or "according to reference" unless they are part of the user's desired title.
4. Prioritize legibility over decorative fidelity:
   - use large system fonts for Chinese/English mixed labels;
   - keep short labels and push explanations outside the image or into a separate table;
   - use high-contrast text on flat fills;
   - export PNG previews at high resolution (e.g. 4K+ width) when the user cares about clarity.
5. If style feedback repeats, stop blind regeneration. Load a visual/design skill or reference, restate the corrected visual target in one compact line, then regenerate.
6. Verify the image with vision/readback before claiming it is done: check text overflow, readability, unwanted meta-labels, and whether the target system's key modules are present.

## Common Pitfalls

- Copying the reference diagram's content when the user only wanted its style.
- Writing explanatory process notes inside the diagram itself.
- Using hand-drawn/cartoon fonts that look stylistically close but make Chinese labels blurry.
- Claiming UI/visual acceptance from source code or file existence without inspecting the rendered output.
- Letting decorative icons crowd out the architecture chain.

## Verification Checklist

- [ ] Style source and content source are separated.
- [ ] Diagram labels come from the target system, not from the reference image unless requested.
- [ ] No unwanted meta-labels are present.
- [ ] Text is legible at the delivered resolution.
- [ ] Rendered PNG/SVG/HTML was inspected before final delivery.
