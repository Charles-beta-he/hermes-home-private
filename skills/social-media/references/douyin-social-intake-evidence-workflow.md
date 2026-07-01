# Douyin / short-video inspiration intake evidence workflow

Use this reference when the user shares a Douyin/TikTok/Xiaohongshu/WeChat Channels (视频号)-style link for analysis, inspiration, Hermes, UI, workflow, product, agent design, memory, or creative tooling. Scope calibration is mandatory: if the user asks generally to “分析” or “添加任务池”, analyze the content itself first (what it says, facts vs opinions, product/business/technical/user implications, opportunities, risks). Hermes/taskpool/workflow absorption is only one labeled subsection unless the user explicitly asks for that as the sole scope. The goal is to extract reusable class-level patterns without cargo-culting a social post.

## Landing-zone classifier

Before writing durable artifacts, split the source into:

- **Reusable procedure / pitfall / verification checklist** → patch a class-level skill or add a scoped reference.
- **Project-specific fact/path/URL/branch** → project profile or scoped evidence reference, not global skill text.
- **Concrete engineering follow-up** → taskpool candidate/proposal, not a fake skill.
- **Session progress / one-off narrative** → no durable write.
- **Stable user preference** → memory/user profile plus the governing skill if it changes how that class of task should run.

## Evidence-first extraction pattern

1. Resolve the short link to a canonical URL and record both.
2. Extract metadata if available: author, title/description, publish time, stats, canonical item id.
3. Save a request-specific evidence directory under a private evidence area.
4. Preserve raw evidence where lawful and available: metadata JSON, images/video, sampled frames/contact sheets.
5. OCR or visually inspect media; separate visible text from inference.
6. If the post references a repo/tool/site, verify the canonical source directly before judging value.
7. If the post makes a regulatory/compliance/policy claim, verify against official government/platform documentation before answering; separate “policy helps with friction” from “policy grants an exemption/license.”
8. Write an intake note with: source facts, OCR, transcript summary when available, verified external facts, transferable pattern, risks/redlines, and recommended landing zone.
9. Only create a taskpool follow-up when there is concrete engineering work; include evidence refs, acceptance criteria, anti-drift checks, explicit non-goals, and enough priority/dependency/triage metadata for the taskpool CLI to accept it without a second repair pass.
10. For `brain_task_orchestrator.py add`, include the current required triage trio up front: `--priority-layer`, `--dependency-order`, and `--multimodel-triage-result`. Social inspiration/advisory tasks commonly use `priority_layer=P2`, dependency order that places evidence/IA before any implementation or write-action work, and a multimodel triage note such as “single-source inspiration intake; no multimodel required until prototype design review or implementation promotion.” If the CLI fail-closes with missing priority/dependency/triage metadata, retry with those fields instead of hand-writing task Markdown.

## WeChat Channels / 视频号 link intake

When the user provides a `https://weixin.qq.com/sph/<id>` short link, resolve it first with a normal/mobile browser user agent and record the canonical preview URL. The observed stable shape is:

`https://channels.weixin.qq.com/finder-preview/pages/sph?id=<id>`

Treat HTTP 200 and page title “视频号” as link-resolution evidence only, not content evidence. The preview shell often exposes little or no post content without platform context, so do not infer video claims from the URL alone. If metadata/OCR/transcript is unavailable, create the intake/task with an explicit evidence gap and ask for screenshots, transcript, or user-provided summary rather than logging into WeChat or bypassing controls.

## Douyin SSR extraction fallback

When a `v.douyin.com` link redirects to `www.iesdouyin.com/share/{video|note}/{id}/`, prefer the SSR metadata path before heavier browser automation:

1. `GET` the short URL with a mobile/Douyin-like user agent and `allow_redirects=false`; record the `Location`.
2. Normalize to `https://www.iesdouyin.com/share/{video|note}/{id}/`.
3. Fetch the share page and parse `window._ROUTER_DATA = {...}</script>` as JSON.
4. Read `loaderData[* /page].videoInfoRes.item_list[0]` for `desc`, `author`, `statistics`, `images`, and `video.play_addr` candidates.
5. For notes, download `images[].url_list[0]` and make a contact sheet for OCR. For videos, download only available play candidates, run `ffprobe`, sample frames with `ffmpeg`, and make a contact sheet.
6. If local ASR is available (for example `faster_whisper`), transcribe the saved video and store both JSON and timestamped text beside the media evidence. Mark ASR text as imperfect evidence and normalize obvious recognition errors only in the intake note, not in the raw transcript.
7. Treat this as evidence capture, not a downloader bypass. If SSR metadata/media is absent or blocked, state the evidence gap and ask for screenshots/transcript rather than inventing content.

## Scope calibration pitfall

Do not narrow generic social-link analysis to “what Hermes can absorb.” For this user, a generic “分析/添加任务池” request should create/execute a content-analysis task whose primary sections cover the post itself: source facts, visible content, core claims, fact/opinion split, product/business/technical/user scenarios, opportunities, risks, and credibility. Add “Hermes/taskpool/agent 可吸收点” as a derived subsection only after the content analysis, unless the user explicitly requests Hermes absorption as the whole task.

Taskpool naming and acceptance criteria must reflect that broad scope. Avoid titles like “评估其对 Hermes taskpool / agent 工作流的可吸收价值” for a generic social-link request; use “内容综合复盘 / 机会风险评估 / 可吸收点” language, and make the Hermes/workflow section explicitly derived rather than the main objective.

## Standard analysis sections

- Source / canonical URL
- Local evidence files
- OCR / visible content / transcript or explicit evidence gap
- What the post says: core claims and examples
- Fact vs opinion / marketing-expression split
- Product, business, technical, user-scenario analysis
- Opportunities, risks, and redlines
- Verified external sources
- What it really is
- Transferable Hermes pattern (derived subsection, not the whole analysis)
- What not to copy
- Recommended absorption path
- Initial verdict

## Agent architecture post addendum

For posts about AI-agent memory systems, multi-agent collaboration, workspaces, OpenClaw/OpenAgents-style projects, or “爆火” AI tooling:

1. Capture media evidence first: notes/images directly, videos via sampled frames/contact sheet when SSR exposes playable media.
2. Verify the named or visually implied repo/package independently. Save repo metadata and README/package excerpts, not just the social post.
3. Compare visible social-slide claims such as stars/forks/version against current GitHub/NPM/API facts. If they mismatch, mark the slide metric as unverified instead of treating it as product evidence.
4. Read governance/source docs (`README`, `AGENTS`, `INVARIANTS`, launch plans, package manifests) before extracting patterns; landing-page slogans are usually too shallow.
5. Extract class-level architecture only: memory graph/scoped recall/workroom/evidence/control-plane patterns. Keep source URLs and repo facts in the scoped evidence note.
6. See `references/douyin-agent-architecture-intake-cases.md` for two reusable case lenses: graph-memory systems and agent collaboration/workroom systems.

## Redline defaults

- Social popularity is routing/context, never engineering proof.
- Do not install, run, log in, clone deeply, register MCP servers, write hooks/config, spend paid tokens, flash hardware, trade, or publish content during intake unless the user explicitly approved that side effect.
- Do not bulk-import external agents/skills/tools into the active Hermes skill graph.
- Do not promote a local social-video method into a global mandatory rule without repeated evidence.
- Do not store secrets, tokens, connection strings, private credentials, or personal data from screenshots; redact as `[REDACTED]`.
- Keep source-specific claims scoped to the evidence note unless they generalize across multiple validated sources.

## Useful output framing

For the final user-facing answer, prefer:

```text
结论：值得/不值得/只值得部分吸收。
证据：canonical source + local evidence + verified repo/site facts.
可吸收：class-level pattern.
不可照搬：side effects / unverified claims / platform assumptions.
已落地：evidence path and optional taskpool id.
下一步：implementation-ready task or explicit no-action.
```

## Anti-conditions

Do not use this workflow for ordinary social-media posting, analytics, or distribution tasks; use the platform-specific/social distribution references instead. Do not use it as a downloader bypass workflow; if retrieval is blocked, ask for screenshots/transcript or mark the evidence gap.
