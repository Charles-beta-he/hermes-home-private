# Short-video architecture-diagram extraction

Scope: public short-video or image-note pages whose reusable value is an architecture diagram, roadmap, or box-and-arrow system sketch. Applicability: use when the user asks to inspect the architecture inside a social-media clip/note. Anti-condition: do not use this for ordinary video summaries, private/gated media, or adopting a named artifact without authoritative source verification.

## Procedure

1. Resolve the short link and record final URL, author/source, publish time, visible caption, page type, slide count, and access boundary.
2. Inspect DOM images/video elements. For image notes, deduplicate primary images by URL stem or natural dimensions.
3. Download all primary slides into a scoped evidence directory and save an index with source URL, local path, byte size, and short hash.
4. Build a contact sheet for inventory, then inspect individual slides for OCR when module labels are small.
5. If the slide names a concrete external artifact, verify that artifact from an authoritative source before treating it as real. If not verified, label it as a social architecture sketch.
6. Write the analysis as: evidence paths, slide-by-slide OCR, reconstructed layers, data/control flow, reusable primitives, rejected cargo-cult elements, and verification boundaries.

## Analysis lens

- Event spine: typed events, streaming, UI projection, lifecycle hooks.
- Controller actions: send/cancel/approve/compact/rewind/resume.
- Task contract: task kinds as execution policies, not labels.
- Planner/executor boundary: read-only planning, write-capable execution, read-only review.
- Safety pipeline: validate, permission/risk check, execute, output cap, evidence.
- Evidence and rollback: evidence ledger, checkpoints, turn snapshots, closeout gates.
- Long-term capability: skills, memory, compression, cache/budget diagnostics.
- UI control surface: stream controller, tool-call card, approval, cache, checkpoint, evidence panels.

## Pitfalls

- A note can expose an audio element even when the content is images; do not treat audio duration as video evidence.
- Contact sheets are for inventory; inspect individual slides for small-text OCR.
- Social claims about a named framework are leads, not proof. Verify or label unverified.
- Preserve the extraction/mapping pattern; do not save the one-off social link as a global rule.
