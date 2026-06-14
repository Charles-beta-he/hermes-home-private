# Xiaohongshu travel evidence with no-proxy logged-in browser (2026-06)

Use when a domestic-China travel plan needs current Xiaohongshu/social evidence and ordinary browser/web access is blocked by IP-risk pages, login walls, or system VPN/proxy routing.

## Applicability

- User explicitly wants Xiaohongshu evidence for a concrete trip, route, packing list, or避坑 checklist.
- User can provide app screenshots, or explicitly consents to a temporary web login / QR scan.
- Goal is to read public search results and public notes/comments only, then translate them into travel checklist items.

Anti-conditions:

- Do not use for account/private data, messages, publishing, following, liking, collecting, or settings changes.
- Do not store cookies or profile directories durably.
- Do not treat one note as fact; prefer repeated signals or high-consequence risks.
- Do not hard-code exact note URLs/tokens as durable facts; tokens expire.

## Workflow

1. Check whether a system proxy/VPN port is active before blaming Xiaohongshu. On macOS, `scutil --proxy` may show HTTP/HTTPS proxy such as `127.0.0.1:1082`.
2. Try no-proxy access first:
   - Terminal probes: use a no-proxy opener / `curl --noproxy '*'`.
   - Browser path: launch a temporary Chrome profile with `--no-proxy-server`.
3. If Xiaohongshu returns IP-risk/security page in the agent browser but no-proxy Chrome reaches the site, continue with no-proxy Chrome.
4. If search results require login, stop and ask for explicit QR/login consent. After consent, use a temporary profile and read only public results.
5. Extract search-result titles first; then open a small set of high-signal notes for details.
6. Convert findings into: evidence quote → risk judgment → concrete travel checklist item.
7. Close the temporary browser and remove the temporary profile after extraction.

## Practical command pattern

Example shape; adjust port/profile/query per session:

```bash
rm -rf /tmp/xhs-noproxy-profile
open -na 'Google Chrome' --args \
  --user-data-dir=/tmp/xhs-noproxy-profile \
  --no-proxy-server \
  --remote-debugging-port=9223 \
  --remote-allow-origins='*' \
  'https://www.xiaohongshu.com/search_result?keyword=...&type=51'
```

Use CDP only to read public DOM text from the logged-in temporary browser. Do not perform account side effects.

Cleanup:

```bash
pkill -f 'remote-debugging-port=9223' || true
rm -rf /tmp/xhs-noproxy-profile
```

## Search query pack for Hulunbuir self-drive避坑

- 呼伦贝尔 6月 自驾 避坑
- 呼伦贝尔 黑山头 住宿 避坑 热水 虫子
- 呼伦贝尔 莫日格勒河 游牧人家 避坑
- 呼伦贝尔 6月 穿搭 风大 下雨
- 呼伦贝尔 边防公路 草场 停车 避坑
- 呼伦湖 风大 避坑
- 室韦 电动车 续航 避坑

## Evidence synthesis pattern

Classify notes into reusable trip controls:

- Self-drive safety: no smart driving on grassland roads with livestock; no rain-after grassland dirt roads; fuel early; offline maps; carry ID/driver docs for border checkpoints.
- Private pasture/driver kickback: reject driver-pushed private牧场, sudden paid detours, “网红断崖/秋千” claims without verified public route and fee.
- Lodging hygiene: for Heishantou/Mongolian-yurt stays verify bugs, sewer smell, hot water duration, sound insulation, screens/mesh doors, heating/AC, food access.
- Route expectation control: Hulun Lake and Shiwei may be better as short stops than core experiences when reviews emphasize low value, commercialization, wind, or poor facilities.
- Packing: windproof/rain shell, warm layer, long pants, grippy shoes, sunscreen, DEET repellent, wet wipes/wet toilet paper, hand sanitizer, GI and motion-sickness meds.

## Output style

Keep final output executable and evidence-first:

```text
Evidence: <source title> — "short quote"
Risk: <one-sentence interpretation>
Add to马上出发: <specific checklist item>
```

Call out weak evidence when only search titles are available. Prefer quotes from note body/comments for high-consequence recommendations.