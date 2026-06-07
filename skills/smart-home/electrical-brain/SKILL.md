---
name: electrical-brain
description: "Use when handling low-voltage electrical/electronics decisions: USB/SELV power, LED modules/drivers, wires/connectors/switches, current derating, fuses/polyfuses, certification evidence, thermal validation, or electrical BOMs for objects Hermes helps design. Physical actuation still routes through external-control; printed/mechanical design still routes through manufacturing."
---

# Electrical Brain

## Overview

Use when handling low-voltage electrical/electronics decisions: USB/SELV power, LED modules/drivers, wires/connectors/switches, current derating, fuses/polyfuses, certification evidence, thermal validation, or electrical BOMs for objects Hermes helps design. Physical actuation still routes through external-control; printed/mechanical design still routes through manufacturing. This skill is maintained as a `pipeline`-shaped contract: it should guide ordered multi-stage work with gates, evidence, retries, and closure states without stealing adjacent workflows or relying on unstated assumptions.

## When to Use

Use this skill when the user's request matches `electrical-brain` and requires ordered multi-stage work with gates, evidence, retries, and closure states.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this skill when the user asks about:
- 电气 / 低压 / USB / SELV / LED / 灯珠 / 电源适配器 / 开关 / 调光
- wire gauge, connector ratings, current draw, voltage drop, fuse/polyfuse sizing
- electrical BOM selection for a device Hermes designs
- thermal validation of electronics near printed plastic
- whether a powered build is safe to assemble or leave unattended

## Architecture decision

Electrical is independent from Manufacturing when the workflow includes powered hardware. Manufacturing owns printed/mechanical process semantics; Electrical owns power/electronics semantics; External Control owns physical actuation and credential/audit gates.

For the X2D desktop lamp:
- Manufacturing may design and print the base, cover, shade, material profile, slicer settings, and AMS compatibility.
- Electrical must select or constrain the LED puck/module, adapter, switch/dimmer, wire, connector, strain relief, fuse/polyfuse, and thermal validation plan.
- External-control validates live printer/device telemetry and executes only after confirmation/audit.

## Non-negotiables

- No mains AC inside a printed or uncertified enclosure.
- Printed parts are mechanical enclosure/diffuser only; they do not replace certified insulation, fire enclosure, strain relief, or electrical housing.
- Prefer external certified USB/SELV adapter and low-voltage certified/reputable LED module.
- Treat CE-only anonymous marketplace adapters/modules as insufficient evidence for safety-critical approval.
- Fail closed if voltage/current/power ratings are unknown for the selected powered build.
- Fail closed if cable strain relief is absent or solder/PCB terminals carry cable pull force.
- Fail closed if thermal validation is missing for LEDs/electronics near PLA/PETG/printed plastic.

## Desktop lamp electrical BOM policy

Default safe architecture:

```yaml
electrical_bom:
  voltage_class: USB/SELV low-voltage only
  adapter: external certified USB-C/USB-A adapter
  light_source: certified/reputable 5V LED puck/module or low-power LED ring
  switch: inline certified low-voltage USB switch/dimmer
  protection: protected LED module or polyfuse sized 125-150% of measured steady-state current
  wire: current-rated flexible wire; no solder joint carries pull force
  enclosure_boundary: printed parts mechanical only
```

For the current desktop lamp envelope:

```yaml
mechanical_interface:
  led_puck_max_diameter_mm: 50
  led_puck_max_height_mm: 8
  screw_pattern_diameter_mm: 40
  cable_channel_width_mm: 8
  minimum_led_to_shade_gap_mm: 20
thermal_policy:
  led_module_surface_target_c: <=45
  printed_part_surface_target_c: <=45
  soak_test_hours: 4
```

If a real SKU is not selected yet, output an electrical decision boundary rather than pretending the hardware is verified. Say: "specification selected, external hardware not yet verified".

## Electrical verdict format

```yaml
electrical_domain_safety_verdict:
  status: pass|warn|blocked|unknown
  confidence: 0.0-1.0
  voltage_class: usb_selv_low_voltage|mains_ac|unknown
  evidence: []
  selected_bom: null|{adapter, led_module, switch, wire, protection}
  required_external_evidence: []
  stop_conditions: []
  manufacturing_constraints: []
  external_control_constraints: []
```

## Boundaries

Delegate to Manufacturing when:
- STL/3MF/G-code/CAD/material/slicer/AMS/print-quality decision dominates.
- The question is about PETG vs PLA printability, supports, layer height, warping, printer status, or Bambu/X2D telemetry.

Delegate to External Control when:
- a command affects a real device,
- credentials are needed,
- live telemetry/camera/sensor reads are used for an action gate,
- upload/start/pause/stop/heat/move is requested.

## Verification checklist

Before a powered lamp is approved for use:
- Adapter certification/listing checked.
- LED module voltage/current/power known.
- Measured current <=80% of weakest rated adapter/cable/switch/connector.
- Fuse/polyfuse or protected module present when source current can overheat wiring.
- Cable jacket strain relief passes tug/flex test.
- No wire is pinched by the service cover.
- LED and printed surfaces remain <=45C after 4h full-brightness soak.
- No odor, discoloration, warping, connector heating, or adhesive creep.

## References

- `~/.hermes/brains/electrical/brain.yaml`
- `~/.hermes/brains/manufacturing/brain.yaml`
- `~/.hermes/brains/external-control/brain.yaml`
- `~/.hermes/runs/photo-to-print/20260521-133815-wavy-lamp-web-best-practice-v3/03-electrical-decision-boundary.json`

## Common Pitfalls

1. Advancing stages without a gate, evidence artifact, or closure-state check.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.
