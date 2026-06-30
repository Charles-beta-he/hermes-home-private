#!/usr/bin/env python3
"""Fast cron wrapper for the taskpool dynamic runner.

The Hermes cron scheduler applies a short no-agent script timeout.  The dynamic
runner can legitimately need several minutes when local taskpool gates are busy,
so this wrapper makes the cron tick quick and lets the runner's own pid lock and
state/log receipts own the long-running work.

Silent success semantics:
- existing live runner lock: exit 0, no stdout
- newly spawned runner: exit 0, no stdout
- spawn failure: non-zero with a compact JSON error
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HOME = Path.home()
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes"))).expanduser()
RUNNER = HERMES_HOME / "scripts" / "taskpool_dynamic_runner.py"
LOCK = HERMES_HOME / "state" / "taskpool_dynamic_runner.pid"
LOG_DIR = HERMES_HOME / "logs"
STDOUT_LOG = LOG_DIR / "taskpool_dynamic_runner_cron.stdout.log"
STDERR_LOG = LOG_DIR / "taskpool_dynamic_runner_cron.stderr.log"


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def lock_pid() -> int:
    try:
        return int((LOCK.read_text(encoding="utf-8").strip() or "0"))
    except Exception:
        return 0


def result(status: str, **extra: Any) -> dict[str, Any]:
    payload = {"schema": "taskpool_dynamic_runner_cron_v1", "status": status}
    payload.update(extra)
    return payload


def spawn_runner(env: dict[str, str] | None = None) -> dict[str, Any]:
    pid = lock_pid()
    if pid and alive(pid):
        return result("OK", action="already_running", pid=pid)
    if not RUNNER.exists():
        return result("ERROR", action="spawn", reason="runner_missing", runner=str(RUNNER))
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_env = dict(os.environ if env is None else env)
    run_env.setdefault("HERMES_HOME", str(HERMES_HOME))
    run_env.setdefault("HERMES_LOCAL_BRAIN_AUTORUN", "1")
    run_env.setdefault("HERMES_TASKPOOL_DYNAMIC_TIMEOUT", "700")
    run_env.setdefault("HERMES_BRAIN_AUTORUN_STEP_COMMAND_TIMEOUT_SECONDS", "220")
    try:
        stdout_f = STDOUT_LOG.open("a", encoding="utf-8")
        stderr_f = STDERR_LOG.open("a", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, str(RUNNER)],
            cwd=str(HERMES_HOME),
            env=run_env,
            stdout=stdout_f,
            stderr=stderr_f,
            start_new_session=True,
        )
        # Give immediate exec failures a small window to surface without making
        # the scheduler own the whole dynamic runner duration.
        time.sleep(0.2)
        rc = proc.poll()
        if rc is not None and rc != 0:
            return result("ERROR", action="spawn", returncode=rc, pid=proc.pid)
        return result("OK", action="spawned", pid=proc.pid)
    except Exception as exc:
        return result("ERROR", action="spawn", reason=type(exc).__name__, error=str(exc)[:300])


def main() -> int:
    payload = spawn_runner()
    if payload.get("status") == "OK":
        return 0
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
