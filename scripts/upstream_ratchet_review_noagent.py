#!/usr/bin/env python3
"""No-agent wrapper for Hermes upstream ratchet watch + semantic review.

Empty stdout means no new unreviewed upstream state. Non-empty stdout is an
actionable JSON review packet summary.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

script = Path.home() / ".hermes" / "scripts" / "upstream-ratchet-review.py"
try:
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--timeout",
            "90",
            "--only-if-needed",
            "--quiet-no-needed",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=110,
    )
except subprocess.TimeoutExpired as exc:
    log = Path.home() / ".hermes" / "logs" / "upstream-ratchet-review-timeouts.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    import json, datetime
    log.open("a", encoding="utf-8").write(json.dumps({
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "timeout_skip",
        "timeout_seconds": 110,
        "cmd": exc.cmd,
        "safety": "no_agent watchdog stayed silent to avoid cron/user-notification noise",
    }, ensure_ascii=False) + "\n")
    raise SystemExit(0)
if proc.stdout:
    print(proc.stdout, end="")
if proc.returncode != 0:
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    raise SystemExit(proc.returncode)
