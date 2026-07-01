# Multi-Douyin Agent/Workflow Synthesis Pattern

Use when the user shares several Douyin/TikTok-style links in one request and asks what the videos describe, how to absorb them, or which ideas matter.

## Procedure

1. **Resolve each short link independently**
   - Record short URL, canonical URL, aweme/note ID, author, title/caption, publish time, type (`note` vs `video`), duration if available, engagement counts, and access boundary.
   - Do not let one successful link stand in for the others.

2. **Create per-source evidence directories**
   - Suggested shape: `~/.hermes/docs/private/douyin-<topic>-<id>/media-index.json`.
   - For notes: download all primary high-resolution `douyinpic`/`byteimg` images, deduplicate duplicate player/cover URLs, create a contact sheet for OCR inventory, then inspect important slides individually.
   - For videos: first preserve DOM caption/chapter text; if playable media or stable timestamp frames are accessible, add those as stronger evidence. If not, label the analysis as DOM/chapter based.

3. **Separate evidence classes in the synthesis**
   - Image note OCR, video DOM chapter summaries, timestamped frames, and full media transcripts are different proof levels.
   - If a later fetch times out/returns 444/“video does not exist” after earlier DOM extraction, preserve the earlier evidence and mark the later failure as transient/gated. Do not generalize it into “Douyin tools do not work.”

4. **Normalize social claims into engineering primitives**
   - Convert “digital life/consciousness” into testable primitives such as durable memory, state graph, self-modification gate, event ledger, harness, or run lineage.
   - Convert “from 0 to 1 tutorial” into a delivery harness with artifacts and acceptance gates.
   - Convert “studio/workflow UI” into control-plane concepts: execution records, node conversations, replay policies, event streams, interrupt tokens, evidence bundles.

5. **Rank absorption by implementation leverage**
   - Prefer directly actionable UI/control-plane mechanics over high-concept metaphors.
   - For external platforms (WeChat, CloudBase, app stores, payment, physical actions), stop at blueprint/harness unless the user grants credentials and explicit deployment authority.

## Output checklist

- Concise verdict across all sources.
- Per-source evidence observed and local paths.
- What the source claims vs what the evidence proves.
- Real value, limitations, and recommended absorption.
- Cross-source synthesis and priority ranking.
- Explicit rejection list for unverified claims and unsafe side effects.

## Anti-conditions

- Do not create one narrow skill per video or per creator.
- Do not store session-specific URLs in global memory; keep them in the report or an explicitly scoped reference.
- Do not turn social-video claims into product/technical proof without independent artifact verification.
