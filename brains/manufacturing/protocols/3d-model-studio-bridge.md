# 3D Model Studio Bridge Protocol

Goal: absorb useful image-to-3D / GLB-studio patterns, such as those observed in `huangserva/3DCellForge`, without treating a preview/demo studio as a manufacturing pipeline.

This protocol is a bridge between intake/model exploration and the existing photo-to-print pipeline. It may create evidence and draft assets. It must not authorize slicing, upload, start_print, or any physical printer action.

## Source pattern summary

Reference repo inspected:
- URL: https://github.com/huangserva/3DCellForge
- Commit inspected: `df569572b2eb88c31da89913dc269d816d226e5e`
- Local evidence run: `/Users/charles/.hermes/runs/3dcellforge-review-20260526-004244/`
- Multi-model advisory artifact: `/Users/charles/.hermes/tick-20260525-164458-161376-p34586-8dfaaa64-4d596a35/`

Reusable source patterns:
1. Provider normalization ledger: Rodin, Tripo, Fal variants, local Hunyuan3D, local GLB import, and vision metadata can be normalized into one task/status/output envelope.
2. Draft asset inspection: GLB parse, file size, node/mesh/material/texture/triangle counts, and preview verdicts are useful for triage.
3. Local cache/proxy hygiene: imported or fetched models should have a local path, hash, extension validation, and source-domain restrictions.
4. Human preview loop: model-studio preview is useful for visual triage and user approval.

Non-transferable source assumptions:
- `Demo-ready` or visually impressive is not `print-ready`.
- GLB/GLTF preview validity does not prove watertightness, scale, wall thickness, slicer success, material compatibility, or safe actuation.
- Provider success status does not prove license/provenance, similarity, dimension fidelity, or manufacturability.

## Bridge output schema

A studio/generated/imported asset may advance only as a draft evidence packet:

```yaml
schema: hermes_3d_model_studio_bridge_v1
asset_status: draft_only
source:
  origin: local_import|provider_generation|retrieval_preview|manual_url
  provider: rodin|tripo|fal|hunyuan|local|other
  provider_model: string|null
  task_id: string|null
  source_url: string|null
  license_status: known|unknown|not_applicable
  provenance_status: verified_source_page|provider_result|local_user_upload|unknown
input:
  prompt: string|null
  image_refs: []
  object_label: string
  intended_use: string
  requested_scale: string|null
asset:
  local_path: string
  format: GLB|GLTF|STL|3MF|OBJ|unknown
  sha256: sha256:...
  file_bytes: number|null
  header_or_parse_valid: true|false
  metrics:
    node_count: number|null
    mesh_count: number|null
    triangle_count: number|null
    material_count: number|null
    texture_count: number|null
    bounding_box_mm: [number, number, number]|null
visual_triage:
  preview_available: true|false
  model_studio_verdict: demo_ready|solid|usable|needs_better_source|unknown
  visual_fidelity_class: exact_replacement|functional_part|decorative_equivalent|inspiration_only|unknown
  user_visual_approval: true|false
manufacturing_gate:
  can_enter_preflight: true|false
  blockers: []
  required_next_steps: []
```

## Draft GLB/GLTF gate

For generated or model-studio GLB/GLTF, the default status is `draft_only`.

A draft may enter `model_ready` / manufacturing preflight only when all are true:
1. Local artifact exists and has a stable sha256 hash.
2. Format is supported by the downstream path, or a conversion path is explicitly recorded.
3. Header/parse validation succeeds.
4. Source/provider/provenance/license are recorded; unknown license blocks anything beyond private preview unless the user explicitly accepts private/non-redistribution use.
5. Visual preview exists for decorative/appearance work; user has approved the preview when generated or non-retrieved.
6. Similarity class is not `inspiration_only` unless the user explicitly accepts an inspired substitute.
7. Scale and intended use are explicit. Unknown scale blocks functional/exact replacement work.
8. The bridge labels the asset as `draft_only` and points to the normal preflight/slicer path; it never claims printability.

Minimum triage thresholds are advisory, not print gates:
- `triangle_count > 0` and `mesh_count > 0` are required to avoid empty assets.
- Very low triangle count, missing textures for texture-dependent decorative objects, or implausible file size should trigger `needs_better_source` or human review.
- High triangle count may imply decimation or slicer-performance review, not automatic quality.

## Printability veto

The following vetoes block progression beyond draft triage:
- preview/demo quality is the only evidence;
- missing local path or missing hash;
- unknown source/provenance for a generated or downloaded model;
- unknown real-world scale for functional, mating, exact replacement, load-bearing, electrical, food-contact, child/pet/medical, or hot-environment use;
- no side-by-side visual preview for decorative/photo-derived models;
- no deterministic preflight path for watertightness/manifoldness, wall thickness, bed fit, overhang/support, material/profile, and slicer success;
- any requested physical action before external-control packet generation.

## Handoff into Photo-to-Print

Bridge handoff order:
1. Intake / object confirmation.
2. Retrieval-first model candidate search.
3. If retrieval fails and user approves generation/import, create a bridge draft packet.
4. Human reviews visual preview + source/provenance + scale assumptions.
5. Only then call existing manufacturing preflight.
6. Slice only after preflight passes.
7. Real printer actions remain behind external-control.

This preserves the existing policy: generated mesh drafts are last-resort candidates, not automatic selections.

## Gap matrix from 3DCellForge

| Source pattern | Hermes target | Risk if copied naively | Concrete adoption |
|---|---|---|---|
| Multi-provider task/status/download normalization | Provider ledger in bridge draft packet | Opaque provider result treated as trusted model | Record provider, model, task id, raw source class, local hash, and status separately from printability |
| GLB preview quality metrics | Draft triage before preflight | `Demo-ready` mistaken for printable | Metrics may only rank candidates; preflight/slicer gates remain authoritative |
| Local/cached GLB import and proxy restrictions | Local artifact evidence | Remote mutable URL or unsafe source | Require local path, sha256, extension/header validation, provenance/license |
| Vision metadata and generation prompt | Structured intake evidence | Vision confidence becomes model approval | Use as object/intended-use prompt only; object/model approval stays human-gated unless whitelisted |
| Presentation/demo mode | Human preview and visual-fidelity review | Pretty render hides bad scale/walls/supports | Side-by-side preview is one input; mesh/slicer/material gates decide printability |

## Verification commands

```bash
python3 ~/.hermes/scripts/brainctl.py --json brains validate manufacturing
python3 ~/.hermes/scripts/brainctl.py --json brains route "图片生成3D模型并准备打印"
```
