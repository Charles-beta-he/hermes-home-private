# 3DCellForge Multi-Model Review for Manufacturing Brain

Date: 2026-05-25
Source: https://github.com/huangserva/3DCellForge
Inspected commit: `df569572b2eb88c31da89913dc269d816d226e5e`
Local clone: `/Users/charles/.hermes/runs/3dcellforge-review-20260526-004244/repo`
Multi-model artifact: `/Users/charles/.hermes/tick-20260525-164458-161376-p34586-8dfaaa64-4d596a35/`

## Verdict

3DCellForge is useful as a model-studio reference, not as a print pipeline. Its strongest transferable patterns are provider normalization, model-status tracking, GLB/GLTF local persistence, proxy/header hygiene, and preview/demo asset metrics. It does not replace Hermes Manufacturing Brain's retrieval-first, provenance/license, visual-fidelity, mesh QA, preflight, slicer, and external-control gates.

## Evidence-backed source observations

- The project is a React/Vite/Three.js studio for uploading reference images or GLB files, screenshots, GLB export, generation queue, and optional image-to-3D providers.
- Providers are normalized across Rodin, Tripo, Fal variants, Hunyuan3D, local GLB import, and OpenAI vision metadata.
- `src/lib/modelQuality.js` provides asset-side metrics: file bytes, nodes, meshes, materials, textures, triangles, and preview-quality verdicts.
- `server/model-store.mjs` persists local/remote GLB/GLTF assets, validates headers/JSON, restricts proxy URL classes, and limits provider auth attachment.
- `npm install --ignore-scripts && npm test && npm run build` completed successfully in the clone; 26 node tests passed and the Vite build succeeded with a chunk-size warning.

## Alignment with consult_models.py-style norms

The review state used explicit `claims` and `evidence`, and the consult run returned:
- Tier: T1
- Planner fan-out: 4/4 succeeded
- Certification: fanout quorum met, truth grounded
- Consensus: weak consensus on exact patch shapes, strong agreement on bridge direction

Important consistency decisions:
- Keep `state_claim`/evidence separate from recommendations.
- Do not treat provider success or multi-model agreement as truth.
- Use canonical model IDs from the local multi-model system (`claude-opus-4-7`, `gpt-5.5`, `mimo-v2.5-pro`, `deepseek-v4-pro`) only for the consult layer; do not leak these into Manufacturing Brain's provider ledger for 3D generation vendors.
- Keep generated 3D providers (`rodin`, `tripo`, `fal`, `hunyuan`, `local`) as asset provenance, not reasoning-model identities.

## Gap matrix

| Source pattern | Hermes manufacturing target | Risk | Adopted change |
|---|---|---|---|
| Multi-provider task/status/download normalization | Provider asset ledger | Opaque provider result treated as trusted model | Added `3d-model-studio-bridge.md` draft packet schema |
| GLB preview metrics | Draft triage before preflight | `Demo-ready` mistaken for printable | Added demo != print veto |
| Local/cached GLB import and proxy checks | Local artifact evidence | Mutable/unsafe remote asset | Require local path, sha256, header/parse validation |
| Vision metadata and prompts | Structured intake | Vision confidence becomes model approval | Keep vision as evidence; model selection remains gated |
| Preview UI | Human visual review | Pretty render hides bad scale/walls/supports | Require visual preview + human approval for non-retrieved assets |

## Implemented Manufacturing Brain improvements

- Added protocol: `~/.hermes/brains/manufacturing/protocols/3d-model-studio-bridge.md`
- Added capabilities/routing hints in `~/.hermes/brains/manufacturing/brain.yaml`:
  - `model_studio_bridge_planning`
  - `generated_mesh_draft_gate`
  - `provider_asset_ledger_generation`
  - GLB/GLTF/image-to-3D/Rodin/Tripo/Hunyuan3D/Fal routing hints
- Added explicit draft/GLB handoff gate in `photo-to-print-pipeline.md`.
- Added operator-facing bridge guidance to the `manufacturing-brain` skill.

## Hard veto retained

Generated/imported GLB/GLTF is always `draft_only` until it has local hash, provenance/license, scale/intended use, visual preview, human approval when non-retrieved, and deterministic preflight/slicer path. Display/demo quality cannot authorize slicing, upload, start_print, or pickup-ready claims.

## Verification

- `python3 ~/.hermes/scripts/brainctl.py --json brains validate` passed.
- `python3 ~/.hermes/scripts/brainctl.py --json brains route '图片生成3D模型并准备打印'` currently routes to `main` via `default_entry`; manufacturing is present in routing table under manufacturing/3D-printing semantics, but exact phrase routing likely needs future router-keyword enhancement if desired.
