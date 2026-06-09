# Long-video course essence extraction pipeline

Use this reference when the user asks to extract the essence of long local videos, lectures, recorded classes, meetings, or screen recordings.

## Core lesson

Do not treat long-video understanding as a single-model summarization problem. Treat it as an evidence pipeline:

```text
local videos
  -> metadata scan with ffprobe
  -> audio extraction with ffmpeg
  -> ASR with timestamped segments
  -> keyframe extraction
  -> OCR / visual text extraction
  -> timeline evidence fusion
  -> chunk-level structured extraction
  -> global reduce / essence synthesis
  -> local RAG / searchable knowledge base
  -> optional cloud-model enhancement
```

The durable artifact is not only a summary. It should be a learning asset with timestamps and evidence.

## Recommended local stack on Apple Silicon

- Metadata/audio/frames: `ffprobe` and `ffmpeg`.
- ASR first choice: `mlx-whisper` for Apple Silicon.
- ASR alternate: `whisper.cpp` for lightweight CLI automation.
- ASR future GPU path: `faster-whisper` or WhisperX on Linux/NVIDIA.
- Avoid using tiny/base Whisper models for final Chinese technical-course output; they are useful for smoke tests only. Use `large-v3-turbo` or at least `medium` for final passes.
- OCR: PaddleOCR/RapidOCR for engineering use; system OCR or visual model can be used for early validation; Tesseract as fallback.
- Embeddings: local embedding model via Ollama or equivalent; use hybrid search when professional terms matter.

## Why ASR alone is insufficient

Lecture/screen-recording videos often contain key information only on screen:

- PPT titles and chapter markers
- code, commands, filenames, URLs
- formulas and diagrams
- whiteboard content
- toolchain names
- assignments / action items

Always consider keyframes + OCR/visual extraction unless the source is audio-only.

## Output shape

Each video should produce an auditable directory such as:

```text
video-essence/<video_id>/
  metadata.json
  transcript.json
  transcript.srt
  frames/
  ocr.jsonl
  timeline.jsonl
  chunks.jsonl
  essence.md
  cards.md
  qa.md
  vector_store/ or index.db
```

`essence.md` should include:

1. One-sentence conclusion
2. Course outline
3. Core insights with timestamps
4. Knowledge tree
5. Glossary / terminology
6. Code, commands, tools
7. Pitfalls emphasized by the teacher
8. Action items / homework
9. Review cards
10. Timestamp navigation

## Chunking and synthesis

Avoid one-shot summarization for 1-2 hour videos.

1. Split into 3-8 minute chunks or topic-based chapters.
2. Extract structured fields per chunk: theme, concepts, examples, code, pitfalls, action items, evidence timestamps.
3. Reduce into global essence while preserving citations to original timestamps.
4. Build a local RAG index for later questions across videos.

## Node-computer / multi-machine execution

For large libraries, add worker nodes. Nodes should expand throughput, not decide final conclusions.

Good worker tasks:

- ASR
- audio slicing
- fixed/scene keyframe extraction
- OCR
- embedding
- chunk-level map summaries

Keep centralized:

- global reduce synthesis
- final knowledge-base writes
- quality gates
- cloud API calls / keys / cost control

Recommended control-plane shape:

```text
control plane
  -> discover videos
  -> create idempotent tasks
  -> dispatch to worker nodes
  -> collect artifacts
  -> run quality gates
  -> fuse timeline
  -> reduce final essence
  -> write RAG index
```

Prefer event-driven transitions over cron polling for the main pipeline:

```text
video.discovered
  -> asr.task.created
  -> asr.completed
  -> frames.task.created
  -> ocr.completed
  -> timeline.ready
  -> summary.map.created
  -> summary.reduce.ready
  -> rag.indexed
```

## Implementation patterns from local lecture-video runs

For a CLI/MVP, keep the processing stages explicit and resumable:

```text
scan -> process -> summarize -> reduce -> index -> ask
```

Recommended artifact contracts:

- `manifest.json` points to the source video and generated artifacts.
- `transcript.json` stores timestamped ASR segments.
- `ocr.jsonl` stores one OCR record per sampled frame.
- `timeline.jsonl` fuses ASR + OCR + frame paths and should include a `normalized_text` field after terminology correction.
- `essence.md` is a first-pass local summary.
- `essence-reduced.md` is the higher-density course note generated from timeline chunks.
- `vector_index.jsonl` or an equivalent DB stores embedding rows for semantic ask.

Useful commands/behaviors to build into the tool:

- Use `stdin=subprocess.DEVNULL` when calling interactive-ish ASR tools such as `mlx-whisper` from batch loops. Otherwise the subprocess may consume the shell loop's remaining video paths as stdin and corrupt the batch.
- Capture ASR subprocess stdout/stderr (`capture_output=True`, `text=True`) so verbose model logs do not pollute command-substitution outputs such as manifest paths.
- Normalize course terminology before indexing and asking. Common technical-course ASR errors can be fixed with a small regex table first, then promoted later to a domain glossary/confusion set.
- For Chinese text adjacent to English terms, avoid over-strict `\b` word boundaries in correction rules; terms like `Timescript的` or `OVNGS零知识` need to normalize correctly.
- Build semantic indexes over time windows, not every one-second timeline row. For lecture courses, 120-300 second windows usually reduce thousands of rows to dozens of semantically useful documents.
- When Ollama/local embedding returns transient HTTP 500 on long/noisy OCR text, retry with shorter input slices. Store the full evidence text, but embed a capped prefix with backoff (`4000 -> 2000 -> 1000 -> ...`) rather than failing the whole index.
- OCR cleaning should at minimum remove pure punctuation/icon lines, collapse whitespace, and deduplicate repeated OCR lines while preserving mixed technical tokens such as `o1js TypeScript`.

## Quality gates

Before finalizing, verify:

- transcript covers the expected duration
- no large hallucinated repetitions or unexplained blanks
- ASR confidence/logprob/no-speech fields are not suspicious where available
- keyframes exist at expected density
- OCR is deduplicated and not dominated by menus/watermarks/player UI
- every high-value insight has at least one timestamped evidence source
- `manifest.json`, `timeline.jsonl`, `ocr.jsonl`, `essence.md`, and reduced/semantic artifacts exist for every processed video
- vector index row count, embedding dimensions, covered video count, and semantic smoke-query output are verified against real files
- cloud-model output does not introduce claims unsupported by local evidence

## Cloud model role

Cloud models are enhancement layers, not the primary evidence source:

- Claude: structured synthesis, abstraction, critique, final expression.
- Gemini: direct video understanding or difficult-clip validation when upload/cost/privacy are acceptable.
- OpenAI vision/text: keyframe and transcript synthesis.

Default to extracting local evidence first, then send compact evidence packets to cloud models only when useful.
