# Douyin / short-video inspiration intake evidence workflow

Use this reference when the user shares a Douyin/TikTok/Xiaohongshu-style link as inspiration for Hermes, UI, workflow, product, agent design, memory, or creative tooling. The goal is to extract reusable class-level patterns without cargo-culting a social post.

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
8. Write an intake note with: source facts, OCR, verified external facts, transferable pattern, risks/redlines, and recommended landing zone.
9. Only create a taskpool follow-up when there is concrete engineering work; include evidence refs, acceptance criteria, anti-drift checks, and explicit non-goals.

## Douyin SSR extraction fallback

When a `v.douyin.com` link redirects to `www.iesdouyin.com/share/{video|note}/{id}/`, prefer the SSR metadata path before heavier browser automation:

1. `GET` the short URL with a mobile/Douyin-like user agent and `allow_redirects=false`; record the `Location`.
2. Normalize to `https://www.iesdouyin.com/share/{video|note}/{id}/`.
3. Fetch the share page and parse `window._ROUTER_DATA = {...}</script>` as JSON.
4. Read `loaderData[* /page].videoInfoRes.item_list[0]` for `desc`, `author`, `statistics`, `images`, and `video.play_addr` candidates.
5. For notes, download `images[].url_list[0]` and make a contact sheet for OCR. For videos, download only available play candidates, sample frames with `ffmpeg`, and make a contact sheet.
6. Treat this as evidence capture, not a downloader bypass. If SSR metadata/media is absent or blocked, state the evidence gap and ask for screenshots/transcript rather than inventing content.

## Standard analysis sections

- Source / canonical URL
- Local evidence files
- OCR / visible content
- Verified external sources
- What it really is
- Transferable Hermes pattern
- What not to copy
- Risks and redlines
- Recommended absorption path
- Initial verdict

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
