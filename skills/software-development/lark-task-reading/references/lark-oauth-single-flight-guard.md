# Lark OAuth single-flight guard pattern

Use this when Lark/Feishu Task reads are blocked by repeated OAuth prompts, duplicate `Authorization URL` notifications, `EADDRINUSE ::1:3010`, or stale background login output after a token has already become valid.

## Failure mode

Raw `lark-mcp login` is not idempotent in an agent loop:

- the callback port is fixed (`localhost:3010` for this environment);
- a previous login helper can keep listening on the port;
- multiple background helpers can emit old `Authorization URL:` / `AUTO_OPENING_AUTH_URL` watch-pattern output;
- process exit or watch output is not proof that a user token was stored.

Treat those as workflow/state-machine symptoms, not as proof that the Lark reader is broken.

## Preferred command

For status-only checks:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --no-open
```

For recovery when a stale listener may exist:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale
```

The guard should:

1. read the lark-mcp auth store;
2. return immediately when a valid token exists;
3. use a single-flight lock such as `~/.hermes/state/lark_oauth_guard.lock`;
4. fail closed when port 3010 is busy unless `--cleanup-stale` is explicit;
5. open at most one auth URL per guarded run;
6. re-read the token store after login;
7. redact token keys and top-level secrets from JSON output.

## Token expiry semantics

For compatibility with old token records, missing or blank `expiresAt` may be treated as unbounded. But explicit epoch values are real expiry timestamps and must fail closed:

- `expiresAt is None` or `""` -> legacy/unbounded token record;
- `expiresAt == 0` or `"0"` -> expired;
- `expiresAt <= now` -> expired;
- unparsable expiry -> invalid.

Do not lock in Python truthiness bugs such as treating string `"0"` as a valid token.

## Required regression tests

Add or maintain tests for:

- token-valid path does not spawn login;
- active lock does not spawn a second login;
- port busy without cleanup fails closed;
- port busy with cleanup plans cleanup-then-login;
- auth URL extraction from noisy CLI output;
- token-key redaction is non-vacuous: use a long token (longer than `keep_start + keep_end + 3`), assert `...`, shorter length, prefix/suffix retention, no secret middle substring, and `redacted != original`;
- top-level secret redaction for `app_secret`, `client_secret`, `access_token`, `refresh_token`, `token`;
- the `--json` / main entrypoint applies redaction with a long token fixture, not only a helper function;
- `_is_unexpired` boundaries: `None`, `""`, future, `now`, `0`, `"0"`, unparsable.

## Verification sequence

```bash
python3 ~/.hermes/scripts/test_lark_oauth_guard.py
python3 ~/.hermes/scripts/test_lark_task_reader.py
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --no-open
python3 ~/.hermes/scripts/lark_task_reader.py --scope-mode only --summary
```

Certification-sensitive changes should then be packaged as claim-linked evidence and rerun with the exact current-code four-model gate. A previous certified tick becomes provenance only after any guard/test/runbook amend. If the T3 run is truth-grounded but `not_certified`, follow `multi-model-thinking` reference `grounded-not-certified-amend-loop.md`: turn reviewer AMENDs into concrete guard tests/evidence, commit, update the state file to the current commit set, then rerun fresh T3.

## Pitfalls

- Do not paste raw app secrets, OAuth codes, token keys, or user tokens into evidence, skills, memories, or final replies.
- Do not treat old watch-pattern output from a background process as current auth state.
- Do not repeat raw `lark-mcp login` after `NO_TOKEN`; switch to auth-store inspection or the guard.
- Do not claim live task read from a stale snapshot; verify with the reader after the token is valid.
