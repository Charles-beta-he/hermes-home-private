#!/usr/bin/env python3
"""Local no-agent cron heartbeat for high-risk gate status write-through.

Silent on success so scheduler delivers nothing; writes an append-only local receipt.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HOME = Path.home() / ".hermes"
SCRIPT = HOME / "scripts" / "high_risk_gate_control.py"
spec = importlib.util.spec_from_file_location("high_risk_gate_control", SCRIPT)
if not spec or not spec.loader:
    print("high_risk_gate_control import unavailable", file=sys.stderr)
    raise SystemExit(2)
mod = importlib.util.module_from_spec(spec)
sys.modules["high_risk_gate_control"] = mod
spec.loader.exec_module(mod)
result = mod.heartbeat(HOME, actor="cron-worker-auto-status")
if not result.get("ok"):
    print(result, file=sys.stderr)
    raise SystemExit(2)
