---
name: reference-style-diagramming
description: Use when generating architecture diagrams, workflow maps, infographics, or SVG/HTML visuals from a user-provided reference image where matching the visual style is part of acceptance.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [diagramming, visual-style, reference-image, cartoon-infographic, svg, architecture]
    related_skills: [architecture-diagram, design-md, excalidraw, uimax-audit]
---

# Reference Style Diagramming

## Overview

Use this skill when the user provides a reference diagram/image and asks for a new diagram in the same style. In this class of task, content correctness is not enough: visual style match is a first-class acceptance criterion.

Core rule:

```text
Reference image style overrides the default diagram template.
```

Do not default to dark technical architecture diagrams, whiteboard sketches, or generic flat SVGs unless the reference actually looks like that.

## When to Use

Use when the user says or implies:

- “按这个图的风格”, “同样的风格”, “像这张图”, “参考这个图生成”
- “你这个风格不对”, “不是白板，是卡通”, “差很多”
- they provide a screenshot/reference image for diagram style
- they want architecture/workflow/system diagrams as an illustrated poster or infographic

Do not use when:

- no reference style is provided and the user only asks for a schematic
- the user explicitly requests a specific non-reference style such as “dark infra architecture diagram”
- the task is pure UX screenshot reproduction rather than diagram generation

## Procedure

1. **Style classify before drawing**
   - Identify background family: dark grid, whiteboard, light paper, cartoon poster, product infographic, etc.
   - Identify stroke language: thin technical lines, hand-drawn sketch, thick black cartoon outlines.
   - Identify typography: monospace engineering, rounded handwritten, clean product sans.
   - Identify module shapes: sharp rectangles, rounded cards, cloud brains, stickers, speech bubbles, device mockups.
   - Identify icon density: labels only vs illustrated icons/characters/gears/robots/shields.
   - Identify arrow language: straight connectors, thick curved arrows, dashed playful paths, conveyor belts.

2. **Separate content graph from visual rendering**
   - First map the architecture content: nodes, sequence, grouping, event/protocol belt, gates.
   - Then render using the reference visual grammar. Do not let the default architecture style leak into the output.

3. **Generate a first artifact**
   - Prefer editable SVG/HTML when image generation is unavailable or when labels must be exact.
   - If image generation is available, use the source image as a reference and write a prompt that explicitly preserves style family, not just topic.

4. **Visual readback gate**
   - Inspect the rendered output against the reference before finalizing.
   - If style differs, regenerate immediately. Do not defend a mismatched style as “close enough.”

5. **Report honestly**
   - Say what was matched, what remains different, and whether the limitation is due to SVG/manual rendering vs image-generation availability.

## Cartoon Technical Infographic Pattern

When the reference is a cartoon technical information graphic, use this pattern:

- light white/cream background, not dark grid
- thick black outlines on cards, arrows, and icons
- rounded colorful modules with numbered badges
- high-saturation but soft fills: sky blue, lime green, lavender, pink, yellow, teal
- playful illustrated icons: laptop/chat, cloud brain, compass/router, robot/tool adapter, shield/guard, files/API blocks, conveyor belt
- thick curved arrows with cartoon arrowheads
- dashed playful secondary paths
- bottom conveyor/event belt for unified stream/protocol concepts
- short readable labels; avoid dense tiny prose
- use rounded/handwritten/cartoon typography rather than technical monospace

## Pitfalls

1. **Dark-template reflex** — The architecture-diagram default dark grid style is wrong when the reference is a light cartoon infographic.
2. **Whiteboard-vs-cartoon confusion** — White background plus hand-drawn font is not enough. Cartoon style needs thick black strokes, colorful rounded blocks, icons, and playful composition.
3. **Content-only acceptance trap** — Covering the right modules does not satisfy the task if the style is visibly different.
4. **Over-noisy texture trap** — Procedural paper/noise can reduce legibility. Keep backgrounds clean unless the reference itself is noisy.
5. **Tiny label trap** — Cartoon posters still need readable architecture labels; simplify text instead of shrinking it.
6. **Tool setup overclaim** — If image generation is unavailable, state the boundary and use SVG/manual rendering; do not claim image-model-level style fidelity.

## Verification Checklist

Before saying the diagram matches the reference:

- [ ] Reference style family was explicitly classified.
- [ ] Background family matches.
- [ ] Stroke/outline weight matches.
- [ ] Color saturation and card shapes match.
- [ ] Icon density and icon type match.
- [ ] Arrow style matches.
- [ ] Typography direction matches.
- [ ] Main content is legible.
- [ ] Any remaining fidelity gap is stated honestly.

## References

- `references/cartoon-technical-infographic.md` — detailed checklist for cartoon architecture/info-graphic style matching.
