# Douyin 视频：SAM 3D / 单图生成 3D 模型 / ComfyUI 对制造脑的价值

Captured: 2026-06-14

## Social source

Original user share text:

> 0.23 复制打开抖音，看看【GitTopics项目汇的作品】只需上传一张照片，直接获得立体三维模型！ 还在为设... https://v.douyin.com/E3rtUhSWusw/ :5pm Agb:/ Z@z.GV 01/29

Resolved links:
- short: https://v.douyin.com/E3rtUhSWusw/
- resolved share: https://www.iesdouyin.com/share/video/7650710954568617242/?from_ssr=1
- canonical: https://www.douyin.com/video/7650710954568617242

Extracted Douyin metadata:
- aweme_id: `7650710954568617242`
- author: `GitTopics项目汇`
- author signature: `分享全球AI科技前沿。关注我，获得科技灵感`
- description: `只需上传一张照片，直接获得立体三维模型！ 还在为设计图熬秃头？还在为AI影视人物不够生动头疼？SAM 3D-只需上传一张照片，直接获得立体三维模型！结合3DGS、ComfyUI，把3D内容创作从"手工作坊"升级为"自动化工厂"。#AI#cvpr顶会`
- create time: 2026-06-14
- statistics at capture: 5 likes, 0 comments, 0 shares, 4 collects
- video downloaded: `video.mp4`
- contact sheet: `contact_2s.jpg`
- raw router summary: `router_item.json`

## OCR / video-frame evidence

Contact-sheet OCR found:
- `SAM 3D横空出世，Meta颠覆3D视觉模型及代码已开源`
- `从单张2D图像中恢复出逼真的3D场景`
- `将图像中的任何物体3D化，将 Segment Anything 推向三维空间`
- `SAM 3D Body`: one photo can reconstruct human motion/pose and a 3D human model.
- `SAM 3D Object`: one photo can reconstruct object shape, texture, layout; can 360° inspect details; video claims volume/thickness computation.
- Mentions `3DGS` and `ComfyUI` as automation/workflow components.
- Mentions data engine / semi-synthetic data / model-in-the-loop annotation.

## Canonical artifact mapping

Official Meta repos found by GitHub API:

### SAM 3D Objects
- repo: `facebookresearch/sam-3d-objects`
- URL: https://github.com/facebookresearch/sam-3d-objects
- description: `SAM 3D Objects`
- language: Python
- license as reported by GitHub API: `NOASSERTION` (repo README/license file uses SAM license terms; inspect before reuse)
- stars at capture: 6921
- forks at capture: 817
- open issues: 108
- created: 2025-09-29
- pushed: 2026-06-02
- README says it reconstructs full 3D shape geometry, texture, and layout from a single image; handles occlusion/clutter; released code, weights, online demo, and benchmark.
- README quickstart outputs Gaussian splat `.ply` via `output["gs"].save_ply("splat.ply")`.

### SAM 3D Body
- repo: `facebookresearch/sam-3d-body`
- URL: https://github.com/facebookresearch/sam-3d-body
- description: code for SAM 3D Body inference, trained checkpoints/datasets, notebooks.
- language: Python
- license as reported by GitHub API: `NOASSERTION` (repo has SAM license file; inspect before reuse)
- stars at capture: 3251
- forks at capture: 386
- open issues: 68
- created: 2025-07-29
- pushed: 2026-02-19
- README says it is a promptable model for single-image full-body 3D human mesh recovery.

Community ComfyUI wrappers found:
- `PozzettiAndrea/ComfyUI-SAM3DObjects` — ComfyUI wrapper for SAM 3D Objects, 182 stars, license NOASSERTION/SAM-derived; warns it uses experimental `comfy-env` and may download pixi.
- `PozzettiAndrea/ComfyUI-SAM3DBody` — ComfyUI wrapper for SAM 3D Body, 313 stars, GPL-3.0 wrapper with SAM license for vendored SAM code; known multi-person size issue and depth-supported correction attempt.

## Manufacturing Brain value

This is useful, but the landing zone should be **3D model studio bridge / candidate asset generation**, not direct print authorization.

Absorbable patterns:
1. Photo/image -> 3D candidate model pipeline.
2. SAM object/body separation: object reconstruction vs human mesh recovery are different workflows and risks.
3. 3DGS/PLY as preview/render representation, not automatically print-ready STL.
4. ComfyUI as optional studio orchestration for batch generation and visual preview.
5. Generated assets require provenance/license/provider metadata and local hash before entering manufacturing candidates.
6. Visual fidelity gate is critical: mesh QA/slicer success does not prove the generated model matches the source photo.
7. Retrieval-before-generation remains important: search trusted model sources first; use generated mesh only when retrieval fails or user explicitly wants generation.

## Manufacturing / printability boundaries

Hard boundaries for Hermes manufacturing brain:
- Treat SAM 3D outputs as `draft_only` / `studio_preview` until mesh QA, scale, units, visual fidelity, license/provenance, and human approval pass.
- 3DGS `.ply` is not equivalent to watertight printable STL/3MF.
- Single-image reconstruction cannot infer hidden backsides, internal geometry, mating tolerances, load paths, threads, exact dimensions, or material behavior.
- Human/body models have privacy and likeness concerns; do not upload private faces/bodies without explicit permission.
- ComfyUI wrapper installation can download package managers/models and should be side-effect gated.
- Do not connect ComfyUI/Blender/MCP generation directly to printer upload/start.
- Any generated/imported model still must pass: scale assumption, bounding box, mesh validity, orientation search, support preview, material/profile check, slicer preview, visual approval, external-control packet for printing.

## Cost / compute concerns

Cost drivers:
- GPU requirement for SAM 3D inference and model downloads;
- ComfyUI environment/model installation and disk usage;
- cloud demo/API if used instead of local inference;
- repeated generation/refinement passes;
- conversion from 3DGS/mesh to printable geometry;
- human visual QA and slicer preview time.

Recommended low-risk path:
- Use official demos/docs as reference first.
- For local Hermes: add a `photo_to_3d_candidate` stage that records provider/repo/model/checkpoint/local_path/hash/preview only.
- Do not install wrappers or download checkpoints until a dedicated benchmark task is approved.
- Use tiny/public sample images first; no private photos.
- Output candidate manifest and preview, not print-ready status.

## Relationship to existing Manufacturing Brain work

This complements existing manufacturing patterns:
- `3d-model-studio-bridge`: generated/imported GLB/GLTF/mesh drafts as evidence bridge.
- `photo-to-print state machine`: generated model may enter only after object_confirmed/model_strategy_selected and human approval.
- `model similarity policy`: generated model must pass visual_fidelity_gate.
- `Articraft` task: both are candidate 3D asset generation references, but SAM 3D is image-to-3D foundation model; Articraft is code/geometry generation workbench.

## Recommended task framing

`SAM 3D / ComfyUI：制造脑 photo-to-3D candidate 工作流与 draft-only 门禁评估`

Acceptance target:
- Define candidate manifest for image-to-3D generated assets: source photo, provider, model/repo/checkpoint, output format, local hash, units/scale, preview, license/provenance, visual_fidelity_class.
- Map SAM 3D Objects/Body outputs to Manufacturing Brain states: `draft_only`, `studio_preview`, `candidate_model`, `model_ready`.
- Add conversion/QA gates for 3DGS/PLY/mesh -> printable STL/3MF.
- Keep physical printing blocked until normal mesh QA/slicer/external-control gates pass.
- Avoid local install/download unless separately authorized.
