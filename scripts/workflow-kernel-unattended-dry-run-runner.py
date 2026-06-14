#!/usr/bin/env python3
"""Cron entrypoint for Workflow Kernel unattended dry-run receipts.

No external messages are sent. This wrapper delegates to the Hermes Agent repo
Phase55 dry-run scheduler and prints a compact local-only summary.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path.home() / ".hermes" / "hermes-agent"
RUNNER = REPO / "scripts" / "workflow_unattended_dry_run_scheduler.py"
PYTHON = REPO / "venv" / "bin" / "python"


def main() -> int:
    cmd = [str(PYTHON), str(RUNNER), "--append-ledger", "--write-report", "--json"]
    proc = subprocess.run(cmd, cwd=str(REPO), text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
        return proc.returncode
    data = json.loads(proc.stdout)
    receipt = data.get("latest_receipt", {})
    print(json.dumps({
        "status": data.get("status"),
        "phase": 57,
        "would_send": receipt.get("would_send"),
        "external_side_effects_executed": receipt.get("external_side_effects_executed"),
        "unattended_dispatch_enabled": receipt.get("unattended_dispatch_enabled"),
        "idempotency_key": receipt.get("idempotency_key"),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
