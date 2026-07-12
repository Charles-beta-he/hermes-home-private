# Douyin Short-Video / Note Analysis Workflow

Use when the user shares a Douyin short link and asks to analyze the value, summarize the video/note, or extract project details from the clip.

## Evidence-first extraction

1. Open/resolve the short URL and record the canonical Douyin page URL or note ID when visible.
2. Use the page text as the first source of truth: title/caption, author, publish time, counts, comments when accessible. On Douyin web video pages, `document.body.innerText` may expose AI-generated chapter summaries, timestamps, author metrics, publish time, duration, login/comment boundaries, and unlabeled engagement counts even when the visual player is muted or partially gated; capture these as preview evidence before attempting media download or transcription.
3. Inspect DOM media rather than relying only on the visual player:
   - `document.body.innerText` for caption/recommendations/context/chapter summaries/access boundaries.
   - `document.images` for high-resolution note images / covers and their alt text.
   - `document.querySelectorAll('video')` for playable mp4/currentSrc and audio tracks.
   - When `window._ROUTER_DATA` is present, parse `loaderData.*.videoInfoRes.item_list[0]` and save a compact `router_item.json` with `aweme_id`, `desc`, `author`, `statistics`, `images`, and playable video URLs under `~/.hermes/docs/private/<topic>-<aweme_id>/` before summarizing.
4. For image-based notes, download the full-resolution `douyinpic`/`byteimg` images with a browser-like `User-Agent` and Douyin `Referer`, then run vision/OCR on the local files. Avoid judging from a dimmed player screenshot if a login modal overlays the content.
   - Douyin note pages often expose each primary image twice (player image + cover/thumbnail). Deduplicate by URL stem and/or natural dimensions before OCR so you do not analyze the same slide twice.
   - If a fixed login / HD overlay blocks the player, inspect DOM first and, when necessary, temporarily hide only the overlay in the browser context; do not rely on overlay-obscured screenshots.
   - For video posts where a playable MP4 is accessible, download it as evidence, run `ffprobe` for duration, create low-rate contact sheets with `ffmpeg` (for example 1 frame / 2-10 seconds depending on length), and OCR/analyze the contact sheet before judging workflow details, costs, UI steps, or repo names shown only in frames. When using `tile` for a single contact-sheet image, include `-frames:v 1` or an image sequence pattern so ffmpeg does not try to write multiple sheets to the same filename on longer clips.
   - For long playable Douyin web videos where direct media download is expensive/fragile, use the page player as a timestamped evidence surface: set `document.querySelector('video').currentTime = <seconds>`, pause, hide only obstructive login/download overlays when needed, then run screenshot/vision on the visible frame. Record this as timestamped frame evidence, not a full-video transcript. Use this path for system-interaction/UI demos where the user points to a timestamp such as `2:05`.
5. If the media shows an external artifact (GitHub repo, paper, product page, official-doc logo/claim), verify the artifact directly from the source:
   - For GitHub, fetch repo metadata and raw `README.md` / `SKILL.md` / `LICENSE` when visible. For social videos about a CLI/tool/repo, also read the README sections that correspond to visible slide claims (install command, supported agents, skill/command list, local-vs-cloud boundary, license/status) and explicitly compare the social claim to upstream facts instead of stopping at stars/license metadata.
   - For Hermes Agent configuration/tutorial clips, load `hermes-agent` for local workflow boundaries, but treat the official docs at `https://hermes-agent.nousresearch.com/docs` as authoritative before recommending commands. Social videos may show stale or simplified keys (for example `vision.*`); compare against the current docs/config shape (for example `auxiliary.vision.*` for auxiliary vision routing) and label any mismatch as a docs-vs-video delta rather than copying commands blindly.
   - For official-product claims (e.g. "Anthropic/Claude new feature"), look for the official docs/release note; if not found, label the content as social/AI-generated interpretation rather than an official announcement.
   - Separate what the Douyin video claims from what the external artifact actually contains.
   - Before creating a task from the video, search/read existing taskpool or project records for the same artifact. If the repo/tool was already evaluated, do **not** create another generic repo-reading task; create a bounded follow-up around the net-new signal (market demand, provider-selection gate, safety boundary, prototype decision, etc.) and link the prior tasks as evidence.
6. For multi-link comparative requests, create one evidence directory per source (`~/.hermes/docs/private/<platform-topic-aweme_id>/`) with a compact `media-index.json`, then create one synthesis directory/report that cites the per-source evidence. Keep each source's access boundary separate: note/image slides, video DOM chapter extraction, timestamped frame evidence, or inaccessible/gated media are not equivalent evidence classes.
   - If a Douyin page later returns `444`, timeout, or transient “video does not exist” after a successful DOM extraction, do not hard-code a general tool failure. Preserve the successful DOM/chapter/page-text evidence, label the later fetch as transient/gated, and avoid claiming full video transcription or media download.
   - For long videos with AI-generated chapter summaries exposed in page text, the chapter list is acceptable intake evidence for workflow analysis, but not proof that every shown step succeeded in production. Say "DOM chapter/caption evidence" rather than "watched full video" unless you actually downloaded or timestamp-sampled it.
- For AI-agent trend slides, distinguish vocabulary from infrastructure: e.g. Vibe Coding (interaction style), Harness (execution/eval scaffold), Dynamic Workflow (task router), Agent Eval (system-level regression/quality gate), and “digital life/consciousness” (social/product metaphor unless independently verified).
- For automation/tool workflows with paid APIs or write-capable apps (VLM/TTS/video editors, MCP, ComfyUI/Blender/DaVinci, printer/device bridges), make cost/side-effect gates first-class: estimate billable calls/compute/time, default to dry-run or blueprint-only, and do not install, register MCP servers, write timelines, upload media, generate private assets, or start physical actions during intake.
- For 3D/image-to-model/manufacturing clips, treat generated meshes/3DGS/PLY/GLB as `draft_only` or `studio_preview` evidence until provenance/license, scale, visual-fidelity, mesh QA, slicer preview, human approval, and external-control gates pass; never equate a social demo with print readiness.

## Hermes/Ollama local-vision clips

When a Douyin/TikTok-style clip claims that Hermes can gain local vision through a few commands:

1. Treat the clip as an intake signal, not executable truth. Verify the current Hermes documentation first; for auxiliary vision the durable config surface may be `auxiliary.vision.*` (`base_url`, `model`, `api_key`, `provider`) rather than social-video shorthand like `vision.provider`.
2. Keep the landing reversible: create or use an isolated Hermes profile for local/private vision instead of changing the default profile. Record a short profile-local README with model, endpoint, smoke-test command, and rollback commands.
3. Verify the Ollama model in three layers before declaring success:
   - `ollama list` / `/v1/models` shows the model;
   - direct OpenAI-compatible `/v1/chat/completions` vision request succeeds with a data-URL image;
   - Hermes `vision_analyze` succeeds through the isolated profile.
4. Do not equate "model pulled" with "model usable". Some Ollama vision model packages can pull and show capabilities but fail at load time due runtime architecture support (for example, MiniCPM-V 4.6 packages using `qwen35`). Capture the load error as a compatibility boundary, then choose a verified local VLM fallback rather than hard-coding the failed model.
5. Output should separate: social-video claim, current official Hermes config surface, local endpoint verification, profile isolation/rollback, and quality boundary versus cloud vision models.

## Common pitfalls

- Douyin pages often show login/high-definition overlays; do not stop at the overlay screenshot. Extract DOM media URLs and high-resolution note images when possible.
- Do not treat social-video framing as technical validation. Verify linked/open-source artifacts directly.
- Short-video recommendation text can pollute `innerText`; distinguish the main note/caption from related-video listings.
- If the clip is a note with multiple images, page indicators like `1/2` or `2/2` imply multiple image assets; analyze all accessible primary images.

## Output shape

- Start with a concise verdict.
- Then list evidence observed: source page metadata, linked artifact, repo/readme/license/stars if verified.
- Separate **real value**, **limitations**, and **recommended absorption/integration**.
- Call out if the artifact is a prompt/workflow skill rather than a model, library, or technical breakthrough.

## Post-analysis absorption / taskpool landing

When the user accepts the analysis or says to “添加任务池 / 入池 / 吸收”:

1. Convert conclusions into **bounded engineering cards**, not one vague “absorb this video” task.
   - Each card should name the reusable class/pattern to implement (e.g. workflow replay control plane, delivery harness, retrieval harness), not the social-video title alone.
   - Include the local evidence path(s), canonical URL, and the analysis report path in the card body.
   - Add explicit hard gates and anti-claims: no unverified consciousness/AGI/product claims, no credentialed deployment, no third-party code copy, no external side effects unless the user explicitly authorizes them.
2. Use stable idempotency keys derived from the canonical artifact/video id so repeated sessions do not create duplicate generic cards.
3. Prefer priority by implementation leverage:
   - P0/P1 for control-plane primitives that make future workflows observable/replayable/governable.
   - P1/P2 for reusable delivery harnesses or retrieval/evaluation contracts.
   - Lower priority for speculative concepts unless converted into safe engineering gates.
4. After creating cards, read back task IDs, status, and priority before reporting success.

For playable Douyin videos, if a direct `video.currentSrc` MP4 is exposed, save it as local evidence, run `ffprobe`, create a low-rate contact sheet with `ffmpeg`, and analyze the sheet. If direct download is blocked, fall back to timestamped browser-frame evidence and label the boundary clearly.
