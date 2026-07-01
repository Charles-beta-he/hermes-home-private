---
name: manufacturing-brain
description: Use when handling manufacturing/3D-printing workflows, Bambu/X2D printer status, slicer/G-code/material/AMS reasoning, print failure diagnosis, or deciding whether a print situation warrants action. Manufacturing is an independent domain brain even with one capable printer; physical actuation still routes through external-control.
---

# Manufacturing Brain

## Overview

Use when handling manufacturing/3D-printing workflows, Bambu/X2D printer status, slicer/G-code/material/AMS reasoning, print failure diagnosis, or deciding whether a print situation warrants action. Manufacturing is an independent domain brain even with one capable printer; physical actuation still routes through external-control. It is organized as a capability wrapper with explicit safety, idempotency, credential, and read-back checks before any side effect is treated as complete.

## When to Use

Use this skill when the request matches the `manufacturing-brain` trigger and the domain-specific boundaries in this skill apply.

Don't use for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone;
- purely electrical/control questions better handled by `electrical-brain` or `external-control-brain`;
- physical fabrication that would be unsafe without human inspection, material verification, or machine-specific review;
- ordering, payment, or destructive machine actions without explicit authority and rollback/stop path.

Use this skill when the user asks about:
- Bambu / X2D / 拓竹 printer state
- 3D printing, slicing, STL/3MF/G-code, AMS, filament/material, nozzle/bed/layer issues
- print abnormality diagnosis or whether to pause/continue/cancel
- manufacturing workflow evolution
- printed mechatronic assemblies: robot shells, actuator mounts, servo/motor ID maps, IMU/contact-sensor bring-up, calibration offsets, and policy-run readiness for 3D-printed robots or fixtures

## Architecture decision

A single sufficiently capable printer is enough to justify an independent manufacturing brain when:
1. real local telemetry/control exists,
2. recurring material/job/quality decisions are expected,
3. domain-specific safety interpretation is needed,
4. a device adapter exists under external-control.

Manufacturing owns manufacturing semantics. It does not own physical actuation.

## Boundary with external-control

Manufacturing may:
- interpret status and telemetry,
- diagnose print risk,
- review STL/3MF/G-code/profile assumptions,
- produce a domain_safety_verdict,
- produce an action_request for pause/resume/stop/upload/start.

Manufacturing must not directly:
- publish MQTT control commands,
- upload/delete files over FTPS,
- heat, move, pause/resume/stop/start hardware,
- enable/disable motor torque, command actuators, run robot walking/navigation policies, pair controllers, read private camera/microphone streams, or call LLM tools that can move a device,
- store or reveal access codes.

All real-world actions go through the external-control brain safety gate.

## Bambu X2D local facts

Detailed Bambu X2D local facts moved to `references/bambu-x2d-local-facts.md`.

Load it when the specific local X2D printer facts, network/device context, or local adapter constraints matter.

Minimum in-root rule: treat printer telemetry/control as external-control side effects until readback and authority exist.

## Bambu X2D protocol details

**FTPS upload** (implicit TLS):
- Port: 990 (override via `BAMBU_FTPS_PORT` env var)
- Auth: `bblp` / `BAMBU_ACCESS_CODE`
- `ftplib.FTP_TLS` → `.connect()` → `.login()` → `.prot_p()` → `.storbinary("STU <name>", f)`
- Files land in the printer's `/cache/` or user root; the MQTT start command references by name.

**MQTT start_print**:
- Same TLS connection as status (port 8883, `connect_mqtt()`)
- Publish to `device/{SERIAL}/request` topic
- Payload: `{"print": {"sequence_id": "hermes-<ts>", "command": "start", "param": "Metadata/<remote_name>", "url": "ftp://<host>/<remote_name>"}}`
- Wait up to 10s for response on `device/{SERIAL}/report` matching the sequence_id
- Response statuses: `command_sent` (ack received), `sent_no_ack` (no ack within 10s)

## Default workflow

1. Get read-only status through the adapter.
2. Build evidence packet: job, percent, layer, temps, AMS, errors, camera if requested.
3. Diagnose with manufacturing semantics.
4. If action is needed, emit an action_request with risk and command preview.
5. Let external-control execute only after confirmation and audit.

## Printed mechatronic / robot bring-up

Use `~/.hermes/brains/manufacturing/protocols/mechatronic-robot-bringup.md` when a 3D print becomes a powered/sensorized assembly: robot body, servo bracket, actuator linkage, motorized fixture, IMU/contact-sensor platform, or learned-policy robot.

Default stance:
- Treat upstream robot runtimes as reference evidence, not executable integrations.
- Require an actuator topology map: joint/axis name, motor ID/channel, bus/driver, neutral pose, safe range, and physical label.
- Require calibration evidence before motion: zero-pose photo/description, soft offsets, low-torque/read-only motor proof, voltage/power evidence, and sensor orientation/freshness.
- For learned or scripted controllers, require artifact hash, observation/action contract, control frequency, action scaling/filters, simulation/replay or bench proof, stop condition, and rollback plan.
- Manufacturing may output `blocked`, `read_only_ready`, `bench_ready`, or `external_control_action_request_ready`; it must not execute motion.
- Any torque enable, actuator movement, walking, camera-guided navigation, Bluetooth/GPIO/I2C/serial access, or LLM-to-robot function call routes through External-Control. Electrical/current/thermal/fusing questions route through Electrical Brain.

Hard vetoes: missing motor ID map, unknown zero/motor direction, no low-torque/read-only proof, stale/missing IMU/contact data for closed-loop control, unknown policy hash/contract, unknown power protection, or absent External-Control packet.

Reference review: `~/.hermes/brains/manufacturing/reviews/2026-05-25_open-duck-mini-runtime-review.md`.

## Photo-to-print state machine

Detailed photo-to-print state machine moved to `references/photo-to-print-state-machine.md`.

Load it when converting photos or rough ideas into printable geometry, measurement requests, and iteration gates.

Minimum in-root rule: do not infer critical dimensions or safety constraints from a photo without asking for/validating measurements.

## Model source fetch

When the user provides a model URL, check if the source allows automated fetch before attempting. See `references/model-source-automation.md` for the compatibility matrix. Key rules:

- **MakerWorld** (makerworld.com / .com.cn): blocked by Cloudflare Turnstile. Do NOT retry more than once — immediately ask the user to download manually.
- **Printables / Thingiverse / GitHub / direct links**: curl works. Download directly.
- After manual download, resume full pipeline from preflight.

## 3D model studio bridge

Use `~/.hermes/brains/manufacturing/protocols/3d-model-studio-bridge.md` whenever the workflow involves image-to-3D providers, GLB/GLTF import, local generated mesh drafts, or model-studio preview assets. For SAM 3D / ComfyUI / single-photo-to-3D workflows, also use `references/sam3d-photo-to-3d-draft-gates.md`.

Rules:
- Treat Rodin/Tripo/Fal/Hunyuan/local-GLB outputs as `draft_only` evidence packets until proven otherwise.
- Normalize provider, provider_model, task_id, source/provenance/license, local_path, sha256, parse/header validity, preview metrics, and visual-fidelity class before calling `model_ready`.
- Display/demo metrics such as triangle count, texture count, and `Demo-ready` verdict can triage candidates but cannot authorize preflight, slicing, upload, or start_print.
- Generated/imported GLB must have local hash, explicit scale/intended use, visual preview, and human approval for non-retrieved assets before entering the normal manufacturing preflight.
- Existing gates remain authoritative: retrieval-first, similarity/visual-fidelity, mesh QA, watertight/wall/scale/bed/material checks, slicer success, and external-control packet approval.

## Blender / MCP studio bridge

Detailed Blender/MCP studio bridge guidance moved to `references/blender-mcp-studio-bridge.md`.

Load it when using Blender or MCP-style tools to generate/inspect/edit printable models.

Minimum in-root rule: generated geometry still needs manufacturability checks before print advice.

## Model similarity policy

For photo/image-to-print, retrieval comes before generation. First search local curated models and trusted public sources for an exact or near-identical model; only consider generated mesh drafts after the near-identical retrieval path is exhausted and the user approves generation.

For photo-to-decorative/character models, add a `visual_fidelity_gate` before mesh QA/slicing approval. Mesh watertightness and slicer success only prove printability; they do not prove the model is worth printing. Require a side-by-side visual preview against the source photo and label any generic/inspired substitute as `printable_but_visual_fidelity_failed` unless it preserves the subject's defining silhouette, pose, face proportions, attachment method, and material/border context. Field case: the white dog keychain photo required leather backing, stitch border, rectangular strap, seated long-body dog, drooping ears, large black eyes, oval nose, small tongue, and fluffy linework; a generic big-head animal with circular ears/head-hole was not acceptable even though STL/3MF checks passed.

Similarity gates:
- `exact_replacement`: >=0.95 visual/geometric similarity and <=2% dimension deviation.
- `functional_part`: >=0.85 visual/geometric similarity and <=5% dimension deviation; mating/load-bearing dimensions must still be explicitly reviewed.
- `decorative_equivalent`: >=0.75 visual/geometric similarity and <=15% dimension deviation; user visual approval required.
- `inspiration_only`: not a match; only proceed if the user explicitly accepts an inspired alternative.

These thresholds gate selection only. Passing similarity still requires license/provenance, dimensions, preview evidence, preflight, slicing preview, and human approval.

## Multi-model chain policy

Detailed manufacturing multi-model chain policy moved to `references/multi-model-chain-policy.md`.

Load it when multiple model/vision/reasoning passes are needed for geometry, printability, or safety judgments.

Minimum in-root rule: model consensus is advisory; physical dimensions, slicer preview, and machine/material readback decide print action.

## Desktop lamp/base policy

Detailed desktop lamp/base mechanical policy moved to `references/desktop-lamp-base-policy.md`.

Load it for lamp bases, stands, weighted supports, cable routing, or stability/safety decisions.

Minimum in-root rule: physical stability and heat/electrical separation must be verified before fabrication.

## Print-quality experience review

Baseline web-backed profile consensus lives at:
- `~/.hermes/brains/manufacturing/profiles/basic-fdm-quality-profile-consensus.md`
- `~/.hermes/brains/manufacturing/profiles/basic-fdm-quality-profile-consensus.json`

Use it as the conservative starting point for Bambu X2D / Bambu Studio / OrcaSlicer PLA/PETG cosmetic QA: 0.16mm general layer height, 0.12mm fine visual layer height, 50-70mm/s outer walls, 25-45mm/s small text/details, 1000-2000mm/s² outer-wall acceleration, overhang 20-40mm/s, bridge 20-30mm/s, seam hidden/aligned/back or scarf seam, and support contact kept off visible faces.

## Parametric 3D model generation (trimesh + manifold3d)

Detailed trimesh/manifold3d parametric model generation moved to `references/parametric-model-generation.md`.

Load it when generating printable geometry programmatically.

Minimum in-root rule: syntax-valid generated geometry is not enough; run mesh/manufacturability checks before print guidance.

## Pre-print mesh manufacturability analysis

Before slicing, run automated mesh QA to catch geometry-specific risks:

```bash
python3 ~/.hermes/scripts/manufacturing_mesh_qa.py analyze \
  --model /path/model.stl \
  --intended-use "用途" \
  --layer-height 0.16 \
  --nozzle-diameter 0.4 \
  --requested-material PETG \
  --loaded-material "PLA Matte" \
  --output /path/mesh-qa.json \
  --json
```

Issue IDs:
- `shallow_dome_stair_step_risk`: shallow curved surfaces will show concentric layer rings
- `large_flat_wall_ringing_or_banding_risk`: large vertical flat faces will show speed/accel artifacts
- `small_embossed_text_blur_risk`: raised text strokes below nozzle resolution limit
- `tiny_protrusion_fragility_risk`: thin protrusions below reliable feature size
- `material_profile_mismatch`: requested material does not match loaded AMS material

Preflight (`manufacturing_preflight.py model`) now automatically includes `mesh_manufacturability_qa` in its report for STL files. The slice bridge (`manufacturing_slice.py prepare`) now carries `material_binding` with requested material, nozzle, layer height, and profile lookup.

## AMS material auto-injection

Preflight automatically reads the most recent cached X2D status from `~/.hermes/runs/x2d-status/` and extracts loaded AMS materials. When `--material` is specified, it compares against loaded trays and emits `material_profile_mismatch` if no matching tray is found.

Standalone helper:
```bash
python3 ~/.hermes/scripts/x2d_ams_helper.py ~/.hermes/runs/x2d-status/20260521-161721/summary.json --requested-material PETG
```

## Orientation search

For any STL, enumerate 6 principal build orientations and rank by overhang area:

```bash
python3 ~/.hermes/scripts/manufacturing_orientation_search.py search \
  --model /path/model.stl \
  --output /path/orientation.json \
  --json
```

Outputs per-orientation overhang fraction, severe overhang area, bounding box, and recommended orientation. Use before slicing to minimize support contact on visible faces.

## BambuStudio CLI support-slice pitfall

Detailed BambuStudio CLI support-slice pitfall moved to `references/bambustudio-cli-support-slice-pitfall.md`.

Load it when CLI slicer output, support settings, or preview/export behavior disagrees with expectations.

Minimum in-root rule: verify slicer settings and preview artifacts before concluding the model or printer is wrong.

## Slicer preview settings extraction

After slicing to 3MF, extract key slicer settings and run quality review:

```bash
python3 ~/.hermes/scripts/slicer_preview_parse.py /path/sliced.3mf \
  --output /path/preview-settings.json \
  --json
```

Extracted settings: layer height, outer/inner wall speed, support type, seam position, scarf seam, infill density/pattern, wall loops, bridge/overhang speed, acceleration, ironing.

Quality review issues:
- `seam_random_selected`: scattered dots on visible surfaces
- `normal_support_selected`: may leave more scars than tree support
- `outer_wall_speed_high`: ringing/VFA risk
- `layer_height_coarse`: visible stair-stepping
- `scarf_seam_not_enabled`: curved surfaces may show seam

Preflight now emits `quality_experience_review` so common 3D-printing experience issues are visible before slice/start approval. Covered advisory/warn classes include:
- cooling artifacts / cooling lines / uneven gloss on small or visible surfaces,
- seam and layer-line placement,
- overhang, bridge, support strategy, support interface and support-material scarring,
- warping / bed adhesion for large flat parts or ABS/ASA/PC/nylon-like materials,
- stringing / retraction / wet-filament risk for PETG/TPU/nylon-like materials,
- functional-part layer adhesion and load-path orientation.

This review is conservative and does not replace slicer preview. It is a checklist gate: inspect support interface/contact scars, cooling transitions, seam placement, first layer, material/profile, and orientation before approving `slice_ready` or `start_print`.

## Trick research / 邪修 casebook

Detailed trick research / 邪修 casebook moved to `references/trick-research-casebook.md`.

Load it only for experimental print/process hacks where evidence quality and failure risk must be graded.

Minimum in-root rule: label hacks as experimental and separate anecdote from machine/material-specific evidence.

## Verdict format

```yaml
domain_safety_verdict:
  status: normal|warn|critical|unknown
  confidence: 0.0-1.0
  evidence: []
  recommended_action: none|watch|pause|resume|stop|human_inspect
  action_request: null|{...}
```

## References

- `~/.hermes/brains/manufacturing/brain.yaml`
- `~/.hermes/brains/electrical/brain.yaml`
- `~/.hermes/brains/manufacturing/protocols/external-control-boundary.md`
- `~/.hermes/brains/manufacturing/protocols/photo-to-print-pipeline.md`
- `~/.hermes/brains/manufacturing/protocols/glasses-visual-qa.md`
- `~/.hermes/brains/external-control/brain.yaml`

## Common Pitfalls

1. Reporting a tool/API mutation as complete without reading back target state.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] For mutations or external-system actions, command success was paired with target-state read-back.
