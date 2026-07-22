# Codex Agent Loop Architecture Absorption

Status: class-pattern absorbed; current runtime audited; no runtime mutation.

Canonical SSOT:
- `/Users/charles/.hermes/docs/private/openai-codex-agent-loop-absorption-20260722.md`

Reusable class reference:
- `/Users/charles/.hermes/skills/autonomous-ai-agents/references/codex-agent-loop-vs-control-plane.md`

Exact scope:
- separate Codex-style inner loop from Hermes outer control plane;
- preserve exact-prefix/tool-schema/cache contracts;
- preserve per-tool sandbox ownership;
- distinguish main-loop `image_generate` auto selection from provider-native forced `image_generation`;
- make no provider, tool-choice, compression, deployment, or external-dispatch runtime change.

design_doc: The canonical SSOT and reusable reference above are the scoped design and rollback boundary for this architecture-only absorption.

gate_readback: Current-tree targeted verification via `.venv/bin/python -m pytest -q tests/agent/transports/test_codex_transport.py tests/plugins/image_gen/test_openai_codex_provider.py` returned `83 passed` in producer, independent-review, and fresh post-repair runs (latest `5.54s`); direct payload readback returned main Hermes `tool_choice='auto'` with `image_generate`, and nested OpenAI-Codex image-provider `mode='required'` with native `image_generation`. The first adversarial review passed the routing conclusion but blocked stale evidence paths/status; those four documentary blockers were repaired, and a fresh verifier vote remains required for certification. The local Agent OS route and pre-commit BrainConstraintGate remain authority-neutral and block unsupported side effects.

Rollback:
- revert the parent repository commit;
- revert the scoped child submodule commits if the profile pointer is also being rolled back.
