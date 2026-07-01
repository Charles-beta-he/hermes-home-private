# Blender / MCP Studio Bridge

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

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
