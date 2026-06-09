# Hermes Conductor Runtime scaffold pattern

Use this reference when implementing Sakana/Fugu/Conductor-inspired orchestration inside Hermes without destabilizing the main agent loop.

## Core lesson

When the user asks for long-term async/multi-model orchestration, do not hard-wire a new model or external orchestrator into the conversation loop first. Land default-off control-plane primitives, tests, config placeholders, and post-update regression gates before mainline wiring.

## Required architecture shape

1. `ConversationIntentRouter`
   - Classifies each user message into `current_task_control`, `new_background_task`, `status_query`, `normal_chat`, `priority_change`, or `multimodel_escalation`.
   - Initial implementation may use Hermes' default main model as the bootstrap/router model.
   - Router calls must be recorded as control-plane calls, not task execution calls.
   - Always separate `router_model` from `participant_models` in trace output.
   - Force `participant_models=[]` for the router result so the default main model remains eligible later as planner/implementer/arbiter.

2. `TaskLedger`
   - Store durable task state outside the current chat context, preferably SQLite or an existing durable taskpool abstraction.
   - Minimum fields: `task_id`, `origin_session_id`, `title`, `status`, `current_goal`, `constraints`, `latest_user_directive`, `interrupt_policy`, `artifacts`, `last_summary`, `active_worker`, `multimodel_mode`, `history`, timestamps.
   - Support create, update directive, pause, resume, cancel, get active tasks.
   - Status changes such as pause/resume should not overwrite the latest user directive unless they are themselves a scope directive.

3. Optional external provider adapter
   - Sakana Fugu is beta/API-application gated unless official docs say otherwise.
   - Implement as optional provider with `enabled=false`, empty `base_url`, `api_key_env=SAKANA_FUGU_API_KEY`.
   - No key or disabled provider must return fail-soft structured output, not raise.
   - Normalize all output to a Hermes schema and keep `truth_certified=false` unless evidence/truth gates certify it.

4. Model profiles
   - Create a default-off `model_profiles.yaml` placeholder.
   - Include role hints for default main model, GPT, Claude, DeepSeek, MiMo, and optional Fugu.
   - Explicitly document that default-main router usage does not consume later multi-model participation slots.

5. Regression gate
   - Add a post-update check covering py_compile, targeted pytest, default-off config, router isolation, and Fugu fail-soft.
   - Prefer using the repo `.venv/bin/python` inside post-update checks when available; otherwise `sys.executable` may miss pytest and incorrectly fall back to manual tests that cannot provide pytest fixtures like `tmp_path`.

## TDD pattern

Write RED tests first for:

- Task ledger create/update/pause/resume/active query.
- Router classification for status query, new task, current task control, and multimodel escalation.
- Default main model fallback sanitization: discard any model-provided `participant_models` and keep router trace isolated.
- Conductor/Fugu defaults: disabled by default, no API key fail-soft.
- Fugu normalization: provider schema output, evidence requests, risks, confidence, and `truth_certified=false`.

## Mainline wiring pattern (advisory mode)

After the default-off primitives and regression gate pass, wire the router into `conversation_loop.py` in advisory mode:

1. Add `_run_conductor_intent_router()` after `_run_mainline_cognitive_pipeline()`.
2. Read `config.conductor.intent_router.enabled` — default off.
3. Advisory only: write decision to `agent._last_conductor_decision`, log it, but do NOT alter the main conversation loop.
4. Fail-soft: any exception is caught and logged as warning; main loop proceeds unaffected.
5. The function is importable and callable independently for unit tests (use a `FakeAgent` stub with `_conductor_config`).

## Background task worker pattern

For durable async task execution that survives parent session interruption:

1. Create `scripts/hermes_background_task_worker.py` with `BackgroundTaskWorker`.
2. Support `probe --task-id` (read-only state) and `run --task-id [--dry-run]`.
3. `run(dry_run=True)` transitions task through queued→running→done via the ledger, proving wiring without model calls.
4. `run()` scaffold placeholder for future AIAgent fresh-session execution.
5. Use `TaskLedger._set_status()` and `_append_history()` for lifecycle transitions.
6. Do NOT use `delegate_task` for long-running work — parent session interruption cancels leaf subagents.

## MultiModelConductor role/profile planning

Add `MultiModelConductor` to `agent/conductor_runtime.py` for role-based model assignment:

1. `load_model_profiles()` — parse `~/.hermes/config/model_profiles.yaml` with YAML or fallback.
2. `build_role_plan(task_context, router_model, exclude_router_from_participants)` — assign models to roles (scout/planner/implementer/critic/verifier/architect/arbiter).
3. `build_model_specific_instruction(model_id, role, task_context)` — generate role-aware system prompt fragments.
4. Output includes `conductor_trace` with `router_model`, `participant_models`, `role_plan`, `risk_level`, `multimodel_mode`.
5. Router isolation: `exclude_router_from_participants=True` by default — the bootstrap/router model is never assigned to a participant role.
6. Profile `enabled: false` entries (except `default_main`) are excluded from eligible models.

## CLI smoke helper

`scripts/hermes_conductor_runtime.py` provides:
- `config` — verify default-off state
- `route "message"` — classify via intent router
- `create-task --title --goal` — create ledger entry
- `fugu-probe` — verify Fugu fail-soft
- `role-plan [--goal] [--risk] [--mode] [--router-model]` — build role plan from profiles

## Active enablement pattern (scaffold → enabled)

After the default-off scaffold passes regression, enable the conductor:

1. `hermes config set conductor.enabled true`
2. `hermes config set conductor.intent_router.enabled true`
3. `hermes config set conductor.intent_router.router_call_isolated true`
4. Update `~/.hermes/config/model_profiles.yaml` → `conductor.enabled: true`
5. Update post-update-check assertions: change `is not False` → `is not True` for conductor_runtime_enabled and role-plan conductor_enabled
6. Re-run full validation

## conversation_loop wiring with ledger management

When the router is enabled, `_run_conductor_intent_router()` actively manages the ledger:

- `new_background_task` + `action=create` → `ledger.create_task(title, current_goal, origin_session_id)`, attach `created_task_id` to decision
- `current_task_control` + `target_task_id` → `ledger.update_task_directive(target_task_id, message, action)`
- `status_query` + `target_task_id` → `ledger.get_task(target_task_id)`, attach `task_status`, `task_last_summary`, `task_latest_directive` to decision

All operations are try/except wrapped — ledger failures log warnings but never block the main loop.

## consult_models.py integration

Two new functions integrate conductor role planning with the existing multi-model discussion:

- `build_conductor_enhanced_prompt(state, state_hash, model, tier, role_instruction)` — wraps `build_planner_prompt()` with a role-specific instruction prefix when non-empty
- `generate_conductor_trace_for_consult(selected_planners, tier, state, router_model, profile_path)` — produces conductor_trace, role_plan, participant_models, and role_instructions dict; fail-soft on any import/config error

Both are advisory: they do NOT replace the existing quorum/consensus logic.

## Config loading pitfall for scripts

`hermes_cli.config.load_config()` fails with system Python because `hermes_constants.py` uses `type | None` syntax (Python 3.10+). Scripts that run outside the venv (via `python3 script.py`) must load config.yaml directly:

```python
cfg_path = Path.home() / ".hermes" / "config.yaml"
cfg = {}
if cfg_path.exists():
    text = cfg_path.read_text(encoding="utf-8", errors="ignore")
    try:
        import yaml
        loaded = yaml.safe_load(text) or {}
        cfg = loaded if isinstance(loaded, dict) else {}
    except Exception:
        pass
```

Same pattern applies to `conversation_loop.py` — use direct YAML loading, not `hermes_cli.config`.

## Verification commands

```bash
cd ~/.hermes/hermes-agent
# Tests
.venv/bin/python -m pytest tests/agent/test_conductor_runtime.py -q
# Compile check
.venv/bin/python -m py_compile agent/conductor_runtime.py agent/conversation_loop.py tests/agent/test_conductor_runtime.py ~/.hermes/scripts/hermes_conductor_runtime.py ~/.hermes/scripts/hermes_background_task_worker.py ~/.hermes/scripts/post-update-check.py
# CLI smoke
python3 ~/.hermes/scripts/hermes_conductor_runtime.py config
python3 ~/.hermes/scripts/hermes_conductor_runtime.py fugu-probe
python3 ~/.hermes/scripts/hermes_conductor_runtime.py role-plan
python3 ~/.hermes/scripts/hermes_background_task_worker.py probe --task-id nonexistent
# Regression gate
python3 ~/.hermes/scripts/post-update-check.py | grep -A3 -B1 conductor_runtime
```

## Pitfalls

- Do not let a bootstrap/router call count as a multi-model participant.
- Do not let Fugu or any external orchestrator bypass Hermes evidence/truth gates.
- Do not hardcode a Sakana Fugu endpoint until beta docs provide it.
- Do not treat `delegate_task` as durable background execution; parent interruption cancels leaf subagents.
- Do not overwrite `latest_user_directive` with operational status reasons such as pause/resume unless that is the intended directive. Use `update_latest_directive=False` for status-only transitions.
- Do not import `conductor_runtime` or background worker scripts directly in tests without `sys.path` manipulation — the scripts live under `~/.hermes/scripts/`, not inside the `hermes-agent` package. Use `sys.path.insert(0, str(Path.home() / ".hermes" / "scripts"))` before importing.
- Post-update-check must use `.venv/bin/python` when available (not bare `sys.executable`) for `pytest --version` and test runs, otherwise fixtures like `tmp_path` fail in manual-fallback mode.
- Pyright type narrowing: when chaining `.get()` on dict values that may be `None`, assign to a typed local variable first (`conductor_raw = cfg.get("conductor"); conductor: Dict[str, Any] = conductor_raw if isinstance(conductor_raw, dict) else {}`), then call `.get()` on the local.
- When transitioning a feature from default-off scaffold to enabled, update ALL regression gate assertions that check for `is not False` to `is not True` (and vice versa). Missing one causes a false-positive BROKEN result on the next post-update-check run.
- `hermes config set conductor.intent_router.enabled true` works for nested YAML keys — use it instead of manually editing config.yaml for simple boolean/string values.
