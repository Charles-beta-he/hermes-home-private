#!/usr/bin/env python3
"""One-shot local-only External J-space cron heartbeat smoke."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

receipt_dir = Path.home() / ".hermes" / "workflows" / "jspace" / "cron-heartbeat-receipts"
receipt_dir.mkdir(parents=True, exist_ok=True)
receipt = {
    "schema": "jspace_cron_heartbeat_v0_1",
    "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "scope": "local_no_agent_cron_heartbeat",
    "external_side_effects_executed": False,
    "taskpool_lifecycle_write_executed": False,
    "publish_deploy_push_executed": False,
    "destructive_operation_executed": False,
}
path = receipt_dir / "latest.json"
path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"JSPACE_CRON_HEARTBEAT_RECEIPT {path}")
