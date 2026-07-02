#!/usr/bin/env python3
"""Local-only dry-run harness for Sentinel Nudge packets.

Validates packet safety and writes a local receipt. It never sends messages.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

REQUIRED_TOP = ["id", "source_event", "user_goal", "trigger", "scope", "budget", "delivery", "receipts", "rollback", "readback"]


def validate(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_TOP:
        if key not in packet:
            errors.append(f"missing {key}")
    delivery = packet.get("delivery", {}) if isinstance(packet.get("delivery"), dict) else {}
    receipts = packet.get("receipts", {}) if isinstance(packet.get("receipts"), dict) else {}
    rollback = packet.get("rollback", {}) if isinstance(packet.get("rollback"), dict) else {}
    readback = packet.get("readback", {}) if isinstance(packet.get("readback"), dict) else {}
    budget = packet.get("budget", {}) if isinstance(packet.get("budget"), dict) else {}

    mode = delivery.get("mode")
    if mode not in {"local_only", "exact_target_required"}:
        errors.append("delivery.mode must be local_only or exact_target_required")
    if mode == "local_only":
        if delivery.get("platform") is not None or delivery.get("target") is not None:
            errors.append("local_only delivery must not name platform/target")
        if receipts.get("success_silent") is not True:
            errors.append("receipts.success_silent must be true for local_only dry run")
    if mode == "exact_target_required":
        if not delivery.get("platform") or not delivery.get("target"):
            errors.append("exact_target_required delivery requires platform and target")
        if not readback.get("required_commands"):
            errors.append("exact_target_required delivery requires readback.required_commands")

    ledger = receipts.get("ledger_path")
    if not isinstance(ledger, str) or not ledger:
        errors.append("receipts.ledger_path must be non-empty string")
    if receipts.get("failure_alert") is not True:
        errors.append("receipts.failure_alert must be true")
    if not rollback.get("pause_command") or not rollback.get("remove_command"):
        errors.append("rollback.pause_command and rollback.remove_command are required")
    if not isinstance(readback.get("required_commands"), list) or not readback.get("required_commands"):
        errors.append("readback.required_commands must be non-empty list")
    if budget.get("max_external_reads", 0) not in (0, "0") and mode == "local_only":
        errors.append("local_only dry run must not require external reads")
    return errors


def write_receipt(packet: dict[str, Any]) -> Path:
    ledger = Path(packet["receipts"]["ledger_path"]).expanduser()
    ledger.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": int(time.time()),
        "packet_id": packet["id"],
        "source_event": packet.get("source_event"),
        "delivery_mode": packet["delivery"]["mode"],
        "would_deliver_external": packet["delivery"]["mode"] != "local_only",
        "success_silent": packet["receipts"].get("success_silent"),
        "readback_required": packet["readback"].get("required_commands", []),
        "rollback": packet.get("rollback", {}),
        "status": "dry_run_pass",
    }
    with ledger.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return ledger


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: sentinel_nudge_dry_run.py <packet.json>")
        return 2
    try:
        packet = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"SENTINEL_NUDGE_PACKET_INVALID\n- cannot read JSON: {exc}")
        return 1
    if not isinstance(packet, dict):
        print("SENTINEL_NUDGE_PACKET_INVALID\n- root must be object")
        return 1
    errors = validate(packet)
    if errors:
        print("SENTINEL_NUDGE_PACKET_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    ledger = write_receipt(packet)
    print("SENTINEL_NUDGE_DRY_RUN_OK")
    print(json.dumps({"ledger_path": str(ledger), "packet_id": packet["id"], "external_delivery": False}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
