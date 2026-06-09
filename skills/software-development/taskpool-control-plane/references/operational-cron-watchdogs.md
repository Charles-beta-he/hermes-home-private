# Operational Cron Watchdogs for Task Pool Health

Pattern for building `no_agent=True` cron scripts that monitor task pool health and trigger notifications or triage reports.

## Pattern: no_agent cron script

A `no_agent=True` cron job skips the LLM entirely — the scheduler runs the script and delivers its stdout verbatim. No tokens consumed.

**Rules:**
- Script lives in `~/.hermes/scripts/` — the `script` parameter takes just the filename, NOT a full path. `script: iteration_budget_triage.py` ✓ / `script: ~/.hermes/scripts/iteration_budget_triage.py` ✗ (rejected)
- Non-empty stdout = delivered as message; empty stdout = silent (watchdog pattern — nothing to report means no notification)
- Non-zero exit / timeout sends an error alert so a broken watchdog can't fail silently
- Use `deliver: telegram` for human-facing alerts; use `deliver: local` for logs-only

## Deduplication / cooldown pattern

Notification scripts that scan kanban DB should deduplicate to avoid spam:

```python
STATE_FILE = HERMES_HOME / "state" / "<name>_state.json"

def load_state() -> dict[str, float]:
    """Load last notification timestamps per task."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def should_notify(task_id: str, state: dict, cooldown_secs: int = 86400) -> bool:
    now = time.time()
    return now - state.get(task_id, 0) > cooldown_secs

def record_notified(task_id: str, state: dict):
    state[task_id] = time.time()
    STATE_FILE.write_text(json.dumps(state))
```

Clean stale entries (older than 7 days) on each run to prevent unbounded state growth.

## JSONL observability logging

Every watchdog run should append a JSONL log line:

```python
LOG = HERMES_HOME / "logs" / "<name>.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)
with open(LOG, "a") as f:
    f.write(json.dumps({"ts": utc_now(), "count": len(items), ...}, ensure_ascii=False) + "\n")
```

## Kanban DB query pattern

Scan blocked tasks by summary/error keywords:

```python
db = sqlite3.connect(str(KANBAN_DB))
db.row_factory = sqlite3.Row
rows = db.execute("""
    SELECT t.id, t.title, t.assignee, t.priority, t.created_at,
           tr.summary, tr.error
    FROM tasks t
    JOIN task_runs tr ON tr.task_id = t.id AND tr.status = 'blocked'
    WHERE t.status = 'blocked'
      AND (tr.summary LIKE '%keyword1%' OR tr.summary LIKE '%keyword2%')
    ORDER BY t.priority DESC, t.created_at DESC
""").fetchall()
```

## Hook registry integration

For real-time (non-polling) triggers, add `post_task_block` entries to `~/.hermes/hooks/registry.yaml`:

```yaml
  post_task_block:
    description: "Trigger notifications when tasks transition to blocked"
    fail_closed: false
    checks:
      - auth_blocked_telegram_notify
      - iteration_budget_triage_trigger
    on_failure: log_and_continue

shell_hooks:
  post_task_block:
    - command: "python3 ~/.hermes/scripts/auth_blocked_notifier.py"
      matcher: "auth-required|credentials|登录凭证|登录态|凭据"
      timeout: 15
    - command: "python3 ~/.hermes/scripts/iteration_budget_triage.py --json"
      matcher: "Iteration budget exhausted"
      timeout: 30
```

The hook fires on every task→blocked transition and pattern-matches the block reason. Combined with the cron poll, this gives both real-time and periodic coverage.

## Existing watchdog scripts

| Script | Purpose | Cron schedule | Deliver |
|---|---|---|---|
| `iteration_budget_triage.py` | Scan 60/60 exhausted tasks → 续费/拆分/降级/放弃 | Daily 10:00 | telegram |
| `auth_blocked_notifier.py` | Scan credential-missing blocked tasks → TG alert | 3x/day (9/15/21) | telegram |
| `task_pool_guardian.py` | Stale claims + stuck envelopes + health check | Every 10m | local |

## Budget-exhausted triage decision matrix

When categorizing iteration-budget-exhausted tasks:

| Progress | Priority | Complexity | Recommendation | Action |
|---|---|---|---|---|
| substantial | P0+ | any | 续费 | Raise budget to 90-120 |
| substantial | P50+ | any | 续费 | Raise budget to 90 |
| unknown | any | high | 拆分 | Split into subtasks |
| unknown/none | any | low | 降级 | Move to exploratory/backlog |
| none + 3+ failures | any | low | 放弃 | Fundamental blocker |
| any | any | UVISA domain | 续费 (boost) | UVISA project gets priority |

Domain detection keywords:
- UVISA: `Lark`, `Admin`, `uvisa`, `UVISA`
- Hermes infra: `Hermes`, `taskpool`, `kanban`, `brain`
- Learning: `精读`, `书籍`, `学习` → always 降级

## Auth-blocked notification categorization

Extract credential need from task title + summary:

| Keywords in combined | Credential type |
|---|---|
| `Railway` + (`OTP` or `admin`) | Railway admin 登录态 |
| `GitHub` + `credentials` | GitHub credentials |
| `admin` + (`登录` or `auth`) | UVISA Admin 登录凭证 |
| `OTP` alone | OTP 验证访问 |
| fallback | 认证凭证 |

## Pitfalls

- **Script path in cron**: `script` parameter takes just the filename, not the full path. The cron runner resolves it under `~/.hermes/scripts/`.
- **Notification spam**: Always implement cooldown/dedup. 24h per-task cooldown is a good default.
- **Stale state growth**: Clean state entries older than 7 days on each run.
- **Hook + cron double-fire**: If both hook and cron trigger for the same task, the cooldown dedup handles it — the second trigger is suppressed.
- **kanban.db concurrent access**: SQLite reads are safe for concurrent access, but writes should be serialized. Watchdog scripts are read-only (state files are separate).
- **Subprocess timeout for orchestrator `list --json`**: `brain_task_orchestrator.py list --json` scans all `*.md` task files in the Obsidian vault (`~/Documents/brain/05-实践与项目/tasks/`). With 300+ files, cold-cache execution takes ~15s; under I/O pressure it can exceed 30s. Always set `subprocess.run(..., timeout=120)` when calling the orchestrator from a watchdog script. A 30s timeout will cause intermittent `TimeoutExpired` failures that crash the watchdog and trigger error alerts — masking the real health check behind a false script failure. The same applies to `v_state.py` calls.
- **Human-escape is a safety pause, not a broken cron**: `no_agent` autorun wrappers must preflight `agent_team_controller.py status --json` before `--parallel-autorun`. If `envelope_stats.human_escape_triggered` is true, print structured JSON with `status: "SKIP"`, `reason: "SAFETY_PAUSE_POST_ACK_FAILURES"`, `blocks_what`, and `since_ack` counts, then exit 0. This preserves fail-closed behavior while preventing diagnostics from misclassifying deliberate post-ack safety pauses as cron job failures.
- **Classify cron red lights by failure class**: cron-health checks should include `provider_generation`, `delivery`, `scheduler_runtime`, `safety_pause`, and fallback `job_error` classes from `last_error` + `last_delivery_error`. If both provider and delivery errors exist, prefer `provider_generation` for root cause when generation did not finish.
- **Pin unstable agent cron providers**: high-coupled agent cron jobs that inherit the default provider/model can become globally red when the default model has backend no-event/timeout behavior. Pin a known-good provider/model for the job and verify by running the cron job once; do not rely on scheduler retry alone.
