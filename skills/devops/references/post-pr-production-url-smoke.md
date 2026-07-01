# Post-PR production URL smoke check

Use this reference when the user says a PR was merged and asks whether a production/staging URL is "开启 / up / working".

## Goal

Answer availability from fresh external evidence, not from deployment assumptions.

## Checklist

1. Probe the exact URL with a browser-capable path when UI availability matters.
   - Load the URL.
   - Confirm the expected page title or major text/route renders.
   - Check browser console for uncaught JavaScript errors and failed critical network calls.
2. Probe HTTP separately with `curl`.
   - Capture status code, redirect chain/final URL, response time, and one or two identifying headers/request IDs if available.
   - Prefer `curl -sS -L -o /tmp/file -w 'status=%{http_code} time=%{time_total} final=%{url_effective}\n' URL` for concise evidence.
3. If one client reports a TLS/EOF/SSL oddity but browser and curl succeed, classify it as client-specific transport evidence, not as site downtime.
   - Mention the client-specific anomaly only if it affects the user's decision.
4. If the page loads but the app requires login, report the verified boundary honestly: "login shell rendered" rather than "all business flows verified".
5. Final answer should be short and evidence-bound.
   - Example: `已开启：HTTP 200，登录页标题 X 正常渲染，控制台无 JS error，curl 响应 Y 秒。未验证登录后业务流。`

## Pitfalls

- Do not infer production status solely from a successful merge/PR state.
- Do not call the whole app healthy after only checking the public login shell.
- Do not let a single Python urllib/SSL failure override browser + curl success unless multiple independent clients reproduce it.
- Avoid long deployment theory unless the smoke fails or the user asks for diagnostics.
