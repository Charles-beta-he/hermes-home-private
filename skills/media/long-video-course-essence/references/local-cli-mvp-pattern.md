# Local CLI MVP Pattern for Long Video Course Essence

This reference captures a reusable implementation pattern proven on a 7-video local technical course. Keep it as a concrete recipe; adapt paths, models, and domain terms per project.

## Artifact contract

Use plain files first so every stage is inspectable and rerunnable:

- `videos.json` — scanned video inventory
- `<stable-id>-<stem>/manifest.json` — single-video output manifest
- `<stable-id>-<stem>/transcript.json` — ASR output
- `<stable-id>-<stem>/frames/` — extracted frames
- `<stable-id>-<stem>/ocr.jsonl` — OCR rows per frame
- `<stable-id>-<stem>/timeline.jsonl` — merged ASR/OCR/time/frame evidence
- `<stable-id>-<stem>/essence.md` — basic timestamp summary/cards/QA
- `<stable-id>-<stem>/essence-reduced.md` — dense per-video study note
- `vector_index.jsonl` — cross-video semantic index
- `course-final.md` — whole-course final reduce from evidence

## CLI surface that worked well

A minimal but useful CLI can expose these commands:

```bash
python3 -m video_essence.cli scan <video_dir> --output <output_dir>
python3 -m video_essence.cli process <video_file> --output <output_dir> --asr-model mlx-community/whisper-large-v3-turbo --frame-interval 30
python3 -m video_essence.cli summarize <manifest.json> --title <title>
python3 -m video_essence.cli reduce <manifest.json> --title <title> --window-seconds 180
python3 -m video_essence.cli index --output <output_dir> --model nomic-embed-text --window-seconds 180
python3 -m video_essence.cli ask "question" --output <output_dir>
python3 -m video_essence.cli ask "question" --output <output_dir> --semantic --model nomic-embed-text --limit 8
python3 -m video_essence.cli final-reduce --output <output_dir> --title "Course title" --evidence-limit 16
```

## Implementation details worth reusing

### Stable output directories

Use a deterministic id from the video path/metadata plus the sanitized stem. This makes reruns safe and prevents two videos with the same basename from colliding.

### Timeline row shape

Keep each evidence row self-contained enough for search and final reduce:

```json
{
  "video_path": "...",
  "start": 0.0,
  "end": 12.3,
  "asr_text": "...",
  "ocr_text": "...",
  "normalized_text": "...",
  "frame_paths": ["..."]
}
```

### Semantic index row shape

```json
{
  "video_path": "...",
  "start": 0.0,
  "end": 180.0,
  "text": "normalized ASR + OCR window text",
  "frame_paths": ["..."],
  "embedding": [0.01, 0.02]
}
```

### Windowing

For course videos, embedding each tiny ASR row fragments retrieval. Group adjacent timeline rows by time window first:

- 120s: more precise, more rows
- 180s: good default for technical lectures
- 300s+: fewer rows, useful for coarse course-level overview

### Ollama embedding backoff

Ollama `nomic-embed-text` may fail on long/noisy OCR-heavy text. The robust pattern is:

1. truncate to `max_embed_chars` (e.g. 4000)
2. call embedding
3. if it fails, halve the input length and retry
4. stop at a `min_embed_chars` floor; only then fail the row

Capture the retry pattern, not a permanent negative claim about Ollama.

### OCR/path noise filtering for final reduce

When final-reducing generated markdown, strip template boilerplate and path artifacts before keyword extraction. Filter examples:

- `结合下方时间戳证据复习其定义...`
- local path pieces such as `Users`, `charles`, `Desktop`, `video-essence-output-*`
- frame/hash artifacts with long hex substrings
- short OCR garbage such as `ams`, `Show` when isolated

Do not over-filter technical short tokens like `o1js`, `DSL`, or `zkApp`.

## Test suite shape

Useful tests:

- scan discovers videos recursively
- process writes manifest/timeline and handles subprocess stdin safely
- term normalization corrects Chinese-adjacent ASR errors
- OCR cleaning removes repeated noise but keeps technical terms
- ask ranks timestamp evidence and deduplicates adjacent same-frame hits
- semantic ask formats vector hits with timestamps and frames
- index windows timeline rows and truncates/retries long embeddings
- reduce writes per-video essence with evidence sections
- final-reduce combines video reduces and vector evidence
- final-reduce filters template/path/OCR noise

## Verification before reporting done

Run real verification, not just tests:

```bash
python3 -m unittest discover -s tests -v
python3 -m video_essence.cli index --output <output_dir> --model nomic-embed-text --window-seconds 180
python3 -m video_essence.cli ask "real user-style question" --output <output_dir> --semantic --model nomic-embed-text --limit 8
python3 -m video_essence.cli final-reduce --output <output_dir> --title "Course title" --evidence-limit 16
```

Read back counts:

- number of videos/manifests/timelines/OCR files/reduce files
- vector index rows and embedding dimensions
- final `course-final.md` size, lines, timestamp evidence, and key-frame evidence

Commit only after these pass.