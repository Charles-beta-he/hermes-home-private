# Douyin social-link intake pattern

Use when a user shares a Douyin short-link / copy-paste share text and asks to analyze, add to taskpool, or add to the database.

## Why this exists

Douyin preview pages often expose richer structured text in page metadata and `document.body.innerText` than the initial accessibility snapshot. The share text is a lead, not a canonical source. For Hermes/taskpool intake, preserve the social evidence, map claims to canonical repos/docs when possible, and add a rich task instead of a vague “analyze this video”.

## Procedure

1. Resolve the short link.
   - Open `https://v.douyin.com/.../` and record the final `https://www.douyin.com/note/...` or video URL.
   - Extract page title, author, publish time, visible metrics, hashtags, and full visible description.
   - Prefer DOM extraction (`document.body.innerText` plus meta `description`/`keywords`) after navigation; snapshots may omit the long post text.
   - For Douyin `share/note/<id>` image posts, parse the embedded `window._ROUTER_DATA` JSON when present. It often contains `videoInfoRes.item_list[0]` with `desc`, `author`, `statistics`, `create_time`, canonical note id, and `images[].url_list`. Save a compact router/item JSON evidence file, download the carousel images under a durable private evidence directory, and OCR each image before summarizing the post.
   - For Douyin `share/video/<id>` posts, the same `_ROUTER_DATA` path usually exposes `video.play_addr.url_list` / `play_addr_h264` / bitrate play URLs. Save a compact router/item JSON evidence file, download the accessible MP4 under the evidence directory, extract a low-rate contact sheet with `ffmpeg`, then OCR the contact sheet for repo names, cost/pricing screenshots, workflow steps, and caveats before summarizing. Do not claim video content from caption-only metadata when frames were not inspected.
   - If there is no linked canonical repo and the post is an educational diagram/tutorial, frame it as a social-source design scaffold or workflow-pattern lead, not as a concrete upstream project.

2. Treat the social post as a lead.
   - Keep author/date/metrics as social evidence only.
   - Do not treat “production-grade”, star counts, benchmark percentages, or capability claims as verified facts until mapped to canonical artifacts.

3. Map named projects or technical phrases to canonical artifacts.
   - Search GitHub/web for exact project names and distinctive phrases from the post, including repo names visible only in OCR screenshots.
   - Record owner/repo, description, stars/forks, default branch, language, license, topics, update time, top-level structure, README/architecture/package signals.
   - If the mapping is plausible but not proven (for example the post names “LLM Wiki” but no repo link), label it as related/canonical-artifact mapping, not authorship proof.
   - If the mapped artifact is embedded/robotics/hardware/physical-control, classify it as a control-system reference rather than an AI-agent repo; keep intake design-only unless separately authorized. See `references/douyin-hardware-repo-intake-dcar.md` for the Dcar_OpenSource pattern.

4. Write an evidence note under `~/.hermes/docs/private/` before adding the task.
   - Include: original user share text, resolved URL, extracted visible post text, canonical mapping evidence, Hermes interpretation, anti-drift/red lines, and recommended task metadata.
   - For RAG/vector/database posts, explicitly apply the vector boundary: retrieval is candidate context, never taskpool SSOT, lifecycle authority, proof gate, or deterministic replay source.

5. Add a rich taskpool task.
   - Use `lane=evolution`, usually `priority=P2`, `project=hermes-agent`.
   - Choose `architecture_target` from the material: `local-brain` for RAG/memory/retrieval/workflow runtime; `skill-graph` for skill ecosystems; taskpool/control-plane if it changes execution governance.
   - Include `capability_delta`, `anti_drift_check`, `acceptance_evidence`, `objective`, `accept`, `red_line`, `non_goal`, `concepts`, `parallel_boundary`, `priority_layer`, `dependency_order`, `multimodel_triage_result`, and `evidence_ref`.

6. Verify creation.
   - Read back the created task frontmatter and confirm `evidence_refs`, lane, priority, project, `architecture_target`, and `parallel_boundary`.
   - Verify the evidence note references the original short URL, resolved/canonical URL, extracted metadata, downloaded image paths when available, OCR summary, and any canonical repo/docs mapping status.
   - For image-note/carousel posts, verify the evidence directory contains the compact router/item JSON plus all downloaded image files used for OCR; do not rely only on meta description or the first preview image.
   - Refresh dashboard/control-center.
   - If smart-route moves the task to `running`, report that as expected advisory processing, not manual execution.

## Good task framing examples

- `Douyin线索 claude-workflow-studio：图形化多Agent工作流控制面吸收评估`
  - Social lead → canonical GitHub repo → Hermes Workflow/Agent Builder gap mapping.
  - Red lines: no install/run, no Claude Code CLI call, no PTY/file-manager high-risk surface, no UI write to canonical taskpool/Mission ledger.

- `Douyin mHe 生产级RAG：Hermes本地证据检索与数据库治理评估`
  - Social RAG principles → related LLM Wiki artifact → Hermes local-brain retrieval/database benchmark task.
  - Red lines: no vector DB/Tauri/MCP daemon install, no private data upload/indexing, vector retrieval candidate-only.

- `Douyin Agent设计结构吸收：转化为 Hermes Agent Builder Workflow Pack 脚手架模板`
  - Social image-note/tutorial → OCR carousel → extract durable module scaffold (`planner`, `memory`, `tools`, `knowledge`, `agent_core`, `evaluation`, `observability`, `deployment`, `examples`, `docs`) → map to Hermes Agent Builder / Workflow Pack / Agent Card surfaces.
  - Red lines: do not treat the social tutorial as a production framework or canonical repo; do not replace taskpool/Mission/Workflow Kernel with a toy ReAct loop; do not connect toy terminal/code/search/weather tools to real systems; RAG/vector remains candidate context, never SSOT/proof authority.

## Pitfalls

- Do not create one task per social link with only the post title.
- Do not conflate social virality with engineering evidence.
- Do not overclaim that a searched GitHub repo is the exact project used by the author unless the post links it or the repo/author clearly match.
- Do not install external apps, skills, vector databases, browser extensions, MCP servers, or CLI connectors during intake unless the user separately authorizes that side effect.
- Do not use mock-only screenshots or generated summaries as evidence; preserve extracted DOM/meta text and canonical source facts.
