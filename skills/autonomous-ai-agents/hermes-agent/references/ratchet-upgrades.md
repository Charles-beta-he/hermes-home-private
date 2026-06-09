# Ratchet upgrades for Hermes local enhancements

Use this when Hermes tracks upstream while carrying durable local enhancements (task router, token compressor, result spiller, control-plane hardening, provider reliability patches, etc.) and the goal is to keep upstream velocity without losing local gains.

## Core model

Treat Hermes maintenance as four layers:

1. Upstream baseline
   - Keep `origin/main` as the source of truth for vendor behavior.
   - Measure every local enhancement against upstream, not against memory.
2. Local overlay registry
   - Each enhancement is a named overlay with purpose, touched files, enablement mode, tests, rollback, and upstream absorption conditions.
   - Prefer plugin/hook/module overlays over large inline edits to `run_agent.py` or other vendor hot paths.
3. Automatic replay / drift detection
   - Use `~/.hermes/scripts/post-update-check.py` as the replay gate after `hermes update`.
   - Clean apply -> auto replay; semantic conflict or fuzzy apply -> fail closed and require review.
4. Multi-model certification
   - One model extracts upstream diff impact, one does architecture absorption judgement, one does low-cost adversarial review, and a final arbiter issues PASS/FAIL.

## Recommended model roles

- Mechanical diff / impact map: Codex or GPT-5.5
- Architecture absorption / redesign judgement: Claude
- Low-cost contradiction scan: MiMo or DeepSeek
- Final truth gate: highest-trust arbiter (often Claude)

Required outputs:
- impacted overlays
- touched files
- textual vs semantic conflicts
- keep / absorb / redesign decision
- missing tests and rollback notes

## Upgrade workflow

1. Pre-update hygiene gate
   - Run `sh ~/.hermes/scripts/hermes-pre-update-verify.sh`.
   - Fail the update if `git diff --check`, syntax checks, or minimal tests fail.
   - Do not update with a dirty tree; even trailing whitespace should block the ratchet.
2. Capture upstream delta
   - `git fetch origin`
   - Compare `origin/main` against local HEAD and against overlay touchpoints.
3. Build overlay impact map
   - For each overlay, record touchpoints, invariants, tests, default mode, and absorption conditions.
4. Run multi-model review
   - Separate mechanical diffing from architecture judgement.
   - Force a contrary review to catch false "already absorbed" claims.
5. Replay overlays
   - Auto-apply only clean, high-confidence overlays.
   - If upstream now covers the capability, retire the overlay instead of replaying it.
6. Verify
   - Static: `py_compile`, imports, config/schema checks.
   - Tests: overlay-local tests plus touched upstream tests.
   - Behavior: provider smoke tests, CLI flow, routing/transport checks.
7. Ratchet state forward
   - Record overlay status (`kept`, `absorbed`, `redesigned`, `retired`) and verified upstream commit.

## Overlay manifest fields

Each overlay should have a manifest containing at least:
- `id`
- `description`
- `owner`
- `upstream_touchpoints`
- `local_touchpoints`
- `default_mode`
- `apply_strategy` (`patch`, `hook`, `plugin`, `copy`)
- `validation` (compile, pytest targets, smoke commands)
- `absorb_when`
- `rollback_strategy`

## Practical guidance from this session

- The real risk was not just dependency drift but unmanaged local divergence: untracked `agent/codex_circuit_breaker.py`, modified `run_agent.py`, and several other local enhancements while the repo was also behind upstream.
- `pyproject.toml` and `uv.lock` can drift independently of runtime behavior; treat dependency-governance drift separately from runtime/provider failures.
- Provider transport failures and local protection overlays must be diagnosed as two distinct layers. Example: a codex circuit breaker may be local-only, while the actual trigger is upstream transport/API connection instability.
- Current local safety net already exists: `~/.hermes/scripts/hermes-pre-update-verify.sh`, `~/.hermes/scripts/post-update-check.py`, and `~/.hermes/scripts/reliability-update.py`. The next step is to make them overlay-registry-driven instead of relying on ad-hoc hardcoded patch knowledge.

## Pitfalls

- Do not let local enhancements remain as anonymous edits in vendor files; they become impossible to classify as keep/remove/absorb during upgrades.
- Do not treat a successful patch reapply as proof of semantic correctness.
- Do not confuse system Python package versions with the Hermes venv that the CLI actually uses.
- Do not mix upstream sync, dependency lock cleanup, provider debugging, and overlay redesign into one unstructured update step.

## Verification checklist

- `which hermes` and shebang point to the expected venv.
- Runtime package versions are checked inside the Hermes venv, not just system Python.
- Local-vs-upstream diff for touched files is reviewed before replay.
- Overlay-specific tests exist for every durable local enhancement; if an enhancement lacks tests, add those before the next ratchet cycle.
