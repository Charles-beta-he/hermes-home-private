# Desktop Lamp/Base Policy

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Desktop lamp/base policy

For decorative desktop lamps, photo-derived dimensions may be filled by a proportional best-fit scheme when the user is not asking for an exact replacement. This must be labelled `best_aesthetic_proportion_not_exact_replacement`; it is acceptable for appearance/prototype work, but not for mating/exact replacement dimensions.

Use the base generator for the printed mechanical base only:

```bash
python3 ~/.hermes/scripts/manufacturing_lamp_base.py generate \
  --shade-diameter-mm 132 \
  --led-module-diameter-mm 50 \
  --led-module-height-mm 8 \
  --max-module-temp-c 40 \
  --material PETG \
  --output /path/ribbed-low-voltage-lamp-base.stl \
  --manifest /path/lamp-base-manifest.json \
  --json
```

Use the shade generator for the passive diffuser/shell only:

```bash
python3 ~/.hermes/scripts/manufacturing_lamp_shade.py generate \
  --shade-diameter-mm 132 \
  --shade-height-mm 112 \
  --base-socket-outer-diameter-mm 86 \
  --max-led-surface-temp-c 40 \
  --material 'translucent PETG' \
  --output /path/wavy-mushroom-diffuser-shade.stl \
  --manifest /path/lamp-shade-manifest.json \
  --json
```

For v2 base/serviceability, add the service cover, rear cable-channel policy, and LED puck mounting metadata:

```bash
python3 ~/.hermes/scripts/manufacturing_lamp_base.py generate \
  --version v2 \
  --shade-diameter-mm 132 \
  --led-module-diameter-mm 50 \
  --led-module-height-mm 8 \
  --screw-pattern-diameter-mm 40 \
  --screw-hole-diameter-mm 3 \
  --cable-channel-width-mm 8 \
  --service-cover-output /path/bottom-service-cover-v2.stl \
  --output /path/ribbed-low-voltage-lamp-base-v2.stl \
  --manifest /path/lamp-base-v2-manifest.json \
  --json
```

For v2 shade/visual tuning, add a stop/retention lip and select a diffuser material mode:

```bash
python3 ~/.hermes/scripts/manufacturing_lamp_shade.py generate \
  --version v2 \
  --shade-diameter-mm 132 \
  --shade-height-mm 112 \
  --base-socket-outer-diameter-mm 86 \
  --retention-lip-height-mm 4 \
  --diffuser-mode frosted_pla \
  --output /path/wavy-mushroom-diffuser-shade-v2.stl \
  --manifest /path/lamp-shade-v2-manifest.json \
  --json
```

For v3 / web-best-practice mode, encode conservative public best-practice constraints from the evidence note `~/.hermes/brains/manufacturing/reviews/2026-05-21_desktop-lamp-web-best-practices.md`:

```bash
python3 ~/.hermes/scripts/manufacturing_lamp_base.py generate \
  --version v3 \
  --shade-diameter-mm 132 \
  --led-module-diameter-mm 50 \
  --led-module-height-mm 8 \
  --max-module-temp-c 40 \
  --service-cover-output /path/bottom-service-cover-v3.stl \
  --output /path/ribbed-low-voltage-lamp-base-v3.stl \
  --manifest /path/lamp-base-v3-manifest.json \
  --json
python3 ~/.hermes/scripts/manufacturing_lamp_shade.py generate \
  --version v3 \
  --shade-diameter-mm 132 \
  --shade-height-mm 112 \
  --base-socket-outer-diameter-mm 86 \
  --retention-lip-height-mm 4 \
  --diffuser-mode translucent_petg \
  --air-gap-mm 20 \
  --output /path/wavy-mushroom-diffuser-shade-v3.stl \
  --manifest /path/lamp-shade-v3-manifest.json \
  --json
```

V3 adds: external certified USB/SELV adapter only, polyfuse/protected-module recommendation, bottom-intake/high-exhaust ventilation policy, jacket-clamp strain relief policy, 4h full-brightness thermal soak <=45C printed-surface target, 20mm LED-to-shade air gap target, PETG diffuser default, 0-5% shade infill, rear/manual seam, and adapter/current/cable/tug/thermal validation checklist.

For a full kit, produce separate base, service-cover, and shade 3MF projects first. Do not combine into a real start_print packet until slicer previews are reviewed; translucent/frosted shade settings often need visual tuning (perimeters/infill/material color), and the service cover must not pinch the USB cable.

Physical-QA carryover from functional prints:
- Treat every printed device as an assembly, not a single pretty shell: every moving/slipping part needs its mating receiver, stop, lead-in, clearance, and service path.
- Before full print, reserve and document real module envelopes (LED puck diameter/height, screw pattern, cable channel, service cover, air gap) instead of adding electronics after the shell is printed.
- Prefer support-light, wall-connected, chamfered features; avoid broad internal shallow surfaces that create dense hidden supports, slow-cooling scars, or hard-to-remove support islands.
- For lamps, separate optical diffuser tuning from mechanical base printing; print/test diffuser swatches or the shade separately before committing to a full assembled powered object.
- When generating a mushroom/diffuser shade, verify the preview from top before printing: the bottom socket may be large, but the top must not accidentally remain a large chimney/open hole unless explicitly desired. Prefer a small top vent and confirm with exported `Metadata/top_1.png` / plate preview.

Electrical boundary:
- Printed base/shade are mechanical enclosure/diffuser parts only.
- Prefer certified 5V USB/SELV LED puck/module, certified USB adapter, inline low-voltage switch/dimmer.
- No mains AC inside printed parts; no printed part may substitute for certified insulation, strain relief, or electrical housing.
- Fail closed for `--voltage-class mains_ac` or LED module surface temperature >45C.
- PETG/ASA preferred for heat margin; PLA only when the actual LED module stays cool (<45C measured at steady state).
