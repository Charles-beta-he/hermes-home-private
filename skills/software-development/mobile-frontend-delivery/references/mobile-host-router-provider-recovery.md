# Mobile host-router provider recovery and external CLI execution

Use when a mobile/RN/PWA Gateway claims production-grade multi-model routing and the host router can select OAuth/external-process providers such as `claude-code` or `google-gemini-cli`.

## Applicability

- Gateway/mobile dialog path consumes a host model-router `select-pair` result.
- Selected providers may be Hermes-native providers or external CLIs/OAuth-backed providers.
- You need to distinguish: router metadata, actual producer execution, reviewer execution, and provider recovery.

## Anti-conditions

- Do not store project-specific smoke output, account emails, commit IDs, or temporary URLs here.
- Do not mark a provider unavailable forever because one smoke failed; use runtime availability state and recovery probes.
- Do not enter user credentials, Google passwords, browser cookies, or OTPs. OAuth browser consent/callback remains a human boundary.

## Pattern

1. Verify direct provider runtime separately from Hermes wrapper.
   - For `claude-code`, a direct CLI smoke can be authoritative: `claude -p '只回复：TOKEN' --model <model> --max-turns 1`.
   - If direct `claude` works but `hermes --provider claude-code ...` returns no final response, treat it as a wrapper-path issue, not as proof that Claude Code is unavailable.
2. Recovery probes should use the actual executable path for external-process providers.
   - `claude-code` recovery should smoke the real `claude` CLI and only mark available after the expected token appears.
   - Other Hermes-native providers can continue through `hermes --provider ...` smoke.
3. Gateway execution should route external-process providers through the real external CLI when the host router selects that provider.
   - Preserve honest provenance: `actualExecution.source = cli_invocation` unless Hermes core itself returns provider/model metadata.
   - Do not claim core-internal actual execution when only invocation arguments prove the selected model was used.
4. Reviewer lanes need the same external-provider handling as producer lanes.
   - If `reviewerProvider=claude-code`, invoke `claude -p <review prompt> --model <reviewerModel> --max-turns 1` and parse its output into `reviewerDecision`.
5. Code-Assist-backed OAuth providers have separate auth, wrapper, and backend-policy gates. Applicability: only OAuth-backed model providers whose Hermes wrapper hides backend details behind a generic final-response failure. Anti-condition: skip this path when credentials are absent; run normal OAuth login first.
   - Browser OAuth success and `hermes auth status <provider>` may show logged in.
   - A wrapper-level smoke can still fail generically with `no final response was produced`; do not stop there if login is known-good.
   - For actionable diagnosis, call the underlying adapter/backend client directly from the owning runtime environment and run one non-stream chat completion. This can reveal policy/backend errors hidden by the CLI wrapper, such as a 403 account/product-disabled response that requires an appeal or account/project change.
   - If the backend returns an account-policy or Terms-of-Service disablement, classify it as a human/provider policy boundary: keep the provider runtime-unavailable, do not retry-loop or relogin indefinitely, and ask for appeal/account/project change before recovery.
   - To help login when credentials are actually absent, start the provider's OAuth add flow, give the user the browser URL, and accept only the resulting callback URL/code if auto-callback fails. Never ask for credentials.
6. After any provider recovery or external execution path change, rerun the closure chain:
   - provider recovery smoke
   - model-router readiness
   - default mobile dialog producer+reviewer smoke
   - Gateway focused tests/build
   - full production verify
   - project profile/ledger update
   - scoped commit if the repo is under git

## Pitfalls

- Treating `logged in` as equivalent to `provider can produce a final response` lets broken OAuth/external providers into production routing.
- Treating Hermes wrapper failure as provider failure can incorrectly remove an actually working external CLI from reviewer/producer candidates.
- Focused tests can inherit environment flags such as reviewer-enabled from previous tests; explicitly save/restore env vars around tests that assert only producer invocation.
- If a model router marks a provider runtime-unavailable, recovery should be reversible and evidence-driven: reopen only after a real token-matching smoke succeeds.
