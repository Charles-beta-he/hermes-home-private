#!/usr/bin/env python3
"""Cron wrapper for upstream-ratchet-watch.py.

No-agent delivery semantics: empty stdout means silent. The watcher itself is
silent on no upstream change when --quiet-no-change is set.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

watcher = Path.home() / ".hermes" / "scripts" / "upstream-ratchet-watch.py"
proc = subprocess.run(
    [sys.executable, str(watcher), "--quiet-no-change"],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=240,
)
if proc.stdout:
    print(proc.stdout, end="")
if proc.returncode != 0:
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    raise SystemExit(proc.returncode)
