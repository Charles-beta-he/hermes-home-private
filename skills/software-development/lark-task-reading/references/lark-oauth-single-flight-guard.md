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

Use the unified read-only flow for normal task work. It preserves the single-flight OAuth guard and the automatic visible `授权` click, then reads with `auto_auth=False` so there is no second hidden login attempt:

```bash
# Scoped incomplete task list
python3 ~/.hermes/scripts/lark_task_flow.py --scope-mode only --summary

# Single task URL/GUID
python3 ~/.hermes/scripts/lark_task_flow.py \
  --url 'https://applink.larksuite.com/client/todo/detail?guid=<guid>&suite_entity_num=<task>' \
  --summary
```

The unified order is: guard token/preflight → cleanup stale listener if needed → open one OAuth URL → auto-click visible Lark-blue `授权` button when present → re-read token store → read task list or direct GUID → print summary/JSON. It never writes back to Lark and should not print tokens/secrets.

For status-only checks, first prove whether existing auth is already usable without opening a browser:

```bash
python3 ~/.hermes/scripts/lark_task_flow.py --auth-only --no-open --no-auto-authorize
# or lower-level:
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --no-open
```

For lower-level recovery/debugging when a stale listener may exist:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale
```

For explicit lower-level full on-demand automation after the user has authorized Hermes to automate the consent click:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale --auto-authorize
python3 ~/.hermes/scripts/lark_task_reader.py --scope-mode only --summary --no-auto-auth
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

## Related UVISA task-scope references

- `references/uvisa-wallet-account-transaction-scope.md` records the UVISA C-side wallet account transaction matrix from Lark comments (CNY vs non-CNY, tabs, signs, and card/wealth row classes). Use it only for that scoped product surface.

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
- status-only `--no-open` with no token fails as `no_open_would_require_login` and **does not spawn** `lark-mcp login` or leave a listener/lock;
- `--force-refresh --no-open --auto-authorize` fails closed as invalid args because auto-click requires a visible browser page;
- unified `lark_task_flow.py` runs guard first, then calls the reader with `auto_auth=False` / `auto_authorize=False`, preventing a second hidden login attempt;
- unified URL mode extracts `guid=` from Lark applinks and can read a direct task detail after auth succeeds;
- auth URL extraction from noisy CLI output;
- token-key redaction is non-vacuous: use a long token (longer than `keep_start + keep_end + 3`), assert `...`, shorter length, prefix/suffix retention, no secret middle substring, and `redacted != original`;
- top-level secret redaction for `app_secret`, `client_secret`, `access_token`, `refresh_token`, `token`;
- the `--json` / main entrypoint applies redaction with a long token fixture, not only a helper function;
- `_is_unexpired` boundaries: `None`, `""`, future, `now`, `0`, `"0"`, unparsable;
- credential/domain/scope values from auth-store/env are normalized to scalar strings before building `subprocess.Popen` args, so tuple/list-shaped values cannot trigger `sequence item 0: expected str instance, tuple found` before `lark-mcp` starts.

## Verification sequence

```bash
python3 ~/.hermes/scripts/test_lark_oauth_guard.py
python3 ~/.hermes/scripts/test_lark_task_flow.py
python3 ~/.hermes/scripts/test_lark_task_reader.py
python3 ~/.hermes/scripts/lark_task_flow.py --auth-only --no-open --no-auto-authorize
python3 ~/.hermes/scripts/lark_task_flow.py --scope-mode only --summary
```

Interpretation rules:

- `no_open_would_require_login` is a healthy status-only result when no token exists; it proves no browser/login side effect was started.
- `authorize_button_not_found` after an opened OAuth URL is an auth/browser visibility boundary, not a task-read result. Do not claim live Lark evidence; ask for/manual complete visible authorization or inspect the browser page.
- If `lark-mcp login` is left listening on the callback port after an interrupted run, clean only that stale login process plus `~/.hermes/state/lark_oauth_guard.lock`, then rerun status-only before trying a full auth flow.

Certification-sensitive changes should then be packaged as claim-linked evidence and rerun with the exact current-code four-model gate. A previous certified tick becomes provenance only after any guard/test/runbook amend. If the T3 run is truth-grounded but `not_certified`, follow `multi-model-thinking` reference `grounded-not-certified-amend-loop.md`: turn reviewer AMENDs into concrete guard tests/evidence, commit, update the state file to the current commit set, then rerun fresh T3.

## Pitfalls

- Do not paste raw app secrets, OAuth codes, token keys, or user tokens into evidence, skills, memories, or final replies.
- Do not treat old watch-pattern output from a background process as current auth state.
- Do not repeat raw `lark-mcp login` after `NO_TOKEN`; switch to auth-store inspection or the guard.
- Do not claim live task read from a stale snapshot; verify with the reader after the token is valid.
- If `auto_authorize` returns `authorize_button_not_found`, take a one-shot desktop screenshot before retrying. A locked macOS desktop or an OAuth page opened on an invisible Space can make `open <auth_url>` report success while the clicker only sees wallpaper/no browser. Classify this as a user-session visibility blocker; do not ask for or use the lock-screen password. Ask the user to unlock/bring the browser visible, then rerun the unified flow.
- `authorize_button_not_found` after `opened=true` can mean the desktop is locked or the OAuth page opened on a non-visible Space/window, not that the reader is broken. For diagnosis, start one guarded flow, capture a one-time desktop screenshot for the user, and report whether an OAuth page/button is visible. Do not use or type a lock-screen password even if the user provides one; ask the user or a trusted local person to unlock, then rerun the unified flow.
