#!/usr/bin/env python3
"""No-agent wrapper for Hermes upstream ratchet watch + semantic review.

Empty stdout means no new unreviewed upstream state. Non-empty stdout is an
actionable JSON review packet summary.
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "upstream-ratchet-review.py"


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes").expanduser()


def append_event(payload: dict) -> None:
    log = hermes_home() / "logs" / "upstream-ratchet-review-events.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema": "upstream_ratchet_review_noagent_event_v1",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        **payload,
    }
    log.open("a", encoding="utf-8").write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def append_timeout_event(exc: subprocess.TimeoutExpired) -> None:
    timeout_log = hermes_home() / "logs" / "upstream-ratchet-review-timeouts.jsonl"
    timeout_log.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "timeout_skip",
        "timeout_seconds": 110,
        "cmd": exc.cmd,
        "safety": "no_agent watchdog stayed silent to avoid cron/user-notification noise",
    }
    timeout_log.open("a", encoding="utf-8").write(json.dumps(record, ensure_ascii=False) + "\n")
    append_event({"status": "timeout_skip", "timeout_seconds": 110})


def redact(text: str) -> str:
    """Remove common secret-bearing fragments before persisting diagnostics."""
    import re

    redacted = re.sub(r"(?i)(api[_-]?key|secret|token|password)(\s*[:=]\s*)[^\s'\"]+", r"\1\2[REDACTED]", text)
    redacted = re.sub(r"https?://[^\s'\"]+@", "https://[REDACTED]@", redacted)
    return redacted


def safe_tail(text: str, limit: int = 1000) -> str:
    return redact(text or "")[-limit:]


def classify_nonzero(stderr: str) -> str | None:
    if "unexpected branch" in stderr and "expected private/main or integrate/*" in stderr:
        return "skipped_unexpected_branch"
    return None


def main() -> int:
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
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
        append_timeout_event(exc)
        return 0

    if proc.stdout:
        print(proc.stdout, end="")
    if proc.returncode != 0:
        stderr = proc.stderr or ""
        classification = classify_nonzero(stderr)
        if classification:
            append_event({
                "status": classification,
                "returncode": proc.returncode,
                "stderr_tail": safe_tail(stderr),
                "safety": "no_agent watchdog stayed silent; ratchet review skipped until branch is private/main or integrate/*",
            })
            return 0
        if stderr:
            print(stderr, end="", file=sys.stderr)
        append_event({"status": "error", "returncode": proc.returncode, "stderr_tail": safe_tail(stderr)})
        return proc.returncode
    append_event({"status": "ok", "returncode": 0, "printed": bool(proc.stdout)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
