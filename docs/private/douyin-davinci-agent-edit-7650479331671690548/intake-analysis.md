# Douyin 视频：DaVinci AutoEdit Agent 自动剪辑 skill intake

Captured: 2026-06-14

## Social source

Original user share text:

> 7.12 复制打开抖音，看看【小草的作品】达芬奇Agent自动剪辑skill分享 看不懂可私... https://v.douyin.com/iBiRLTVSAYc/ 02/27 HII:/ A@T.Lw :6pm

Resolved links:
- short: https://v.douyin.com/iBiRLTVSAYc/
- resolved share: https://www.iesdouyin.com/share/video/7650479331671690548/?from_ssr=1
- canonical: https://www.douyin.com/video/7650479331671690548

Extracted Douyin metadata:
- aweme_id: `7650479331671690548`
- author: `小草`
- author signature: `心中有太阳，夜晚也明亮`
- description: `达芬奇Agent自动剪辑skill分享 看不懂可私信，适合口播旅行vlog\n#ai #剪辑教程 #脱发焦虑`
- create time: 2026-06-12
- statistics at capture: 9547 likes, 321 comments, 3014 shares, 8854 collects
- video downloaded: `video.mp4`
- contact sheet: `contact_10s.jpg`
- raw router summary: `router_item.json`

## OCR / video-frame evidence

Contact-sheet OCR found:
- Repo/skill location: `https://github.com/liuhaixiu/DaVinci-AutoEdit-Agent` in the video. GitHub search resolved the canonical repo as `https://github.com/liuluhaixiu/DaVinci-AutoEdit-Agent` (note `liuluhaixiu` owner spelling from GitHub API).
- Step 1: tell AI where the media is and how to filter it; can also give material links and let AI download.
- Step 2: provide VLM API; demo uses `gemini 2.5 flash lite`.
- Step 3: input copywriting idea or outline; final script is decided from both video material and user input.
- Step 4: use TTS API if needed; can skip; can provide reference audio to clone own voice; supports multiple voices and different emotional tones.
- Step 5: create edit blueprint; import into DaVinci; skill guides the model to configure MCP; user opens DaVinci and tells the agent ready.
- Additional visible claims: 360 video can be analyzed, but Insta360 Studio preprocessing is recommended; this step can take around one hour. Script uses a separate social-media copywriting skill. Rough cut, subtitles, music are enough for first pass; user can ask GPT to adjust unsatisfactory parts.
- Cost clue: VLM/API analysis shown as about `$0.06` for the demo clip, with author expressing pain/cost concern. Cost accumulates with long clips, high frame sampling, online VLM, TTS, and repeated iterations.

## Canonical GitHub mapping

GitHub API confirmed:
- repo: `liuluhaixiu/DaVinci-AutoEdit-Agent`
- URL: https://github.com/liuluhaixiu/DaVinci-AutoEdit-Agent
- description: `AI自动剪辑的“第一次接触”，一款基于davinci mcp的全自动自媒体视频剪辑skill`
- language: Python
- license: MIT
- stars at capture: 68
- forks at capture: 10
- open issues: 0
- created: 2026-06-12
- pushed: 2026-06-12
- default branch: main

Repo README confirms:
- Codex skills repository for DaVinci Resolve auto-editing.
- Workflow: brief -> media path/topic/goal -> user pacing rules -> LLM/TTS/Resolve config check -> scan video/audio/images -> extract frames/review/tags -> confirm review -> script -> optional TTS -> edit blueprint -> Resolve project/timeline -> audit gaps/repetition/source bounds/write result -> pickup-shot report.
- Bundled skills: `davinci-autoedit-agent`, `viral-video-writer`, `davinci-resolve-editor`.
- Requirements: Python 3.10+, FFmpeg/FFprobe, optional OpenAI-compatible multimodal model, optional TTS HTTP API, optional DaVinci Resolve Studio 18.5+, optional `davinci-resolve-mcp`.
- Resolve free edition may not support external scripting; blueprint-only still works.
- `requirements.txt` only includes `python-dotenv` and `requests`; heavy dependencies are external tools/APIs.
- `.env.example` defines optional LLM/TTS/Resolve API variables; no private defaults.

## Value for Hermes

This is highly relevant to a Hermes media/workflow feature: an **approval-gated automatic editing workflow**.

Absorbable patterns:
1. Media intake and source immutability: original media remains read-only.
2. Stage gates: brief, scan scope, material review, script, TTS plan, edit blueprint, timeline write, render/audit, pickup report.
3. Evidence-driven script: script/copy must be grounded in extracted frames and material review, not generic copy.
4. Resolve/MCP as an external write surface: timeline construction requires explicit approval and write verification.
5. Cost-aware VLM/TTS: estimate and cap billable calls before first paid request.
6. Blueprint-only fallback: if DaVinci scripting/MCP is unavailable, still produce a useful edit decision list / blueprint.
7. Iterative conversation adjustment: user can ask for local timeline/script changes after rough cut.

## Cost model and control proposal

User explicitly worries about cost. The cost surface should be first-class:

Cost drivers:
- video duration and number of clips;
- frame sampling rate and OCR/VLM resolution;
- repeated VLM passes;
- TTS generation/voice clone calls;
- cloud LLM script iterations;
- 360/Insta360 preprocessing time;
- manual review time if APIs are disabled.

Recommended Hermes budget gates:
- `budget_mode: dry_run | low | normal | high`
- preview estimated frames/tokens/API calls before billable work;
- user-defined max spend per run, e.g. `$0.20/$1/$5`;
- sample-first: analyze 30-60 seconds or low-fps proxy before full run;
- cache extracted frames, transcripts, material tags, and VLM outputs by media hash;
- default TTS off unless user asks;
- local/cheap model first where good enough;
- stop after rough cut unless user approves refinement;
- require explicit confirmation before DaVinci write or render.

## Boundaries / red lines

- Do not install repo, Codex skills, DaVinci MCP, or dependencies during intake.
- Do not call paid VLM/TTS APIs without an explicit budget gate.
- Do not mutate source media.
- Do not write to DaVinci project/timeline without user approval and target read-back.
- Do not assume DaVinci free edition can run scripts.
- Do not treat a successful MCP/API call as proof of timeline write; inspect Resolve project/timeline or output artifacts.
- Do not auto-download private/social media links without source permission.

## Recommended task framing

`Douyin DaVinci AutoEdit Agent：Hermes 自动剪辑 workflow 与成本门禁吸收`

Acceptance target:
- Define Hermes auto-edit workflow pack with stages and approvals.
- Add cost estimator/budget gate for VLM/TTS/LLM/Resolve operations.
- Support blueprint-only mode before any DaVinci write.
- Specify evidence artifacts: media manifest, frame sheet, material taxonomy, script, TTS plan, edit blueprint, Resolve write audit, pickup-shot report.
- Keep source media immutable and write surfaces gated.
