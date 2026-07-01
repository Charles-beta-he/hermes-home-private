# WeChat Channels public preview API intake notes

Applicability: user-provided `weixin.qq.com/sph/<id>` or `channels.weixin.qq.com/finder-preview/pages/sph?id=<id>` links where the user asks to analyze public preview evidence and add a governed taskpool card. Use only for public preview metadata. Anti-conditions: do not bypass WeChat app/QR/login gates, do not claim hidden video playback was consumed, do not export cookies/tokens, and do not use the preview alone as adoption authority.

## Durable pattern

1. Resolve the short link to the public preview URL:
   - `https://weixin.qq.com/sph/<shortUri>` -> `https://channels.weixin.qq.com/finder-preview/pages/sph?id=<shortUri>`.
2. If local DNS/proxy resolves Tencent hosts to fake-IP ranges (for example `198.18.*`) and TLS fails, query public DNS for real edge IPs and use `curl --resolve` for `channels.weixin.qq.com:443:<real-ip>` or `weixin.qq.com:443:<real-ip>`. Treat this as a routing workaround, not a claim that the site is broken.
3. Load the preview HTML. It is usually a SPA shell and may not contain metadata directly.
4. The public SPA currently loads JS bundles that call:
   - endpoint: `https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info`
   - method: `POST`
   - body for `/sph` pages: `{"baseReq":{"generalToken":""},"shortUri":"<shortUri>"}`
5. Include browser-like request context. A bare POST can return `{"errCode":-1,"errMsg":"permission verification failed"}`. Add at least:
   - `Content-Type: application/json`
   - `Origin: https://channels.weixin.qq.com`
   - `Referer: https://channels.weixin.qq.com/finder-preview/pages/sph?id=<shortUri>`
   - browser User-Agent
6. Parse only public fields returned by the API: author nickname, description/caption, visible count formats, created time, location wording when present, cover URL, and scene/export IDs if useful for readback. Do not dereference or play gated media unless publicly accessible without bypass.
7. If the preview names an artifact, verify it directly from authoritative sources (GitHub API, README/docs/package registry) before creating an evaluation card.
8. Create/read back the taskpool card. If `brain_task_orchestrator.py add` succeeds but hooks report advisory errors such as multimodel `allowlist_miss`, treat it as mixed: card exists, hook advisory failed. Read the Markdown and patch collapsed acceptance/red-line text before reporting success.

## Example curl

```bash
curl -sS --max-time 30 \
  --resolve channels.weixin.qq.com:443:<REAL_EDGE_IP> \
  -H 'content-type: application/json' \
  -H 'origin: https://channels.weixin.qq.com' \
  -H 'referer: https://channels.weixin.qq.com/finder-preview/pages/sph?id=<SHORT_URI>' \
  -A 'Mozilla/5.0' \
  'https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info' \
  --data '{"baseReq":{"generalToken":""},"shortUri":"<SHORT_URI>"}'
```

## Pitfalls

- `permission verification failed` after a bare API call usually means missing browser request context, not proof that public preview metadata is unavailable.
- Fake-IP TLS errors are an environment routing symptom; capture the successful `--resolve` pattern rather than saving a negative tool claim.
- Visible social metrics and marketing claims are leads, not verified artifact facts. Convert claims such as “8x faster”, “free”, or “zero API fee” into future verification requirements.
