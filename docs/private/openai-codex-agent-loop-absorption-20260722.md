# OpenAI Codex Agent Loop Absorption for Hermes

```yaml
schema: hermes_reference_review_v1
id: openai-codex-agent-loop-20260722
source_media: https://openai.com/index/unrolling-the-codex-agent-loop/
source_repo: https://github.com/openai/codex
project: hermes-agent
status: shadow-contract-implemented-default-off
risk: D2
review_date: 2026-07-22
```

## Goal

Absorb the durable engineering contracts from OpenAI's “Unrolling the Codex agent loop” into Hermes without collapsing Hermes's control-plane scope into a coding-only harness. Resolve exactly how GPT image requests traverse Hermes `image_generate` and provider-native image generation.

## Non-goals

- Do not copy Codex implementation wholesale.
- Do not grant a coding worker lifecycle, deployment, external-write, or notification authority.
- Do not force `image_generate` for educational or analytical mentions of image generation.
- Do not change runtime behavior without a failing contract and evidence that the current behavior violates it.
- No push, deploy, external dispatch, credential entry, or production mutation.

## Spec Brief: image-output intent shadow contract

### Goal

Add a versioned, capability-driven image-output intent contract that can observe and compare each turn without changing current `tool_choice="auto"`, executing tools, or claiming production authority.

### Boundaries and non-goals

- Runtime default remains disabled.
- `mode: enforce` is rejected, not silently accepted.
- No provider switch, paid generation, deployment, push, external dispatch, or credential entry.
- The deterministic classifier is a conservative shadow evidence adapter, not the global semantic authority.
- Raw user prompts are not persisted; receipts contain a SHA-256 digest, length, decision, capability projection, and alignment.

### Business rules

1. Intent values are versioned as `generate_asset`, `edit_asset`, `analyze_asset`, `prompt_only`, `explain_only`, and `ambiguous`.
2. Negative intents win over generation cues; ambiguous requests preserve the existing automatic model path.
3. Provider capabilities are projected from the existing `modalities` and `max_reference_images` contract rather than hardcoded by provider name.
4. Artifact-required intents are eligible only when `image_generate` is available and the active provider advertises the required capability.
5. Every route and finalized receipt keeps `runtime_mutation_authorized: false`.
6. Negative-intent generation, missing expected generation, capability contradictions, or schema-version drift produce `review_required: true` and `production_gate: block` only for future promotion; they do not alter the current response.
7. `kill_switch` disables observation before provider resolution.

### Evidence requirements

- RED/GREEN unit evidence for classifier precedence, capability normalization, provider/tool blockers, default-off, kill switch, unsupported enforce mode, local private JSONL readback, conflict escalation, version drift, and turn-result projection.
- Existing Codex transport and OpenAI-Codex provider tests must remain green.
- Independent review must distinguish default-off shadow implementation from production enforcement certification.

## Source facts

1. The Codex inner loop distinguishes a user turn from repeated model/tool iterations.
2. Model behavior is a function of the harness, tools, instructions, and context policy, not the model alone.
3. Exact-prefix stability affects prompt-cache reuse; tool schemas and ordering are part of that prefix.
4. Codex shell sandboxing does not automatically govern MCP tools.
5. Provider-native `/responses/compact` can preserve model-specific state that a portable text summary cannot.

Canonical class-level extraction:

- `~/.hermes/skills/autonomous-ai-agents/references/codex-agent-loop-vs-control-plane.md`

## Current Hermes evidence

### Already aligned

- `agent/transports/codex.py::_content_cache_key` content-addresses the stable instructions + sorted tool schemas instead of volatile per-fire session IDs.
- `agent/transports/codex.py::ResponsesApiTransport.build_kwargs` sends the Responses API tools with `tool_choice="auto"` and enables parallel tool calls.
- `agent/context_compressor.py` preserves tool-call/result atomicity, supports deterministic degraded reconstruction, and aborts on known model-capability/auth/network failure categories instead of silently discarding all middle history.
- Hermes already separates inner-loop execution from outer session, memory, skill, delegation, cron, gateway, taskpool, and evidence controls.

### Remaining risks

- Generic summary failures may still take a deterministic degraded compression path unless `compression.abort_on_summary_failure` is enabled. This is explicit and observable, not silent, but needs task-level policy rather than a universal forced default.
- Multi-provider fallback can break prefix-cache locality and can change compaction/tool semantics.
- Broad tool and MCP surfaces require per-tool sandbox/approval ownership; host-level sandbox assumptions must not be projected onto remote tools.
- Main-loop tool selection remains probabilistic under `tool_choice="auto"`; concrete artifact requests rely on the model following the tool contract and Hermes execution policy.

## GPT image-generation routing contract

There are two tool-selection layers:

```text
concrete image request
  -> main GPT/Hermes loop sees `image_generate`
     (`tool_choice="auto"`; model selects, not globally forced)
  -> Hermes dispatches `image_generate` to configured image provider
  -> provider generates/edits the image
```

If the configured provider is Hermes `openai-codex`, a second nested Responses request is constructed by:

- `plugins/image_gen/openai-codex/__init__.py::_build_responses_payload`

That request declares OpenAI's native `{"type": "image_generation"}` tool and forces it with:

```json
{
  "type": "allowed_tools",
  "mode": "required",
  "tools": [{"type": "image_generation"}]
}
```

Therefore:

- GPT as the main chat model does not by itself imply OpenAI image generation.
- The main Hermes call normally chooses `image_generate` for an actual image artifact request, but its transport uses automatic tool choice rather than a hardcoded image-intent router.
- Once `image_generate` is selected, dispatch to the configured backend is deterministic.
- Only the `openai-codex` image backend's nested native `image_generation` call is explicitly required/forced.
- In the current session, the exposed tool reports FAL/FLUX as the active image backend, so an image request here would not default to OpenAI's native Image Generator merely because the main model is GPT.

## Decisions

1. Keep Hermes as the outer control plane and use Codex-style runtimes as constrained workers/executors.
2. Preserve `tool_choice="auto"` in the general main loop; global forcing would misroute discussion, prompt-writing, comparison, and analysis requests.
3. Preserve deterministic forcing inside a provider-specific image generation request, where intent is already resolved.
4. Do not flip compression policy globally in this absorption pass: current code has explicit degraded reconstruction and category-specific fail-closed behavior; a default flip needs workload evidence and dedicated regression tests.
5. Absorb the architecture and routing contracts into the class skill; avoid a speculative runtime rewrite where current code already implements the durable mechanisms.

## Negative cases

- “Explain how image generation works” must not necessarily create an image.
- “Write me a prompt for an image model” must not necessarily invoke `image_generate` unless the user also asks for the artifact.
- Missing/disabled `image_generate` must not be described as successful image generation.
- A GPT main model with a FAL image provider must not be reported as OpenAI native image generation.
- An MCP tool must not be described as protected by the local terminal sandbox without tool-specific evidence.
- A compression summary failure must not be reported as lossless compaction.

## Default-off shadow implementation

Implemented locally in the private Hermes tree:

- `agent/image_intent_routing.py` — versioned intent, provider capability, route and alignment contracts.
- `agent/conversation_loop.py::_run_image_intent_shadow_router` — once-per-turn default-off observer; it calls the same active image-backend capability resolver used by the dynamic `image_generate` schema only after the feature and shadow mode gates pass.
- `agent/turn_finalizer.py::finalize_turn` — returns finalized shadow alignment in `result.image_intent_shadow` without changing the response.
- `hermes_cli/config.py::DEFAULT_CONFIG.image_intent_routing` — disabled by default; supports `shadow`, `kill_switch`, optional local JSONL, and rejects `enforce`.
- `tests/agent/test_image_intent_routing.py` plus the turn-finalizer regression — contract, negative, drift, conflict and readback evidence.

Configuration surface:

```yaml
image_intent_routing:
  enabled: false
  mode: shadow
  kill_switch: false
  ledger_enabled: false
  ledger_path: ""
```

The current implementation has no path that authorizes runtime mutation. Enabling shadow changes only local observability/readback. Production enforcement remains a separately gated, uncertified boundary.

## Acceptance and evidence

- [x] Canonical article and source repository resolved.
- [x] Turn/iteration, model/harness, cache, compaction, and sandbox boundaries extracted.
- [x] Current Hermes transport and compressor paths inspected.
- [x] Main-loop automatic image-tool selection separated from provider-native forced image generation.
- [x] Class-level reusable reference created and linked from the autonomous-agent umbrella skill.
- [x] Independent adversarial review completed in two slices: the pre-repair review returned `BLOCK` for four documentary issues while passing the routing conclusion; after commits `e6769c40a`, `2002f22f5`, and `12205bd35`, a fresh isolated-context verifier returned `PASS` and reran all 83 targeted tests successfully. This certifies only class-pattern absorption plus the audited current runtime contract; it is not multi-model, deployment, or paid-image-generation certification.
- [x] Targeted tests for Codex cache-key behavior and OpenAI-Codex image-provider request shape passed in producer, repair, and independent-verifier runs; latest baseline verifier result: `83 passed in 1.53s`.
- [x] Default-off shadow contract tests cover conservative negative precedence, capability projection, tool/provider blockers, kill switch, rejected enforce mode, stale-state cleanup, private JSONL without raw prompts, existing-file permission tightening, schema drift, conflict promotion block, and turn-result readback.
- [x] The shadow helper uses `load_config_readonly()` so enablement and kill switch follow the profile-scoped hot config without copying or caching a stale emergency switch.
- [x] The shadow capability projection reuses `tools.image_generation_tool.get_active_image_capabilities()`, the resolver that mirrors actual plugin/FAL dispatch, rather than inferring the image backend from the main chat model/provider.
- [x] Exact-slice independent Claude Sonnet review returned `PASS` with no security, logic, or specification blockers. It certified only the default-off shadow/observation boundary. Two non-blocking notes remain fail-safe: outer mode parsing does not trim surrounding whitespace before capability resolution, and directory chmod is best-effort while the ledger file itself is force-read back by code/tests as `0600`.
- [x] The runtime slice was committed locally as `632f613ca` (`feat: add default-off image intent shadow contract`); no push, deployment, production enablement, or paid generation was performed.
- [x] Fresh scoped regression after final hardening: `318 passed in 3.86s`; conductor/image-routing/verification-stop integration slice: `184 passed in 1.71s`; Ruff, `py_compile`, and `git diff --check` passed.
- [x] A broad `tests/agent` run reached `5453 passed, 37 skipped, 127 failed`. The broad run is not recorded as a PASS. Failures were distributed across pre-existing credential/keychain, cache/global-state, and app-session test surfaces outside this slice; representative changed-path neighbors passed in fresh isolated processes (`49 passed` for verification-stop and `63 passed` for Codex app-server session). This limits certification to the explicit scoped commands, not the whole agent suite.

## Fresh verification evidence

```text
main Responses transport:
{'tool_choice': 'auto', 'tools': ['image_generate'], 'cache_key_prefix': 'pck_'}

openai-codex image provider:
{'tool_choice': {'type': 'allowed_tools', 'mode': 'required',
                 'tools': [{'type': 'image_generation'}]},
 'native_tool': 'image_generation', 'native_model': 'gpt-image-2'}
```

The first attempted test command used the system Python environment and failed because `pytest` was not on `PATH`; verification was rerun with the project `.venv/bin/python` and passed.

## Evidence commands

```bash
(
  cd /Users/charles/.hermes/hermes-agent
  .venv/bin/python -m pytest -q \
    tests/agent/transports/test_codex_transport.py \
    tests/plugins/image_gen/test_openai_codex_provider.py

  .venv/bin/python -m pytest -q \
    tests/agent/test_image_intent_routing.py \
    tests/agent/test_turn_finalizer_cleanup_guard.py \
    tests/agent/test_turn_finalizer_interrupt_alternation.py \
    tests/agent/test_turn_finalizer_final_response_persistence.py \
    tests/tools/test_image_generation_image_to_image.py \
    tests/agent/test_image_gen_registry.py \
    tests/agent/transports/test_codex_transport.py \
    tests/plugins/image_gen/test_openai_codex_provider.py \
    tests/hermes_cli/test_config.py \
    tests/hermes_cli/test_config_validation.py \
    tests/hermes_cli/test_config_drift.py

  .venv/bin/python -m pytest -q \
    tests/agent/test_conductor_runtime.py \
    tests/agent/test_image_routing.py \
    tests/agent/test_verification_stop.py

  git show --check --stat --oneline 632f613ca
)

(
  cd /Users/charles/.hermes
  git show --check --stat --oneline 2002f22f5
  git status --short -- \
    docs/private/openai-codex-agent-loop-absorption-20260722.md \
    skills/autonomous-ai-agents/SKILL.md \
    skills/autonomous-ai-agents/references/codex-agent-loop-vs-control-plane.md \
    workflows/projects/hermes-agent-os-control-plane/15-codex-agent-loop-architecture-absorption/README.md
)
```

## Converge boundary

The class-pattern absorption and default-off shadow contract are locally implemented when code, config, negative cases, conflict/version gates, result readback, regression tests, and an independent review agree. This still does not certify `mode: enforce`, universal semantic classification, production rollout, real paid generation, provider credential/billing availability, cross-version behavior not represented by the versioned capability contract, push, deployment, or external dispatch. Crossing any of those boundaries requires a new exact authorization and fresh evidence.
