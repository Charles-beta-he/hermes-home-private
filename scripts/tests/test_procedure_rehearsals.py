#!/usr/bin/env python3
"""Tests for explicit, local-only procedure rehearsals."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "procedure_rehearsals.py"


def load_module():
    spec = importlib.util.spec_from_file_location("procedure_rehearsals", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_local_delivery_writes_payload_receipt_and_post_write_readback(tmp_path):
    mod = load_module()
    result = mod.rehearse_local_delivery(tmp_path, payload="procedure-canary")

    assert result["ok"] is True
    payload_path = Path(result["payload_path"])
    receipt_path = Path(result["receipt_path"])
    readback_path = Path(result["readback_path"])
    assert payload_path.read_text(encoding="utf-8") == "procedure-canary\n"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    assert receipt["procedure_id"] == "delivery.local.output"
    assert receipt["result"] == "PASS"
    assert receipt["acceptance_atoms"] == {"payload_written": True, "receipt_readback": True}
    assert receipt["negative_assertions"] == {"no_external_send": True}
    assert receipt["side_effects_observed"] == ["local_write"]
    assert readback["receipt_id"] == receipt["receipt_id"]
    assert readback["status"] == "PASS"
    assert receipt["evidence_refs"] == [str(payload_path), str(readback_path)]


def test_local_delivery_refuses_empty_payload(tmp_path):
    mod = load_module()
    try:
        mod.rehearse_local_delivery(tmp_path, payload="")
    except ValueError as exc:
        assert "payload" in str(exc)
    else:
        raise AssertionError("empty payload must fail closed")


def test_experience_ratchet_lifecycle_rehearsal_exercises_all_gates_in_isolation(tmp_path):
    mod = load_module()

    result = mod.rehearse_experience_ratchet_lifecycle(tmp_path)

    assert result["ok"] is True
    receipt_path = Path(result["receipt_path"])
    result_path = Path(result["lifecycle_result_path"])
    readback_path = Path(result["readback_path"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    lifecycle = json.loads(result_path.read_text(encoding="utf-8"))
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    assert receipt["procedure_id"] == "experience.ratchet.lifecycle"
    assert receipt["result"] == "PASS"
    assert receipt["execution_mode"] == "live_e2e"
    assert receipt["acceptance_atoms"] == {
        "promotion_guarded": True,
        "stale_demoted": True,
        "failure_reopened": True,
        "retention_applied": True,
    }
    assert receipt["negative_assertions"] == {
        "no_silent_promotion": True,
        "no_history_erasure": True,
    }
    assert receipt["side_effects_observed"] == ["local_write"]
    assert lifecycle["summary"]["stale_demoted"] == 1
    assert lifecycle["summary"]["failure_reopened"] == 1
    assert lifecycle["summary"]["retention_applied"] == 1
    assert lifecycle["home"].startswith(str(tmp_path / "procedure-rehearsals"))
    assert readback["status"] == "PASS"
    assert readback["isolated_store"] is True
