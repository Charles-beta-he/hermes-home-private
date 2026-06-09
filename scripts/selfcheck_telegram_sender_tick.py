#!/usr/bin/env python3
"""Governed Telegram sender tick for Hermes selfcheck alerts.

Consumes `telegram_delivery_dry_run_verified` records and sends only to the
explicit allowlisted Telegram target. Emits stdout only when a send was attempted
or failed; otherwise stays silent for no-agent cron.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path.home() / ".hermes" / "hermes-agent"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from hermes_cli.env_loader import load_hermes_dotenv

    load_hermes_dotenv()
except Exception:
    pass

from agent.selfcheck_operator import run_telegram_delivery_tick


def main() -> int:
    try:
        receipts = run_telegram_delivery_tick()
    except Exception as exc:
        print(json.dumps({"status": "error", "error": exc.__class__.__name__}, ensure_ascii=False))
        return 1
    if receipts:
        compact = [
            {
                "status": r.get("status"),
                "channel": r.get("channel"),
                "target_id": r.get("target_id"),
                "message_id": r.get("message_id"),
                "error_type": r.get("error_type"),
            }
            for r in receipts
        ]
        print(json.dumps({"status": "attempted", "receipts": compact}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
