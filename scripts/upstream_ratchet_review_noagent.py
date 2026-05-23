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
proc = subprocess.run(
    [
        sys.executable,
        str(script),
        "--only-if-needed",
        "--quiet-no-needed",
        "--discussion",
    ],
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    timeout=1800,
)
if proc.stdout:
    print(proc.stdout, end="")
if proc.returncode != 0:
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    raise SystemExit(proc.returncode)
