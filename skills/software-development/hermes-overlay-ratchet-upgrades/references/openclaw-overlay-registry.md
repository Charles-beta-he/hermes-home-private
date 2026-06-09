# Overlay-driven ratchet upgrades for Hermes local enhancements

Use this when a Hermes checkout carries local control-plane or provider patches that must survive upstream pulls without staying as anonymous vendor drift.

## Durable pattern

1. Register every local enhancement in a single overlay registry file, e.g.:
   `~/.hermes/overlays/hermes-local-enhancements.json`
2. Each overlay entry should carry:
   - `id`, `name`, `kind`
   - `description`
   - `families`
   - `artifact_paths`
   - `config_flags`
   - `verification`
   - `upstream_absorb_when`
3. Treat the registry as the canonical source for upgrade governance; do not leave important local behavior only as untracked code edits.

## Concrete Hermes landing from this session

The following local enhancements were suitable registry entries:
- `openclaw-control-plane`
- `task-router-activation-hints`
- `prompt-scoped-policy-context`
- `memory-write-gate`
- `token-compressor-path`
- `result-spiller-path`
- `codex-circuit-breaker-local`

## Required tooling integrations

### 1) Gap analyzer must be overlay-aware
`openclaw_to_hermes_gap.py analyze` originally only counted `openclaw.plugin.json` manifests. Extend manifest indexing so local overlay registry entries also appear as manifest-first assets. This prevents false conclusions like `manifests: 0` when the repo actually carries substantial local control-plane landings.

### 2) post-update-check must validate registry and artifacts
Add an overlay check that:
- verifies the registry file exists
- parses JSON
- ensures at least one overlay is registered
- checks every `artifact_paths` target exists under the Hermes repo

This turns post-update-check into an overlay-aware governance gate instead of a pure hardcoded patch detector.

### 3) pre-update verify must derive targets from current overlays
Do not hardcode stale compile/test targets such as retired files (`agent/model_health.py`, `agent/task_classifier.py`).
Instead:
- keep a small always-check runtime core
- extend `py_compile` targets from overlay `artifact_paths`
- extend pytest targets from overlay `verification` commands

This keeps ratchet verification aligned with the currently registered local surface area.

## Important pitfall

If pre-update verification still fails after cleaning obvious whitespace drift, inspect the supposedly protected runtime files for deeper pre-existing syntax/indentation damage. In this session, removing trailing whitespace from `tools/mcp_tool.py` exposed that the file still had a deeper indentation problem elsewhere; the blocker was not the new overlay work itself.

## Verification pattern

Use all three layers:
1. focused pytest for the landed local control-plane tests
2. `python3 ~/.hermes/scripts/openclaw_to_hermes_gap.py analyze --repo ~/.hermes/hermes-agent`
3. `python3 ~/.hermes/scripts/post-update-check.py`
4. `sh ~/.hermes/scripts/hermes-pre-update-verify.sh`

Expected direction of travel:
- gap analysis should count local overlays as manifests
- post-update-check should report overlay registry OK
- pre-update verify should fail only on real current code problems, not stale file references
