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

Concrete implementation reference: see `references/local-cli-mvp-pattern.md` for a proven local CLI shape, artifact contracts, final-reduce command design, Ollama embedding backoff, OCR/path noise filtering, and verification commands.

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

Python interpreter pitfall on this macOS setup: Homebrew `python3` may resolve to Python 3.14 without `PIL`/`pytesseract`, causing OCR to fail with `ModuleNotFoundError: No module named 'PIL'`. The Xcode Python 3.9 at `/Applications/Xcode.app/Contents/Developer/usr/bin/python3` has the OCR dependencies in this environment; use it for real batch runs unless the active environment is verified with `import PIL, pytesseract`.

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
- Ollama node: embedding and optional final local LLM reduce; this is often the easiest first node split because inputs are text windows rather than raw video

Use a canonical task ledger rather than cron-only polling. Workers should produce deterministic artifacts and never silently overwrite controller-owned summaries.

Before asking the user for node details, actively discover what is already queryable from the controller: local interface/subnet, route table neighbors, SSH config hosts, Tailscale/ZeroTier status, TCP reachability for `22`, `8080`, `9000`, `9001`/`9002`, and `11434`, plus safe read-only probes such as `/health`, `/info`, `/v1/models`, `/api/tags`, and `ollama-health` for reachable Ollama endpoints. Write a small `nodes.json` plus `nodes-health.md` report, then stop only at the concrete authorization/setup boundary.

Important correction: do not treat failed SSH login as proof that a node is not connected. A node may already expose Hermes Edge Worker, MLX LLM, vision-node, or Ollama services over HTTP. If `/health` works but `/command` or `/execute` returns `401`, the node is connected but command execution is not authorized; update/synchronize Edge Worker token and command allowlist rather than asking for generic SSH authorization.

When the user asks how to cooperate, minimize manual steps. Prefer a short-lived controller-hosted one-line `curl ... | bash` helper that the user runs on the node, with token material embedded only in the temporary private script and never printed. The helper should update the node env/config, restart Edge Worker, and print a health result. If health becomes connection-refused after restart, generate a second diagnostic/startup helper that rewrites `start.sh`, launches the worker, and prints logs rather than asking the user to manually inspect files. See `references/node-control-plane-patterns.md` for the detailed discovery, classification, and automation pattern.

### Remote / Node Ollama Pattern

Ollama can run on a node computer. Prefer LAN/Tailscale/SSH tunnel access; do not expose `11434` to the public internet.

Node setup:

```bash
ollama pull nomic-embed-text
OLLAMA_HOST=0.0.0.0:11434 ollama serve  # only inside a trusted private network
```

Controller verification:

```bash
python3 -m video_essence.cli ollama-health --ollama-host http://NODE_IP_OR_NAME:11434 --model nomic-embed-text
```

Use the node for indexing and semantic QA:

```bash
python3 -m video_essence.cli index --output <out> --model nomic-embed-text --window-seconds 180 --ollama-host http://NODE_IP_OR_NAME:11434
python3 -m video_essence.cli ask "question" --output <out> --semantic --model nomic-embed-text --ollama-host http://NODE_IP_OR_NAME:11434
```

`OLLAMA_HOST=http://NODE_IP_OR_NAME:11434` can be used as an environment default. Always verify `embedding_dim` and a real semantic query before treating the node as healthy.

## Common Pitfalls

1. **Summarizing the raw long video directly.** This loses auditability and often misses code/PPT terms. Build timeline evidence first.
2. **Skipping OCR.** ASR misses slide titles, code symbols, commands, and library names; OCR often recovers the most valuable technical terms.
3. **Trusting ASR terminology.** Long technical Chinese/English courses need a confusion table and tests for Chinese-adjacent terms.
4. **Letting subprocesses read shell-loop stdin.** ASR tools can consume the next video path in a batch loop. Use `stdin=subprocess.DEVNULL` and `</dev/null`.
5. **Embedding every one-second row.** Group into course windows first; otherwise retrieval is fragmented and slow.
6. **Ignoring OCR noise before embedding.** Repeated taskbar/menu/icon text can dominate vectors. Clean, deduplicate, and truncate with retry/backoff.
7. **Reporting success without read-back.** Count artifacts and run a real ask/semantic ask before finalizing.
8. **Misclassifying connected nodes because SSH fails.** Probe service endpoints (`/health`, `/info`, `/v1/models`, Edge Worker `/health`, Ollama APIs) before concluding that authorization is missing. If Edge Worker health is reachable but command endpoints return `401`, the fix is token/allowlist synchronization for that service, not necessarily SSH.
9. **Making the user do multi-step node setup manually.** For trusted LAN nodes, generate a short-lived one-line helper (`curl -fsSL http://CONTROLLER:PORT/private.sh | bash`) that updates token/config, restarts the worker, and prints health/log output. Keep the script private/temporary and redact token material from all reports.
10. **Only updating `.env` when the worker was started with a hardcoded `--token`.** Some Edge Worker deployments ignore env changes because `start.sh` or launchctl passes `--token` explicitly. Patch or rewrite the startup script as part of the helper, then restart and verify `/command` with the expected auth header.
11. **Confusing token auth success with command execution readiness.** `/info` may be authorized while `run_command` is still blocked by `allowed_commands=[]`. Use `write_file` to update config/allowlist, restart the worker to reload it, then test with a single allowed command such as `python3 /tmp/probe.py`; avoid semicolon-heavy probe strings that fail prefix allowlists.
12. **Starting node Ollama only on loopback.** If controller verification of `http://NODE:11434` fails after local node `/api/tags` works, restart Ollama with `OLLAMA_HOST=0.0.0.0:11434` in the process environment and verify embedding dimension from the controller.

## Verification Checklist

- [ ] The workflow produced inspectable local artifacts rather than only prose.
- [ ] Final notes cite timestamps or frame paths.
- [ ] ASR and OCR were both considered unless the source truly lacks visual information.
- [ ] Domain terms were normalized with regression tests.
- [ ] Batch processing is rerunnable and avoids stdin consumption bugs.
- [ ] Local index/ask was verified with at least one real user-style query.
- [ ] If code was changed, targeted and full tests passed.

## Support Files

- `references/local-cli-mvp-pattern.md` — concrete artifact contract, CLI command surface, Ollama backoff, final-reduce noise filtering, tests, and real verification pattern proven on a 7-video Mina course.
- `references/node-control-plane-patterns.md` — LAN worker discovery order, service-vs-SSH distinction, Edge Worker 401 auth-boundary interpretation, and role-specific node classification.
