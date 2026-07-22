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

gate_readback: Baseline transport/provider verification returned `83 passed in 1.53s`; direct payload readback preserved main Hermes `tool_choice='auto'` with `image_generate` and nested OpenAI-Codex `mode='required'` with native `image_generation`. The initial default-off shadow slice was committed as child `632f613ca`. Later adversarial reviews reopened certification and found strict-boolean, ledger safety/privacy, config-failure readback, stale-turn identity, nested-schema, unavailable-provider fallback, and source-inspection blockers. These were repaired and committed as child `57cb785a9bc41fd4117bd369f60b456e07d687ce`. A final independent verifier bound `PASS` to binary diff SHA-256 `90c34f313cae05d7f69e793cc1ab62e5f1b8576f5fa953315f3bc3e949a776df` with `63 passed`, `35 passed`, and clean `git diff --check`; producer evidence additionally recorded `511 passed`, Ruff, `py_compile`, and post-commit `98 passed` plus clean `git show --check`. A broad agent run previously produced `5453 passed, 37 skipped, 127 failed`; therefore it remains explicitly not a full-suite PASS. Certification is limited to the default-off, shadow-only observation/readback and ledger boundary. It does not authorize enforce mode, production configuration, real provider credentials, paid generation, push, deployment, or external dispatch. The local Agent OS route and pre-commit BrainConstraintGate remain authority-neutral and block unsupported side effects.

Rollback:
- revert the parent repository commit;
- revert child hardening commit `57cb785a9` first, then revert initial runtime commit `632f613ca` if the profile pointer is also being rolled back;
- keep `image_intent_routing.enabled=false` or set `kill_switch=true` during any investigation.
