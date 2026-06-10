# Multi-social-platform distribution OSS verification (2026-06-10)

## User question

“验证分发多社交平台，应该有开源项目支持”

Context: Solo Pipeline should generate evidence-backed social content / publishing packages and distribute them to platforms such as 小红书, 抖音, 视频号, B站, YouTube, TikTok, LinkedIn, X, etc., while keeping account login and public posting under explicit user control.

## Search / verification method

- Loaded Hermes `social-media` skill umbrella.
- Queried GitHub via `gh search repos` for multi-platform publishing, social scheduler, crosspost, Chinese video matrix, Postiz.
- Cloned selected repos under `/Users/charles/.hermes/runs/social-distribution-oss-verify-2026-06-10/` for local README/source inspection.
- Inspected platform-specific files, CLI/MCP docs, and publish code paths where available.

## Verified candidate projects

### 1. gitcoffee-os/postbot

- URL: https://github.com/gitcoffee-os/postbot
- Stars at verification: 1084
- Forks: 144
- Language: TypeScript
- License from GitHub search: Apache-2.0
- Updated: 2026-06-10 search result / pushed 2026-05-05 via `gh repo view`
- Claim: open-source multi-platform content sync/distribution tool, supporting articles/notes/moments/images/video/audio to WeChat/Weibo/Toutiao/Xiaohongshu/Zhihu/Baijiahao/QQ OM/Shipinhao/Douyin/Kuaishou/Bilibili, extensible to X/Facebook/Instagram/TikTok/YouTube/LinkedIn.
- Local source evidence:
  - `src/media/publisher/platform/video/xiaohongshu.publisher.ts`
  - `src/media/publisher/platform/video/douyin.publisher.ts`
  - `src/media/publisher/platform/video/weixinChannels.publisher.ts`
  - `src/media/publisher/platform/video/bilibili.publisher.ts`
  - `src/media/publisher/platform/video/kuaishou.publisher.ts`
  - also article/moment/audio platform folders.
- Xiaohongshu evidence:
  - `xiaohongshu.publisher.ts` uploads a video through `input[type="file"]`, fills title/content, optionally fills cover, and only clicks Publish when `contentData.isAutoPublish` is true.
- Fit:
  - Best source for browser-extension/content-script style platform adapters.
  - Good reference for field selectors and payload schema for Chinese platforms.
- Caveat:
  - Selector fragility; platform UI changes may break.
  - Extension/content-script architecture may not map directly to Hermes without an adapter.
  - Public posting must retain human approval gate.

### 2. hanliang97/MatrixMedia

- URL: https://github.com/hanliang97/MatrixMedia
- Stars at verification: 82
- Forks: 13
- Language: JavaScript
- License from GitHub search: GPL-2.0
- Claim: Electron + CLI tool for batch video distribution. README says CLI publish is fully automated for 7 platforms: 抖音、快手、百家号、哔哩哔哩、头条、视频号、小红书.
- Local source evidence:
  - `CLI_SKILLS.md` documents `cli login`, `cli publish`, `cli accounts`, `cli history`.
  - `.cursor/skills/matrixmedia-cli-publish/SKILL.md` is an AI-agent-callable skill.
  - `mcp/src/tools/publish.ts` exposes MCP tool `publish_video`.
  - Upload adapters exist under `src/main/services/upLoad/`: `dy.js`, `xhs.js`, `sph.js`, `blbl.js`, `ks.js`, etc.
- CLI coverage from docs:
  - `cli login`: Douyin only.
  - `cli publish`: `dy | tt | ks | blbl | bjh | sph | xhs`.
  - `cli accounts`: all platforms.
  - `cli history`: all platforms.
  - Non-Douyin login must be done once in GUI; CLI reuses the GUI session partition.
- MCP evidence:
  - `mcp/src/tools/publish.ts` has tool `publish_video`, required args `platform`, `file`, `title`, `phone`, optional `tags`, `publishAt`, `show`.
  - Current MCP enum in `publish.ts` lists `dy, ks, blbl, bjh, tt, sph`; xhs is documented elsewhere but not in this specific enum, so verify/fix before relying on MCP for 小红书.
- Fit:
  - Best fit for Hermes/Solo Pipeline because it has explicit CLI/MCP/JSON-output conventions.
  - Can be wrapped by Hermes as an external command after user logs into GUI.
- Caveat:
  - GPL-2.0 if embedding code; prefer external command boundary rather than copying code.
  - Requires Electron app/session management.
  - Non-Douyin login not CLI; needs human login.

### 3. kebenxiaoming/matrix

- URL: https://github.com/kebenxiaoming/matrix
- Stars at verification: 905
- Forks: 196
- Language: Python
- License from search: Apache-2.0
- Claim: Playwright-based script system for video distribution to 抖音、快手、视频号、小红书.
- Local evidence:
  - `publish_video_queue.py`
  - `user_queue_login.py`
  - `douyin_uploader/main.py`, `xhs_uploader/main.py`, `tencent_uploader/main.py`, `kuaishou/main.py`
  - `xhs-api/app2024.py` for XHS `x-s`/`x-t` handling according to README.
- Fit:
  - Good Python reference for queue-based multi-platform video publishing and login/cookie handling.
- Caveat:
  - Requires MySQL + Redis + supervisor per README.
  - More operationally heavy than needed for the first Hermes prototype.
  - Mentions XHS signing internals; treat carefully and avoid anti-platform-abuse behavior.

### 4. gitroomhq/postiz-app

- URL: https://github.com/gitroomhq/postiz-app
- Stars at verification: 31668
- Forks: 5854
- Language: TypeScript
- License from GitHub search: AGPL-3.0
- Claim: agentic social media scheduling tool; supports international platforms including Instagram, YouTube, LinkedIn, Reddit, TikTok, Facebook, Pinterest, Threads, X, Slack, Discord, Mastodon, Bluesky.
- Local evidence:
  - Integration providers under `libraries/nestjs-libraries/src/integrations/social/` include e.g. `linkedin.provider.ts`, `youtube.provider.ts`, `facebook.provider.ts`, `tiktok.provider.ts`, `mastodon.provider.ts`, etc.
  - README points to Public API, Node SDK, N8N custom node, and Postiz agent CLI.
- Fit:
  - Best international scheduler/API-backed option.
  - Good if later publishing to X/LinkedIn/YouTube/TikTok/Reddit rather than Chinese platforms.
- Caveat:
  - AGPL; avoid copying code into proprietary local product unless license obligations are acceptable.
  - Full self-hosting is heavier than first prototype.

### 5. gitroomhq/postiz-agent

- URL: https://github.com/gitroomhq/postiz-agent
- Stars at verification: 281
- Forks: 49
- Language: TypeScript
- Claim: Postiz Agents CLI, connect Claude/OpenClaw/etc to schedule posts across 28+ platforms.
- Local evidence:
  - README states command `postiz posts:create`, `integrations:list`, `auth:login`, API key option.
  - Supports multi-platform post with `-i "twitter-id,linkedin-id,facebook-id"`.
  - Supports media and JSON complex post flows.
- Fit:
  - Best CLI boundary for international platforms if Postiz is used.
- Caveat:
  - Needs Postiz account/self-host and connected integrations.
  - Chinese platforms are not the focus.

### 6. Anil-matcha/Free-AI-Social-Media-Scheduler

- URL: https://github.com/Anil-matcha/Free-AI-Social-Media-Scheduler
- Stars at verification: 2092
- Forks: 229
- Language: JavaScript
- License from README badge/search: MIT
- Claim: self-hosted AI scheduler, currently YouTube and TikTok live; Instagram/Facebook/X/LinkedIn/Threads/Pinterest coming soon.
- Fit:
  - Lightweight reference for scheduling UI and self-hosted app.
- Caveat:
  - Only YouTube/TikTok live per README; uses MuAPI; not a broad cross-platform base today.

## Recommended architecture for Hermes/Solo Pipeline

Use a two-lane distribution architecture:

1. **Chinese platform lane** — primary target: 小红书/抖音/视频号/B站/快手.
   - Preferred first adapter: MatrixMedia external CLI/MCP boundary.
   - Reference adapter code: PostBot platform publishers.
   - Heavy queue reference: kebenxiaoming/matrix.

2. **International platform lane** — X/LinkedIn/YouTube/TikTok/Reddit/Mastodon/etc.
   - Preferred first adapter: Postiz Agent CLI or Postiz API.
   - Full self-host/reference: postiz-app.

## Safety / governance boundary

- Do not auto-click public Publish by default. Default mode should be draft/fill/preview/human-confirm.
- Login/QR/phone verification must be performed by the user.
- Store only session pointers/status in Hermes; never store plaintext passwords/API secrets in docs/tasks/memory.
- External command boundary is preferred for GPL/AGPL projects: call CLI/MCP rather than copying source.
- Platform automation is brittle and ToS-sensitive; every platform adapter must have a health check and failure evidence.

## Recommended taskpool intake

Create tasks:

1. Evaluate MatrixMedia as Chinese-platform distribution adapter for Hermes/Solo Pipeline.
2. Evaluate PostBot publishers as source of Chinese platform selectors/payload schema.
3. Evaluate Postiz Agent CLI for international social scheduling adapter.
4. Design Hermes distribution adapter interface: `draft`, `fill`, `preview`, `publish_requires_approval`, `status`, `history`.
5. Prototype only a non-posting flow first: generate publish package + adapter dry-run + login status check.
