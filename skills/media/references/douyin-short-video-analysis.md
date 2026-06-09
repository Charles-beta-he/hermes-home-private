# Douyin Short-Video / Note Analysis Workflow

Use when the user shares a Douyin short link and asks to analyze the value, summarize the video/note, or extract project details from the clip.

## Evidence-first extraction

1. Open/resolve the short URL and record the canonical Douyin page URL or note ID when visible.
2. Use the page text as the first source of truth: title/caption, author, publish time, counts, comments when accessible.
3. Inspect DOM media rather than relying only on the visual player:
   - `document.body.innerText` for caption/recommendations/context.
   - `document.images` for high-resolution note images / covers and their alt text.
   - `document.querySelectorAll('video')` for playable mp4/currentSrc and audio tracks.
4. For image-based notes, download the full-resolution `douyinpic`/`byteimg` images with a browser-like `User-Agent` and Douyin `Referer`, then run vision/OCR on the local files. Avoid judging from a dimmed player screenshot if a login modal overlays the content.
   - Douyin note pages often expose each primary image twice (player image + cover/thumbnail). Deduplicate by URL stem and/or natural dimensions before OCR so you do not analyze the same slide twice.
   - If a fixed login / HD overlay blocks the player, inspect DOM first and, when necessary, temporarily hide only the overlay in the browser context; do not rely on overlay-obscured screenshots.
5. If the media shows an external artifact (GitHub repo, paper, product page, official-doc logo/claim), verify the artifact directly from the source:
   - For GitHub, fetch repo metadata and raw `README.md` / `SKILL.md` / `LICENSE` when visible.
   - For official-product claims (e.g. "Anthropic/Claude new feature"), look for the official docs/release note; if not found, label the content as social/AI-generated interpretation rather than an official announcement.
   - Separate what the Douyin video claims from what the external artifact actually contains.
6. Analyze value at the right abstraction level: practical workflow value, novelty, limitations, adoption signals, and how/if to integrate it into the user's existing workflows. For AI-agent trend slides, distinguish vocabulary from infrastructure: e.g. Vibe Coding (interaction style), Harness (execution/eval scaffold), Dynamic Workflow (task router), and Agent Eval (system-level regression/quality gate).

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
