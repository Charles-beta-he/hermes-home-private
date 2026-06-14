# SAM 3D / image-to-3D draft-gate pattern

Use when evaluating SAM 3D, ComfyUI image-to-3D wrappers, 3DGS/PLY outputs, or any "upload one photo and get a 3D model" workflow for Manufacturing Brain / photo-to-print.

## Core rule

Image-to-3D outputs are **candidate evidence**, not printable parts. They enter the manufacturing workflow as `draft_only` or `studio_preview` until provenance, scale, visual fidelity, mesh QA, slicer preview, and human approval pass.

`3DGS` / Gaussian splat `.ply` / textured preview output is not equivalent to a watertight printable STL/3MF.

## Canonical surfaces to distinguish

- Object reconstruction: e.g. SAM 3D Objects-style single/multi-object geometry, texture, layout, splat/mesh outputs.
- Human/body reconstruction: e.g. SAM 3D Body-style human mesh recovery. This adds likeness/privacy and body-image consent concerns.
- ComfyUI wrappers: useful studio orchestration, but installation may download package managers, models, wrappers, and large checkpoints; treat as side-effectful setup.
- Blender/MCP/studio tools: viewport/import/edit evidence only; they do not prove manufacturability or print readiness.

## Candidate manifest fields

```yaml
photo_to_3d_candidate:
  source_photo_path: null
  source_photo_sha256: null
  consent_scope: private|public_sample|user_approved
  provider_or_repo: null
  model_name_or_checkpoint: null
  wrapper_or_workflow: null
  output_format: ply|glb|gltf|obj|stl|3mf|other
  local_output_path: null
  output_sha256: null
  license_status: unknown|known|incompatible
  provenance_status: unknown|verified_source|generated_local|cloud_output
  unit_scale_assumption: unknown|explicit
  bounding_box_mm: null
  preview_path: null
  visual_fidelity_class: exact_replacement|functional_part|decorative_equivalent|inspiration_only|failed|unknown
  mesh_validity: unknown|valid|needs_repair|invalid
  printability_state: draft_only|studio_preview|candidate_model|model_ready|blocked
  human_approval: pending|approved|rejected
```

## Gate sequence

1. Confirm source-photo consent and intended use.
2. Prefer retrieval of exact/near-identical trusted models before generation unless the user explicitly wants generated art/prototype output.
3. If generation is approved, record provider/repo/model/checkpoint/workflow and local output hash.
4. Capture a visual preview and compare against the source photo.
5. Classify visual fidelity; do not proceed if the output is only generic/inspired when an exact/functional match is needed.
6. Convert/repair only after human approval of the preview.
7. Run mesh QA: watertightness, manifoldness, scale, wall thickness, overhang/orientation, bounding box, units.
8. Run slicer preview and material/profile checks.
9. Only after all checks pass may the asset enter `model_ready`.
10. Printing/upload/start remains blocked until External-Control receives a fresh action packet and explicit confirmation.

## Hard vetoes

- Private person/body/face photo without explicit consent.
- Unknown or incompatible license/provenance for reuse.
- Hidden geometry, mating features, threads, load paths, or exact dimensions inferred from a single image without measurement evidence.
- Claiming 3DGS/PLY preview means printable STL/3MF.
- Installing ComfyUI nodes, downloading checkpoints, or using cloud demos without explicit setup/budget/privacy approval.
- Bypassing retrieval-before-generation, visual-fidelity, mesh-QA, slicer, or external-control gates.

## Cost/compute notes

Treat local SAM3D/ComfyUI evaluation as a benchmark task, not a casual intake step. It can require GPU VRAM, large checkpoint downloads, dependency isolation, and disk space. Start with public sample images and dry-run manifests before private photos or local installs.
