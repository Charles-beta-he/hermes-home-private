# Runtime prompt-gate landing notes

Use these notes when converting the Objective–Model–Path–Verification workflow from an optional skill into a runtime prompt gate.

## Durable pattern

- Keep the claim bounded: this is a prompt/runtime planning gate, not a learned world model or JEPA-like architecture change.
- Gate injection should be configurable, e.g. `agent.objective_model_path_guidance`, with a safe default only when the relevant tool/skill capability exists.
- Avoid injecting guidance when the runtime cannot actually load/use the required skill; otherwise the system prompt promises a capability that may not be executable.
- Tests should cover:
  - guidance appears when enabled and the skill/tool capability is available;
  - guidance is absent when disabled;
  - guidance is absent when required tool capability is unavailable;
  - generated prompt names the governing skill so future agents can load it explicitly.
- Smoke-test the built prompt, not just unit helpers: instantiate the agent or prompt builder with mocked tool definitions/config and assert the final system prompt contains the gate text and skill name.

## Verification evidence to collect

- Focused unit tests for the new gate behavior.
- A nearby regression subset for existing system-prompt/tool-use behavior.
- Syntax/compile checks for touched Python files.
- A final smoke probe showing `GATE_PRESENT=True` and `SKILL_NAME_PRESENT=True` or equivalent.

## Operational boundary

If the active conversation is running through the same gateway/process being modified, do not restart it casually inside the reply chain. Land code, tests, commits, and explain that the runtime gate takes effect after the next safe gateway restart unless the user explicitly approves interruption.
