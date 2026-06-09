# Hermes Agent Cards Runtime Boundary Follow-through

Date: 2026-06-09

## Scope

User authorized continuing from the Agent Cards documentation/validator layer until the overall boundary.

This follow-through advanced from default-off scaffold to default-on specialist routing and default-on Agent Card prompt context:

- Agent Card runtime helper module;
- deterministic specialist profile recommendations;
- routing decisions with `apply` as the default;
- `off` / `shadow` escape hatches for rollback or observation-only routing mode;
- worker prompt Agent Card context enabled by default;
- `HERMES_ENABLE_AGENT_CARD_CONTEXT=0/off/false/no` escape hatch for prompt rollback;
- worker subprocess profile handoff via `hermes -p <chosen_profile> chat ...`;
- profile-auth-aware worker model chain filtering so routed profiles skip known-unavailable providers such as Gemini OAuth when missing;
- tests proving task/Kanban/lifecycle/proof gates remain unmutated by routing/context;
- prompt budget test proving Agent Card context delta stays bounded;
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
- `runtime_boundary: controlled_apply_with_escape_hatches`

This does not change any Kanban assignee. It only chooses the Hermes profile for the spawned worker subprocess.

### 2. Runtime helper module

`agent_cards_runtime.py` provides:

- `load_cards()`
- `task_domain(task)`
- `recommend_profiles(task)`
- `routing_decision(task)`
- `render_agent_card_context(task, profile, enabled=...)`

The module is deterministic and read-only for task state. `routing_decision` supports `off`, `shadow`, and `apply`; `apply` is default, while `shadow` remains observation-only rollback mode.

### 3. Optional worker context integration

`agent_team_controller.py` now has:

- `build_agent_card_context_pack(task, profile=None)`

It renders Agent Card context by default. Disable with:

```bash
HERMES_ENABLE_AGENT_CARD_CONTEXT=off
```

Accepted disable values: `0`, `false`, `off`, `no`, `disabled`.

Prompt budget probe on a representative task:

- context off: 4635 chars
- context on: 6242 chars
- delta: 1607 chars / 34.67%
- test cap: delta <= 2200 and total <= 8000

The rendered context explicitly says:

- Agent Cards do not expand permissions.
- Agent Cards do not authorize lifecycle mutation.
- Conflicts with task/policy gates must fail closed.

### 4. Controlled routing apply mode

`agent_team_controller.py` records an `agent_card_routing_decision` trace for each delegated worker. Default mode is now `apply`, so the worker subprocess is launched through the recommended specialist Hermes profile.

Rollback / observation-only modes:

```bash
HERMES_AGENT_CARD_ROUTING_MODE=shadow
```

or:

```bash
HERMES_AGENT_CARD_ROUTING_MODE=off
```

The worker command is shaped as:

```bash
hermes -p <chosen_profile> chat ...
```

and the worker subprocess environment also gets:

- `HERMES_PROFILE=<chosen_profile>`
- `HERMES_PROFILE_NAME=<chosen_profile>`

This does not mutate task notes, Kanban assignees, lifecycle state, proof gates, or model chain semantics. It only routes the spawned worker process through a specialist Hermes profile.

### 5. Profile-auth-aware model chain filtering

When routed through a named profile, the controller checks `hermes -p <profile> doctor` once per controller process and drops providers known to be unavailable for that profile.

Current known boundary handled:

- named specialist profiles have OpenAI Codex auth;
- named specialist profiles lack Google Gemini OAuth;
- advisory chains therefore skip `google-gemini-cli` under routed profiles instead of wasting the first attempt on a predictable auth miss.

## Verification

Tests added:

- default routing is apply with off/shadow escape hatches;
- recommendations prefer domain card profiles;
- context can be explicitly disabled;
- default worker context includes Agent Card guidance;
- Agent Card context carries no-authority-expansion rule;
- Agent Card prompt delta stays within the configured budget cap;
- profile-provider filtering drops unavailable Gemini for routed profiles.

## Boundary reached

This is the next safe boundary after default-on specialist routing and default-on Agent Card prompt context.

Still not enabled automatically:

1. Default-on multimodel conductor routing
   - Would alter model/provider orchestration.
   - Requires quorum/quotas/fallback/truth-gate regression.

2. Canonical skill writer / external skill installation
   - Would mutate production skills.
   - Requires human review and gated writer.

3. External side-effect executors
   - Would write/send/deploy externally.
   - Requires explicit confirmation, digest-bound executor, audit event, and rollback path.

## Current verdict

Hermes has now advanced from documentation-only Google-style Agent Cards to default-on specialist worker profile routing plus default-on Agent Card worker prompt guidance. The system still does not mutate task lifecycle/proof gates through Agent Cards. The next boundary is multimodel conductor default-on or digest-bound write-through/external side-effect executors.
