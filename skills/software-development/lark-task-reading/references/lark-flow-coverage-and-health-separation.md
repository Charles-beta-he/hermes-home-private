# Lark flow coverage and health/remediation separation

Use this when designing, auditing, or operating Lark OAuth/task-reader self-checks. It prevents a green token probe or 100% check-attachment score from being misreported as end-to-end workflow coverage.

## Four evidence layers

Report these independently:

1. **Static capability** — scripts, flags, profiles, and check registrations exist.
2. **Current state** — token validity, lock state, callback-port state, and latest guard action.
3. **Contract tests** — deterministic tests cover token-valid short-circuit, active-lock single-flight, stale-listener planning, browser-open/auto-click invocation, secret redaction, and no second hidden auth attempt.
4. **Live workflow evidence** — a real run proves browser opened, authorization click succeeded, callback completed, token persisted, lock released, and a separately authorized reader smoke succeeded.

A coverage registry showing 100% classification/check attachment proves only that checks are registered. It must not imply layer 4.

## Split the operational lanes

Keep three explicit commands/semantics instead of one overloaded health command:

- `health/status`: strictly read-only; never opens a browser, clicks, refreshes a token, kills a process, removes a lock, or reads tasks.
- `repair-auth`: may clean a proven stale OAuth lock/listener and start one guarded login; requires an exact authority grant and post-action token readback.
- `reader-smoke`: performs a bounded read-only Task API call after token readiness; does not write comments/status and requires separate scope/authority from status-only health.

Do not label a command `local_read` if it always passes `--cleanup-stale`; cleanup can kill a listener or remove a lock. Either remove cleanup from the health path or classify the exceptional branch as a local mutation.

## In-progress process inspection

A process-aware OAuth check should record, without secrets:

- state: `idle | token_missing | lock_acquired | listener_ready | browser_opened | waiting_authorization | callback_received | token_persisted | reader_ready | failed`;
- lock age, owner PID, and whether that PID is alive;
- callback port and listener identity;
- elapsed time versus a bounded SLA;
- whether the browser was opened and the authorize action was attempted;
- final token validity and lock/listener cleanup readback.

An active lock is not automatically stale. Never spawn a second login while its owner is alive. A valid token normally short-circuits login, but process inspection may still need to flag an orphan lock/listener separately.

## Automated authorization gate

When the user explicitly authorizes automated Lark OAuth:

1. Run the single-flight guard with stale cleanup and `--auto-authorize`.
2. Never type passwords, OTPs, API keys, or other credentials.
3. The clicker may target only the expected visible Lark primary authorization control and must fail closed if not found.
4. Verify `login_success`, token validity, callback listener release, and lock release.
5. Run the status-only probe again; do not treat login process exit alone as success.
6. Run a Task API reader smoke only if the user also authorized task reading.

## Coverage naming

Use names that match proven behavior:

- `lark_auth_token_watch` for token/guard status;
- `lark_oauth_process_watch` for lock/listener/state-machine observation;
- `lark_auto_authorize_contract` for deterministic auto-click/login tests;
- `lark_reader_readonly_smoke` for a real bounded Task API read.

Avoid `lark_auth_and_reader_watch` when the implementation never calls the reader.

## Verification checklist

- [ ] Static capability, current state, contract tests, and live workflow evidence are reported separately.
- [ ] Health is strictly read-only or honestly classified as local mutation.
- [ ] In-progress lock/PID/listener state is observed without starting duplicate login.
- [ ] Auto-authorization requires exact user authority and produces token/lock/port readback.
- [ ] Reader readiness is not inferred from token validity.
- [ ] Check-attachment percentage is not presented as end-to-end workflow coverage.
