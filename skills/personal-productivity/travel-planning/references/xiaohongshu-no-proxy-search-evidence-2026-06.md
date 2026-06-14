# Xiaohongshu no-proxy search evidence pattern (2026-06)

Use when a domestic China travel task needs Xiaohongshu social evidence and the normal browser/web path is blocked by IP-risk, VPN/proxy reputation, or login gating.

## Applicability

- The user asks to search Xiaohongshu for travel避坑 / route / clothing / lodging signals.
- The machine has a local VPN/proxy port configured, but the user asks to avoid it.
- The goal is public evidence extraction, not account operation.

Anti-conditions:

- Do not bypass login, CAPTCHA, SMS, payment, or private-account boundaries.
- Do not state that Xiaohongshu evidence was read unless note cards/content were actually visible.
- Do not save account cookies, tokens, QR-login state, or other credentials in skills or memory.

## Procedure

1. Check the active system proxy first, then explicitly bypass it for probes.
   - macOS proxy check: `scutil --proxy`.
   - Terminal probe pattern: Python `urllib.request.build_opener(urllib.request.ProxyHandler({}))` or `curl --noproxy '*' ...`.
2. If a normal browser automation stack shows `安全限制 / IP存在风险 / 300012`, do not keep hammering it.
3. For a no-proxy desktop probe, launch an isolated Chrome profile with proxy disabled:
   - `open -na 'Google Chrome' --args --user-data-dir=/tmp/xhs-noproxy-profile --no-proxy-server 'https://www.xiaohongshu.com/search_result?keyword=...'`
   - Use a temporary profile so it does not disturb the user's main Chrome session.
4. If the page loads but says `登录后查看搜索结果`, stop at the login wall. Ask for one of:
   - user-provided app screenshots of search results/comments; or
   - explicit permission for the user to QR-login in the temporary no-proxy Chrome session.
5. When relying on user screenshots, preserve the chain as:
   - query term;
   - quoted original evidence line;
   - risk judgment;
   - concrete itinerary/checklist item.

## Queries that worked as high-signal prompts for Hulunbuir-style trips

- `呼伦贝尔 6月 自驾 避坑`
- `呼伦贝尔 黑山头 住宿 避坑 热水 虫子`
- `莫日格勒河 游牧人家 避坑`
- `额尔古纳湿地 换乘点 避坑`
- `呼伦湖 风大 避坑`
- `呼伦贝尔 6月 穿搭 下雨 风大`
- `呼伦贝尔 边防公路 草场 停车 避坑`
- `室韦 电动车 续航 避坑`

## Reporting pattern

Be explicit about evidence boundaries:

- `已避开系统代理 127.0.0.1:<port> 直连；小红书搜索页打开，但返回登录后查看搜索结果；未读取到笔记卡片。`
- Then provide only screenshot-backed items or clearly labeled provisional route/weather checklist items.

## Pitfalls

- Search-engine snippets for Xiaohongshu are weak evidence; treat them as discovery only.
- The public home feed can load while search results remain login-gated; do not confuse home-feed cards with search evidence.
- If DevTools/CDP is used for page inspection, do not collect or persist cookies/tokens. Use it only to read visible DOM state and resource names.