#!/usr/bin/env python3
"""Quiet watchdog for UVISA/Lark governance debt.

No output means no alert. Non-empty output is designed for no_agent cron delivery.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

HOME = Path.home()
AUDIT = HOME / ".hermes/scripts/uvisa_lark_governance_audit.py"


def main() -> int:
    raw = subprocess.check_output(["python3", str(AUDIT), "--json", "--redact", "--scope", "uvisa-lark"], text=True)
    data = json.loads(raw)
    issues: list[str] = []
    count = int(data.get("git_boundary", {}).get("sensitive_tracked_count") or 0)
    if count:
        issues.append(f"sensitive tracked/runtime candidates still present: {count}")
    drift = data.get("lark_skill_drift") or []
    hashes = {item.get("sha12") for item in drift if item.get("exists") and item.get("sha12")}
    if len(hashes) > 1:
        issues.append(f"lark skill overlay drift still present: {len(hashes)} distinct hashes")
    duplicates = data.get("image_evidence", {}).get("duplicates") or {}
    if duplicates:
        issues.append(f"unclassified duplicate evidence image groups: {len(duplicates)}")
    if not issues:
        return 0
    print("UVISA/Lark governance watchdog alert:")
    for issue in issues:
        print(f"- {issue}")
    print("Run: python3 ~/.hermes/scripts/uvisa_lark_governance_audit.py --json --redact --scope uvisa-lark > ~/.hermes/tmp/uvisa_lark_governance_audit_latest.json")
    print("Runbook: /Users/charles/.hermes/docs/private/uvisa-lark-governance.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
