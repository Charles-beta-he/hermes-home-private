# LongCat-Video-Avatar 1.5 digital-persona intake (2026-06-10)

## Social source

- User shared WeChat Channels URL: https://weixin.qq.com/sph/AokCgvaxrU
- Browser-resolved URL: https://channels.weixin.qq.com/finder-preview/pages/sph?id=AokCgvaxrU
- Visible account: `AI慢聊`
- Visible date: 2026-06-10
- Visible post text/OCR:
  - `LongCat-Video-Avatar 1.5 值得看的不是“又一个数字人 Demo”，而是照片 + 音频生成视频这条开源链路终于能开放出来并开始被调试、拼接、开源化。MIT 许可，Whisper-Large 升级，README 给了 demo 命令，适合开发者先看边界再上手。#LongCat #LongCatVideo #美团开源 #数字人 #AI视频 #教程 #GitHub #AI工具`
- Visible video overlay/OCR:
  - `美团重磅开源 LongCat-Video-Avatar`
  - `一张照片加音频就能生成口播`
  - `直接把成本打下来`
- Note: WeChat preview was QR-overlay blocked; extracted visible frame/text only. Treat social post as lead, not authority.

## Canonical artifacts verified

### Project/homepage repos

- `MeiGen-AI/LongCat-Video-Avatar`
  - URL: https://github.com/MeiGen-AI/LongCat-Video-Avatar
  - Local clone: `/Users/charles/.hermes/runs/longcat-video-avatar-intake-2026-06-10/main`
  - Commit: `7cbb465960c154304d60b5e715250b740ef96a8d`
  - README says original LongCat-Video-Avatar supports AT2V, ATI2V, and Video Continuation for single-stream and multi-stream audio.

- `MeiGen-AI/LongCat-Video-Avatar-1.5-Page`
  - URL: https://github.com/MeiGen-AI/LongCat-Video-Avatar-1.5-Page
  - Local clone: `/Users/charles/.hermes/runs/longcat-video-avatar-intake-2026-06-10/page15`
  - Commit: `b4bc0daacb7385e9cc872a0cbedf624aab09c746`
  - README says v1.5 replaces Wav2Vec2 with Whisper-Large, improves lip sync, stability, long-video generation, stylized domains, single/multi-stream audio, and 8-step distillation.

### Canonical code repo

- `meituan-longcat/LongCat-Video`
  - URL: https://github.com/meituan-longcat/LongCat-Video
  - Stars at inspection: 4260; forks: 666; license: MIT; pushed 2026-05-27; updated 2026-06-10.
  - Local clone: `/Users/charles/.hermes/runs/longcat-video-avatar-intake-2026-06-10/code`
  - README says LongCat-Video is a 13.6B foundational video generation model; Avatar 1.5 weights are available on Hugging Face and ModelScope.
  - README install path requires Python 3.10, CUDA-oriented PyTorch 2.6.0+cu124, flash-attn 2.7.4.post1, ffmpeg/librosa/avatar requirements.
  - README Avatar 1.5 commands require `torchrun --nproc_per_node=2`, `--context_parallel_size=2`, `--model_type avatar-v1.5`, `--use_distill`, optional `--use_int8`.
  - License section says model weights are MIT; repository LICENSE is MIT.

## Relevant source evidence

- `README.md` lines 160-210: Avatar 1.5 single/multi audio commands.
- `README.md` lines 164-172: usage tips: audio CFG, prompt detail, ref image index, mask frame range, 480p/720p, dual-audio mode, distill required for 1.5, INT8 optional.
- `run_demo_avatar_single_audio_to_video.py`:
  - input JSON fields: `prompt`, `cond_image`, `cond_audio.person1`.
  - `stage_1` modes include `at2v` and `ai2v`.
  - v1.5 uses `whisper-large-v3` audio encoder.
  - requires CUDA distributed process group (`nccl`) and GPU device selection.
  - separates vocals via `audio_separator` and `Kim_Vocal_2.onnx`.
  - long-video continuation loop uses `generate_avc` segment by segment.
- `assets/avatar/single_example_1.json` shows photo+audio+prompt schema.
- `assets/avatar/multi_example_1.json` shows two-person audio schema with `audio_type: para`.

## Interpretation for Hermes digital persona

This is highly relevant to a future Hermes digital image, but not as a live conversational avatar runtime yet.

Best fit:
1. **Asynchronous persona video generation**: generate short intro/explainer/daily-report videos from a still persona image + TTS audio.
2. **Content pipeline endpoint**: text -> TTS -> audio-driven avatar video -> publish-package artifact.
3. **Digital persona asset studio**: controlled profile image, consent/provenance, voice policy, subtitle/watermark, output review.
4. **Multi-character demos**: possible later for interviews/podcast-style content, but higher safety and quality bar.

Poor first fit:
- Low-latency live avatar in Telegram/desktop conversation.
- Local Mac inference without external GPU; CUDA/flash-attn/large weights make this unsuitable for default local Hermes runtime.
- Unreviewed public posting or likeness cloning.

## Recommended Hermes architecture boundary

Define a `video_avatar_generate` adapter contract rather than embedding model code into Hermes core:

```json
{
  "persona_id": "hermes-default",
  "consent_ref": "user-approved-persona-asset",
  "prompt": "A friendly assistant speaking to camera...",
  "image_path": "/abs/persona.png",
  "audio_path": "/abs/tts.wav",
  "mode": "ai2v",
  "duration_policy": {"segments": 1, "resolution": "480p"},
  "backend": "longcat-avatar-1.5-remote-gpu",
  "safety": {"watermark": true, "review_required": true},
  "outputs": {"video_path": "...", "provenance_json": "..."}
}
```

Adapter options:
- `remote_gpu_worker` first: Modal/RunPod/manual GPU host wrapper, because local Mac is not a realistic default.
- `local_gpu` only if CUDA GPU is available.
- `hosted_api` if a compliant provider appears.
- `watchlist` if weight/download/runtime cost is too high.

## Safety / governance

- Require explicit consent for persona image and voice/audio.
- Store provenance: input image hash, audio hash, prompt, model/version, backend, timestamp, reviewer.
- Default output is draft/review, not public publish.
- Watermark or metadata for generated digital-human media.
- Do not clone third-party likeness/voice without rights.
- Keep LongCat dependencies and weights out of Hermes core; isolate in worker/container.

## Taskpool recommendation

Existing tasks already evaluated generic LongCat Avatar 1.5 integration on 2026-06-03. Do not add another duplicate generic evaluation. Add a narrower follow-up focused on Hermes digital-persona pipeline:

- Title: `设计 Hermes 数字形象 video_avatar_generate 适配器契约与远程 GPU 原型边界`
- lane: `evolution`
- priority: `P2`
- project: `hermes-agent`
- architecture_target: `local-brain`
- acceptance: adapter contract, consent/provenance schema, backend selection, no local install, no model run, no public publish.

## Go / no-go

- Go for architecture/design intake and taskpool follow-up.
- Go later for a remote-GPU dry-run only after explicit budget/GPU authorization and approved persona assets.
- No-go for immediate local install/run on this Mac and no-go for live real-time avatar claims.
