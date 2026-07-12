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

For status-only checks, first prove whether existing auth is already usable without opening a browser or starting a callback listener:

```bash
python3 ~/.hermes/scripts/lark_task_flow.py --health-check
# or lower-level:
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --status-only --no-open
```

`--no-open` alone is **not** status-only: it can suppress browser opening while still spawning `lark-mcp login`, acquiring the guard lock, and listening on the callback port. A true health lane must pass `--status-only`, return `auth_required` when the token is invalid, and prove these negative assertions: no login call, no listener, no browser, no Task read, no token mutation, and no stale-process cleanup.

Status-only must also be non-mutating at the filesystem helper level. A common hidden violation is calling a convenience method such as `lock.is_active()` before branching on `status_only` when that method automatically unlinks a stale lock. Split observation from repair—for example, `is_active(cleanup_stale=False)` in health and the default cleanup behavior only in the explicitly authorized repair lane. Regression coverage must use a real temporary stale lock (not a mocked `is_active`) and assert that file existence, bytes, inode/mtime metadata, login calls, and lock acquisition are unchanged. A mocked lock-state helper can prove control flow while completely missing the local deletion side effect.

For lower-level recovery/debugging when a stale listener may exist:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale
```

For explicit lower-level full on-demand automation after the user has authorized Hermes to automate the consent click:

```bash
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale --auto-authorize
python3 ~/.hermes/scripts/lark_task_reader.py --scope-mode only --summary --no-auto-auth
```

### Authorization lifetime and routing

Do not silently reinterpret every prior OAuth grant as one-shot, and do not silently reinterpret it as permanent. Record the grant scope explicitly as either:

- `one_shot`: valid only for the named recovery attempt;
- `durable_scoped`: token-invalid/expired may route from `auth_required` to the guarded `repair-auth` lane until revoked, within the named account/profile and side-effect limits.

When a valid `durable_scoped` recovery grant exists, preserve the configured automation: status-only health still performs no mutation, but the orchestrator should schedule the separate single-flight recovery lane instead of repeatedly stopping for the same authorization. Without a valid durable grant, emit a DecisionPacket and wait. Task reading remains a separate procedure and must not be inferred from OAuth-recovery authority; comments, completion, and status writes always require their own grant.

### Persistent grant consumer contract

Treat the runtime profile as the selector and a separate grant artifact as the authority source. The consumer must fail closed unless all of these are true:

1. the profile schema is recognized and the OAuth-recovery policy is explicitly enabled;
2. the profile says ordinary selfcheck may not execute recovery and that Task read/Lark write are not conferred by this grant;
3. the grant path resolves inside a trusted authority-grant root; reject a symlinked grant, traversal/out-of-root path, non-regular file, and—where the root is configurable—**any symlink component in the profile path, configured root, its ancestors, or the grant path**;
4. the grant has a `subject` bound to the exact active profile identity and exact normalized profile path; a scope-correct grant for another profile/account must fail closed rather than being reusable across identities;
5. the grant schema, active status, action, scope, trigger, entrypoint, concurrency/page limits, per-run TTL, and negative side-effect assertions match the consumer contract;
6. revoked, malformed, missing, identity-mismatched, or partially shaped grants return `auto_authorize=false` rather than falling back to permissive defaults.

Treat path and identity checks as separate invariants: path confinement prevents artifact substitution, while subject binding prevents a valid artifact from being replayed for another profile. Testing only the leaf with `Path.is_symlink()` is insufficient because a parent alias can redirect the entire trusted root.

### Timeout, process-tree, and output boundaries

OAuth recovery has two cleanup layers and both need tests:

- the parent flow must start its guard in an isolated process group and, on its own timeout, terminate the whole group with bounded TERM→KILL escalation before a status-only readback;
- the guard's internal `run_login` timeout must also terminate descendants spawned by `lark-mcp login`, not only the direct `Popen` parent. A direct parent can exit while browser/helper descendants survive.

Do not use blocking `stdout.readline()` as the deadline mechanism. Wait for readability with a bounded selector, re-check the deadline before reading, and keep the post-timeout readback in a separate bounded status-only group. Verify cleanup with both a deterministic mocked descendant tree and a real harmless child-process harness; then check the callback listener and exact login-process residuals.

Sanitize every public mode, not only JSON. JSON output must remove raw child tails, auth URLs, nested error/reason fields, and exceptions; plain-text mode should print only a fixed or explicit allowlisted action/error code. Short secrets must be masked completely rather than preserved because a prefix/suffix redactor can otherwise reveal the whole value.

Do not expose a bare CLI `--auto-authorize` switch that bypasses this policy. A one-shot override must itself carry an exact grant/receipt; otherwise only a negative override such as `--no-auto-authorize` is safe. Health must override automation to false even when the durable policy is active.

Keep machine-local profiles local when repository policy intentionally excludes them. Do not automatically force-add an ignored profile merely to make a commit reproducible. Commit a redacted grant/template and consumer/tests when appropriate, verify the live ignored profile separately, and report that the runtime policy is active but unversioned. Never put credentials or token values in the grant artifact.

Each real recovery should emit a sanitized receipt proving login success, token readback, lock/port release, authority reference or digest, and the negative boundaries (`no_task_read`, `no_lark_write`, `no_secret_entry`, `no_external_send`). Let repeated-success thresholds advance on natural independent expiries; do not force-refresh a valid token merely to manufacture a second receipt.

Required tests for the durable consumer include: active grant enables recovery; revoked/malformed/missing grant disables it; out-of-root, leaf-symlink, and symlinked-ancestor paths are rejected; subject/profile ID and exact profile-path mismatch are rejected; health remains status-only; the negative CLI override wins over ambient environment; auth-only performs zero Task reads/Lark writes; and post-action lock/port/process cleanup is read back.

When a hardened consumer adds new mandatory grant fields, do not silently rewrite the live authority artifact as part of the code patch. Let the old grant fail closed, complete all safe static/unit/status-only verification, and present a separate exact human gate for amending the authority record. Updating code, updating authority, and exercising OAuth are three distinct actions.

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
- explicit `--status-only --no-open` with no/invalid token returns `auth_required`, preserves the planned recovery action separately, and **does not** call login, acquire/leave a lock, spawn a listener, open a browser, read Tasks, mutate the token store, or clean stale processes;
- a real stale-lock filesystem fixture survives status-only byte-for-byte with unchanged metadata; do not mock the lock-status method in this test, because the method itself may contain stale-file cleanup;
- `--no-open` without `--status-only` is not accepted as evidence of a read-only health lane;
- `--force-refresh --no-open --auto-authorize` fails closed as invalid args because auto-click requires a visible browser page;
- unified `lark_task_flow.py` runs guard first, then calls the reader with `auto_auth=False` / `auto_authorize=False`, preventing a second hidden login attempt;
- unified URL mode extracts `guid=` from Lark applinks and can read a direct task detail after auth succeeds;
- auth URL extraction from noisy CLI output;
- token-key redaction is non-vacuous: use a long token (longer than `keep_start + keep_end + 3`), assert `...`, shorter length, prefix/suffix retention, no secret middle substring, and `redacted != original`;
- top-level secret redaction for `app_secret`, `client_secret`, `access_token`, `refresh_token`, `token`;
- the `--json` / main entrypoint applies redaction with a long token fixture, not only a helper function;
- `_is_unexpired` boundaries: `None`, `""`, future, `now`, `0`, `"0"`, unparsable;
- credential/domain/scope values from auth-store/env are normalized to scalar strings before building `subprocess.Popen` args, so tuple/list-shaped values cannot trigger `sequence item 0: expected str instance, tuple found` before `lark-mcp` starts.

## Independent staged-slice review: hash immutability gate

When an independent reviewer is asked to vote on an exact staged/cached hash, treat the Git index as an immutable review subject even though another process may restage files concurrently:

1. Compute the requested digest from the exact byte stream (`git diff --cached --binary`) and verify the staged pathname allowlist before reading code. A mismatch is `NO_VOTE`, not `BLOCK`.
2. Materialize the allowlisted index blobs with `git show :path` into a temporary snapshot and inspect/test that snapshot. Do not silently substitute worktree files; first prove `git diff -- path...` is empty if tests have hard-coded worktree module paths.
3. Record the initial digest and per-file blob digests. Run only offline/mocked safety probes unless the review grant explicitly authorizes OAuth, Task reads, browser action, or external writes.
4. Recompute the cached digest immediately before publishing findings. If it changed—even if the pathname set stayed identical—discard all PASS/BLOCK findings and line references as stale and return only `NO_VOTE` with the old/new digests and the index paths whose blobs changed.
5. Never carry provisional counterexamples from the old snapshot into a verdict on the new index. They may have been exactly what the concurrent restage fixed. Restart review from the new requested hash instead.

A useful drift readback compares each saved index blob with a fresh `git show :path`; staged `--stat` growth alone is supporting evidence, not identity proof. This gate prevents a correct review of revision A from being misreported as a vote on revision B.

## Verification sequence

```bash
python3 ~/.hermes/scripts/test_lark_oauth_guard.py
python3 ~/.hermes/scripts/test_lark_task_flow.py
python3 ~/.hermes/scripts/test_lark_task_reader.py
python3 ~/.hermes/scripts/lark_task_flow.py --health-check
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --status-only --no-open
# Only with an applicable one-shot or durable-scoped recovery grant:
python3 ~/.hermes/scripts/lark_oauth_guard.py --json --cleanup-stale --auto-authorize
# Only when Task reading is separately in scope:
python3 ~/.hermes/scripts/lark_task_flow.py --scope-mode only --summary
```

Interpretation rules:

- `auth_required` from an explicit status-only run is a healthy degraded-status result when no valid token exists: it proves recovery is needed while the negative assertions prove no recovery side effect was started. `planned_action=start_login` is intent metadata, not evidence that login ran.
- If an applicable `durable_scoped` recovery grant exists, route `auth_required` to the separate repair lane; do not weaken status-only semantics or ask repeatedly for the same grant.
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
