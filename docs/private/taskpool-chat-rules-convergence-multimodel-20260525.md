# Taskpool / Chat Rules Convergence — Multi-model Review

Date: 2026-05-25
Scope: Hermes taskpool execution workers launched with `hermes chat --ignore-rules` versus normal chat rule loading.

## Evidence

- Chat prompt stack: `agent/system_prompt.py::build_system_prompt_parts` loads identity, tool guidance, skills, context files, memory/profile unless skipped.
- CLI boundary: `cli.py` maps `--ignore-rules` to `skip_context_files=True` and `skip_memory=True`.
- Execution worker: `~/.hermes/scripts/agent_team_controller.py::delegate_to_worker` launches `hermes chat ... --ignore-rules`.
- Taskpool handoff: `~/.hermes/scripts/brain_task_orchestrator.py::render_*_handoff` injects Brain Overlay Contract and Project Profile but not a canonical user/Hermes rule digest.

## Model positions

### MiMo
- Keep worker isolation but add compact rules digest to execution-worker prompt.
- Do not use full memory injection.
- Keep `--ignore-rules` for smoke/consult style probes.

### DeepSeek
- Use a two-layer digest: global invariant rules plus task/review-specific rules.
- Inject via task metadata/prompt/env, scoped to the worker lifecycle.
- Test that execution workers receive the digest while review/smoke isolation remains clean.

### Gemini
- Preserve process/workdir/session isolation for multi-model workers.
- Treat `--ignore-rules` as prompt-layer cleanup only; it must never bypass tool/sandbox/proof gates.
- Add prompt/payload isolation tests and state pollution tests where possible.

### GPT-5.5
- Avoid a raw boolean spreading through runtime; prefer explicit runtime kind/scope eventually.
- `ignore_chat_rules` must never affect permission/tool/proof/lifecycle/multimodel truth gates.
- Distinguish task_worker execution from multimodel_review and smoke.

## Synthesis

Implement the smallest safe step now:
1. Add a compact canonical execution rules digest builder in repo code, sourced from stable local Hermes files when available:
   - `~/.hermes/AGENTS.md`
   - selected durable memory/profile files if readable later, but avoid full memory dump in this slice.
2. Inject the digest into execution-worker prompts in `agent_team_controller.py` before launching `hermes chat --ignore-rules`.
3. Do not inject it into consult_models / smoke / independent review paths in this slice.
4. Add tests proving:
   - digest contains the key execution-worker invariant and source text;
   - `delegate_to_worker` prompt contains the digest while command still uses `--ignore-rules`;
   - no broad CLI behavior is changed.

## Boundary for this pass

Stop before a broad CLI/runtime-kind migration. That needs a larger contract and could break existing `hermes chat --ignore-rules` workflows. The current pass should only close the unsafe execution-worker gap with targeted tests.
