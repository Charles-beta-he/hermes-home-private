---
name: manufacturing-brain
description: Use when handling manufacturing/3D-printing workflows, Bambu/X2D printer status, slicer/G-code/material/AMS reasoning, print failure diagnosis, or deciding whether a print situation warrants action. Manufacturing is an independent domain brain even with one capable printer; physical actuation still routes through external-control.
---

# Manufacturing Brain

## Overview

Use when handling manufacturing/3D-printing workflows, Bambu/X2D printer status, slicer/G-code/material/AMS reasoning, print failure diagnosis, or deciding whether a print situation warrants action. Manufacturing is an independent domain brain even with one capable printer; physical actuation still routes through external-control. It is organized as a capability wrapper with explicit safety, idempotency, credential, and read-back checks before any side effect is treated as complete.

## When to Use

Use this skill when the request matches the `manufacturing-brain` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

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

Current local adapter profile lives at:
`~/.hermes/brains/manufacturing/devices/bambu-x2d.yaml`

Current safe status CLI:
`BAMBU_ACCESS_CODE=... python3 ~/.hermes/scripts/bambu_x2d.py status`

Upload + start (mutating, requires external-control gate approval):
```bash
- BambuStudio dispatch is not just raw FTP + MQTT: it first exports a valid sliced print file (`send_gcode`), validates AMS/nozzle mapping, then calls `bambu_network_start_local_print_with_record` or cloud fallback via the official networking module.
- For newer/eMMC-capable machines, BambuStudio checks a port-6000 `FileTransferTunnel` URL shaped like `bambu:///local/<ip>?port=6000&user=bblp&passwd=<code>` before/alongside legacy FTP/SD-card upload. Prefer this route for X2D/H2D automation instead of assuming writable FTPS.
- Legacy LAN FTP upload may fail even with correct access code: `553 Could not create file` means the printer/storage refused local FTP writes. Treat as fail-closed and switch to official network module / eMMC tunnel / BambuStudio automation.
- `BAMBU_ACCESS_CODE=... python3 ~/.hermes/scripts/bambu_x2d.py start --remote name.3mf` sends MQTT `project_file` with URL `file:///sdcard/cache/name.3mf` and param `Metadata/plate_1.gcode`, but only after a verified upload of a sliced package.
- Before start, verify the 3MF is sliced and contains `Metadata/plate_1.gcode`; a project-only 3MF is not directly printable. AMS/nozzle mapping, then calls `bambu_network_start_local_print_with_record` or cloud fallback via the official networking module.
- For newer/eMMC-capable machines, BambuStudio checks a port-6000 `FileTransferTunnel` URL shaped like `bambu:///local/<ip>?port=6000&user=bblp&passwd=<code>` before/alongside legacy FTP/SD-card upload. Prefer this route for X2D/H2D automation instead of assuming writable FTPS.
- Legacy LAN FTP upload may fail even with correct access code: `553 Could not create file` means the printer/storage refused local FTP writes. Treat as fail-closed and switch to official network module / eMMC tunnel / BambuStudio automation.
- `BAMBU_ACCESS_CODE=... python3 ~/.hermes/scripts/bambu_x2d.py start --remote name.3mf` sends MQTT `project_file` with URL `file:///sdcard/cache/name.3mf` and param `Metadata/plate_1.gcode`, but only after a verified upload of a sliced package.
- Before start, verify the 3MF is sliced and contains `Metadata/plate_1.gcode`; a project-only 3MF is not directly printable.
```

Do not persist the access code in plaintext. For glasses/agent automation, store it once in macOS Keychain:
```bash
python3 ~/.hermes/scripts/bambu_credentials.py set
python3 ~/.hermes/scripts/bambu_credentials.py status
```
Adapters prefer `BAMBU_ACCESS_CODE` env for one-off overrides, then Keychain `hermes-bambu-x2d/lan-access-code` for unattended automation.

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

If the user has no model yet and wants a safe first X2D pilot package, generate a tiny calibration artifact first:

```bash
python3 ~/.hermes/scripts/manufacturing_calibration_cube.py \
  --output /path/calibration-cube-12mm.stl \
  --manifest /path/calibration-cube-manifest.json \
  --size-mm 12 \
  --json
```

Use the one-command safe runner when the user already has a local model and wants a complete dry-run proof:

```bash
python3 ~/.hermes/scripts/photo_to_print_runner.py dry-run-existing-model \
  --photo /path/input.jpg \
  --object-label "目标物" \
  --intended-use "用途" \
  --model /path/model.stl \
  --device-status-json /path/status.json \
  --output-dir /path/photo-to-print-run \
  --json
```

The runner executes the full safe path: job init, object/model approvals, candidate evidence, preflight, local 3MF export, action packet creation, and external-control dry-run gate. It never uploads or starts the printer.

Use the durable step-by-step CLI for finer-grained control:

```bash
python3 ~/.hermes/scripts/photo_to_print_job.py init --photo /path/input.jpg --object-hint "目标物" --intended-use "用途" --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> object_confirmed --object-label "..." --confidence 0.93 --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> model_strategy_selected --strategy retrieval --risk-tier T1 --approved-by-human --json
python3 ~/.hermes/scripts/model_candidate_search.py plan \
  --object-label "目标物" \
  --intended-use "用途" \
  --intake-mode photo \
  --intake-mode voice \
  --intake-mode text \
  --output /path/candidates.json \
  --json
python3 ~/.hermes/scripts/model_candidate_search.py evaluate \
  --object-label "目标物" \
  --candidate-title "候选模型标题" \
  --source Printables \
  --license-status known \
  --provenance-status verified_source_page \
  --format STL \
  --dimensions "20x15x12mm" \
  --preview-evidence thumbnail_and_model_page \
  --similarity-class functional_part \
  --visual-similarity 0.88 \
  --dimension-deviation-pct 4 \
  --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> model_ready --model-path /path/model.stl --provenance "..." --license "..." --approved-by-human --json
python3 ~/.hermes/scripts/manufacturing_preflight.py model /path/model.stl --intended-use "用途" --material PLA --output /path/preflight.json --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> preflight_passed --preflight-report /path/preflight.json --approved-by-human --json
python3 ~/.hermes/scripts/manufacturing_slice.py prepare /path/model.stl --output /path/job.3mf --report /path/slice-report.json --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> slice_ready --slice-path /path/job.3mf --slice-report /path/slice-report.json --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py action-request <job_id> --intent start_print --device-status-json /path/status.json --json
python3 ~/.hermes/scripts/external_control_gate.py execute /path/action-packet.json --confirm-token TOKEN --dry-run --json
```

The CLI records state/evidence only. `action-request` creates an external-control packet and audit stub; it never executes printer actions.

Glasses / Rokid trigger policy:
- Confirmations spoken through glasses may trigger the safe runner or enqueue a print intent, but direct physical printing remains blocked until external-control validates a fresh action packet and operator confirmation.
- Photo/vision requests from glasses are treated as evidence intake only; they do not imply model selection, slicing approval, or start_print approval.
- For glasses-side visual QA, create a packet with `python3 ~/.hermes/scripts/manufacturing_visual_qa.py intake --image /path/photo.jpg --question '...' --output /path/packet.json`; use Hermes vision to inspect the photo, then store findings with `manufacturing_visual_qa.py report`. Protocol: `~/.hermes/brains/manufacturing/protocols/glasses-visual-qa.md`.

## Model source fetch

When the user provides a model URL, check if the source allows automated fetch before attempting. See `references/model-source-automation.md` for the compatibility matrix. Key rules:

- **MakerWorld** (makerworld.com / .com.cn): blocked by Cloudflare Turnstile. Do NOT retry more than once — immediately ask the user to download manually.
- **Printables / Thingiverse / GitHub / direct links**: curl works. Download directly.
- After manual download, resume full pipeline from preflight.

## 3D model studio bridge

Use `~/.hermes/brains/manufacturing/protocols/3d-model-studio-bridge.md` whenever the workflow involves image-to-3D providers, GLB/GLTF import, local generated mesh drafts, or model-studio preview assets.

Rules:
- Treat Rodin/Tripo/Fal/Hunyuan/local-GLB outputs as `draft_only` evidence packets until proven otherwise.
- Normalize provider, provider_model, task_id, source/provenance/license, local_path, sha256, parse/header validity, preview metrics, and visual-fidelity class before calling `model_ready`.
- Display/demo metrics such as triangle count, texture count, and `Demo-ready` verdict can triage candidates but cannot authorize preflight, slicing, upload, or start_print.
- Generated/imported GLB must have local hash, explicit scale/intended use, visual preview, and human approval for non-retrieved assets before entering the normal manufacturing preflight.
- Existing gates remain authoritative: retrieval-first, similarity/visual-fidelity, mesh QA, watertight/wall/scale/bed/material checks, slicer success, and external-control packet approval.

## Blender / MCP studio bridge

Reference review: `~/.hermes/brains/manufacturing/reviews/2026-06-03_blender-mcp-reference-review.md`.

Use this pattern when the workflow involves Blender, Blender MCP, MCP-exposed 3D studio tooling, viewport screenshots, scene/object inspection, asset import, or AI-assisted scene/model editing before print.

Default stance:
- Treat Blender/MCP as an optional **studio evidence bridge**, not as manufacturing approval and not as a printer control plane.
- Blender viewport screenshots, scene info, object info, material assignments, and world bounding boxes are useful review evidence; they do not prove mesh manufacturability or print readiness.
- Imported/generated assets from Sketchfab, PolyHaven, Hyper3D/Rodin, Hunyuan3D, or similar providers remain `draft_only` until provenance/license, scale, visual fidelity, mesh QA, preflight, slicer preview, and external-control gates pass.
- Keep retrieval-before-generation: exact/near-identical trusted sources first; generated meshes only after retrieval is exhausted and the user approves generation.

Permission tiers for Blender-like MCP tools:
- `read_only`: scene info, object info, viewport screenshot, provider/status checks, search results, preview thumbnails.
- `studio_mutation`: create/modify/delete objects, transform assets, set textures/materials, lighting/camera changes, import downloaded/generated assets. Requires scope-bounded user intent and local artifact/provenance recording.
- `external_fetch`: download/import from asset libraries or model generators. Requires source URL, license/provenance status, local path, sha256, and provider metadata before entering manufacturing candidates.
- `arbitrary_code`: tools like `execute_blender_code` that call arbitrary Python inside Blender. Treat as full local process execution; require explicit approval, bounded code, no secrets, no printer/device control, and no credential persistence.
- `physical_action`: never owned by Blender/MCP. Any upload/start/pause/resume/stop/robot motion routes through External-Control.

Blender/MCP intake requirements before `model_ready`:
- record source repo/tool/provider and whether telemetry is disabled or explicitly approved;
- record local exported mesh path and sha256;
- record unit/scale assumption and world bounding box;
- capture at least one viewport screenshot or equivalent preview for human/vision review;
- label generated/imported assets as `draft_only`, `studio_preview`, `candidate_model`, or `model_ready` explicitly;
- redact API keys, tokens, cloud credentials, and built-in demo/free-trial keys as `[REDACTED]` in all notes and task artifacts.

Hard vetoes:
- telemetry enabled without explicit consent for prompts/code/screenshots/scene metadata;
- copying bundled third-party API keys into Hermes config, docs, memories, skills, or tasks;
- remote Blender socket exposure without separate network/security review;
- using arbitrary Blender Python to access files, network, credentials, printers, robot devices, or other external actuators;
- claiming a viewport render or successful import means the part is printable or safe to start.

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

For end-to-end photo/vision-to-print or any high-risk print decision, run multi-model synthesis and keep three ledgers separate: evidence, dissent, and engineering verification. Current reference artifact:

`~/.hermes/brains/manufacturing/reviews/2026-05-21_x2d-photo-to-print-multimodel-review.md`

Canonical chain:
- Intake Brain: structured intent only; no model selection or physical action.
- Vision & Measurement Brain: object confidence, ambiguity, trusted dimension source, uncertainty.
- Retrieval / Similarity Brain: near-identical search and similarity class before generation.
- Manufacturing Brain: material/printability/slicer/quality/load-path proposal.
- Safety / Policy Brain: independent veto; conservative disagreement wins.
- External Control Brain: only layer that can execute physical action after fresh telemetry, idempotency, packet hash, runtime credential, and confirmation token.
- Human Confirmation Orchestrator: final confirmation must bind model hash, slice hash, device id, material/profile, risk tier, and real-action flag.

Implemented quantitative gates:
- `model_candidate_search.py plan --object-confidence N`: object_class_confidence must be >=0.85 before normal retrieval; otherwise fail closed and ask clarification.
- `model_candidate_search.py plan --printer "Bambu X2D" --device-status-json status.json --material MATERIAL --require-loaded-material`: matches the owned Bambu X2D profile, reads AMS/spool material types from read-only status, and can fail closed when the requested material is not loaded.
- `model_candidate_search.py evaluate --required-material MATERIAL --available-material PLA --available-material PETG`: blocks candidates whose required material/profile is not currently available or operator-approved for loading.
- `model_candidate_search.py evaluate --similarity-class exact_replacement --trusted-dimension-source ... --dimension-uncertainty-pct ...`: exact replacement requires a trusted dimension source and <=2% uncertainty/deviation.
- `model_candidate_search.py evaluate --key-dimension-deviation-mm ... --key-dimension-deviation-pct ...`: functional mating dimensions block if >0.5mm or >2% when supplied.
- `manufacturing_preflight.py model --material ... --nozzle-diameter ... --layer-height ... --nozzle-temp ... --bed-temp ... --use-environment-temp-c ...`: material/profile hard bounds block unsafe temperature/layer/environment combinations.
- `external_control_gate.py execute`: real-action telemetry target age <=5s, and optional assumptions must match device/material/nozzle/plate/AMS telemetry.
- `external_control_gate.py execute`: packet-bound confirmation rejects dry-run/final packet hash mismatch.
- `manufacturing_trick_research.py record-success`: first verified successes go to casebook; skill promotion requires 3 matching verified local successes, not one web claim.

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

## Print-quality experience review

Baseline web-backed profile consensus lives at:
- `~/.hermes/brains/manufacturing/profiles/basic-fdm-quality-profile-consensus.md`
- `~/.hermes/brains/manufacturing/profiles/basic-fdm-quality-profile-consensus.json`

Use it as the conservative starting point for Bambu X2D / Bambu Studio / OrcaSlicer PLA/PETG cosmetic QA: 0.16mm general layer height, 0.12mm fine visual layer height, 50-70mm/s outer walls, 25-45mm/s small text/details, 1000-2000mm/s² outer-wall acceleration, overhang 20-40mm/s, bridge 20-30mm/s, seam hidden/aligned/back or scarf seam, and support contact kept off visible faces.

## Parametric 3D model generation (trimesh + manifold3d)

When modifying an existing functional printed model from user feedback, do not replace it with a simplified parametric substitute unless the user explicitly approves losing the original mechanism. Preserve the original function and part topology first; implement changes as targeted deltas (e.g. shallower blocker/ramp, one-at-a-time limiter, sliding cover) against the original mechanism, and label any simplified redesign as non-equivalent / do-not-print until reviewed.

When no existing .stl model matches the user's request and the geometry is parametrically describable (boxes, ramps, cylinders, CSG combinations), generate the mesh in code using trimesh creation primitives + boolean operations.

**CSG engine**: On this machine, `manifold3d` is the working CSG backend for trimesh. Neither `blender` nor `open3d` are in PATH. Always specify `engine='manifold'` in boolean calls. If manifold3d is missing, install with `pip3 install manifold3d`.

**Pattern**:
```python
import trimesh
outer = trimesh.creation.box(extents=(w, d, h))
inner = trimesh.creation.box(extents=(w-2*wall, d-wall, h-wall))
shell = trimesh.boolean.difference([outer, inner], engine='manifold')
feature = trimesh.creation.cylinder(radius=r, height=h)
result = trimesh.boolean.union([shell, feature], engine='manifold')
result.export('/path/output.stl')
```

**Diagnostic: face-normal angle distribution** — for functional parts with ramps/chutes/slopes, analyze face angles to verify dispensing geometry:
```python
normals = mesh.face_normals
angles = np.degrees(np.arccos(np.clip(np.abs(normals[:, 2]), 0, 1)))
# bins: flat(0-10), slight(10-25), moderate(25-45), steep(45-70), vertical(70-90)
```

Existing parametric generators:
- `manufacturing_calibration_cube.py` — 12mm calibration cube
- `manufacturing_lamp_base.py` — ribbed lamp base (v1/v2/v3)
- `manufacturing_lamp_shade.py` — diffuser shade (v1/v2/v3)
- `manufacturing_cigarette_box.py` — cigarette box with reduced-ramp, limiter, sliding lid
- `manufacturing_popup_cigarette_box_v4.py` — surgical popup cigarette-box repair after physical QA: support-light internal guide ribs, mated sliding-cover receiver grooves, and regular/slim limiter test inserts

Cigarette-box physical QA lessons:
- Do not solve anti-jam by adding a broad shallow internal ramp/liner if it creates dense internal supports or slow-cooling spaghetti; prefer small wall-connected chamfered guide ribs and verify `components == 1`.
- Sliding-cover fixes must modify both sides of the assembly: cover rails/stops plus matching receiver grooves/lead-in on the mating upper/body part. A rail-only cover is not a complete assembly design.
- Do not assume a universal cigarette diameter. Regular/thick and slim cigarettes need either a chosen throat variant or swappable/test limiter inserts; one fixed single-cigarette limiter cannot be optimal for both.
- Before full print, inspect slicer support preview layer-by-layer; avoid dense normal support inside the cigarette channel and curved/visible faces. Use tree/manual supports and support blockers unless a real floating island is proven.

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

When fixing `floating regions` by enabling support from CLI, a minimal process JSON can fail with `process not compatible with printer`. Load the X2D machine profile together with the custom process profile:

```bash
'/Applications/BambuStudio.app/Contents/MacOS/BambuStudio' \
  model_a.stl model_b.stl \
  --load-settings '/Users/charles/Library/Application Support/BambuStudio/system/BBL/machine/Bambu Lab X2D 0.4 nozzle.json;/path/support_tree_x2d_process.json' \
  --orient 1 --arrange 1 --slice 0 --export-3mf output-name.3mf --outputdir /path/out
```

Prefer the persisted helper instead of hand-building commands:

```bash
python3 ~/.hermes/scripts/bambu_studio_slice.py slice \
  /path/base.stl /path/lid.stl \
  --output /path/out/job.3mf \
  --machine-json '/Users/charles/Library/Application Support/BambuStudio/system/BBL/machine/Bambu Lab X2D 0.4 nozzle.json' \
  --process-json /path/tree-support-process.json \
  --json
```

BambuStudio CLI quirks verified on the smoke-box run:
- pass a **basename** to `--export-3mf` and an absolute `--outputdir`; absolute `--export-3mf` can create doubled output paths,
- do not combine `--export-png` and `--export-3mf` in one CLI invocation,
- use explicit machine/process/filament JSON file paths for automation; do **not** mutate `system/BBL.json` or `ota/presets/BBL.json` just to make a custom GUI dropdown preset appear,
- GUI lane should load original STL files and stock presets; CLI-exported projects/sliced packages are send artifacts, not reliable GUI-edit artifacts.

For BambuStudio CLI, trust `result.json` (`return_code: 0`, `warning_message: ""`, support feature times present) over scary but non-fatal stderr lines like `update_values_to_printer_extruders... could not found extruder_type Bowden` when valid G-code/3MF artifacts are produced. Multi-plate jobs must not be started by a hardcoded `Metadata/plate_1.gcode` path unless intentionally printing only plate 1.

Pre-print guard pitfall: a CLI-sliced 3MF that contains `Metadata/plate_1.gcode` is not automatically “ready to click print”. Bambu Studio / Handy may warn “打印机上安装的耗材变轨器与切片文件不匹配” when the embedded sliced package has stale/incorrect AMS, filament switcher, color/profile, nozzle, or plate assumptions (field case: `slice_info.config` had `has_filament_switcher=false` and mismatched filament color/profile against live X2D AMS). Before saying “只需要点击打印”, run:

```bash
python3 ~/.hermes/scripts/bambu_3mf_preprint_guard.py /path/job.3mf \
  --status-json /path/fresh-x2d-status-or-summary.json \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --json
```

Decision policy:
- `direct_print_ready`: still requires external-control action packet + fresh telemetry + human confirmation before upload/start.
- `requires_live_ams_verification` / `fail_closed`: do not claim click-print readiness; fetch fresh X2D status or export a GUI-reslice project.
- `gui_reslice_project`: safe to open in Bambu Studio, but not directly printable until the user maps current AMS/material, clicks Slice, and confirms a warning-free send screen.

Use `bambu_studio_slice.py --artifact-mode gui-reslice-project` to produce a GUI recovery file without embedded stale G-code. Use `--artifact-mode sliced` only for direct-print candidates, and only after the guard confirms material/AMS/nozzle/plate compatibility.

Audited local dispatch helper:
```bash
python3 ~/.hermes/scripts/x2d_dispatch_print.py /path/sliced.3mf \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --dry-run
python3 ~/.hermes/scripts/x2d_dispatch_print.py /path/sliced.3mf \
  --requested-material 'PLA Matte' \
  --requested-color FFFFFFFF \
  --yes-start
```
This wrapper reads the Bambu access code from env/Keychain, fetches fresh status, refuses project-only/stale-G-code artifacts, records an external-control dry-run packet, then executes the official Bambu local print helper only after a typed token.

Glasses/taskpool intent worker:
```bash
python3 ~/.hermes/scripts/x2d_print_intent_worker.py \
  --three-mf /path/sliced.3mf \
  --source rokid \
  --autonomy auto \
  --risk-tier P0 \
  --allow-autostart
```
The worker classifies P0/P1/P2, performs dispatch dry-run first, and autostarts only for P0 trusted repeat/calibration/test jobs after all external-control gates pass. See `~/.hermes/brains/manufacturing/protocols/x2d-glasses-autoprint-pipeline.md`.

GUI pitfall: BambuStudio CLI-exported project 3MFs can be unsuitable for GUI reopening if the custom process JSON contains `compatible_printers`; BambuStudio may write invalid XML like `value=""Bambu Lab X2D 0.4 nozzle""`, causing GUI warnings such as “此文件不包含任何几何数据” or CLI errors like “Archive does not contain a valid model config”. `bambu_studio_slice.py` now auto-repairs this narrow defect for `--artifact-mode gui-reslice-project` by removing malformed `Metadata/model_settings.config` compatible-printers metadata; verify XML and vertex/triangle counts before opening. If repaired project still fails, open the original STL files and re-apply settings inside GUI.

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

When `quality_experience_review` flags risks, use bounded web research before trying unusual slicer/profile fixes:

```bash
python3 ~/.hermes/scripts/manufacturing_trick_research.py plan \
  --preflight /path/preflight.json \
  --printer "Bambu X2D" \
  --material PLA \
  --json
```

Policy:
- Web findings are candidates, not truth. Never auto-apply a hack from the internet.
- Reject unsafe machine modifications: firmware/electrical bypass, thermal-runaway disablement, sensor/interlock bypass, temperature-limit override, credential/cloud-upload tricks.
- A candidate needs at least two independent sources, before/after evidence, same-material or reasoned transfer, and operator review.
- Successful local results are remembered in the manufacturing casebook, not raw user memory:
  `~/.hermes/brains/manufacturing/knowledge/trick-casebook.jsonl`.
- Generalizable repeated successes may be promoted into this skill with `skill_manage`; unverified web claims must not be promoted.

Record a successful verified fix:

```bash
python3 ~/.hermes/scripts/manufacturing_trick_research.py record-success \
  --risk-id support_material_review \
  --title "PETG interface support reduced PLA support scars" \
  --printer "Bambu X2D" \
  --material PLA \
  --model-class "decorative miniature" \
  --settings "support interface material PETG; top z distance 0; interface layers 2" \
  --evidence-url https://example/source1 \
  --evidence-url https://example/source2 \
  --before "support scars on visible face" \
  --after "support removed cleanly; no visible scars" \
  --outcome success \
  --json
```

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
