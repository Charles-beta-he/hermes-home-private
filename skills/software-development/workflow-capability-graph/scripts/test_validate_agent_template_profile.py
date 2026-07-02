#!/usr/bin/env python3
"""Tests for validate_agent_template_profile.py.

Run:
  python3 ~/.hermes/skills/software-development/workflow-capability-graph/scripts/test_validate_agent_template_profile.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate_agent_template_profile.py")


def run_validator(payload: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f)
        path = f.name
    try:
        return subprocess.run([sys.executable, str(SCRIPT), path], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    finally:
        Path(path).unlink(missing_ok=True)


def valid_profile() -> dict:
    return {
        "id": "agent-template:reference-reviewer",
        "name": "Reference Reviewer",
        "purpose": "Review external reference repos without runtime authority.",
        "source_refs": ["file:evidence/source-evidence.json"],
        "capability_graph_refs": ["capability:source_reference_intake"],
        "intent_routes": ["reference_repo_absorption"],
        "inputs": {"allowed_sources": ["local_files"], "freshness_rules": ["pin_head"], "privacy_class": "private"},
        "outputs": {"artifact_types": ["report", "graph"], "delivery_targets": "local_only"},
        "authority": {
            "read": "local",
            "local_write": "scoped",
            "external_write": "none",
            "code_execution": "none",
            "credentials": "never_agent_typed",
            "publish_deploy_push": "exact_gate_required",
            "destructive": "exact_gate_required_with_backup",
        },
        "side_effect_matrix": {
            "S0_read_only": ["inspect evidence"],
            "S1_local_write": ["write report"],
            "S2_external_read": [],
            "S3_external_write": [],
            "S4_publish_deploy_push": [],
            "S5_destructive": [],
            "S6_payment_credentials": [],
            "S7_broad_fanout": [],
        },
        "gates": {"preflight": ["source_identity_gate"], "evidence": ["file_line_refs"], "approval": [], "rollback": ["remove local files"], "receipt_readback": ["read report"]},
        "runtime": {"model_policy": "default", "tool_policy": ["file"], "budget_policy": "bounded", "kill_switch": "stop job"},
        "observability": {"receipts": ["local json"], "ledgers": ["SSOT"], "health_checks": ["validator"]},
        "cannot_do": ["external dispatch", "credential entry"],
    }


def test_valid_profile_passes() -> None:
    result = run_validator(valid_profile())
    assert result.returncode == 0, result.stdout
    assert "VALID_AGENT_TEMPLATE_PROFILE" in result.stdout


def test_external_delivery_without_exact_gate_fails() -> None:
    payload = valid_profile()
    payload["outputs"]["delivery_targets"] = "exact_allowlist_required"
    payload["gates"]["receipt_readback"] = []
    result = run_validator(payload)
    assert result.returncode != 0
    assert "receipt_readback" in result.stdout


def test_missing_side_effect_class_fails() -> None:
    payload = valid_profile()
    del payload["side_effect_matrix"]["S6_payment_credentials"]
    result = run_validator(payload)
    assert result.returncode != 0
    assert "S6_payment_credentials" in result.stdout


if __name__ == "__main__":
    tests = [test_valid_profile_passes, test_external_delivery_without_exact_gate_fails, test_missing_side_effect_class_fails]
    failures = []
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failures.append(test.__name__)
    if failures:
        raise SystemExit(1)
    print("VALIDATOR_TESTS_OK")
