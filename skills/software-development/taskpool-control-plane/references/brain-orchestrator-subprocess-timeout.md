# brain_task_orchestrator.py Subprocess Timeout Pattern

## Problem

`brain_task_orchestrator.py list --json` scans all `.md` files in `~/Documents/brain/05-实践与项目/tasks/`. With 300+ task files, this takes 60-90+ seconds on macOS (Xcode Python 3.9). Any script calling it as a subprocess with `timeout<120` will fail with a timeout error.

## Symptoms

- `kanban_bridge.py` returns `{"status": "error", "error": "Command '['python3', '...brain_task_orchestrator.py', 'list', '--json']' timed out after 30 seconds"}`
- Cron watchdog scripts fail silently (non-zero exit, error alert delivered)
- Multiple zombie `brain_task_orchestrator.py` processes accumulate, each consuming 3-7.5GB RAM

## Root Cause

The `iter_tasks()` function (line 2745) reads every `.md` file in `TASKS_DIR`, parses YAML frontmatter, and constructs `Task` objects. With 322+ files, this is inherently slow. The `edge_node_registry` import adds ~1s. The Xcode Python 3.9 runtime is slower than Homebrew python3.

## Fix Pattern

### 1. Increase subprocess timeout to 120s

```python
# Before (fails):
r = subprocess.run(
    ['python3', str(ORCHESTRATOR), 'list', '--json'],
    capture_output=True, text=True, timeout=30
)

# After (works):
r = subprocess.run(
    ['python3', str(ORCHESTRATOR), 'list', '--json'],
    capture_output=True, text=True, timeout=120
)
```

### 2. Pre-flight zombie cleanup

Before running any orchestrator-dependent script:

```bash
ps aux | grep brain_task_orchestrator | grep -v grep
```

If stale processes exist (running >2 minutes, high RSS):

```bash
pkill -f brain_task_orchestrator
```

### 3. Timeout reference table

| Orchestrator subcommand | Typical duration | Safe timeout |
|---|---|---|
| `list --json` | 60-90s | 120s |
| `next --reconcile --json` | 90-180s | 300s |
| `dashboard --write` | 60-120s | 180s |
| `selfcheck --json` | 10-30s | 60s |
| `proof-check --json` | 30-60s | 120s |
| `eligibility-check --json` | 10-30s | 60s |

### 4. Detection in cron/watchdog scripts

```python
# At the top of any script that calls brain_task_orchestrator:
import subprocess, os, signal

# Kill stale orchestrator processes before calling
result = subprocess.run(['pgrep', '-f', 'brain_task_orchestrator'], capture_output=True, text=True)
for pid in result.stdout.strip().split('\n'):
    if pid:
        try:
            os.kill(int(pid), signal.SIGTERM)
        except (ProcessLookupError, ValueError):
            pass
```

## Files affected

- `~/.hermes/scripts/kanban_bridge.py` — timeout at line 37 (fixed from 30→120)
- Any cron watchdog that calls `brain_task_orchestrator.py list --json`
- `~/.hermes/scripts/brain_task_dispatch_tick.py` — calls various orchestrator subcommands

## Verification

After fixing timeout:
1. Run `python3 ~/.hermes/scripts/kanban_bridge.py` — should return `{"status": "ok", ...}`
2. Check `ps aux | grep brain_task_orchestrator | grep -v grep` — should be empty or show only one active process
3. Check `~/.hermes/state/kanban_bridge_state.json` — `errors` array should not grow
