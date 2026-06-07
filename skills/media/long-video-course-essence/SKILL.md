---
name: long-video-course-essence
description: Use when extracting reusable study notes, timestamped evidence, searchable summaries, or RAG/semantic QA from long local course videos, meeting recordings, screencasts, or lecture videos. Prefer local ASR/OCR/timeline evidence before any LLM reduce.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [video, course, asr, ocr, rag, local-first, evidence]
    related_skills: [media, youtube-content, mlops, test-driven-development]
---

# Long Video Course Essence Extraction

## Overview

Use a local evidence pipeline before asking any large model to summarize a long video. The durable artifact is not the prose summary; it is the timestamped evidence spine: ASR transcript, OCR text, key frames, normalized terms, and timeline rows that can be searched or reduced later.

This workflow is designed for local course videos, classroom recordings, code screencasts, and meeting recordings where the user wants reusable study assets rather than a one-off summary. It works especially well on Apple Silicon with `ffmpeg`, `mlx-whisper`, Tesseract OCR, and Ollama embeddings.

## When to Use

Use this skill when the user asks to:

- analyze long local videos or courses on disk
- extract the essence / 精髓 / 复习笔记 from lecture videos
- build timestamped notes from meeting recordings or screencasts
- create searchable evidence from videos using ASR + OCR
- turn a folder of videos into a local knowledge base or RAG source
- compare technical approaches for long-video summarization

Don't use for:

- short online video links where a transcript is already available; use `youtube-content` when applicable
- pure video editing, subtitles-only work, or visual design critique
- generating an unconstrained summary with no need for timestamps, OCR, or retrieval
- tasks that require cloud-only media APIs because the user explicitly wants upload-based processing

## Core Principle

Do not send the whole long video directly to one model. Build evidence first:

```
video
 -> audio extraction
 -> ASR transcript
 -> key-frame extraction
 -> OCR over slides/code/screens
 -> term normalization
 -> timeline.jsonl evidence rows
 -> per-video essence/reduce
 -> cross-video index
 -> semantic ask / final reduce
```

Every final claim should be traceable to at least one of:

- source video path
- timestamp range
- ASR segment
- OCR text
- key-frame path

## Recommended Local Stack

| Layer | Preferred local tool | Notes |
| --- | --- | --- |
| Video/audio | `ffmpeg`, `ffprobe` | Extract audio, key frames, metadata |
| ASR on Apple Silicon | `uvx --from mlx-whisper mlx_whisper` | Use `mlx-community/whisper-large-v3-turbo` for real runs; tiny only for smoke tests |
| OCR | Tesseract/Pytesseract first | Crop slide region; remove taskbars and repeated OCR noise |
| Term correction | regex/confusion table | Correct high-frequency ASR errors such as o1js/TypeScript/Circom/Groth16 |
| Embedding | Ollama `nomic-embed-text` | Use windowed chunks and backoff/truncation for long noisy text |
| Storage | JSON/JSONL first | Keep artifacts inspectable; later migrate to SQLite/Chroma/Qdrant if needed |
| Reduce | local rules first, optional LLM later | Rules provide auditability; LLM final reduce should consume evidence, not raw videos |

## Pipeline Stages

### 1. Discover and scope videos

- Search only the relevant folder when possible; full desktop recursion can be slow.
- Use `ffprobe` with timeouts and cache results for large folders.
- Create a stable video id from path/metadata so reruns are resumable.

Artifacts:

- `videos.json`
- one output directory per video: `<stable-id>-<stem>/`

### 2. Process each video into evidence

For each video:

1. Extract audio to `audio.wav`.
2. Run ASR to `transcript.json`.
3. Extract frames at a fixed interval, often 30 seconds for courses.
4. OCR frames to `ocr.jsonl`.
5. Merge ASR + OCR + frame paths into `timeline.jsonl`.
6. Write `manifest.json`.

Important pitfall: some ASR tools read stdin. When batch-processing shell loops, invoke subprocesses with `stdin=subprocess.DEVNULL` and, for shell scripts, redirect child commands with `</dev/null` so the ASR process cannot consume subsequent loop lines.

### 3. Normalize terms

Build a domain-specific confusion table as soon as real ASR errors appear. For technical courses this is critical.

Examples from a Mina/o1js course:

- `OVNGS`, `O1JS`, `O1js` -> `o1js`
- `Timescript`, `Type Script`, `Typescript` -> `TypeScript`
- `Globe 16` -> `Groth16`
- `Sircon`, `Skern Skern` -> `Circom`
- `Trusted setup setup` -> `Trusted setup`

Do not rely on English word boundaries when terms sit next to Chinese characters. Test cases should include strings like `基于Timescript的` and `语言叫Sircon`.

### 4. Generate per-video summaries

Generate at least two levels:

- `essence.md`: basic timestamped summary, cards, QA
- `essence-reduced.md`: denser course note with knowledge tree, high-value timestamps, pitfalls, review route, and evidence boundaries

A good course essence includes:

- one-sentence conclusion
- knowledge map
- important timestamps
- key concepts and terms
- commands/code/API names from OCR
- pitfalls and misconceptions
- review cards or practice tasks
- evidence links back to frames/timestamps

### 5. Build cross-video index

For semantic retrieval:

- group timeline rows into time windows (e.g. 120-180 seconds)
- embed normalized text with local embedding model
- write `vector_index.jsonl`
- store video path, start/end timestamps, text, frame paths, embedding

If Ollama returns HTTP 500 on long/noisy inputs, reduce `max_embed_chars` and use backoff/truncation. Course OCR can create repeated noise; always clean and deduplicate before embedding.

### 6. Ask and final reduce

Use two retrieval modes:

- keyword/text ask for exact terms
- semantic ask for conceptual queries

Final reduce should not read raw video. It should consume:

- per-video `essence-reduced.md`
- top keyword/semantic evidence
- representative timeline chunks
- key frame paths

Then produce a course-level `course-final.md` with traceable conclusions.

## Batch Verification Checklist

Before reporting completion, verify with real files:

- [ ] `videos.json` has the expected video count
- [ ] every video has `manifest.json`
- [ ] every video has `transcript.json`
- [ ] every video has `ocr.jsonl`
- [ ] every video has `timeline.jsonl`
- [ ] every video has `essence.md` or equivalent summary
- [ ] per-video reduce files exist when requested
- [ ] vector index exists when semantic ask is requested
- [ ] embeddings have consistent dimensions
- [ ] at least one keyword ask returns timestamped evidence
- [ ] at least one semantic ask returns timestamped evidence
- [ ] all project tests pass after code changes

## Node Worker Extension

For multiple machines, keep one controller and many workers:

- controller: task ledger, quality gates, final reduce, index write, user-facing QA
- workers: audio extraction, ASR, frame extraction, OCR, chunk embedding

Use a canonical task ledger rather than cron-only polling. Workers should produce deterministic artifacts and never silently overwrite controller-owned summaries.

## Common Pitfalls

1. **Summarizing the raw long video directly.** This loses auditability and often misses code/PPT terms. Build timeline evidence first.
2. **Skipping OCR.** ASR misses slide titles, code symbols, commands, and library names; OCR often recovers the most valuable technical terms.
3. **Trusting ASR terminology.** Long technical Chinese/English courses need a confusion table and tests for Chinese-adjacent terms.
4. **Letting subprocesses read shell-loop stdin.** ASR tools can consume the next video path in a batch loop. Use `stdin=subprocess.DEVNULL` and `</dev/null`.
5. **Embedding every one-second row.** Group into course windows first; otherwise retrieval is fragmented and slow.
6. **Ignoring OCR noise before embedding.** Repeated taskbar/menu/icon text can dominate vectors. Clean, deduplicate, and truncate with retry/backoff.
7. **Reporting success without read-back.** Count artifacts and run a real ask/semantic ask before finalizing.

## Verification Checklist

- [ ] The workflow produced inspectable local artifacts rather than only prose.
- [ ] Final notes cite timestamps or frame paths.
- [ ] ASR and OCR were both considered unless the source truly lacks visual information.
- [ ] Domain terms were normalized with regression tests.
- [ ] Batch processing is rerunnable and avoids stdin consumption bugs.
- [ ] Local index/ask was verified with at least one real user-style query.
- [ ] If code was changed, targeted and full tests passed.
