#!/usr/bin/env python3
"""Silent resident tick for Hermes selfcheck sentinel wakeups.

Runs the active wake-up loop without executing repairs or sending messages.
Default stdout is empty so scheduler/no-agent delivery remains silent; set
HERMES_SELFCHECK_SENTINEL_VERBOSE=1 for a compact local summary.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
HERMES_AGENT = HERMES_HOME / "hermes-agent"
if sys.version_info < (3, 10):
    for candidate in (HERMES_AGENT / ".venv" / "bin" / "python", HERMES_AGENT / "venv" / "bin" / "python"):
        if candidate.exists() and Path(sys.executable) != candidate:
            os.execv(str(candidate), [str(candidate), __file__, *sys.argv[1:]])
if str(HERMES_AGENT) not in sys.path:
    sys.path.insert(0, str(HERMES_AGENT))

from agent.selfcheck_operator import run_sentinel_tick  # noqa: E402


def main() -> int:
    wakeups = run_sentinel_tick(source="cron_sentinel", debounce_seconds=300)
    if os.environ.get("HERMES_SELFCHECK_SENTINEL_VERBOSE", "").strip().lower() in {"1", "true", "yes", "on"}:
        print(json.dumps({"wakeups": [w.__dict__ for w in wakeups]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
