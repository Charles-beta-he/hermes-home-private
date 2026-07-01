# Merge-regression debugging patterns after large upstream upgrades

Applicability: use during post-merge debugging when tests hang or fail after conflict resolution in a Python/async/tooling-heavy codebase. These are reusable symptom-to-root-cause patterns; do not store specific branch names or session progress here.

Anti-conditions:
- Do not apply these as blanket claims that a feature is broken; reproduce the failing test and inspect the active code first.
- Do not encode missing local dependencies or invalid credentials as durable failures.

## Pattern: duplicate async call + non-reentrant lock

Symptom:
- A focused async/tool test hangs under `pytest-timeout`.
- Stack shows a call wrapper waiting on an event loop or selector, often inside a helper that already serializes access with an `asyncio.Lock`.

Investigation:
1. Run the single failing test with `--timeout=<n> --timeout-method=thread -x` to capture the stack.
2. Inspect the wrapper and the lower helper. Look for conflict-resolution artifacts where both sides of the merge were kept:
   - same RPC/tool call executed once before a lock and again inside the lock;
   - helper already acquires `server._rpc_lock`, while the callback re-enters the same lock;
   - duplicated context-setting blocks.
3. Fix by keeping exactly one call and exactly one lock owner. If the helper owns serialization, the callback body should be lock-free and only publish per-call context in a `try/finally`.
4. Add/keep a regression test that asserts the tool is called once and the test completes under timeout.

## Pattern: test helper misses new environment preflight

Symptom:
- Unit tests for service management fail on platforms that do not support the service manager, before reaching the behavior under test.

Investigation/fix:
1. Determine whether the test is about preflight behavior or about downstream command sequencing.
2. For downstream command-sequencing tests, mock the newly introduced preflight seam explicitly.
3. For preflight tests, keep real preflight coverage in narrow tests.
4. For launch/service-definition refresh tests, patch generated service content to avoid real temporary-home guardrails unless that guardrail is the subject of the test.

## Pattern: stale import paths after module moves

Symptom:
- Monkeypatch fails with `ModuleNotFoundError` for a path that existed before the merge.

Fix:
- Patch the active implementation module path, not the old compatibility path.
- Search imports/usages before changing production code; often only tests retained the old path.

## Pattern: async test accidentally nested/overwritten

Symptom:
- Pytest reports `async def functions are not natively supported` even though pytest-asyncio is installed and nearby async tests run.

Root cause:
- A merge left two `async def test_*` declarations adjacent, so the second test lost its decorator or became nested under the first function.

Fix:
- Remove the stale/empty duplicate declaration and ensure each async test has its own decorator.

## Pattern: degradation flag semantics after reconnect

Symptom:
- Tests disagree on whether a send-path degraded flag should clear after polling reconnect.

Root-cause model:
- Polling recovery and send-path recovery can be separate surfaces. A successful polling restart is not always proof that the send path can deliver; a bounded Bot API probe is stronger evidence.

Preferred invariant:
- Reconnect failed -> keep degraded.
- Reconnect succeeded + send-path probe succeeded -> clear degraded.
- Reconnect succeeded + send-path probe failed -> keep degraded so callers can fall back instead of silently dropping messages.
- Late heartbeat/probe can clear degraded after recovery.

## Verification checklist

- Reproduce the smallest failing test before editing.
- Patch the root cause, not the assertion only.
- Re-run the exact failing test, then the focused domain file/suite.
- Run `git diff --check` and targeted `py_compile` for edited Python files.
- Watch for unawaited coroutine warnings after mocking `asyncio.ensure_future`; close suppressed coroutine objects or return a task-like fake with callbacks.
