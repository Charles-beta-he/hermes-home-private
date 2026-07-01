# Gemini CLI / OAuth provider wiring

Extracted from `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-agent/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Gemini CLI / OAuth provider wiring

When the user asks to connect Gemini to Hermes because they already subscribed in the browser, do not assume a fresh login is required.

1. Check whether Hermes already has a reusable Gemini OAuth session before changing config.
   - Run `hermes doctor` and look for `Google Gemini OAuth (logged in ...)`.
   - If already logged in, prefer wiring the existing `google-gemini-cli` provider instead of forcing a new auth flow.
2. Verify the provider with a one-shot query before editing config.
   - Example: `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview -q '只回复: GEMINI_OK'`
3. If the user did not explicitly ask to replace their main model, preserve the current primary provider and attach Gemini as a fallback first.
   - Use top-level `fallback_providers` in `~/.hermes/config.yaml`.
   - Example entry:
     ```yaml
     fallback_providers:
       - provider: google-gemini-cli
         model: gemini-3.1-pro-preview
     ```
4. Verify the wiring after config change.
   - `hermes fallback list`
   - another direct `hermes chat --provider google-gemini-cli ... -q ...` probe
5. Report the distinction clearly:
   - `google-gemini-cli` = Gemini CLI / Cloud Code Assist OAuth path
   - `gemini` = Google AI Studio API-key provider

### Multi-model integration points for Gemini OAuth

If Gemini should participate in Hermes multi-model orchestration (not just direct `/model` switching), wire every layer that resolves models by pricing/quorum metadata:

1. `/model` picker: `hermes_cli/model_switch.py` must ask `hermes_cli.auth.get_auth_status()` for `oauth_external` / `external_process` providers because `google-gemini-cli` login state lives in `~/.hermes/auth/google_oauth.json`, not generic `auth.json` or credential pool.
2. Provider display: `hermes_cli/providers.py` should label `google-gemini-cli` as `Google Gemini (OAuth)` so picker output is user-readable.
3. Main/fallback config: preserve current primary unless explicitly changed; set Gemini under top-level `fallback_providers`.
4. Pricing/router metadata: add canonical Gemini OAuth models such as `gemini-3.1-pro-preview` and `gemini-3-flash-preview` to `pricing.models` with `provider: google-gemini-cli` and candidate groups (`chat`, `codegen`, `reviewer`, optionally `hard_reasoning`/`arbiter`).
5. Multi-brain quorum: add the canonical Gemini model to `~/.hermes/config/quorum.yaml` tiers as an additional planner while keeping `min_quorum` below total planners so expired OAuth/capacity throttle does not block certification. If taskpool ratification has a hardcoded core panel (e.g. `REQUIRED_RATIFICATION_MODELS`), do **not** remove Gemini from quorum to silence `unexpected_*`; model it as an optional/allowed ratification participant and set T2/T3 `quorum` high enough to actually include it.
6. Script invocation: `~/.hermes/scripts/consult_models.py`, `~/.hermes/scripts/cross-patch.py`, and `~/.hermes/scripts/ensemble-vote.py` must treat `google-gemini-cli` as a supported Hermes provider so they pass `--provider google-gemini-cli` to `hermes chat`. Prefer augmenting from `hermes_cli.providers.HERMES_OVERLAYS` with a static fallback to avoid hardcoded-list drift.
7. Smart routing / verification: add Gemini models to `smart_model_routing.candidate_models` and, where useful, `verification.tiers.*.reviewers` rather than making Gemini the default producer.
8. Verification commands:
   - `./venv/bin/python -m pytest tests/hermes_cli/test_gemini_oauth_in_model_picker.py tests/agent/test_gemini_fast_fallback.py`
   - `./venv/bin/python -m py_compile ~/.hermes/scripts/consult_models.py ~/.hermes/scripts/cross-patch.py ~/.hermes/scripts/ensemble-vote.py`
   - `python3 ~/.hermes/scripts/consult_models.py status`
   - `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview -q '只回复: GEMINI_OK' --quiet --max-turns 1 --ignore-rules`
   - `python3 ~/.hermes/scripts/model-router.py probe`
9. If the user says only “测试一下” after Gemini wiring, run the concise smoke-test triad instead of re-auditing everything:
   - Direct OAuth call: `hermes chat --provider google-gemini-cli -m gemini-3.1-pro-preview -q '只回复: GEMINI_OK' --quiet --max-turns 1 --ignore-rules`
   - Router probe: `python3 ~/.hermes/scripts/model-router.py probe`
   - Focused regression: `./venv/bin/python -m pytest tests/hermes_cli/test_gemini_oauth_in_model_picker.py tests/agent/test_gemini_fast_fallback.py`
- For multi-provider power users, switching the default model to Gemini without being asked can unnecessarily displace an existing primary workflow. Safer default: keep the current main provider and add Gemini as fallback unless the user explicitly wants Gemini as primary.
- `google-gemini-cli` and `gemini` are different Hermes providers; do not describe the OAuth path as AI Studio API-key setup.
- `anthropic` and `claude-code` are different Claude entitlement paths. For Claude Max / Claude Code OAuth users, canonical Claude models should resolve to runtime provider `claude-code` when the `claude` CLI is available; do not treat `hermes chat --provider anthropic ...` extra-usage errors as proof that Claude Code / Claude Max is offline or exhausted.
