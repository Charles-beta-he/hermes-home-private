# App-Only Booking Evidence

Extracted from `/Users/charles/.hermes/skills/personal-productivity/travel-planning/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## App-only booking evidence

Scope: use this only when a travel plan reaches concrete booking research and ordinary web pages do not provide current bookable options. Do not use it for high-level itinerary brainstorming.

For mainland China local food/nightlife/play recommendations, ordinary web search and foreign maps are weak evidence. Prefer 大众点评 / 美团 / 小红书 / 抖音 / 高德 / 百度地图 app screenshots plus OCR, then official map APIs, before relying on Google/Bing/OSM. Use `references/china-local-food-play-evidence-2026-06.md` for the evidence hierarchy, platform boundaries, local probe scripts, GitHub adapter candidates, and live-response workflow. When the user asks whether a venue is good or requests nearby food/play recommendations, run or cite the local evidence pipeline (`china_local_evidence_pipeline.py`) when available; if native app pages are blocked, ask for screenshots instead of inventing platform rankings.

For domestic social-platform travel evidence (Xiaohongshu/Douyin screenshots, login-gated searches, "马上出发" checklists, or a visual "show me" evidence board), use `references/domestic-social-travel-evidence-board.md`. It covers screenshot OCR, no-proxy temporary browser login, quote→risk→action synthesis, HTML evidence-board output, and cleanup/privacy rules.

1. Prefer current, source-attributed booking evidence over generic search snippets.
2. If a booking web page blocks automation, switch to safer channels: official availability endpoints, official/provider apps, user-provided app screenshots, or semi-automated browsing in the user's real app session.
3. Stop for passwords, SMS/captcha, payment, biometric checks, or other secrets.
4. Summarize booking research as options with source, time, price, fit/risk, and next action.

See `references/china-travel-booking-evidence-2026.md` for a scoped domestic-booking evidence pattern.
