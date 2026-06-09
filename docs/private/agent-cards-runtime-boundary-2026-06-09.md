# Hermes Agent Cards Runtime Boundary Follow-through

Date: 2026-06-09

## Scope

User authorized continuing from the Agent Cards documentation/validator layer until the overall boundary.

This follow-through advanced two safe runtime layers deeper than documentation:

- default-off Agent Card runtime helper module;
- deterministic specialist profile recommendations;
- shadow/apply routing decisions with `shadow` as the default;
- optional worker prompt Agent Card context gated by `HERMES_ENABLE_AGENT_CARD_CONTEXT=1`;
- worker subprocess profile handoff only when `HERMES_AGENT_CARD_ROUTING_MODE=apply` or `HERMES_AGENT_CARD_ROUTING=1` is explicitly set;
- tests proving default runtime behavior remains unchanged;
- validation that coverage/classification stayed healthy.

## Landed artifacts

- `/Users/charles/.hermes/scripts/agent_cards_runtime.py`
- `/Users/charles/.hermes/scripts/test_agent_cards_runtime.py`
- `/Users/charles/.hermes/scripts/agent_team_controller.py`
- `/Users/charles/.hermes/docs/private/agent-cards-v1.json`

## What changed

### 1. Agent Cards now include recommendation metadata

Each architecture domain in `agent-cards-v1.json` now has:

- `recommended_runtime_profiles`
- `runtime_boundary: recommendation_only_default_off`

This is intentionally advisory. It does not change any Kanban assignee.

### 2. Runtime helper module

`agent_cards_runtime.py` provides:

- `load_cards()`
- `task_domain(task)`
- `recommend_profiles(task)`
- `routing_decision(task)`
- `render_agent_card_context(task, profile, enabled=...)`

The module is deterministic and read-only. `routing_decision` supports `off`, `shadow`, and `apply`; `shadow` is default and recommendation-only.

### 3. Optional worker context integration

`agent_team_controller.py` now has:

- `build_agent_card_context_pack(task, profile=None)`

It returns an empty string by default. It only renders card context when:

```bash
HERMES_ENABLE_AGENT_CARD_CONTEXT=1
```

The rendered context explicitly says:

- Agent Cards do not expand permissions.
- Agent Cards do not authorize lifecycle mutation.
- Conflicts with task/policy gates must fail closed.

### 4. Controlled routing apply mode

`agent_team_controller.py` records an `agent_card_routing_decision` trace for each delegated worker. Default mode is `shadow`, so it only records the recommended profile.

When explicitly launched with:

```bash
HERMES_AGENT_CARD_ROUTING_MODE=apply
```

or:

```bash
HERMES_AGENT_CARD_ROUTING=1
```

the worker subprocess environment gets:

- `HERMES_PROFILE=<chosen_profile>`
- `HERMES_PROFILE_NAME=<chosen_profile>`

This does not mutate task notes, Kanban assignees, lifecycle state, proof gates, or model chain. It only routes the spawned worker process through a specialist Hermes profile when the operator explicitly enables apply mode.

## Verification

Tests added:

- recommendations prefer domain card profiles;
- context is default-off;
- opt-in context carries no-authority-expansion rule;
- worker context excludes cards by default;
- worker context includes cards only when env opt-in is set.

## Boundary reached

This is the overall safe boundary for this authorization.

Still not enabled automatically:

1. Default-on specialist profile routing
   - The apply path exists, but default remains `shadow`.
   - Profile doctor smoke checks passed for config/OpenAI Codex auth on workflow/hermes-agent/brain-mirror/media/mlops/dev/hermes-core.
   - Boundary: named profiles do not have Google Gemini OAuth logged in, so advisory worker fallback chains would spend time failing Gemini before fallback unless profile OAuth is completed or the model chain becomes profile-auth-aware.
   - Enabling it globally needs a staged rollout config, live shadow metrics, profile auth parity, and rollback.

2. Always-on Agent Card worker prompt injection
   - Would alter every worker prompt and token budget.
   - Requires budget/performance tests and prompt-regression checks.

3. Default-on multimodel conductor routing
   - Would alter model/provider orchestration.
   - Requires quorum/quotas/fallback/truth-gate regression.

4. Canonical skill writer / external skill installation
   - Would mutate production skills.
   - Requires human review and gated writer.

5. External side-effect executors
   - Would write/send/deploy externally.
   - Requires explicit confirmation, digest-bound executor, audit event, and rollback path.

## Current verdict

Hermes has now advanced from documentation-only Google-style Agent Cards to a default-off runtime scaffold. The next step is no longer safe as silent self-architecture work: it would change live dispatch or worker behavior and therefore needs an explicit runtime rollout decision.
