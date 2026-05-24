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

### Claude Code
- The first-pass digest restores global safety invariants, but it does **not** by itself solve the user's main complaint: "I do not want to say the same requirement once in taskpool and again in chat."
- Root cause: `build_worker_context()` included title/id/project/boundary but did not include task-level requirement fields such as `body`, `acceptance_criteria`, `red_lines`, `non_goals`, `workflow_contract`, and `evidence_refs`.
- Correct interpretation of isolation: workers should not inherit chat persona, arbitrary memory, or unrelated conversation history; workers **must** inherit the concrete requirements already persisted into the task record.
- Minimal fix: add a deterministic task-spec snapshot section. Chat says it once, taskpool stores it once, worker receives a compact snapshot once.
- Keep caps/truncation on every injected field to avoid token blowup and prevent reintroducing full chat history through the back door.

## Synthesis

Implement the smallest safe step now:
1. Add a compact canonical execution rules digest builder in repo code, sourced from stable local Hermes files when available:
   - `~/.hermes/AGENTS.md`
   - selected durable memory/profile files if readable later, but avoid full memory dump in this slice.
2. Inject the digest into execution-worker prompts in `agent_team_controller.py` before launching `hermes chat --ignore-rules`.
3. Add a compact task-level requirements snapshot sourced from the task record:
   - `body` / `description`
   - `acceptance_criteria`
   - `red_lines`
   - `non_goals`
   - `evidence_refs`
   - `workflow_contract`
4. Do not inject these sections into consult_models / smoke / independent review paths in this slice unless explicitly scoped later.
5. Add tests proving:
   - digest contains the key execution-worker invariant and source text;
   - task-spec snapshot preserves user requirements already captured in the task;
   - `delegate_to_worker` prompt contains both digest and task-spec snapshot while command still uses `--ignore-rules`;
   - no broad CLI behavior is changed.

## Boundary for this pass

Stop before a broad CLI/runtime-kind migration. That needs a larger contract and could break existing `hermes chat --ignore-rules` workflows. The current pass should only close the unsafe execution-worker gap with targeted tests: global safety digest plus task-spec requirement inheritance.
