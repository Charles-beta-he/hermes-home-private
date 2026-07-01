# Provider catalog vs runtime entitlement debugging

Applicability: use when an LLM/provider model appears in one source of truth (email approval, docs page, models.dev, marketing page, cached picker list, or `/v1/models`) but exact runtime calls return `Not supported model`, `Invalid API Key`, empty final responses, or provider-wrapper failures.

Anti-conditions:
- Do not store account-specific keys, token values, private URLs, or one-session model availability as global truth.
- Do not conclude a model is unavailable from one endpoint if the provider has multiple account/plan endpoints.
- Do not conclude approval emails are wrong without testing the exact key + base URL + model tuple.

## Procedure

1. Split the evidence sources before judging availability.
   - External announcement or approval email: entitlement claim.
   - Public docs / models.dev: catalog claim.
   - Hermes picker/cache/static list: local discovery claim.
   - `/v1/models` with the configured key/base URL: account endpoint catalog.
   - Minimal `/chat/completions` call: runtime availability.

2. Read the active provider configuration and redact secrets.
   - Resolve provider slug aliases (`mimo` -> `xiaomi`, etc.).
   - Capture `base_url`, whether a key exists, and which env/config path supplies it.
   - Never print raw API keys; only report presence/length or redacted prefix if unavoidable.

3. Probe the configured endpoint first.
   - `GET {base_url}/models` with the active Authorization header.
   - `POST {base_url}/chat/completions` with the exact model id and a tiny prompt.
   - Prefer a model already known to work as a control call on the same base/key.

4. Compare failure classes.
   - `401 Invalid API Key` on a public/default endpoint while another plan endpoint works usually means the key is scoped to the plan endpoint, not globally invalid.
   - `400 Not supported model <id>` on the configured endpoint means that exact key/base tuple has not exposed the model, even if external docs list it.
   - A model in models.dev but not in `/v1/models` is only a public catalog candidate, not verified account availability.

5. If the user provides an approval email or docs screenshot, treat it as a correction to the hypothesis, not as a reason to skip runtime proof.
   - Extract model id, docs URL, key instructions, and endpoint hints from the screenshot/docs.
   - Re-test the exact documented model id.
   - If runtime still rejects it, state the narrower conclusion: entitlement may be approved, but the current key/base tuple is not yet synchronized or is the wrong endpoint.

6. Next actions after mismatch.
   - Ask the user to create/regenerate a provider key in the approved console if the email says existing/new keys should work but runtime rejects the current one.
   - Update only local env/config with the user's explicit key placement; never ask them to paste a secret into chat.
   - Re-run `/v1/models`, the new model smoke test, and a known-good control model.

## Reporting template

- Claim source: `<email/docs/catalog/cache>` says `<model>` exists/approved.
- Active runtime tuple: provider `<slug>`, base URL `<redacted/base only>`, key present `<yes/no>`.
- Account catalog readback: `/v1/models` includes `<list or missing model>`.
- Runtime smoke: `<model>` -> `<status/error>`; control model -> `<status>`.
- Conclusion: distinguish `approved by provider` from `callable through current Hermes key/base`.
- Safe next step: regenerate/switch key or base URL, then re-probe; do not paste secrets in chat.

## MiMo-style example pattern

If `models.dev` or an approval email lists `mimo-v2.5-pro-ultraspeed`, but the active configured base such as a token-plan endpoint returns `/v1/models` without that model and `POST /chat/completions` returns `Not supported model mimo-v2.5-pro-ultraspeed`, report: the approval/catalog exists, but the current key/base tuple does not expose UltraSpeed yet. A new key or the documented UltraSpeed endpoint may be required before Hermes should add it as verified callable.
