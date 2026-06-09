# Google-style Agent Cards for Hermes self-architecture

Use this reference when a user asks whether Hermes agents/domains conform to Google-style agent structure, asks to push agent architecture to the next boundary, or asks to move from classification coverage toward runtime use.

## Scope

Hermes self-architecture only: runtime profiles, taskpool/Kanban workers, architecture domains, Agent Card validation, and default-off prompt/context scaffolds.

Do not apply this pattern to ordinary app projects unless they explicitly adopt the same event-governed control-plane architecture.

## Google-style Agent Card fields

A machine-readable card should cover:

- `goal`
- `role`
- `observation`
- `memory`
- `planning`
- `tools`
- `actions`
- `policy`
- `evaluation`
- `collaboration`
- `escalation`

For Hermes, these fields are descriptive contracts only unless a separate runtime gate explicitly consumes them. A card never expands permissions by itself.

## Safe progression ladder

1. Documentation SSOT
   - Write a scoped doc comparing Hermes profiles/domains with Google-style agent components.
   - Keep external claims short and source-linked.

2. Machine-readable Agent Cards
   - Store a JSON SSOT for runtime profiles and architecture domains.
   - Include all required fields above.
   - Mark runtime routing as `recommendation_only_default_off` unless a separate rollout has been authorized.

3. Read-only validator
   - Validate that cards cover all profile dirs, Kanban assignees, and active architecture scopes.
   - Validate each card has the Google-style fields.
   - Validate active brain tasks still have canonical classification fields.
   - The validator must not mutate Kanban, brain notes, profile config, or worker prompts.

4. Default-off runtime scaffold
   - Provide deterministic helpers such as `task_domain(task)`, `recommend_profiles(task)`, and `render_agent_card_context(task, enabled=...)`.
   - Recommendations must report `recommendation_only` and state that task assignment is not changed.
   - Prompt/card context must be disabled by default and require an explicit flag/env var such as `HERMES_ENABLE_AGENT_CARD_CONTEXT=1`.
   - Injected context must say it does not expand permissions or authorize lifecycle mutation.

5. Overall boundary / human authorization point
   Stop before any of these live behavior changes:
   - automatic specialist profile routing;
   - always-on worker prompt Agent Card injection;
   - default-on multimodel conductor routing;
   - canonical skill writer or external skill installation;
   - external side-effect executors.

## Verification pattern

Before reporting closure, run and report:

- Agent Card validator: status PASS, no missing runtime/domain cards, no field gaps.
- Agent coverage v2: score 1.0 or requested target, no caps, no drift.
- v_state: healthy or explicitly degraded with bottleneck.
- taskpool/selfcheck: PASS, no failures.
- unit tests for default-off behavior:
  - profile recommendation does not mutate assignment;
  - card context is default-off;
  - opt-in context includes no-authority-expansion language;
  - worker context excludes cards by default;
  - worker context includes cards only under explicit opt-in.
- secret scan / diff check before commit when files are committed.

## Pitfalls

- Do not treat Agent Cards as runtime authorization. Cards summarize role/tool/policy; gates still decide authority.
- Do not silently change dispatch from a general/brain-mirror lane to specialist profiles. Use shadow/dry-run metrics and rollback first.
- Do not always inject cards into worker prompts without prompt-budget and behavior regression tests.
- Do not call documentation-level Google alignment "full runtime conformance"; distinguish architecture conformance from live multi-specialist execution.
- Do not promote external skill intake to production skills without a canonical writer gate and human/review approval.
