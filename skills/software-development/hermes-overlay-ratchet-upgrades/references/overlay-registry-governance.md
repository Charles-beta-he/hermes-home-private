# Overlay registry governance for local Hermes enhancements

Use this when a local Hermes fork has accumulated durable custom behavior that must survive upstream pulls without relying on stale hardcoded verify lists.

## Registry shape

Keep a machine-readable registry at `~/.hermes/overlays/hermes-local-enhancements.json`.

Recommended per-overlay fields:
- `id`
- `name`
- `kind`
- `description`
- `families`
- `artifact_paths`
- `config_flags`
- `verification`
- `upstream_absorb_when`

This turns local drift into explicit assets instead of hidden vendor edits.

## Ratchet workflow learned in practice

1. Register each durable local enhancement in the overlay registry before tightening verification.
2. Make `openclaw_to_hermes_gap.py analyze --repo <repo>` merge overlay entries into the manifest index so local landed capability appears in the dashboard.
3. Make `post-update-check.py` validate overlay registry JSON, required keys, and artifact existence.
4. Make `hermes-pre-update-verify.sh` derive `py_compile` and focused `pytest` targets from the registry instead of hardcoding old patch-era file names.
5. Run the full gate:
   - `python3 ~/.hermes/scripts/post-update-check.py`
   - `sh ~/.hermes/scripts/hermes-pre-update-verify.sh`
   - `python3 ~/.hermes/scripts/openclaw_to_hermes_gap.py analyze --repo ~/.hermes/hermes-agent`

## Specific pitfall recovered this session

If `git diff --check` stops failing but pre-update verify still dies in `py_compile`, inspect the patched vendor/runtime file itself for indentation drift, not just trailing whitespace. In this session, `tools/mcp_tool.py` still had over-indented lines like:
- `result = await server.session.call_tool(...)`
- `result = await server.session.list_resources()`
- `result = await server.session.read_resource(...)`
- `result = await server.session.list_prompts()`
- `result = await server.session.get_prompt(...)`

A quick search for repeated over-indented `result = await server.session.` lines is a strong follow-up probe after whitespace cleanup.

## Verification target selection rule

Prefer registry-driven verification over stale bespoke file lists:
- `py_compile`: core runtime files + every registered Python artifact
- `pytest`: canonical integration tests plus any test files referenced by overlay `verification` commands

## Expected success signals

- `post-update-check.py` reports overlay registry OK
- pre-update verify exits 0
- focused pytest stays green
- gap dashboard verdict reflects landed local control-plane capability rather than `manifests: 0`
