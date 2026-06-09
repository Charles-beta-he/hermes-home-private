# Hermes Agent Cards Runtime Boundary Follow-through

Date: 2026-06-09

## Scope

User authorized continuing from the Agent Cards documentation/validator layer until the overall boundary.

This follow-through advanced one safe layer deeper than documentation:

- default-off Agent Card runtime helper module;
- deterministic specialist profile recommendations;
- optional worker prompt Agent Card context gated by `HERMES_ENABLE_AGENT_CARD_CONTEXT=1`;
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
- `render_agent_card_context(task, profile, enabled=...)`

The module is deterministic and read-only.

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

1. Automatic specialist profile routing
   - Would mutate task assignment/dispatch behavior.
   - Requires separate rollout plan, dry-run shadow metrics, rollback, and profile auth checks.

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
