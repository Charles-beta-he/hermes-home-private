# Desktop Batch Closure Pattern for Long-Video Essence

Use this reference when the user asks to process a whole local desktop/folder of long course videos “until human intervention is needed”.

## Closure shape

A complete batch is more than per-video summaries. Close the loop with:

1. ASR/OCR/timeline artifacts for each unique source video.
2. `essence.md` and `essence-reduced.md` per video.
3. Cross-video `vector_index.jsonl`.
4. A real semantic ask output file using the chosen Ollama host.
5. `course-final.md` for each course/output group.
6. A top-level human-readable entrance index listing output folders, key files, processed counts, duplicates, and quality caveats.
7. Full artifact audit: count manifests, check every manifest directory for transcript/OCR/timeline/essence/reduced, and report missing count.

## Duplicate handling

When scanning broad desktop trees, do not process duplicate MP4s just because paths differ. Compute content hashes for suspicious duplicates and map them to the already-processed canonical video.

Report duplicates explicitly with SHA256 evidence so “unprocessed by path” is not mistaken for missed work.

Example closure wording:

```text
Scanned 16 mp4 files; 14 unique manifest outputs; 2 paths are exact SHA256 duplicates of an already-processed video.
```

## Slow indexing fallback

Very long timeline rows plus OCR noise can make node embedding index runs look hung, especially if window text reaches hundreds of thousands of characters before truncation. The durable fix is not to abandon semantic indexing; rerun with tighter embedding input limits and a larger time window when appropriate:

```python
build_index(output_root, window_seconds=600, max_embed_chars=1200, min_embed_chars=128, ollama_host="http://NODE:11434")
```

Then verify:

- `vector_index.jsonl` exists
- row count is non-zero
- embeddings have a consistent dimension
- a semantic ask returns timestamped evidence

## Human intervention boundary

Stop at a human boundary only after the evidence pipeline is complete. For noisy recordings, the boundary is usually a quality/product decision, not a technical failure:

- use current notes for review
- invest in OCR/ASR noise governance
- add domain-specific term normalization
- perform evidence-grounded LLM cleanup
- build a timestamp/video-jump UI

Make this distinction explicit in the final report.