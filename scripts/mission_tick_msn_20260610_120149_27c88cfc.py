#!/usr/bin/env python3
"""Generated Hermes mission tick script for msn_20260610_120149_27c88cfc."""
from __future__ import annotations

import json
import sys

from hermes_cli.missions import MissionStore

MISSION_ID = 'msn_20260610_120149_27c88cfc'


def main() -> int:
    store = MissionStore()
    result = store.tick(MISSION_ID, dry_run=False)
    status = result.get("status")
    if status in {"prompt_created", "dry_run"} and result.get("prompt"):
        print(result["prompt"])
        return 0
    if status == "blocked_on_human":
        print("[Hermes Mission blocked on human decision]")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if status == "budget_exhausted":
        print("[Hermes Mission budget exhausted]")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    # No actionable prompt. Empty stdout keeps agent cron quiet when configured
    # as a watchdog; explicit status is kept in the mission ledger.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
