#!/usr/bin/env python3
"""Tests for brain_task_multimodel_loop_runner.py.
Run with: python3 ~/.hermes/scripts/test_brain_task_multimodel_loop_runner.py
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
SCRIPT = HOME / ".hermes" / "scripts" / "brain_task_multimodel_loop_runner.py"


def load_module():
    spec = importlib.util.spec_from_file_location("brain_task_multimodel_loop_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def certified_discussion() -> dict:
    return {
        "status": "certified",
        "models_consulted": ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"],
        "agreement_matrix": {"framing": 0.95, "approach": 0.95, "implementation_order": 0.95},
        "issue_ledger": [{"id": "I-001", "severity": 3, "status": "resolved"}],
        "remaining_risks": [],
        "ratification_votes": [
            {"model": "claude", "vote": "approve", "best_within_constraints": True},
            {"model": "codex", "vote": "approve", "best_within_constraints": True},
            {"model": "deepseek", "vote": "approve", "best_within_constraints": True},
            {"model": "mimo", "vote": "approve", "best_within_constraints": True},
        ],
        "truth_assessment": {"evidence_coverage": 1.0, "unsupported_high_severity_claim_ids": [], "contradicted_high_severity_claim_ids": []},
    }


def test_certified_discussion_stops_loop():
    module = load_module()
    verdict = module.evaluate_discussion(certified_discussion())
    assert verdict["done"] is True, verdict
    assert verdict["next_action"] == "LOOP_DONE", verdict
    assert verdict["blocking_reasons"] == [], verdict


def test_verify_ratification_exposes_explicit_pass_reasons_api():
    module = load_module()
    passed, reasons = module.verify_ratification(certified_discussion())
    assert passed is True
    assert reasons == []


def test_should_continue_inverts_ratification_api():
    module = load_module()
    should_continue, reason = module.should_continue(certified_discussion())
    assert should_continue is False
    assert reason == "all_criteria_met"


def test_amend_vote_continues_loop():
    module = load_module()
    data = certified_discussion()
    data["ratification_votes"][2]["vote"] = "amend"
    verdict = module.evaluate_discussion(data)
    assert verdict["done"] is False, verdict
    assert verdict["next_action"] == "continue_loop", verdict
    assert "non_approve_vote" in verdict["blocking_reasons"], verdict
    should_continue, reason = module.should_continue(data)
    assert should_continue is True
    assert "non_approve_vote" in reason


def test_unresolved_high_severity_issue_blocks_even_if_status_certified():
    module = load_module()
    data = certified_discussion()
    data["issue_ledger"].append({"id": "I-002", "severity": 4, "status": "unresolved"})
    verdict = module.evaluate_discussion(data)
    assert verdict["done"] is False, verdict
    assert "open_high_severity_issue" in verdict["blocking_reasons"], verdict


def test_run_consult_timeout_fails_closed_without_traceback():
    module = load_module()
    original_run = module.subprocess.run
    def fake_run(*args, **kwargs):
        raise module.subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout", 1), output="partial-out", stderr="partial-err")
    module.subprocess.run = fake_run
    try:
        result = module.run_consult(Path("/tmp/state.json"), tier="T3", quorum=4, max_rounds=3, timeout=1)
    finally:
        module.subprocess.run = original_run
    assert result["returncode"] == "timeout", result
    assert result["timed_out"] is True, result
    assert "discussion_result_path" in result, result


def test_build_consult_command_uses_quorum4_discussion_and_keep():
    module = load_module()
    cmd = module.build_consult_run_command(Path("/tmp/state.json"), tier="T3", quorum=4, max_rounds=5, timeout=180)
    joined = " ".join(str(x) for x in cmd)
    assert "consult_models.py" in joined, cmd
    assert "--quorum 4" in joined, cmd
    assert "--discussion" in cmd, cmd
    assert "--keep" in cmd, cmd
    assert "--max-rounds 5" in joined, cmd


def test_cli_fixture_certified_exits_zero_and_writes_state():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        fixture = write_json(root / "discussion_result.json", certified_discussion())
        out = root / "state.json"
        r = subprocess.run([
            sys.executable,
            str(SCRIPT),
            "--discussion-result",
            str(fixture),
            "--round-dir",
            str(root / "rounds"),
            "--state-out",
            str(out),
            "--skip-deterministic",
            "--json",
        ], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr or r.stdout
        payload = json.loads(r.stdout)
        assert payload["status"] == "LOOP_DONE", payload
        assert payload["rounds_used"] == 1, payload
        assert out.exists(), payload


def test_cli_fixture_not_certified_max_rounds_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        data = certified_discussion()
        data["status"] = "not_certified"
        data["issue_ledger"].append({"id": "I-003", "severity": 3, "status": "unresolved"})
        fixture = write_json(root / "discussion_result.json", data)
        r = subprocess.run([
            sys.executable,
            str(SCRIPT),
            "--discussion-result",
            str(fixture),
            "--round-dir",
            str(root / "rounds"),
            "--skip-deterministic",
            "--max-loop-rounds",
            "1",
            "--json",
        ], capture_output=True, text=True)
        assert r.returncode == 3, r.stderr or r.stdout
        payload = json.loads(r.stdout)
        assert payload["status"] == "NOT_CERTIFIED_MAX_ROUNDS", payload
        assert payload["rounds"][0]["verdict"]["done"] is False, payload


if __name__ == "__main__":
    test_certified_discussion_stops_loop()
    test_verify_ratification_exposes_explicit_pass_reasons_api()
    test_should_continue_inverts_ratification_api()
    test_amend_vote_continues_loop()
    test_unresolved_high_severity_issue_blocks_even_if_status_certified()
    test_run_consult_timeout_fails_closed_without_traceback()
    test_build_consult_command_uses_quorum4_discussion_and_keep()
    test_cli_fixture_certified_exits_zero_and_writes_state()
    test_cli_fixture_not_certified_max_rounds_fails_closed()
    print("PASS")
