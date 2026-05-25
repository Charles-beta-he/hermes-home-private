# Photo-to-Print Pipeline Protocol

Goal: user provides a photo and points to an object; Hermes manages the path to a printable object and only notifies the user when pickup is ready.

## Capability boundary

This is a phased protocol. Photo-to-perfect-CAD is not assumed solved.

Manufacturing owns: object-to-manufacturing intent, model/provenance choices, printability, material/profile/slicer reasoning, print-risk verdicts, pickup-ready certification.
Vision owns: object localization, recognition, ambiguity/occlusion confidence, geometry uncertainty.
Dev/MLops owns: connectors, model search/CAD/reconstruction toolchain, slicer/preflight verifiers, monitoring evaluators.
External-control owns: all physical printer actions, runtime auth material, MQTT/FTPS/RTSP transport, confirmation, idempotency, audit.

## Durable job state machine

The pipeline is represented by persistent job JSON files managed by:

`python3 ~/.hermes/scripts/photo_to_print_job.py ...`

Default job root:

`~/.hermes/brains/manufacturing/jobs/photo-to-print/`

Job schema:

```yaml
schema: hermes_photo_to_print_job_v1
job_id: p2p-...
state: intake|object_confirmed|model_strategy_selected|model_ready|preflight_passed|slice_ready|external_control_pending|printing|monitoring|completed|pickup_ready|archived
inputs:
  photo: /path/to/photo
  object_hint: ...
  intended_use: ...
risk_tier: T0|T1|T2|T3|T4
approvals: {}
evidence: {}
artifacts: {}
external_control:
  mode: fail_closed
  last_action_request: null|{...}
events: []
```

CLI entrypoints:

```bash
python3 ~/.hermes/scripts/photo_to_print_job.py init --photo /path/input.jpg --object-hint "目标物" --intended-use "用途" --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> object_confirmed --object-label "..." --confidence 0.93 --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> model_strategy_selected --strategy retrieval --risk-tier T1 --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> model_ready --model-path /path/model.stl --provenance "..." --license "..." --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> preflight_passed --preflight-report /path/preflight.json --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> slice_ready --slice-path /path/job.3mf --slice-report /path/slice-report.json --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py action-request <job_id> --intent start_print --device-status-json /path/status.json --json
```

The action-request command only emits an external-control packet and writes an audit stub. It never uploads, starts, pauses, heats, moves, or otherwise controls the printer.

One-command safe runner for already selected local models:

`python3 ~/.hermes/scripts/photo_to_print_runner.py dry-run-existing-model --photo /path/input.jpg --object-label "目标物" --intended-use "用途" --model /path/model.stl --device-status-json /path/status.json --output-dir /path/run --json`

Rokid/glasses print utterances are high-impact physical actions. The glasses may trigger intent intake and confirmation prompts, but must not directly upload/start a print from voice or image alone. Real upload/start requires external-control validation with fresh telemetry, idempotency, audit, runtime auth-material source, and explicit operator confirmation.

## Pipeline stages

1. Photo intake
   - Input: photo, selected object hint, intended use, desired size/material/color if known.
   - Output: object_selection_packet with crop/mask, confidence, ambiguity, missing views.
   - Fail closed if object is ambiguous or unsafe category.

2. Model strategy
   - Model intake is multi-entry: photo, voice/text description, existing local STL/3MF, URL, local scan, manual dimensions, parametric CAD, and generated mesh draft all converge to the same evidence schema.
   - Photo is only one entry point; it must not dominate selection when text, dimensions, local library history, or source provenance are stronger.
   - Retrieval-first: search trusted STL/3MF/CAD sources for an existing printable model.
   - Expanded source registry: LocalLibrary, MakerWorld, Printables, ParametricCAD, GrabCAD, Thangs, Thingiverse, Yeggi, Cults3D, MyMiniFactory, and GeneratedMeshDraft.
   - Baseline CLI: `python3 ~/.hermes/scripts/model_candidate_search.py plan --object-label "目标物" --intended-use "用途" --intake-mode photo --intake-mode voice --output /path/candidates.json --json`.
   - The baseline candidate tool only creates evidence/search URLs and generation options; it does not download files, open pages, or perform physical actions.
   - Selection accuracy gate: `python3 ~/.hermes/scripts/model_candidate_search.py evaluate --object-label "目标物" --candidate-title "..." --source Printables --license-status known --provenance-status verified_source_page --format STL --dimensions "..." --preview-evidence thumbnail_and_model_page --similarity-class functional_part --visual-similarity 0.88 --dimension-deviation-pct 4 --json`.
   - Near-identical retrieval before generation: image/photo generation is never first choice when a same/near-same model likely exists. The system searches LocalLibrary, MakerWorld, Printables, and other trusted sources first; GeneratedMeshDraft is allowed only after near-identical retrieval is exhausted and the user approves the draft path.
   - Similarity thresholds: exact replacement requires >=0.95 visual/geometric similarity and <=2% dimension deviation; functional equivalents require >=0.85 and <=5%; decorative equivalents require >=0.75 and <=15%; inspiration-only alternatives require explicit user approval and are not treated as matches.
   - Parametric reconstruction: generate simple CAD for boxes, hooks, stands, brackets, knobs, holders when dimensions are known.
   - Generative mesh draft: allowed only as last-resort draft requiring mesh/preflight review; never auto-selected.
   - Model-studio bridge: image-to-3D providers and GLB/GLTF imports may be used only through `protocols/3d-model-studio-bridge.md`, producing a `hermes_3d_model_studio_bridge_v1` draft packet with provider/task/source metadata, local path, hash, parse/header validity, preview metrics, visual-fidelity class, and explicit blockers.
   - Demo != print veto: a GLB `Demo-ready`/preview-quality verdict, triangle count, texture count, or provider success status is asset triage only. It cannot satisfy model_ready, printability, slicing, or printer-action approval.
   - Draft handoff gate: generated/imported GLB/GLTF remains `draft_only` until source/provenance/license, local artifact hash, scale assumptions, visual preview, human approval for non-retrieved assets, and deterministic preflight path are present.
   - Human/CAD fallback: request more photos, dimensions, or human approval when geometry is underdetermined.

3. Model/provenance approval
   - Required artifacts: source/license, preview, dimensions, scale assumptions, intended use risk tier.
   - Human approval required until class is whitelisted by repeated successful runs.

4. Printability preflight
   - Checks: model file existence/hash, supported extension, intended-use risk tier, slicer availability, manifold/watertight, unit/scale sanity, bed fit, overhang/support risk, thin walls, material/profile compatibility, slicer success, estimated time/filament/cost.
   - Baseline CLI: `python3 ~/.hermes/scripts/manufacturing_preflight.py model /path/model.stl --intended-use "用途" --material PLA --output /path/preflight.json --json`.
   - Output: manufacturing_preflight_verdict plus quality_experience_review.
   - Quality review covers common operator-experience failures before slice approval: cooling artifacts/cooling lines on small visible surfaces, seam/layer-line placement, overhang/bridge/support strategy, support interface/support-material scarring, warping/bed adhesion, stringing/retraction/wet filament risk, and functional-part layer adhesion/load-path orientation.
   - If risks remain unclear or unusual fixes are needed, generate a bounded "trick research" plan: `python3 ~/.hermes/scripts/manufacturing_trick_research.py plan --preflight /path/preflight.json --printer "Bambu X2D" --material PLA --json`.
   - Web-found "邪修" fixes are never auto-applied; they need independent sources, before/after evidence, operator review, and a low-risk test. Verified local successes are appended to `~/.hermes/brains/manufacturing/knowledge/trick-casebook.jsonl` via `record-success`; unverified web claims are not remembered.

5. Slicing / local 3MF artifact
   - Local-first via OrcaSlicer/BambuStudio CLI.
   - Baseline CLI: `python3 ~/.hermes/scripts/manufacturing_slice.py prepare /path/model.stl --output /path/job.3mf --report /path/slice-report.json --json`.
   - The slicer bridge creates a real local 3MF project artifact and structured report; it does not upload or start the printer.
   - No upload/start before external-control approval.

6. External-control action packet
   - Required for upload/start/pause/resume/stop/heat/move.
   - Includes device identity, fresh telemetry, command preview, confirmation marker, idempotency identifier, audit path.

7. Print monitoring
   - Inputs: Bambu status/watch telemetry, HMS/errors, optional camera snapshots.
   - Detect: first-layer failure, no-progress, temperature mismatch, AMS/filament issue, printer error, job mismatch.
   - Any anomaly routes to manufacturing verdict; physical action routes to external-control.

8. Pickup-ready certification
   - Requires: completion telemetry, job identity match, no active errors, cooldown/stabilization threshold, optional camera/visual sanity, audit references, successful notification delivery.
   - During early phases, require human visual confirmation before declaring pickup-ready if camera evidence is unavailable or confidence is low.

## Multi-model deliberation gates

For high-risk or end-to-end photo/vision-to-print decisions, use multi-model synthesis instead of single-model confidence. Keep source/evidence, model dissent, and engineering verification separate.

Reference review artifact:

`~/.hermes/brains/manufacturing/reviews/2026-05-21_x2d-photo-to-print-multimodel-review.md`

Recommended brain/model chain:

1. Intake Brain: voice/photo/text intent only; cannot select model or execute physical action.
2. Vision & Measurement Brain: object candidates, confidence, ambiguity, reference-scale evidence, dimension uncertainty.
3. Retrieval / Similarity Brain: local/web near-identical search and similarity class; generation remains last resort.
4. Manufacturing Brain: material, printability, slicer, support, quality, and load-path proposal.
5. Safety / Policy Brain: independent veto over safety category, license/provenance, generated mesh state, material environment, trick research, and confirmation completeness.
6. External Control Brain: only physical-action executor; requires fresh telemetry, idempotency, audit, packet hash, runtime auth material, and confirmation marker.
7. Human Confirmation Orchestrator: packet-bound final confirmation; any model hash, slice hash, device state, material, or packet hash change invalidates confirmation.

Dissent policy:
- Safety/Policy veto beats Manufacturing proposal.
- Vision/retrieval disagreement downgrades exact replacement to clarification.
- Manufacturing/telemetry disagreement blocks real action.
- Low confidence or missing critical fields blocks progression to real print.
- Multi-model agreement is not truth; it only raises confidence after deterministic checks pass.

Additional quantitative gates now implemented:
- `model_candidate_search.py plan --object-confidence N` fails closed below 0.85.
- `model_candidate_search.py plan --printer "Bambu X2D" --device-status-json status.json --material MATERIAL --require-loaded-material` matches the owned printer profile and AMS/spool material inventory before candidate selection.
- `model_candidate_search.py evaluate --required-material MATERIAL --available-material ...` blocks candidate profiles requiring materials that are not currently available or operator-approved for loading.
- `model_candidate_search.py evaluate` enforces exact-replacement trusted dimension source and <=2% dimension uncertainty/deviation.
- `model_candidate_search.py evaluate` enforces supplied functional mating dimensions at <=0.5mm and <=2%.
- `manufacturing_preflight.py model` supports material/profile hard-bound inputs: nozzle diameter, layer height, nozzle temp, bed temp, and use environment temperature.
- `external_control_gate.py execute` rejects telemetry older than 5s, optional device/material/nozzle/plate/AMS mismatches, and dry-run/final packet hash mismatches.
- `manufacturing_trick_research.py record-success` requires 3 matching verified local successes before a case becomes skill-patch eligible.

## Human checkpoints

Mandatory now:
- confirm selected object from photo,
- confirm model/provenance/license or generated CAD preview,
- confirm scale/material/color/function,
- confirm slicer preview/time/filament estimate,
- confirm print start,
- confirm anomaly intervention,
- optionally confirm pickup-ready until verifier is trusted.

Can be removed only for whitelisted low-risk decorative repeat classes after repeated evidence:
- object selection confidence stable,
- model provenance trusted,
- preflight passes,
- start action audited,
- monitoring catches failures,
- pickup-ready false positive rate remains zero across successful jobs.

## Risk tiers

T0 read-only planning: no action.
T1 low-risk decorative existing model: approvals can be gradually reduced.
T2 generated/modified model: require model, dimension, preflight, and start approval.
T3 functional/load-bearing/electrical/hot/food-contact/child/pet/medical/weapon-like: explicit human review; no auto-approval.
T4 unsafe/illegal: refuse.

## Evidence metrics

- object_selection_confidence and ambiguity notes,
- model provenance/license present,
- mesh validity and slicer success,
- scale/bed/material compatibility,
- external-control audit id for every physical action,
- first-layer and monitoring evidence,
- no active errors at completion,
- pickup-ready verdict confidence,
- notification delivery proof.
