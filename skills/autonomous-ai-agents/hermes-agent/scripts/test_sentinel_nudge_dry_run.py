#!/usr/bin/env python3
"""Tests for sentinel_nudge_dry_run.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("sentinel_nudge_dry_run.py")


def packet(tmp: Path) -> dict:
    return {
        "id": "nudge:local-reference-review",
        "source_event": "manual",
        "user_goal": "Produce a local-only dry run receipt.",
        "trigger": {"kind": "manual", "cadence_or_event": "manual test"},
        "scope": {"allowed_inputs": ["local SSOT"], "allowed_outputs": ["local receipt"], "forbidden_outputs": ["external message"]},
        "budget": {"max_runtime": "30s", "max_tool_calls": 3, "max_external_reads": 0},
        "delivery": {"mode": "local_only", "platform": None, "target": None, "payload_class": "receipt"},
        "receipts": {"ledger_path": str(tmp / "ledger.jsonl"), "success_silent": True, "failure_alert": True},
        "rollback": {"pause_command": "noop", "remove_command": "rm local receipt"},
        "readback": {"required_commands": ["read ledger"]},
    }


def run(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f)
        path = f.name
    try:
        return subprocess.run([sys.executable, str(SCRIPT), path], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    finally:
        Path(path).unlink(missing_ok=True)


def test_local_only_writes_receipt() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        result = run(packet(root))
        assert result.returncode == 0, result.stdout
        assert "SENTINEL_NUDGE_DRY_RUN_OK" in result.stdout
        ledger = root / "ledger.jsonl"
        rows = [json.loads(line) for line in ledger.read_text().splitlines()]
        assert rows[-1]["delivery_mode"] == "local_only"
        assert rows[-1]["would_deliver_external"] is False


def test_external_target_required_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = packet(Path(td))
        p["delivery"]["mode"] = "exact_target_required"
        p["delivery"]["target"] = None
        result = run(p)
        assert result.returncode != 0
        assert "target" in result.stdout.lower()


def test_success_silent_required_for_local_only() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = packet(Path(td))
        p["receipts"]["success_silent"] = False
        result = run(p)
        assert result.returncode != 0
        assert "success_silent" in result.stdout


if __name__ == "__main__":
    failures = []
    for test in [test_local_only_writes_receipt, test_external_target_required_fails_closed, test_success_silent_required_for_local_only]:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failures.append(test.__name__)
    if failures:
        raise SystemExit(1)
    print("SENTINEL_DRY_RUN_TESTS_OK")
