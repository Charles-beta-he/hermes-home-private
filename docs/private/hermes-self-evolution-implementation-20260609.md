# Hermes self-evolution implementation SSOT — 2026-06-09

schema: hermes_self_optimization_implementation_v1
id: hermes-self-evolution-implementation-20260609
parent_ssot: /Users/charles/.hermes/docs/private/hermes-self-evolution-roadmap-20260609.md
status: implemented_verified_committed

## User authorization

User approved the roadmap and then authorized: "认可，推进至全盘落地".

## Objective & cost

Objective:
- Move the objective-model-path-verification process from passive skill-only guidance into executable Hermes behavior with tests.
- Keep the first implementation low-risk, default-safe, and evidence-backed.

Cost function:
- Minimize blast radius in the main conversation loop.
- Avoid over-triggering verbose planning for simple tasks.
- Avoid hidden mutation of taskpool/config/runtime state.
- Preserve existing user/developer instruction precedence.
- Prefer deterministic, unit-testable classification over LLM-only hidden behavior.

Hard constraints:
- Source code changes must be scoped to `/Users/charles/.hermes/hermes-agent` and committed there.
- Do not alter user config, provider settings, credentials, cron jobs, or live taskpool state in this implementation.
- Do not auto-enqueue taskpool work; leave integration candidates in this SSOT unless implemented and tested.
- Any runtime behavior must be opt-out or narrowly triggered and must not replace tool execution/verification.

## Situation model

Relevant artifacts:
- Process skill already landed: `/Users/charles/.hermes/skills/software-development/objective-model-path-verification/SKILL.md`.
- Parent roadmap: `/Users/charles/.hermes/docs/private/hermes-self-evolution-roadmap-20260609.md`.
- Hermes source checkout: `/Users/charles/.hermes/hermes-agent`.

Candidate implementation surfaces to inspect:
- Prompt assembly / system message construction.
- Skill loading and mandatory skill reminders.
- A deterministic helper module plus focused tests.
- Taskpool intake/closeout templates, if safe.

## Candidate paths

### Path A — Prompt-only skill exists, no runtime code
Outcome: safe but incomplete; user explicitly asked for full landing.
Decision: rejected.

### Path B — Universal config-gated runtime hint for high-risk / full-scope requests
Outcome: low-risk, testable, gives future sessions a visible planning/verification gate without changing tools or taskpool.
Risks: prompt bloat or over-planning simple requests.
Mitigation: compact hint, explicit trigger list inside the hint, no hidden latest-message classifier, `agent.objective_model_path_guidance` opt-out, unit tests.
Decision: selected after code inspection. A prompt-level gate is safer than a hidden classifier because it preserves model judgment and avoids mid-turn prompt mutation.

### Path C — Taskpool automatic enqueue / lifecycle policy changes
Outcome: powerful, but high blast radius and can mutate live queues.
Decision: defer unless code inspection reveals an existing suggest-only hook with clear tests.

### Path D — Multi-model role routing changes
Outcome: useful long-term but provider/quorum-sensitive.
Decision: defer to separate SSOT after evidence bundle and consult_models tests.

## Implementation plan

1. Inspect Hermes prompt assembly and skill-loading code paths.
2. Add a compact, opt-out runtime guidance block for the objective/model/path gate.
3. Wire the compact instruction into the stable system-prompt tier only when tools are available.
4. Add focused tests covering default injection, opt-out, and no-tools behavior.
5. Update this SSOT with exact files/commands/evidence.
6. Commit only scoped source/docs/skill changes.

## Evidence log

- Created this SSOT before runtime code changes.
- Inspected `agent/system_prompt.py`: system prompt is assembled into stable/context/volatile tiers; safe integration point is stable prompt guidance, not per-turn hidden mutation.
- Inspected `agent/prompt_builder.py`: existing universal guidance constants (`TASK_COMPLETION_GUIDANCE`, tool-use enforcement, execution guidance) provide the established pattern for compact behavioral blocks.
- Inspected `agent/agent_init.py`: `agent` config section already initializes prompt-guidance toggles such as `task_completion_guidance`; added matching `objective_model_path_guidance` toggle.
- Implemented runtime prompt block `OBJECTIVE_MODEL_PATH_GUIDANCE` in `agent/prompt_builder.py`.
- Wired the block in `agent/system_prompt.py` when `agent.valid_tool_names` is non-empty and `agent._objective_model_path_guidance` is true.
- Added config initialization in `agent/agent_init.py`: `agent.objective_model_path_guidance` defaults to true.
- Added focused tests in `tests/run_agent/test_run_agent.py::TestObjectiveModelPathGuidance` covering default injection, opt-out, and no-tools behavior.
- Verification commands run from `/Users/charles/.hermes/hermes-agent`:
  - `uv run --extra dev pytest tests/run_agent/test_run_agent.py::TestObjectiveModelPathGuidance -q` → `3 passed in 8.54s`.
  - `uv run --extra dev pytest tests/run_agent/test_run_agent.py::TestBuildSystemPrompt tests/run_agent/test_run_agent.py::TestTaskCompletionGuidance tests/run_agent/test_run_agent.py::TestToolUseEnforcementConfig tests/run_agent/test_run_agent.py::TestObjectiveModelPathGuidance -q` → `35 passed in 56.01s`.
  - `uv run --extra dev python -m compileall agent/prompt_builder.py agent/system_prompt.py agent/agent_init.py tests/run_agent/test_run_agent.py` → exit code 0.
- Hermes-agent scoped source commit: `3b7fbae3a Add objective model path prompt gate`.
