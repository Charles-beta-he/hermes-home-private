# Post-update ratchet replay pattern

Use this when Hermes is already on latest `origin/main`, an update-created stash exists, and `post-update-check.py` reports a small number of local overlay drifts.

## Pattern

1. Treat the stash as audit material first, not something to `git stash pop` blindly.
   - Compare `stash@{0}` against current `HEAD`.
   - Separate tracked overlays still needed in worktree from historical stash-only changes already superseded by upstream.

2. Prefer replaying only the still-relevant overlays.
   - Keep already-landed tracked local overlays in worktree if they still pass verification.
   - Re-apply only the specific drifts surfaced by `post-update-check.py`.

3. Be cautious with helper patch scripts.
   - If a replay helper script does broad regex replacement, inspect the resulting diff immediately.
   - In this session, `apply-mcp-timeout-patch.py` produced malformed indentation in `tools/mcp_tool.py`; the durable lesson is to verify helper-script output before trusting it.
   - If the helper drifted, repair the patch manually and keep the centralization pattern, not the broken textual transform.

4. For MCP timeout drift, the stable intent is:
   - define `_MCP_SAFETY_NET_SEC`
   - centralize RPC locking in `_mcp_rpc_call`
   - update each MCP operation to go through `_run_on_mcp_loop(lambda: _mcp_rpc_call(server, _call), timeout=timeout_sec)`
   - then verify with the Hermes venv Python, not arbitrary system Python

5. For hook-registry trust-boundary drift, fix the trust boundary instead of suppressing the check.
   - If a shell hook points outside the allowlist, move or mirror the hook into `~/.hermes/scripts/` or `~/.hermes/agent-hooks/`.
   - Update both `~/.hermes/hooks/registry.yaml` and the active config(s) that still reference the out-of-policy path.
   - If a profile mirror exists, sync that config too so the next restore/export does not resurrect the drift.

## Verification stack

Run these after replaying overlays:

1. `./venv/bin/python -m py_compile ...` for each changed Python file
2. `python3 ~/.hermes/scripts/hermes_hook_registry_selfcheck.py`
3. `python3 ~/.hermes/scripts/post-update-check.py`
4. Targeted `./venv/bin/pytest -q ...` covering the touched overlay surfaces

## Session example

This pattern was used successfully when:
- repo was already at `HEAD == origin/main`
- stash was `hermes-update-autostash-*`
- remaining real overlays were only a small tracked subset
- drift fixes needed were `mcp_rpc_timeout_guard` and `hook_registry_selfcheck`
- targeted verification passed after replay (`327 passed, 1 skipped` in the selected test slice)
