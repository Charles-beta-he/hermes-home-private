# Mission progress audit pattern

Use when the user asks to check progress of a long-running Hermes Mission / self-advancing workflow, especially from a dashboard screenshot.

## Read-only audit sequence

1. Identify the mission id from the UI or board.
2. Read the mission control-plane state:
   - `hermes mission board --json`
   - `hermes mission inbox --json`
   - `hermes mission report <mission_id>`
   - `hermes mission signals <mission_id> --json`
   - `hermes mission doctor <mission_id>`
3. Inspect the durable ledger when the CLI summary is too high-level:
   - `~/.hermes/missions.db`
   - tables: `missions`, `mission_events`, `mission_decisions`, `mission_flow_signals`
   - summarize: mission row, event type counts, last stage reports, decision history, signal status counts and oldest/newest pending age.
4. Correlate with scheduler state:
   - find the mission cron job in `~/.hermes/cron/jobs.json` or `hermes cron list`
   - report enabled/state, last run/status/error, next run, script, repeat/completed.
5. If the mission is modifying Hermes itself, inspect the Hermes source checkout before judging completeness:
   - `git -C ~/.hermes/hermes-agent status --short --branch`
   - `git -C ~/.hermes/hermes-agent diff --stat`
   - `git -C ~/.hermes/hermes-agent diff --cached --stat`
   - recent commits if relevant.

## Interpretation rules

- `status=active` plus a recent ok cron run means the mission is not dead.
- `open decisions = 0` / empty inbox means it is not waiting on user choice.
- `ticks_used == ticks_max` is a budget boundary even if cron remains active; expect future ticks to stall/report budget exhausted until budget is explicitly renewed.
- Many pending/stale `mission_flow_signals` with low consumed count means event flow is backed up; call this out separately from mission status.
- Recent `stage_report` entries are the strongest progress evidence. Quote their actual verification commands/results, risks, and next_step.
- For Hermes self-modification missions, uncommitted diffs are not closed work. Distinguish “implemented and tested locally” from “scoped commit completed” and from “pushed/deployed”.

## Reporting shape

Keep the answer decision-oriented:

- current state: active/paused/blocked, stage, cadence, budget used, cron last/next run;
- latest real progress: last stage report + verification evidence;
- blockers/risks: open decisions, exhausted budget, stale signals, local uncommitted diffs, provider/cron errors;
- next safe action: usually consolidate diff + focused tests + scoped commit before expanding the mission or increasing budget.

Do not automatically dispatch events, run due cron, change budget, commit, push, or mutate mission state during a progress audit unless the user explicitly asks for action beyond inspection.