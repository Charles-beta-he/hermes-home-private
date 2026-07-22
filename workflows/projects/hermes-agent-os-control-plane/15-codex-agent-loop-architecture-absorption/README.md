# Codex Agent Loop Architecture Absorption

Status: class-pattern absorbed; current runtime audited; default-off image-intent shadow contract implemented locally; production enforcement blocked.

Canonical SSOT:
- `/Users/charles/.hermes/docs/private/openai-codex-agent-loop-absorption-20260722.md`

Reusable class reference:
- `/Users/charles/.hermes/skills/autonomous-ai-agents/references/codex-agent-loop-vs-control-plane.md`

Exact scope:
- separate Codex-style inner loop from Hermes outer control plane;
- preserve exact-prefix/tool-schema/cache contracts;
- preserve per-tool sandbox ownership;
- distinguish main-loop `image_generate` auto selection from provider-native forced `image_generation`;
- add a versioned, default-off, shadow-only image-output intent and active-backend capability observation contract;
- reject `enforce`, execute no tool, mutate no tool choice/messages/provider, and retain no raw user prompt in optional local evidence;
- block future production promotion on negative-intent generation, missing expected generation, capability contradiction, or contract-version drift;
- make no provider switch, paid generation, deployment, push, or external-dispatch change.

design_doc: The canonical SSOT and reusable reference above are the scoped design and rollback boundary for this architecture-only absorption.

gate_readback: Baseline transport/provider verification returned `83 passed in 1.53s`; direct payload readback preserved main Hermes `tool_choice='auto'` with `image_generate` and nested OpenAI-Codex `mode='required'` with native `image_generation`. The new default-off shadow slice was independently reviewed as exact-slice `PASS`, committed locally as child `632f613ca`, and passed fresh scoped regressions (`318 passed in 3.86s`; conductor/image-routing/verification-stop `184 passed in 1.71s`) plus Ruff, `py_compile`, and `git diff --check`. A broad agent run produced `5453 passed, 37 skipped, 127 failed`; therefore it is explicitly not a full-suite PASS. Its failures were on pre-existing credential/keychain, cache/global-state, and app-session surfaces outside this child slice, with representative neighbors passing in clean isolated reruns. Certification remains limited to the default-off shadow/observation contract and audited current image path; it does not authorize enforce mode, production configuration, paid generation, push, deployment, or external dispatch. The local Agent OS route and pre-commit BrainConstraintGate remain authority-neutral and block unsupported side effects.

Rollback:
- revert the parent repository commit;
- revert child runtime commit `632f613ca` if the profile pointer is also being rolled back;
- keep `image_intent_routing.enabled=false` or set `kill_switch=true` during any investigation.
