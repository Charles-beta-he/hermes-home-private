---
name: media
description: Use when you need the Media workflow umbrella. See references/ for detailed
  guides.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - media
    - workflow
    - umbrella
    - routing
    related_skills:
    - gif-search
    - spotify
    - youtube-content
---

# Media

## Overview

This umbrella skill is the routing surface for media. Use it to choose the most specific child skill, reference, or workflow instead of treating the category name as a one-size-fits-all procedure.

## When to Use

- You need help somewhere inside media and want the quickest route to the right child skill.
- You are not yet sure which media sub-workflow best matches the request.
- You want a compact map of the media skill family before loading a more specific procedure.
- Don't use for: a request that already clearly matches one specific media child skill; load that child skill directly.

## Routing Guide

- `gif-search` — you need to search and download GIFs from Tenor using curl.
- `spotify` — you need to control Spotify — play music, search the catalog, manage playlists and library, inspect devices and playback state.
- `youtube-content` — the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat content from any YouTube video.
- Long local lecture/class/meeting videos — use `references/long-video-essence-pipeline.md`. Treat these as evidence-pipeline tasks: ASR + keyframes/OCR + timestamped evidence fusion + chunked map-reduce + RAG, with optional cloud-model enhancement. Consider node-computer workers for ASR/OCR/frame extraction at scale.
- Douyin/TikTok-style short links or notes — use `references/douyin-short-video-analysis.md`. Resolve the short URL, extract caption/page text plus DOM media URLs, download high-resolution note images/video sources when accessible, and verify any linked artifact (GitHub/research/product) directly before judging value.
- AI-assisted video editing / DaVinci Resolve / automatic rough-cut workflows — use `references/davinci-autoedit-cost-gated-workflow.md`. Treat VLM/TTS/LLM calls and Resolve/MCP timeline writes as separate approval gates; start with source-immutable media review, cost estimate, and blueprint-only fallback before any paid call or edit write.
- WeChat Channels / 视频号 public preview links — scope: `weixin.qq.com/sph/...` and resolved `channels.weixin.qq.com/finder-preview/...`; use `references/wechat-channels-video-analysis.md`. Applicability: user asks to analyze/summarize/extract workflow value from the link. Anti-condition: do not infer a referenced artifact is valid from the video alone; verify the artifact directly first.
- Sci-fi / mecha voice generation — use `references/sci-fi-mecha-voice-generation.md` when generated speech needs a dramatic synthetic style such as cockpit, mecha boot sequence, tactical comms, or operational readiness. Prefer controllable Chinese TTS plus audio post-processing; plain OS voices usually read text but miss style. For this user's Hermes boot voice, also read `references/mecha-voice-generation-session-notes.md` for LOCCENT-style Chinese cadence, MiMo V2.5 TTS/voiceclone paths, fixed-loudness A/B comparison, and game-reference clone boundaries. For short Hermes notification identity sounds and desktop sound-wave visuals, read `references/mecha-notification-identity-and-waveform.md`; current preferred notification direction is BT Unit Ready / reliable heavy-mech partner, short Chinese-only text, semantic rhythm, and `-16 LUFS` fixed loudness. For MiMo V2.5 experiments, use `scripts/mimo_mecha_tts_experiment.py` as a reusable candidate generator. For game-inspired A/B directions and the safe voiceclone boundary, also read `references/mecha-game-voice-reference-and-clone.md`. For game-inspired comparison directions (Armored Core warning, Titanfall/BT reliable unit, MechWarrior/BattleTech Betty, Zone of the Enders/ADA, Front Mission, DAEMON X MACHINA), use `references/mecha-game-voice-comparison.md`; for boot voice the user previously liked concise Chinese LOCCENT female control-room reporting with pauses, not mixed Chinese/English.

## Selection Rules

- Prefer the narrowest child skill that matches the user request, platform, and desired artifact.
- Stay at the umbrella level only for routing, taxonomy, or category-wide orientation.
- If the request spans multiple subskills, use this umbrella to map the lane first, then hand off to the specific workflow that will do the real work.

## Absorbed Workflow Packages (2 consolidated in curator umbrella pass)

These former narrow child skills are now treated as subsections/reference packages under this class-level umbrella. Load the package only when the task needs that provider/tool's detailed commands, templates, or scripts; otherwise use the umbrella routing rules above.

- `gif-search` → `references/absorbed/gif-search/SKILL.md`: Use when you need to search and download GIFs from Tenor using curl.
- `youtube-content` → `references/absorbed/youtube-content/SKILL.md`: Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, or wants to extract and reformat content from any YouTube video.


## Common Pitfalls

1. Using the media umbrella as the full procedure even though a more specific child skill already fits.
2. Reading the routing map but never loading the referenced child skill or support material that contains the actual execution steps.
3. Choosing a child skill without checking that its platform, tools, and expected artifacts match the current task.

## Verification Checklist

- [ ] The request was mapped to the best-fitting child skill or explicitly kept at umbrella level for routing only.
- [ ] The selected child skill descriptions, references, and prerequisites were checked before substantive execution.
- [ ] Any claimed handoff, output, or route decision was read back against the specific child workflow before completion.
- [ ] Pipeline control: each stage has an explicit gate before the workflow advances.
