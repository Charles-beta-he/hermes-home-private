# OAuth CLI Provider Runtime Diagnostics

Use when a local CLI/provider reports an OAuth login exists but model calls still fail. This is a reusable diagnostic path for OAuth-backed developer tooling such as Hermes `google-gemini-cli` / Google Code Assist, Claude Code, and similar external-process providers.

## Core distinction

Do not stop at "logged in". Split provider health into four gates:

1. Auth presence: the CLI/tool has a stored OAuth session or credential file.
2. Runtime invocation: the expected provider command or adapter can be called directly.
3. Backend authorization: the upstream service accepts the account/project for the product.
4. Router eligibility: local routing/availability state includes or excludes the model based on a real smoke.

A provider can pass gate 1 and fail gate 3. Treat that as a real external/account boundary, not a local login failure.

## Procedure

1. Check auth status with the tool's native status command.
   - Example: `hermes auth status google-gemini-cli`.
2. Run a minimal direct model smoke with a unique token.
   - Prefer the provider's lowest-layer adapter/CLI when the high-level CLI only says "no final response".
3. If the direct call fails, capture the upstream error body verbatim enough to distinguish:
   - expired/invalid OAuth token,
   - missing project or disabled API,
   - quota/rate limit,
   - account/product policy denial,
   - network/proxy failure.
4. Only mark the provider recovered after a real token-matching smoke succeeds.
5. Re-run router/readiness probes after changing availability state.
6. If backend policy denies the account, stop at a human gate; do not retry-login loops or bypass policy.

## Hermes google-gemini-cli / Code Assist pattern

When `hermes auth status google-gemini-cli` says logged in but `hermes --provider google-gemini-cli ...` returns only `no final response`, probe the lower adapter directly from the Hermes repo venv:

```bash
cd ~/.hermes/hermes-agent
venv/bin/python - <<'PY'
import traceback
from agent.gemini_cloudcode_adapter import GeminiCloudCodeClient
from agent import google_oauth
creds = google_oauth.load_credentials()
print({'email': getattr(creds, 'email', None), 'project_id': getattr(creds, 'project_id', None), 'managed_project_id': getattr(creds, 'managed_project_id', None)})
try:
    c = GeminiCloudCodeClient()
    r = c.chat.completions.create(
        model='gemini-3-flash-preview',
        messages=[{'role': 'user', 'content': '只回复：GEMINI_SMOKE_OK'}],
        stream=False,
        max_tokens=50,
    )
    print('CONTENT:', r.choices[0].message.content if getattr(r, 'choices', None) else r)
except Exception as e:
    print('EXC', type(e).__name__, str(e))
    traceback.print_exc()
PY
```

If the error is `Code Assist HTTP 403` with `PERMISSION_DENIED` / `TOS_VIOLATION` and an appeal URL, the account is product-policy disabled even though OAuth login succeeded. The safe result is:

- keep `google-gemini-cli` unavailable in local provider state,
- let routers filter it out,
- tell the user to submit the upstream appeal or use another eligible Google account/project,
- verify the rest of the router still passes with alternate providers.

## Recovery script pattern

Provider recovery scripts should not rely only on a high-level CLI wrapper if that wrapper collapses errors into a generic "no final response". Add provider-specific low-level probes that return actionable error tails, but still only transition `unavailable -> available` after a token-matching smoke succeeds.

## Verification checklist

- [ ] Auth status checked separately from runtime smoke.
- [ ] Direct adapter/CLI smoke used a unique token and bounded timeout.
- [ ] Upstream error class captured without secrets.
- [ ] Availability state only changed to available after successful smoke.
- [ ] Router/readiness re-run after recovery attempt.
- [ ] External policy/account blocks ended in a human gate, not local workaround claims.

## Anti-conditions

- Do not save a permanent claim that the provider is broken; OAuth/account state can change.
- Do not capture passwords, OAuth tokens, refresh tokens, cookies, or full credential files.
- Do not treat network/IP geography as proof of product availability; it is only one diagnostic signal.
