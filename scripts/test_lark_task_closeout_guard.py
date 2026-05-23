import importlib.util
import json
import subprocess
import sys
from pathlib import Path

MODULE_PATH = Path.home() / ".hermes" / "scripts" / "lark_task_closeout_guard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("lark_task_closeout_guard", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_local_implementation_regression_must_not_complete_lark_task():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "implementation",
        "local_verification": ["npm run build PASS", "browser-harness local PASS"],
        "commit": "abc1234",
        "remote_build_status": "success",
    })
    assert result["allowed"] is False
    assert result["classification"] == "implementation_sendback_only"
    assert "online_ui_retest_required" in result["blockers"]
    assert result["lark_completed_at_allowed"] is False


def test_implementation_phase_requires_non_main_task_branch():
    mod = load_module()
    main_result = mod.evaluate_closeout_gate({
        "phase": "implementation",
        "current_branch": "main",
        "base_branch": "main",
    })
    assert main_result["lark_completed_at_allowed"] is False
    assert main_result["implementation_branch_gate"]["allowed"] is False
    assert "local_implementation_on_protected_base_branch" in main_result["implementation_branch_gate"]["blockers"]
    assert "fetch_and_checkout_task_branch" in main_result["implementation_branch_gate"]["required_action"]

    feature_result = mod.evaluate_closeout_gate({
        "phase": "implementation",
        "current_branch": "lark-task-loop",
        "base_branch": "main",
    })
    assert feature_result["lark_completed_at_allowed"] is False
    assert feature_result["implementation_branch_gate"]["allowed"] is True
    assert feature_result["implementation_branch_gate"]["blockers"] == []


def test_cli_reports_current_branch_gate_for_implementation_phase():
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--phase",
            "implementation",
            "--current-branch",
            "main",
            "--base-branch",
            "main",
            "--json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["implementation_branch_gate"]["allowed"] is False
    assert "local_implementation_on_protected_base_branch" in payload["implementation_branch_gate"]["blockers"]


def test_online_ui_retest_requires_user_dispatch_and_online_evidence():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "online-ui-retest",
        "local_verification": ["npm run build PASS"],
        "remote_build_status": "success",
        "online_url": "https://uvisa-admin-production.example/users",
        "ui_regression_status": "pass",
    })
    assert result["allowed"] is False
    assert "missing_user_dispatch_evidence" in result["blockers"]
    assert "missing_online_ui_screenshot_or_report" in result["blockers"]


def test_complete_online_ui_retest_allows_lark_completed_at():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "online-ui-retest",
        "user_dispatch_evidence": "user said dispatch online UI retest",
        "remote_build_status": "deployed",
        "online_url": "https://uvisa-admin-production.example/users",
        "online_ui_evidence": ["/tmp/uvisa-admin-online-users-1512x982.png"],
        "ui_regression_status": "pass",
        "lark_final_evidence": "description contains online UI evidence",
    })
    assert result["allowed"] is True
    assert result["classification"] == "final_lark_closeout_allowed"
    assert result["lark_completed_at_allowed"] is True


def test_cli_blocks_local_phase_before_any_writeback():
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--phase",
            "implementation",
            "--local-verification",
            "npm run build PASS",
            "--commit",
            "abc1234",
            "--json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["lark_completed_at_allowed"] is False
    assert "online_ui_retest_required" in payload["blockers"]
