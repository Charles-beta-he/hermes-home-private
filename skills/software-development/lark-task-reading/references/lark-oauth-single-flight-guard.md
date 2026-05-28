# Lark OAuth single-flight guard pattern

Use this when Lark/Feishu Task reads are blocked by repeated OAuth prompts, duplicate `Authorization URL` notifications, `EADDRINUSE` on the configured callback port, or stale background login output after a token has already become valid.

## Failure mode

Raw `lark-mcp login` is not idempotent in an agent loop:

- the callback port is fixed by the current profile/config (`localhost:8765` here; older notes may mention `3010`);
- a previous login helper can keep listening on the port;
- multiple background helpers can emit old `Authorization URL:` / `AUTO_OPENING_AUTH_URL` watch-pattern output;
- process exit or watch output is not proof that a user token was stored.

Treat those as workflow/state-machine symptoms, not as proof that the Lark reader is broken.

## Preferred command

For status-only checks, first prove whether existing auth is already usable:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --no-open
```

For recovery when a stale listener may exist:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale
```

For full on-demand automation after the user has authorized Hermes to automate the consent click:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale --auto-authorize
python3 ~/.hermes/scripts/lark_task_reader.py --scope-mode only --summary
```

Do **not** combine `--auto-authorize` with `--no-open` for a login-spawning run such as `--force-refresh`; the auto-clicker can only click a visible browser consent page after the guard opens the OAuth URL. The guard fails closed on this invalid combination so future sessions do not silently believe auto-authorization was attempted.

For an explicit real refresh test even when the current token is still valid, add `--force-refresh`:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale --auto-authorize --force-refresh
```

`lark_task_reader.py` now performs this guarded auth recovery by default when its token preflight sees `NO_TOKEN` / `TOKEN_EXPIRED`; pass `--no-auto-auth` to keep the old fail-fast behavior, or `--no-auto-authorize` to open the browser without clicking the visible `授权` button.

The guard should:

1. read the lark-mcp auth store;
2. return immediately when a valid token exists;
3. use a single-flight lock such as `~/.hermes/state/lark_oauth_guard.lock`;
4. fail closed when the configured callback port is busy unless `--cleanup-stale` is explicit;
5. open at most one auth URL per guarded run;
6. optionally, with `--auto-authorize`, click only the large Lark-blue primary consent button visible on the macOS screen; fail closed if it cannot be found;
7. re-read the token store after login;
8. redact token keys and top-level secrets from JSON output.

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
- `_is_unexpired` boundaries: `None`, `""`, future, `now`, `0`, `"0"`, unparsable;
- credential/domain/scope values from auth-store/env are normalized to scalar strings before building `subprocess.Popen` args, so tuple/list-shaped values cannot trigger `sequence item 0: expected str instance, tuple found` before `lark-mcp` starts.

## Verification sequence

```bash
python3 ~/.hermes/scripts/test_lark_oauth_guard.py
python3 ~/.hermes/scripts/test_lark_task_reader.py
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --no-open
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale --auto-authorize
python3 ~/.hermes/scripts/lark_task_reader.py --scope-mode only --summary
```

Certification-sensitive changes should then be packaged as claim-linked evidence and rerun with the exact current-code four-model gate. A previous certified tick becomes provenance only after any guard/test/runbook amend. If the T3 run is truth-grounded but `not_certified`, follow `multi-model-thinking` reference `grounded-not-certified-amend-loop.md`: turn reviewer AMENDs into concrete guard tests/evidence, commit, update the state file to the current commit set, then rerun fresh T3.

## Pitfalls

- Do not paste raw app secrets, OAuth codes, token keys, or user tokens into evidence, skills, memories, or final replies.
- Do not treat old watch-pattern output from a background process as current auth state.
- Do not repeat raw `lark-mcp login` after `NO_TOKEN`; switch to auth-store inspection or the guard.
- Do not claim live task read from a stale snapshot; verify with the reader after the token is valid.
