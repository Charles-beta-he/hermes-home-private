# Mission Control in Control Tower Dashboard

Use this reference when evolving Hermes Mission / Control Tower / dashboard UX for high-abstract long-running directions.

## Context

The Mission control plane is the objective/ledger/human-gate scaffold for: user chooses a high-level direction, Hermes advances bounded slices, and real forks are returned as human decisions. The Control Tower dashboard is the right visual projection surface, but it must remain a projection/operator surface, not the source of truth.

Canonical sources:
- Mission DB: `~/.hermes/missions.db` via `hermes_cli.missions.MissionStore`
- Mission tick scripts: `~/.hermes/scripts/mission_tick_<mission_id>.py`
- Cron jobs: `~/.hermes/cron/jobs.json`
- Control Tower ledger: `~/.hermes/control_tower.db`
- Dashboard plugin projection: `plugins/control-tower/dashboard/`

## Proven slice

A low-risk, directly usable dashboard slice is:

1. Backend plugin API exposes mission projection only:
   - Add `GET /api/plugins/control-tower/missions` in `plugins/control-tower/dashboard/plugin_api.py`.
   - Return `MissionStore().board()` and `MissionStore().inbox()`.
   - Do not mutate Mission state from the first slice.

2. Frontend Control Tower plugin renders Mission Control:
   - Use the dashboard plugin SDK authenticated fetch path (`window.__HERMES_PLUGIN_SDK__.authedFetch`) or inject `X-Hermes-Session-Token` fallback; plain `fetch('/api/plugins/...')` can render 401 inside the page.
   - Show: mission count, open decision count, mission id, status, ticks used/max, cron installed, needs-user, next action, and direction.
   - Display open decisions with the exact `hermes mission decide ...` command.

3. Register the plugin even when it imperatively renders into the DOM:
   - Existing Control Tower code appends its own DOM root, but the host still expects dashboard plugins to call `window.__HERMES_PLUGINS__.register(name, Component)`.
   - If omitted, the host may show: `THE PLUGIN’S SCRIPT DID NOT CALL REGISTER(), OR THE SCRIPT ERRORED` even while the plugin content appears.
   - Minimal compatibility pattern: after `loadSnapshot()`, call `window.__HERMES_PLUGINS__.register('control-tower', () => null)`.

## Projection governance / SSOT boundary

For Control Tower/Dashboard taskpool/Kanban work, preserve the current task lifecycle SSOT boundary:

- Brain taskpool markdown (`brain_task_orchestrator.py` + `~/Documents/brain/05-实践与项目/tasks/*.md`) is canonical for task lifecycle.
- Kanban DB is an execution projection.
- Control Tower ledger, Dashboard, and Console are operator/governance projections unless a separate ADR migrates authority.
- `GET /api/plugins/control-tower/snapshot` must be read-only: do not call observation-ingest helpers that write `adapter_observations` or `events` during dashboard refresh. Keep explicit ingest helpers separate from snapshot helpers.
- Surface projection drift through report-only diagnostics such as `kanban_coverage.py --json` / `agent_coverage_v2`; next actions should be read-only diagnosis or governed Brain→Kanban reconcile, not direct lifecycle mutation from the UI.
- Do not render projection governance as a hero-sized technical panel. Use a compact Chinese operator status strip/chip on the first screen; put raw `status`, `mode`, `runtimeSelector`, snake_case actions, and drift kinds behind details.
- When comparing execution-flow dry-run output against active taskpool rows, exclude terminal flow statuses (`done`, `archived`, `cancelled`, `completed`) before computing missing-task drift. See `references/kanban-projection-blockage-and-console-drift.md` for the full triage and UI acceptance pattern.

## Verification commands

Run focused checks after dashboard plugin changes:

```bash
uv run python -m py_compile plugins/control-tower/dashboard/plugin_api.py hermes_cli/missions.py
node --check plugins/control-tower/dashboard/dist/index.js
uv run pytest -q tests/test_missions.py tests/test_project_metadata.py -q
```

Then smoke the actual dashboard:

```bash
uv run hermes dashboard --port 9119 --no-open --skip-build
# open http://127.0.0.1:9119/control-tower
```

Dashboard smoke pitfall:
- Do not treat a startup line such as `Hermes Web UI → http://127.0.0.1:9119` as proof the server is running. The process may print the URL and then fail to bind because the port is already in use.
- After starting a dashboard background process, poll/read the process status. If it exited with an address-in-use error, retry on a different local port and verify with a real page/API/browser readback.
- After browser smoke verification, stop the temporary dashboard process; an exit code such as `-15` from your explicit kill is expected cleanup, not a crash.

Expected visible result:
- Sidebar includes `CONTROL TOWER` under plugins.
- Page title is `CONTROL TOWER`.
- No plugin registration warning.
- A `MISSION CONTROL / High-level directions` section shows active missions.
- Mission row shows `Status`, `Ticks`, `Cron`, `User`, and `Next`.
- If Mission event-flow projection is enabled, the page shows a `Mission event flow` / `Signals and taskpool bridge` panel with pending/stale signal counts, consumed latency, bridge pending count, and recent bridged task rows.

## Product direction

Treat the dashboard as a CEO/operator cockpit:

P0 projection:
- Mission Board
- Human Decision Inbox
- Cron readiness
- Blocked reasons
- Next operator action

P1 detail page:
- Direction
- Stage reports
- Evidence
- Tick history
- Open/answered decisions
- Cron job state

P2 controlled actions:
- Pause/resume mission
- Decide open decision
- Install cron
- Request handoff

All P2 actions must call MissionStore / ledger APIs and remain auditable; the UI must not become a second fact source.
