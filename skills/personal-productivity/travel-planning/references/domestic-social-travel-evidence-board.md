# Domestic social travel evidence board pattern

Use when a travel plan depends on Xiaohongshu/Douyin/social screenshots or login-gated social search, and the user wants an executable "马上出发" checklist or visual show-me artifact.

## Applicability

- Domestic China travel planning where 小红书/抖音 notes are used as weak-to-medium social evidence for practical pitfalls.
- The goal is not generic inspiration; it is route, packing, safety, lodging, navigation, or booking risk control.
- Especially useful when the user asks to "找证据", "补充马上出发", "show me", or wants a visual artifact from social evidence.

Anti-conditions:

- Do not treat social posts as authoritative facts for prices, closures, permissions, or legal access; verify dynamic/official facts separately when decisions depend on them.
- Do not copy risky comment hacks such as paying to enter fenced/private areas, bypassing closures, or following unofficial pasture tracks.
- Do not preserve login profiles or cookies after the session unless explicitly asked.

## Evidence acquisition pattern

1. Prefer user-provided screenshots first. OCR/summarize them into: original quote, risk class, actionable travel item.
2. If web search is needed and the user authorizes login, use a scoped browser/profile and avoid system VPN/proxy ports when the platform flags proxy IPs.
   - Example Chrome flags: `--user-data-dir=/tmp/xhs-noproxy-profile --no-proxy-server --remote-debugging-port=<port>`.
   - Stop at password/SMS/payment gates. User may scan/login themselves.
   - After extracting public search results/notes, close Chrome and delete the temp profile.
3. Search in high-signal query clusters, not one generic query:
   - destination + month + 自驾/避坑
   - specific stop + 住宿/热水/虫子/厕所
   - specific scenic spot + 导航/停车/断崖/牧场
   - weather/packing terms: 风大/下雨/穿搭/防晒/驱蚊
4. For each note, capture compact source metadata: title, author/date/likes when visible, and the exact quote that supports the action.
5. Separate evidence tiers:
   - user screenshot/OCR quote;
   - login-gated social-note quote;
   - comment corroboration;
   - public weather/official source;
   - your route judgment.

## Synthesis pattern

Convert social evidence into an executable board:

- **Risk headline**: e.g. 私牧回扣、雨后野路、住宿热水、厕所、加油、风雨窗口.
- **Quoted evidence**: one or two short original phrases.
- **Decision rule**: what to do / avoid.
- **Trip placement**: which day or stop it affects.
- **Downgrade gate**: weather, time, route, or fatigue condition that changes the plan.

Avoid long undifferentiated note summaries. The output should tell the traveler what to do at departure time.

## Visual show-me artifact pattern

When the user says "show me" or asks to follow a taskpool/report style, create a small local HTML evidence board rather than only prose:

- hero verdict: the main decision in one sentence;
- route topology: D1-Dn or hub/branch layout;
- evidence cards: quote → risk → action;
- weather/traffic gates;
- final checklist;
- source/caveat footer saying visualization is derived from evidence, not the fact source.

Verification before reporting:

- write the HTML to an explicit path;
- read back or stat the file;
- open locally when browser tools are available;
- check console errors if JavaScript is present.

## Cleanup / privacy

- Use temporary profiles for social login research.
- Remove the temporary profile after extraction unless the user asks to keep it.
- Never report or store user account identifiers, cookies, private messages, or profile data.
