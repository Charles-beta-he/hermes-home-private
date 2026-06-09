# 抖音项目 intake：PageAgent / AI 直接操作浏览器

Date: 2026-06-08

## Source inspected

- Short URL: https://v.douyin.com/w09mqmJUb4c/
- Resolved URL: https://www.douyin.com/video/7648214705970175695
- Author: 企鹅加德
- Publish time: 2026-06-06 17:39
- Visible description: `ai直接操作你家浏览器的开源项目#ai新星计划 #vibecoding #vibecoding大赏 #ai #开源 @抖音科技`
- Video duration: 00:36
- Engagement visible: 2163 / 33 / 2721 / 353
- Page search/context keyword: `playwright`

## Visible video/context evidence

The browser page text and visible video frame indicate a browser-control open-source project. Video frame OCR showed a left-side navigation with items resembling:
- `PageAgent`
- `PageAgent...`
- `PageController`
- `自定义 UI`
- `安全与权限`
- `功能特性`
- `模型`
- `自定义工具`
- `知识注入`
- `数据脱敏`
- `Chrome...`
- `MCP Server`
- `接入第三方`

Comments and related videos reinforce the mechanism class:
- comments mention `browser agent`, `playwright`, token cost, step/context limitations, forum export to Excel/Word.
- related recommendation mentions `Browser Harness` and `CLI+Skill 浏览器AI自动化框架`.

## Preliminary mapping

Likely project class: PageAgent / browser-agent automation with Playwright or Chrome control, possibly Alibaba/Tongyi ecosystem.

Important: the exact canonical GitHub repo is not fully proven from the Douyin page alone. GitHub search found related `PageAgent` wrappers/adapters, but the task should first identify the authoritative upstream source before any implementation or installation.

## Suggested taskpool framing

Create a governed P2 evolution task to analyze the PageAgent/browser-agent mechanism as a complement/competitor to existing Hermes browser/computer_use/OculOS/Browser Harness evaluation tasks.

Key deltas to inspect:
- Browser control path: Playwright vs CDP vs extension vs MCP.
- Whether it exposes deterministic DOM/a11y/tool schema or relies on screenshot vision.
- Token-cost strategy: step compression, scripted workflows, reusable skills, no-LLM automation paths.
- Safety model: permission prompts, domain allowlist, data desensitization, third-party connection, sandboxing.
- Context continuity: multi-step memory, task state, limits noted by comments.
- Hermes landing zone: browser harness integration, external-control safety, skill-graph workflow recipes, or taskpool evidence capture.

Anti-drift:
- Do not create a vague “analyze browser agent” survey.
- First identify the canonical upstream repo/source.
- Compare net-new mechanisms against OculOS and Browser Harness, instead of repeating the same Computer Use critique.
- Do not install browser extensions, grant permissions, or run third-party automation without explicit approval.
